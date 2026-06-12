(function () {
  const targetMeta = {
    "Epidermal Growth Factor Receptor": {
      gene: "EGFR",
      disease: "Non-small cell lung cancer",
      area: "Oncology",
    },
    "Janus Kinase 2": {
      gene: "JAK2",
      disease: "Myeloproliferative neoplasms",
      area: "Hematology",
    },
    "Beta-secretase 1": {
      gene: "BACE1",
      disease: "Alzheimer's disease",
      area: "Neuroscience",
    },
    "Tumor Necrosis Factor": {
      gene: "TNF",
      disease: "Autoimmune inflammation",
      area: "Immunology",
    },
    "HIV Integrase": {
      gene: "POL",
      disease: "HIV infection",
      area: "Antiviral",
    },
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function fmt(value, digits = 2) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
    return Number(value).toFixed(digits);
  }

  function show(element) {
    element.classList.remove("hidden");
    element.classList.add("fade-in");
  }

  function hide(element) {
    element.classList.add("hidden");
    element.classList.remove("fade-in");
  }

  function toast(message) {
    const node = document.getElementById("toast");
    node.textContent = message;
    show(node);
    window.clearTimeout(toast.timer);
    toast.timer = window.setTimeout(() => hide(node), 2800);
  }

  function renderTarget(session, molecules) {
    const card = document.getElementById("target-card");
    const meta = targetMeta[session.identified_target_name] || {
      gene: "Target",
      disease: "Curated benchmark target",
      area: "Prototype",
    };
    const confidence = Math.round((session.confidence_score || 0) * 100);
    const toxicCount = molecules.filter((molecule) => molecule.is_toxic).length;
    const filteredCount = molecules.filter((molecule) => molecule.is_filtered).length;

    card.innerHTML = `
      <div>
        <h3>${escapeHtml(session.identified_target_name || "No target matched")}</h3>
        <div class="target-meta">
          <span class="badge">${escapeHtml(meta.gene)}</span>
          <span class="badge">${escapeHtml(meta.area)}</span>
          <span class="badge warn">${escapeHtml(meta.disease)}</span>
        </div>
        <div class="confidence">
          <div class="confidence-row">
            <span>Identification confidence</span>
            <strong>${confidence}%</strong>
          </div>
          <div class="confidence-track">
            <div class="confidence-fill" style="width: ${confidence}%"></div>
          </div>
        </div>
      </div>
      <div class="target-stats">
        <div class="stat-tile">
          <span class="muted">Molecules ranked</span>
          <strong>${molecules.length}</strong>
        </div>
        <div class="stat-tile">
          <span class="muted">Passed filter</span>
          <strong>${session.molecules_passed_filter}</strong>
        </div>
        <div class="stat-tile">
          <span class="muted">Problematic</span>
          <strong>${filteredCount}</strong>
        </div>
        <div class="stat-row">
          <span>Toxic included</span>
          <strong>${toxicCount}</strong>
        </div>
      </div>
    `;
  }

  function renderMolecules(molecules, onSelect) {
    const grid = document.getElementById("molecule-grid");
    if (!molecules.length) {
      grid.innerHTML = `<div class="target-card"><p class="muted">No molecules match the current filter.</p></div>`;
      return;
    }

    grid.innerHTML = molecules
      .map((molecule) => {
        const badgeClass = molecule.is_toxic ? "toxic" : molecule.is_filtered ? "warn" : "safe";
        const badgeText = molecule.is_toxic ? "Toxic" : molecule.is_filtered ? "Problematic" : "Clean";
        return `
          <article class="molecule-card" data-molecule-id="${molecule.id}" tabindex="0">
            <div class="molecule-image">
              <img src="${window.MolGenixAPI.assetUrl(molecule.image_path)}" alt="${escapeHtml(molecule.name)} structure" loading="lazy" />
            </div>
            <h3>${escapeHtml(molecule.name)}</h3>
            <div class="rank-line">
              <span>Rank ${molecule.rank ?? "n/a"}</span>
              <span>${escapeHtml(molecule.target_name)}</span>
            </div>
            <div class="metric-grid">
              <div class="metric"><span>Docking</span><strong>${fmt(molecule.docking_score, 1)}</strong></div>
              <div class="metric"><span>QED</span><strong>${fmt(molecule.qed_score, 3)}</strong></div>
              <div class="metric"><span>LogP</span><strong>${fmt(molecule.logp, 1)}</strong></div>
              <div class="metric"><span>TPSA</span><strong>${fmt(molecule.tpsa, 1)}</strong></div>
            </div>
            <div class="target-meta">
              <span class="badge ${badgeClass}">${badgeText}</span>
              <span class="badge">${molecule.lipinski_pass ? "Lipinski pass" : "Lipinski fail"}</span>
            </div>
            <div class="admet-dots" aria-label="ADMET indicators">
              ${molecule.admet.map((metric) => `<span class="dot ${metric.status.toLowerCase()}" title="${escapeHtml(metric.label)}: ${escapeHtml(metric.status)}"></span>`).join("")}
            </div>
          </article>
        `;
      })
      .join("");

    grid.querySelectorAll(".molecule-card").forEach((card) => {
      const id = Number(card.dataset.moleculeId);
      card.addEventListener("click", () => onSelect(id));
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(id);
        }
      });
    });
  }

  function renderMoleculeModal(molecule) {
    const modal = document.getElementById("molecule-modal");
    const backdrop = document.getElementById("modal-backdrop");
    const content = document.getElementById("modal-content");
    const docking = molecule.docking_detail;

    content.innerHTML = `
      <div class="modal-body">
        <div>
          <img src="${window.MolGenixAPI.assetUrl(molecule.image_path)}" alt="${escapeHtml(molecule.name)} structure" />
          <div class="smiles-box">
            <code>${escapeHtml(molecule.smiles)}</code>
            <button class="copy-button" type="button" data-copy-smiles>Copy</button>
          </div>
        </div>
        <div>
          <p class="eyebrow">${escapeHtml(molecule.target_name)}</p>
          <h2 id="modal-title">${escapeHtml(molecule.name)}</h2>
          <div class="target-meta">
            <span class="badge ${molecule.is_toxic ? "toxic" : molecule.is_filtered ? "warn" : "safe"}">${molecule.is_toxic ? "Toxic" : molecule.is_filtered ? "Problematic" : "Clean"}</span>
            <span class="badge">Rank ${molecule.rank ?? "n/a"}</span>
            <span class="badge">QED ${fmt(molecule.qed_score, 3)}</span>
          </div>
          <div class="table-shell">
            <table class="property-table">
              <tbody>
                <tr><td>Docking score</td><td>${fmt(molecule.docking_score, 1)} kcal/mol</td></tr>
                <tr><td>Molecular weight</td><td>${fmt(molecule.molecular_weight, 1)}</td></tr>
                <tr><td>LogP</td><td>${fmt(molecule.logp, 1)}</td></tr>
                <tr><td>H-bond donors</td><td>${molecule.h_bond_donors}</td></tr>
                <tr><td>H-bond acceptors</td><td>${molecule.h_bond_acceptors}</td></tr>
                <tr><td>Rotatable bonds</td><td>${molecule.rotatable_bonds}</td></tr>
                <tr><td>Filter reason</td><td>${escapeHtml(molecule.filter_reason || "None")}</td></tr>
              </tbody>
            </table>
          </div>
          <h3>ADMET</h3>
          <div class="table-shell">
            <table class="admet-table">
              <thead><tr><th>Metric</th><th>Value</th><th>Signal</th></tr></thead>
              <tbody>
                ${molecule.admet.map((metric) => `<tr><td>${escapeHtml(metric.label)}</td><td>${escapeHtml(metric.value)}</td><td>${escapeHtml(metric.status)}</td></tr>`).join("")}
              </tbody>
            </table>
          </div>
          ${docking ? `
            <h3>Docking interactions</h3>
            <div class="table-shell">
              <table class="property-table">
                <tbody>
                  <tr><td>Binding pocket</td><td>${escapeHtml(docking.binding_pocket)}</td></tr>
                  <tr><td>Key residues</td><td>${escapeHtml(docking.key_residues.join(", "))}</td></tr>
                  <tr><td>Interactions</td><td>${escapeHtml(docking.interaction_types.join(", "))}</td></tr>
                  <tr><td>Affinity</td><td>${escapeHtml(docking.affinity)}</td></tr>
                  <tr><td>RMSD</td><td>${fmt(docking.rmsd, 2)}</td></tr>
                </tbody>
              </table>
            </div>
          ` : `<p class="muted">Detailed docking interaction fields are shown for rank 1 molecules.</p>`}
        </div>
      </div>
    `;

    content.querySelector("[data-copy-smiles]").addEventListener("click", async () => {
      await navigator.clipboard.writeText(molecule.smiles);
      toast("SMILES copied");
    });

    show(backdrop);
    modal.showModal();
  }

  function closeModal() {
    const modal = document.getElementById("molecule-modal");
    const backdrop = document.getElementById("modal-backdrop");
    if (modal.open) modal.close();
    hide(backdrop);
  }

  function renderReport(report) {
    const preview = document.getElementById("report-preview");
    const download = document.getElementById("download-report-button");
    const paragraphs = report.summary.split("\n\n").filter(Boolean);
    preview.innerHTML = `
      <h3>${escapeHtml(report.title)}</h3>
      <div class="target-meta">
        <span class="badge safe">Druggability ${fmt(report.druggability_score, 1)} / 100</span>
      </div>
      ${paragraphs.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}
    `;
    download.href = `${window.MolGenixAPI.baseUrl}${report.download_url}`;
    show(preview);
    show(download);
  }

  window.MolGenixUI = {
    show,
    hide,
    toast,
    renderTarget,
    renderMolecules,
    renderMoleculeModal,
    closeModal,
    renderReport,
  };
})();
