/**
 * SpendWise - Transactions Controller
 * Complete CRUD, sorting, filtering, searching, pagination, and modal forms.
 */

const Transactions = {
  state: {
    page: 1,
    pageSize: 10,
    totalPages: 1,
    type: "",
    category: "",
    fromDate: "",
    toDate: "",
    search: "",
    sortBy: "date",
    sortOrder: "desc",
    editingId: null,
    searchDebounceTimer: null
  },

  async load() {
    this.populateCategoryFilter();
    this.setupListeners();
    await this.fetchTransactions();
  },

  setupListeners() {
    // Only bind once
    if (this._listenersBound) return;
    this._listenersBound = true;

    // Search input with debounce
    const searchInput = document.getElementById("txSearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        clearTimeout(this.state.searchDebounceTimer);
        this.state.searchDebounceTimer = setTimeout(() => {
          this.state.search = e.target.value.trim();
          this.state.page = 1;
          this.fetchTransactions();
        }, 300);
      });
    }

    // Filters
    const typeFilter = document.getElementById("txTypeFilter");
    if (typeFilter) {
      typeFilter.addEventListener("change", (e) => {
        this.state.type = e.target.value;
        this.state.page = 1;
        this.populateCategoryFilter();
        this.fetchTransactions();
      });
    }

    const catFilter = document.getElementById("txCategoryFilter");
    if (catFilter) {
      catFilter.addEventListener("change", (e) => {
        this.state.category = e.target.value;
        this.state.page = 1;
        this.fetchTransactions();
      });
    }

    const fromDateInput = document.getElementById("txFromDate");
    if (fromDateInput) {
      fromDateInput.addEventListener("change", (e) => {
        this.state.fromDate = e.target.value;
        this.state.page = 1;
        this.fetchTransactions();
      });
    }

    const toDateInput = document.getElementById("txToDate");
    if (toDateInput) {
      toDateInput.addEventListener("change", (e) => {
        this.state.toDate = e.target.value;
        this.state.page = 1;
        this.fetchTransactions();
      });
    }

    const sortSelect = document.getElementById("txSortSelect");
    if (sortSelect) {
      sortSelect.addEventListener("change", (e) => {
        const [field, order] = e.target.value.split(":");
        this.state.sortBy = field;
        this.state.sortOrder = order;
        this.fetchTransactions();
      });
    }

    const pageSizeSelect = document.getElementById("txPageSizeSelect");
    if (pageSizeSelect) {
      pageSizeSelect.addEventListener("change", (e) => {
        this.state.pageSize = parseInt(e.target.value, 10);
        this.state.page = 1;
        this.fetchTransactions();
      });
    }

    // Modal type switcher updates categories dropdown
    const modalTypeSelect = document.getElementById("txFormType");
    if (modalTypeSelect) {
      modalTypeSelect.addEventListener("change", () => {
        this.updateModalCategoryDropdown();
      });
    }

    // Form submit
    const txForm = document.getElementById("transactionForm");
    if (txForm) {
      txForm.addEventListener("submit", (e) => this.handleFormSubmit(e));
    }
  },

  populateCategoryFilter() {
    const catSelect = document.getElementById("txCategoryFilter");
    if (!catSelect) return;

    const currentVal = this.state.category;
    let list = [];
    if (this.state.type === "income") {
      list = App.state.categories.income || [];
    } else if (this.state.type === "expense") {
      list = App.state.categories.expense || [];
    } else {
      list = [
        ...(App.state.categories.expense || []),
        ...(App.state.categories.income || [])
      ];
      // Deduplicate
      list = [...new Set(list)];
    }

    catSelect.innerHTML = `<option value="">All Categories</option>` +
      list.map(c => `<option value="${App.escapeHtml(c)}" ${c === currentVal ? 'selected' : ''}>${App.escapeHtml(c)}</option>`).join("");
  },

  updateModalCategoryDropdown(selectedCategory = "") {
    const typeSelect = document.getElementById("txFormType");
    const catSelect = document.getElementById("txFormCategory");
    if (!typeSelect || !catSelect) return;

    const type = typeSelect.value;
    const categories = (type === "income") 
      ? App.state.categories.income 
      : App.state.categories.expense;

    catSelect.innerHTML = `<option value="" disabled selected>Select Category</option>` +
      categories.map(c => `<option value="${App.escapeHtml(c)}" ${c === selectedCategory ? 'selected' : ''}>${App.escapeHtml(c)}</option>`).join("");
  },

  async fetchTransactions() {
    const tbody = document.getElementById("transactionsTableBody");
    const emptyState = document.getElementById("transactionsEmptyState");
    const tableContainer = document.getElementById("transactionsTableContainer");
    if (!tbody) return;

    try {
      const data = await API.getTransactions({
        page: this.state.page,
        page_size: this.state.pageSize,
        type: this.state.type,
        category: this.state.category,
        from_date: this.state.fromDate,
        to_date: this.state.toDate,
        search: this.state.search,
        sort_by: this.state.sortBy,
        sort_order: this.state.sortOrder
      });

      this.state.totalPages = data.total_pages;

      if (data.items.length === 0) {
        tbody.innerHTML = "";
        if (emptyState) emptyState.style.display = "flex";
        if (tableContainer) tableContainer.style.display = "none";
        this.renderPagination(data);
        return;
      }

      if (emptyState) emptyState.style.display = "none";
      if (tableContainer) tableContainer.style.display = "block";

      tbody.innerHTML = data.items.map(t => {
        const isIncome = t.type === "income";
        const badgeClass = isIncome ? "badge-income" : "badge-expense";
        const sign = isIncome ? "+" : "-";

        return `
          <tr>
            <td><strong>${t.date}</strong></td>
            <td>
              <div style="font-weight:600; color:var(--text-primary);">${App.escapeHtml(t.description)}</div>
              ${t.notes ? `<div style="font-size:0.8rem; color:var(--text-muted);">${App.escapeHtml(t.notes)}</div>` : ''}
            </td>
            <td><span class="badge ${badgeClass}">${App.escapeHtml(t.category)}</span></td>
            <td><span style="font-size:0.85rem; color:var(--text-secondary);">${App.escapeHtml(t.payment_method || "—")}</span></td>
            <td style="font-weight:700; color:${isIncome ? 'var(--income-color)' : 'var(--expense-color)'};">
              ${sign}${App.formatCurrency(t.amount)}
            </td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn-icon" title="Edit" onclick="Transactions.openEditModal(${t.id})">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
                <button class="btn-icon" title="Delete" style="color:var(--expense-color);" onclick="Transactions.confirmDelete(${t.id}, '${App.escapeHtml(t.description)}')">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

      this.renderPagination(data);
    } catch (err) {
      App.showToast(`Error fetching transactions: ${err.message}`, "error");
    }
  },

  renderPagination(data) {
    const pageInfo = document.getElementById("txPageInfo");
    const prevBtn = document.getElementById("txPrevPageBtn");
    const nextBtn = document.getElementById("txNextPageBtn");

    if (pageInfo) {
      const start = data.total === 0 ? 0 : (data.page - 1) * data.page_size + 1;
      const end = Math.min(data.page * data.page_size, data.total);
      pageInfo.textContent = `Showing ${start}-${end} of ${data.total} entries (Page ${data.page} of ${data.total_pages})`;
    }

    if (prevBtn) prevBtn.disabled = data.page <= 1;
    if (nextBtn) nextBtn.disabled = data.page >= data.total_pages;
  },

  changePage(delta) {
    const newPage = this.state.page + delta;
    if (newPage >= 1 && newPage <= this.state.totalPages) {
      this.state.page = newPage;
      this.fetchTransactions();
    }
  },

  // Modal Handling
  openAddModal() {
    this.state.editingId = null;
    const titleEl = document.getElementById("txModalTitle");
    const form = document.getElementById("transactionForm");
    if (titleEl) titleEl.textContent = "Add New Transaction";
    if (form) form.reset();

    // Default values
    const dateInput = document.getElementById("txFormDate");
    if (dateInput) dateInput.value = new Date().toISOString().slice(0, 10);

    const typeSelect = document.getElementById("txFormType");
    if (typeSelect) typeSelect.value = "expense";

    this.updateModalCategoryDropdown();
    this.populatePaymentMethods();

    const errorDiv = document.getElementById("txFormError");
    if (errorDiv) errorDiv.style.display = "none";

    const modal = document.getElementById("transactionModal");
    if (modal) modal.classList.add("active");
  },

  async openEditModal(id) {
    this.state.editingId = id;
    const titleEl = document.getElementById("txModalTitle");
    if (titleEl) titleEl.textContent = "Edit Transaction";

    try {
      const tx = await API.getTransaction(id);

      const typeSelect = document.getElementById("txFormType");
      if (typeSelect) typeSelect.value = tx.type;

      this.updateModalCategoryDropdown(tx.category);
      this.populatePaymentMethods(tx.payment_method);

      document.getElementById("txFormAmount").value = tx.amount;
      document.getElementById("txFormDescription").value = tx.description;
      document.getElementById("txFormDate").value = tx.date;
      document.getElementById("txFormNotes").value = tx.notes || "";

      const errorDiv = document.getElementById("txFormError");
      if (errorDiv) errorDiv.style.display = "none";

      const modal = document.getElementById("transactionModal");
      if (modal) modal.classList.add("active");
    } catch (err) {
      App.showToast(`Failed to load transaction: ${err.message}`, "error");
    }
  },

  populatePaymentMethods(selected = "") {
    const pmSelect = document.getElementById("txFormPaymentMethod");
    if (!pmSelect) return;
    const methods = App.state.categories.payment_methods || [];
    pmSelect.innerHTML = `<option value="">Select Payment Method (Optional)</option>` +
      methods.map(m => `<option value="${App.escapeHtml(m)}" ${m === selected ? 'selected' : ''}>${App.escapeHtml(m)}</option>`).join("");
  },

  async handleFormSubmit(e) {
    e.preventDefault();
    const errorDiv = document.getElementById("txFormError");
    if (errorDiv) errorDiv.style.display = "none";

    const amount = parseFloat(document.getElementById("txFormAmount").value);
    const type = document.getElementById("txFormType").value;
    const category = document.getElementById("txFormCategory").value;
    const description = document.getElementById("txFormDescription").value.trim();
    const date = document.getElementById("txFormDate").value;
    const paymentMethod = document.getElementById("txFormPaymentMethod").value || null;
    const notes = document.getElementById("txFormNotes").value.trim() || null;

    if (isNaN(amount) || amount <= 0) {
      this.showFormError("Amount must be a positive number greater than 0");
      return;
    }
    if (!category) {
      this.showFormError("Please select a category");
      return;
    }
    if (!description) {
      this.showFormError("Please provide a description");
      return;
    }
    if (!date) {
      this.showFormError("Please select a date");
      return;
    }

    const payload = {
      amount,
      type,
      category,
      description,
      date,
      payment_method: paymentMethod,
      notes
    };

    try {
      if (this.state.editingId) {
        await API.updateTransaction(this.state.editingId, payload);
        App.showToast("Transaction updated successfully!", "success");
      } else {
        await API.createTransaction(payload);
        App.showToast("Transaction added successfully!", "success");
      }
      App.closeModal("transactionModal");
      await this.fetchTransactions();
      // Also update dashboard if user returns
      if (typeof Dashboard !== "undefined") Dashboard.load();
    } catch (err) {
      this.showFormError(err.message);
    }
  },

  showFormError(msg) {
    const errorDiv = document.getElementById("txFormError");
    if (errorDiv) {
      errorDiv.textContent = msg;
      errorDiv.style.display = "block";
    }
  },

  confirmDelete(id, description) {
    App.showConfirm(
      "Delete Transaction",
      `Are you sure you want to delete "${description}"? This action cannot be undone.`,
      async () => {
        try {
          await API.deleteTransaction(id);
          App.showToast("Transaction deleted successfully.", "success");
          await this.fetchTransactions();
          if (typeof Dashboard !== "undefined") Dashboard.load();
        } catch (err) {
          App.showToast(`Delete failed: ${err.message}`, "error");
        }
      }
    );
  }
};
