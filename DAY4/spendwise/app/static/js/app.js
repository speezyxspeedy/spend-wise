/**
 * SpendWise - Core Application Logic
 * Navigation, state coordination, notifications, theme toggling, and helpers.
 */

const App = {
  state: {
    currentMonth: new Date().toISOString().slice(0, 7), // YYYY-MM
    activeTab: "dashboard",
    theme: localStorage.getItem("spendwise_theme") || "dark",
    categories: { expense: [], income: [], payment_methods: [] }
  },

  init() {
    this.applyTheme(this.state.theme);
    this.setupNavigation();
    this.setupMonthPicker();
    this.setupThemeToggle();
    this.setupConfirmationModal();
    this.loadCategories();

    // Initial view load
    this.switchTab("dashboard");
  },

  // Theme Management
  applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("spendwise_theme", theme);
    this.state.theme = theme;

    const icon = document.getElementById("themeIcon");
    if (icon) {
      icon.innerHTML = theme === "dark" 
        ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`
        : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    }
  },

  setupThemeToggle() {
    const toggleBtn = document.getElementById("themeToggleBtn");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        const newTheme = this.state.theme === "dark" ? "light" : "dark";
        this.applyTheme(newTheme);
        // Refresh charts on theme change to adjust colors
        if (typeof Dashboard !== "undefined" && this.state.activeTab === "dashboard") {
          Dashboard.load();
        } else if (typeof Analytics !== "undefined" && this.state.activeTab === "analytics") {
          Analytics.load();
        }
      });
    }
  },

  // Navigation / Tabs
  setupNavigation() {
    const navButtons = document.querySelectorAll(".nav-item button");
    navButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        if (tab) this.switchTab(tab);
      });
    });

    // Mobile menu toggle
    const mobileBtn = document.getElementById("mobileMenuBtn");
    const sidebar = document.querySelector(".sidebar");
    if (mobileBtn && sidebar) {
      mobileBtn.addEventListener("click", () => {
        sidebar.classList.toggle("mobile-open");
      });
    }
  },

  switchTab(tabName) {
    this.state.activeTab = tabName;

    // Update sidebar active class
    document.querySelectorAll(".nav-item").forEach(item => {
      item.classList.toggle("active", item.querySelector(`button[data-tab="${tabName}"]`) !== null);
    });

    // Close mobile menu if open
    const sidebar = document.querySelector(".sidebar");
    if (sidebar) sidebar.classList.remove("mobile-open");

    // Update view panes
    document.querySelectorAll(".tab-pane").forEach(pane => {
      pane.classList.remove("active");
    });
    const activePane = document.getElementById(`tab-${tabName}`);
    if (activePane) activePane.classList.add("active");

    // Update Header Title
    const titles = {
      dashboard: "Financial Overview",
      transactions: "Transactions Management",
      budgets: "Monthly Budgets & Targets",
      analytics: "Reports & Financial Insights"
    };
    const titleEl = document.getElementById("pageTitle");
    if (titleEl) titleEl.textContent = titles[tabName] || "SpendWise";

    // Trigger tab specific controller
    if (tabName === "dashboard" && typeof Dashboard !== "undefined") {
      Dashboard.load();
    } else if (tabName === "transactions" && typeof Transactions !== "undefined") {
      Transactions.load();
    } else if (tabName === "budgets" && typeof Budgets !== "undefined") {
      Budgets.load();
    } else if (tabName === "analytics" && typeof Analytics !== "undefined") {
      Analytics.load();
    }
  },

  // Month Picker
  setupMonthPicker() {
    const picker = document.getElementById("globalMonthPicker");
    if (picker) {
      picker.value = this.state.currentMonth;
      picker.addEventListener("change", (e) => {
        if (e.target.value) {
          this.state.currentMonth = e.target.value;
          this.refreshCurrentTab();
        }
      });
    }
  },

  refreshCurrentTab() {
    if (this.state.activeTab === "dashboard" && typeof Dashboard !== "undefined") {
      Dashboard.load();
    } else if (this.state.activeTab === "budgets" && typeof Budgets !== "undefined") {
      Budgets.load();
    } else if (this.state.activeTab === "transactions" && typeof Transactions !== "undefined") {
      Transactions.load();
    }
  },

  // Pre-fetch categories
  async loadCategories() {
    try {
      this.state.categories = await API.getCategories();
    } catch (err) {
      console.warn("Could not load categories from server:", err);
    }
  },

  // Toast Notifications
  showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "❌";
    if (type === "warning") icon = "⚠️";

    toast.innerHTML = `<span>${icon}</span><span style="flex:1;">${this.escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  },

  // Confirmation Modal
  confirmCallback: null,
  setupConfirmationModal() {
    const confirmBtn = document.getElementById("confirmActionBtn");
    const cancelBtn = document.getElementById("cancelConfirmBtn");
    const modal = document.getElementById("confirmModal");

    if (confirmBtn) {
      confirmBtn.addEventListener("click", () => {
        if (this.confirmCallback) this.confirmCallback();
        this.closeModal("confirmModal");
      });
    }
    if (cancelBtn) {
      cancelBtn.addEventListener("click", () => this.closeModal("confirmModal"));
    }
  },

  showConfirm(title, message, onConfirm) {
    const modal = document.getElementById("confirmModal");
    const titleEl = document.getElementById("confirmTitle");
    const msgEl = document.getElementById("confirmMessage");

    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message;
    this.confirmCallback = onConfirm;

    if (modal) modal.classList.add("active");
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
  },

  // Helpers
  formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return "₹0.00";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  },

  escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
};

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
