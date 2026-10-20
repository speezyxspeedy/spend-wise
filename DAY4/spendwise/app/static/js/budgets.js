/**
 * SpendWise - Budgets Controller
 * Overall and category-specific budget tracking, threshold alerts, and progress bars.
 */

const Budgets = {
  state: {
    editingId: null,
    budgets: []
  },

  async load() {
    this.setupListeners();
    await this.fetchBudgets();
  },

  setupListeners() {
    if (this._listenersBound) return;
    this._listenersBound = true;

    // Toggle category dropdown based on is_overall
    const isOverallRadio = document.getElementById("budgetTypeOverall");
    const isCategoryRadio = document.getElementById("budgetTypeCategory");
    const catGroup = document.getElementById("budgetCategoryGroup");

    if (isOverallRadio && isCategoryRadio && catGroup) {
      isOverallRadio.addEventListener("change", () => {
        catGroup.style.display = isOverallRadio.checked ? "none" : "block";
      });
      isCategoryRadio.addEventListener("change", () => {
        catGroup.style.display = isCategoryRadio.checked ? "block" : "none";
      });
    }

    const form = document.getElementById("budgetForm");
    if (form) {
      form.addEventListener("submit", (e) => this.handleFormSubmit(e));
    }
  },

  async fetchBudgets() {
    const month = App.state.currentMonth;
    const container = document.getElementById("budgetsListContainer");
    const emptyState = document.getElementById("budgetsEmptyState");
    const overallCard = document.getElementById("overallBudgetCardContainer");
    if (!container) return;

    try {
      const budgets = await API.getBudgets(month);
      this.state.budgets = budgets;

      const overall = budgets.find(b => b.is_overall);
      const categoryBudgets = budgets.filter(b => !b.is_overall);

      // Render Overall Budget Card
      this.renderOverallBudget(overall);

      if (categoryBudgets.length === 0 && !overall) {
        container.innerHTML = "";
        if (emptyState) emptyState.style.display = "flex";
        return;
      }

      if (emptyState) emptyState.style.display = "none";

      // Render Category Budgets
      container.innerHTML = categoryBudgets.map(b => this.createBudgetCardHtml(b)).join("");

    } catch (err) {
      App.showToast(`Error fetching budgets: ${err.message}`, "error");
    }
  },

  renderOverallBudget(overall) {
    const container = document.getElementById("overallBudgetCardContainer");
    if (!container) return;

    if (!overall) {
      container.innerHTML = `
        <div class="budget-card" style="border: 2px dashed var(--border-color); background: transparent; text-align: center; padding: 32px 20px;">
          <h4 style="font-size: 1.1rem; margin-bottom: 6px;">No Overall Monthly Budget Set</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px;">
            Set a monthly spending limit for ${App.state.currentMonth} to track your total spending and get alerts.
          </p>
          <button class="btn btn-primary" onclick="Budgets.openAddModal(true)">
            + Set Overall Budget
          </button>
        </div>
      `;
      return;
    }

    const pct = Math.min(overall.usage_percentage, 100);
    const badgeStatus = overall.warning_level;
    const badgeText = badgeStatus === "exceeded" 
      ? "Limit Exceeded" 
      : badgeStatus === "warning" 
      ? "Warning (≥80%)" 
      : "Healthy";

    container.innerHTML = `
      <div class="budget-card" style="border-left: 4px solid var(--accent-primary);">
        <div class="budget-card-header">
          <div class="budget-card-title">
            <span style="font-size:1.3rem;">🎯</span>
            <div>
              <div>Overall Monthly Budget (${overall.month})</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">Total target for all combined expenses</div>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="badge badge-${badgeStatus}">${badgeText}</span>
            <button class="btn-icon" title="Edit" onclick="Budgets.openEditModal(${overall.id}, ${overall.amount})">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="btn-icon" title="Delete" style="color:var(--expense-color);" onclick="Budgets.confirmDelete(${overall.id}, 'Overall Monthly Budget')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>

        <div class="progress-track" style="height: 14px;">
          <div class="progress-fill ${badgeStatus}" style="width: ${pct}%;"></div>
        </div>

        <div class="budget-metrics">
          <div>
            <span style="color:var(--text-muted);">Spent:</span>
            <strong>${App.formatCurrency(overall.spent_amount)}</strong> (${overall.usage_percentage}%)
          </div>
          <div>
            <span style="color:var(--text-muted);">Remaining:</span>
            <strong style="color:${overall.remaining_amount >= 0 ? 'var(--income-color)' : 'var(--expense-color)'};">
              ${App.formatCurrency(overall.remaining_amount)}
            </strong>
          </div>
          <div>
            <span style="color:var(--text-muted);">Budget:</span>
            <strong>${App.formatCurrency(overall.amount)}</strong>
          </div>
        </div>
      </div>
    `;
  },

  createBudgetCardHtml(b) {
    const pct = Math.min(b.usage_percentage, 100);
    const badgeStatus = b.warning_level;
    const badgeText = badgeStatus === "exceeded" 
      ? "Limit Exceeded" 
      : badgeStatus === "warning" 
      ? "Warning (≥80%)" 
      : "Healthy";

    return `
      <div class="budget-card">
        <div class="budget-card-header">
          <div class="budget-card-title">
            <span style="font-size:1.1rem;">🏷️</span>
            <div>${App.escapeHtml(b.category)}</div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="badge badge-${badgeStatus}">${badgeText}</span>
            <button class="btn-icon" title="Edit" onclick="Budgets.openEditModal(${b.id}, ${b.amount})">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="btn-icon" title="Delete" style="color:var(--expense-color);" onclick="Budgets.confirmDelete(${b.id}, '${App.escapeHtml(b.category)}')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>

        <div class="progress-track">
          <div class="progress-fill ${badgeStatus}" style="width: ${pct}%;"></div>
        </div>

        <div class="budget-metrics">
          <div>
            <span style="color:var(--text-muted);">Spent:</span>
            <strong>${App.formatCurrency(b.spent_amount)}</strong> (${b.usage_percentage}%)
          </div>
          <div>
            <span style="color:var(--text-muted);">Remaining:</span>
            <strong style="color:${b.remaining_amount >= 0 ? 'var(--income-color)' : 'var(--expense-color)'};">
              ${App.formatCurrency(b.remaining_amount)}
            </strong>
          </div>
          <div>
            <span style="color:var(--text-muted);">Budget:</span>
            <strong>${App.formatCurrency(b.amount)}</strong>
          </div>
        </div>
      </div>
    `;
  },

  openAddModal(forceOverall = false) {
    this.state.editingId = null;
    const titleEl = document.getElementById("budgetModalTitle");
    const form = document.getElementById("budgetForm");
    const errorDiv = document.getElementById("budgetFormError");
    const monthInput = document.getElementById("budgetFormMonth");
    const typeGroup = document.getElementById("budgetTypeRadioGroup");
    const catGroup = document.getElementById("budgetCategoryGroup");

    if (titleEl) titleEl.textContent = "Create Budget";
    if (form) form.reset();
    if (errorDiv) errorDiv.style.display = "none";
    if (monthInput) monthInput.value = App.state.currentMonth;

    if (typeGroup) typeGroup.style.display = "flex";

    const isOverallRadio = document.getElementById("budgetTypeOverall");
    const isCategoryRadio = document.getElementById("budgetTypeCategory");

    if (forceOverall) {
      if (isOverallRadio) isOverallRadio.checked = true;
      if (catGroup) catGroup.style.display = "none";
    } else {
      if (isCategoryRadio) isCategoryRadio.checked = true;
      if (catGroup) catGroup.style.display = "block";
    }

    this.populateCategoryOptions();

    const modal = document.getElementById("budgetModal");
    if (modal) modal.classList.add("active");
  },

  openEditModal(id, currentAmount) {
    this.state.editingId = id;
    const titleEl = document.getElementById("budgetModalTitle");
    const typeGroup = document.getElementById("budgetTypeRadioGroup");
    const catGroup = document.getElementById("budgetCategoryGroup");
    const amountInput = document.getElementById("budgetFormAmount");
    const monthInput = document.getElementById("budgetFormMonth");
    const errorDiv = document.getElementById("budgetFormError");

    if (titleEl) titleEl.textContent = "Edit Budget Amount";
    if (typeGroup) typeGroup.style.display = "none";
    if (catGroup) catGroup.style.display = "none";
    if (amountInput) amountInput.value = currentAmount;
    if (monthInput) monthInput.value = App.state.currentMonth;
    if (errorDiv) errorDiv.style.display = "none";

    const modal = document.getElementById("budgetModal");
    if (modal) modal.classList.add("active");
  },

  populateCategoryOptions() {
    const catSelect = document.getElementById("budgetFormCategory");
    if (!catSelect) return;

    const expenseCategories = App.state.categories.expense || [];
    catSelect.innerHTML = `<option value="" disabled selected>Select Category</option>` +
      expenseCategories.map(c => `<option value="${App.escapeHtml(c)}">${App.escapeHtml(c)}</option>`).join("");
  },

  async handleFormSubmit(e) {
    e.preventDefault();
    const errorDiv = document.getElementById("budgetFormError");
    if (errorDiv) errorDiv.style.display = "none";

    const amount = parseFloat(document.getElementById("budgetFormAmount").value);
    const month = document.getElementById("budgetFormMonth").value;

    if (isNaN(amount) || amount <= 0) {
      this.showFormError("Budget amount must be greater than zero");
      return;
    }
    if (!month) {
      this.showFormError("Please select a target month");
      return;
    }

    try {
      if (this.state.editingId) {
        await API.updateBudget(this.state.editingId, { amount });
        App.showToast("Budget updated successfully!", "success");
      } else {
        const isOverall = document.getElementById("budgetTypeOverall").checked;
        const category = isOverall ? null : document.getElementById("budgetFormCategory").value;

        if (!isOverall && !category) {
          this.showFormError("Please select a category for this budget");
          return;
        }

        await API.createBudget({
          month,
          is_overall: isOverall,
          category,
          amount
        });
        App.showToast("Budget created successfully!", "success");
      }

      App.closeModal("budgetModal");
      await this.fetchBudgets();
      if (typeof Dashboard !== "undefined") Dashboard.load();
    } catch (err) {
      this.showFormError(err.message);
    }
  },

  showFormError(msg) {
    const errorDiv = document.getElementById("budgetFormError");
    if (errorDiv) {
      errorDiv.textContent = msg;
      errorDiv.style.display = "block";
    }
  },

  confirmDelete(id, name) {
    App.showConfirm(
      "Delete Budget",
      `Are you sure you want to delete the budget for "${name}"?`,
      async () => {
        try {
          await API.deleteBudget(id);
          App.showToast("Budget removed.", "success");
          await this.fetchBudgets();
          if (typeof Dashboard !== "undefined") Dashboard.load();
        } catch (err) {
          App.showToast(`Delete failed: ${err.message}`, "error");
        }
      }
    );
  }
};
