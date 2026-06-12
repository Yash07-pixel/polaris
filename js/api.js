(function () {
  const API_BASE_URL = window.MOLGENIX_API_BASE_URL || "http://127.0.0.1:8000";

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      try {
        const payload = await response.json();
        message = payload.detail || message;
      } catch (error) {
        // Keep the generic message when a response is not JSON.
      }
      throw new Error(message);
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return response;
  }

  window.MolGenixAPI = {
    baseUrl: API_BASE_URL,
    assetUrl(path) {
      if (!path) return "";
      if (/^https?:\/\//i.test(path)) return path;
      return `${API_BASE_URL}/${path.replace(/^\/+/, "")}`;
    },
    createSession(query) {
      return request("/api/v1/sessions/", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
    },
    getSessionMolecules(sessionId, options = {}) {
      const params = new URLSearchParams();
      params.set("sort", options.sort || "rank");
      if (options.lipinskiOnly) params.set("lipinski_only", "true");
      return request(`/api/v1/molecules/session/${sessionId}?${params.toString()}`);
    },
    getMolecule(id) {
      return request(`/api/v1/molecules/${id}`);
    },
    generateReport(sessionId) {
      return request("/api/v1/reports/generate", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId }),
      });
    },
  };
})();
