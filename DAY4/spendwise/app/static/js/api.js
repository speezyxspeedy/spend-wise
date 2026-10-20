/**
 * SpendWise API Client Wrapper
 * Handles communication with the FastAPI backend, error extraction, and responses.
 */

const API = {
  baseUrl: "",

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultHeaders = {
      "Content-Type": "application/json",
      "Accept": "application/json"
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, config);

      // Handle non-JSON responses (like CSV downloads)
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("text/csv")) {
        if (!response.ok) throw new Error("Failed to export CSV");
        return await response.blob();
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        let errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
        if (Array.isArray(data.detail)) {
          errorMsg = data.detail.map(d => `${d.loc?.join(".")}: ${d.msg}`).join(", ");
        }
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Health
  checkHealth() {
    return this.request("/api/health");
  },

  // Categories & payment methods
  getCategories() {
    return this.request("/api/categories");
  },

  // Dashboard
  getDashboard(month) {
    const query = month ? `?month=${encodeURIComponent(month)}` : "";
    return this.request(`/api/dashboard${query}`);
  },

  // Transactions
  getTransactions(params = {}) {
    const searchParams = new URLSearchParams();
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
        searchParams.append(key, params[key]);
      }
    });
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request(`/api/transactions${query}`);
  },

  getTransaction(id) {
    return this.request(`/api/transactions/${id}`);
  },

  createTransaction(payload) {
    return this.request("/api/transactions", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateTransaction(id, payload) {
    return this.request(`/api/transactions/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },

  deleteTransaction(id) {
    return this.request(`/api/transactions/${id}`, {
      method: "DELETE"
    });
  },

  // Budgets
  getBudgets(month) {
    const query = month ? `?month=${encodeURIComponent(month)}` : "";
    return this.request(`/api/budgets${query}`);
  },

  createBudget(payload) {
    return this.request("/api/budgets", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateBudget(id, payload) {
    return this.request(`/api/budgets/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },

  deleteBudget(id) {
    return this.request(`/api/budgets/${id}`, {
      method: "DELETE"
    });
  },

  // Analytics
  getAnalytics(fromDate, toDate) {
    const searchParams = new URLSearchParams();
    if (fromDate) searchParams.append("from_date", fromDate);
    if (toDate) searchParams.append("to_date", toDate);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request(`/api/analytics${query}`);
  },

  // CSV Export URL builder
  getExportUrl(params = {}) {
    const searchParams = new URLSearchParams();
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
        searchParams.append(key, params[key]);
      }
    });
    return `/api/export/csv?${searchParams.toString()}`;
  }
};
