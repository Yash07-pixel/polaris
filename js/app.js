(function () {
  const state = {
    session: null,
    molecules: [],
    sort: "rank",
    lipinskiOnly: false,
  };

  const elements = {
    form: document.getElementById("query-form"),
    input: document.getElementById("query-input"),
    runButton: document.getElementById("run-button"),
    processing: document.getElementById("processing-section"),
    targetSection: document.getElementById("target-section"),
    moleculesSection: document.getElementById("molecules-section"),
    reportSection: document.getElementById("report-section"),
    sortSelect: document.getElementById("sort-select"),
    lipinskiToggle: document.getElementById("lipinski-toggle"),
    reportButton: document.getElementById("generate-report-button"),
    modalClose: document.getElementById("modal-close"),
    modalBackdrop: document.getElementById("modal-backdrop"),
  };

  function setLoading(isLoading) {
    elements.runButton.disabled = isLoading;
    elements.runButton.classList.toggle("is-loading", isLoading);
    elements.runButton.lastChild.textContent = isLoading ? " Analyzing" : " Run discovery";
  }

  async function runWorkflow(query) {
    setLoading(true);
    MolGenixUI.show(elements.processing);
    MolGenixUI.hide(elements.targetSection);
    MolGenixUI.hide(elements.moleculesSection);
    MolGenixUI.hide(elements.reportSection);

    try {
      await wait(700);
      const session = await MolGenixAPI.createSession(query);
      state.session = session;

      if (session.status !== "COMPLETE") {
        throw new Error(session.failure_reason || "No predefined demo target matched this query.");
      }

      await loadMolecules();
      MolGenixUI.renderTarget(state.session, state.molecules);
      MolGenixUI.show(elements.targetSection);
      MolGenixUI.show(elements.moleculesSection);
      MolGenixUI.show(elements.reportSection);
      elements.targetSection.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      MolGenixUI.toast(error.message);
    } finally {
      setLoading(false);
      MolGenixUI.hide(elements.processing);
    }
  }

  async function loadMolecules() {
    if (!state.session) return;
    state.molecules = await MolGenixAPI.getSessionMolecules(state.session.id, {
      sort: state.sort,
      lipinskiOnly: state.lipinskiOnly,
    });
    MolGenixUI.renderMolecules(state.molecules, openMolecule);
  }

  async function openMolecule(id) {
    try {
      const molecule = await MolGenixAPI.getMolecule(id);
      MolGenixUI.renderMoleculeModal(molecule);
    } catch (error) {
      MolGenixUI.toast(error.message);
    }
  }

  async function generateReport() {
    if (!state.session) return;
    elements.reportButton.disabled = true;
    elements.reportButton.textContent = "Generating...";
    try {
      const report = await MolGenixAPI.generateReport(state.session.id);
      MolGenixUI.renderReport(report);
      MolGenixUI.toast("Report ready");
    } catch (error) {
      MolGenixUI.toast(error.message);
    } finally {
      elements.reportButton.disabled = false;
      elements.reportButton.textContent = "Generate report";
    }
  }

  function wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  elements.form.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = elements.input.value.trim();
    if (!query) {
      MolGenixUI.toast("Enter a biomedical query");
      elements.input.focus();
      return;
    }
    runWorkflow(query);
  });

  document.querySelectorAll("[data-query]").forEach((button) => {
    button.addEventListener("click", () => {
      elements.input.value = button.dataset.query || "";
      elements.input.focus();
    });
  });

  elements.sortSelect.addEventListener("change", async () => {
    state.sort = elements.sortSelect.value;
    await loadMolecules();
  });

  elements.lipinskiToggle.addEventListener("change", async () => {
    state.lipinskiOnly = elements.lipinskiToggle.checked;
    await loadMolecules();
  });

  elements.reportButton.addEventListener("click", generateReport);
  elements.modalClose.addEventListener("click", MolGenixUI.closeModal);
  elements.modalBackdrop.addEventListener("click", MolGenixUI.closeModal);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      MolGenixUI.closeModal();
    }
  });
})();
