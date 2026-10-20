/**
 * SpendWise - Dashboard Controller
 * Renders KPIs, alerts, responsive Chart.js visualisations, and recent transactions.
 */

const Dashboard = {
  charts: {
    incomeExpense: null,
    categoryBreakdown: null
  },

  async load() {
    const month = App.state.currentMonth;
    const container = document.getElementById("tab-dashboard");
    if (!container) return;

    try {
      const data = await API.getDashboard(month);
      this.renderKPIs(data);
      this.renderAlerts(data.budget_warnings);
      this.renderRecentTransactions(data.recent_transactions);
      this.renderCharts(data);
    } catch (err) {
      App.showToast(`Failed to load dashboard data: ${err.message}`, "error");
    }
  },

  renderKPIs(data) {
    // Total Income
    const incomeEl = document.getElementById("kpiIncome");
    if (incomeEl) incomeEl.textContent = App.formatCurrency(data.total_income);

    // Total Expenses
    const expenseEl = document.getElementById("kpiExpense");
    if (expenseEl) expenseEl.textContent = App.formatCurrency(data.total_expenses);

    // Net Balance
    const balanceEl = document.getElementById("kpiBalance");
    if (balanceEl) {
      balanceEl.textContent = App.formatCurrency(data.remaining_balance);
      balanceEl.style.color = data.remaining_balance >= 0 ? "var(--income-color)" : "var(--expense-color)";
    }

    // Savings Rate
    const savingsEl = document.getElementById("kpiSavingsRate");
    if (savingsEl) {
      savingsEl.textContent = `${data.savings_rate.toFixed(1)}%`;
      savingsEl.style.color = data.savings_rate >= 20 ? "var(--income-color)" : "var(--text-primary)";
    }

    // Monthly Budget Usage
    const budgetUsageEl = document.getElementById("kpiBudgetUsage");
    const budgetSubtextEl = document.getElementById("kpiBudgetSubtext");
    if (budgetUsageEl) {
      if (data.overall_budget !== null && data.overall_budget > 0) {
        budgetUsageEl.textContent = `${data.budget_usage_percent.toFixed(1)}%`;
        if (budgetSubtextEl) {
          budgetSubtextEl.textContent = `${App.formatCurrency(data.budget_spent)} of ${App.formatCurrency(data.overall_budget)}`;
        }
        if (data.budget_usage_percent >= 100) {
          budgetUsageEl.style.color = "var(--expense-color)";
        } else if (data.budget_usage_percent >= 80) {
          budgetUsageEl.style.color = "var(--warning-color)";
        } else {
          budgetUsageEl.style.color = "var(--income-color)";
        }
      } else {
        budgetUsageEl.textContent = "Not Set";
        if (budgetSubtextEl) {
          budgetSubtextEl.innerHTML = `<a href="javascript:App.switchTab('budgets')" style="color:var(--accent-primary);text-decoration:none;">Set monthly budget →</a>`;
        }
      }
    }
  },

  renderAlerts(warnings) {
    const alertsContainer = document.getElementById("dashboardAlerts");
    if (!alertsContainer) return;

    if (!warnings || warnings.length === 0) {
      alertsContainer.innerHTML = "";
      return;
    }

    const html = warnings.map(w => {
      const isExceeded = w.status === "exceeded";
      const icon = isExceeded ? "⚠️" : "🔔";
      return `
        <div class="alert-banner ${isExceeded ? 'exceeded' : 'warning'}">
          <span style="font-size: 1.2rem;">${icon}</span>
          <div style="flex:1;">
            <strong>${App.escapeHtml(w.name)}</strong>: ${App.escapeHtml(w.message)}
          </div>
          <button class="btn btn-secondary" style="padding:4px 10px;font-size:0.8rem;" onclick="App.switchTab('budgets')">Manage Budget</button>
        </div>
      `;
    }).join("");

    alertsContainer.innerHTML = html;
  },

  renderRecentTransactions(transactions) {
    const tbody = document.getElementById("recentTransactionsTableBody");
    const emptyState = document.getElementById("recentTransactionsEmpty");
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
      tbody.innerHTML = "";
      if (emptyState) emptyState.style.display = "block";
      return;
    }

    if (emptyState) emptyState.style.display = "none";

    tbody.innerHTML = transactions.map(t => {
      const isIncome = t.type === "income";
      const badgeClass = isIncome ? "badge-income" : "badge-expense";
      const sign = isIncome ? "+" : "-";

      return `
        <tr>
          <td>${t.date}</td>
          <td>
            <strong>${App.escapeHtml(t.description)}</strong>
            ${t.payment_method ? `<div style="font-size:0.75rem;color:var(--text-muted);">${App.escapeHtml(t.payment_method)}</div>` : ''}
          </td>
          <td><span class="badge ${badgeClass}">${App.escapeHtml(t.category)}</span></td>
          <td style="font-weight:700; color:${isIncome ? 'var(--income-color)' : 'var(--expense-color)'};">
            ${sign}${App.formatCurrency(t.amount)}
          </td>
        </tr>
      `;
    }).join("");
  },

  renderCharts(data) {
    if (typeof Chart === "undefined") {
      console.warn("Chart.js is not loaded yet.");
      return;
    }

    const isDark = App.state.theme === "dark";
    const textColor = isDark ? "#94a3b8" : "#475569";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";

    // 1. Income vs Expense Bar Chart
    const ctxBar = document.getElementById("dashboardBarChart")?.getContext("2d");
    if (ctxBar) {
      if (this.charts.incomeExpense) this.charts.incomeExpense.destroy();

      this.charts.incomeExpense = new Chart(ctxBar, {
        type: "bar",
        data: {
          labels: ["Income", "Expenses", "Net Savings"],
          datasets: [{
            data: [data.total_income, data.total_expenses, Math.max(0, data.remaining_balance)],
            backgroundColor: [
              "#10b981", // Income
              "#f43f5e", // Expense
              "#6366f1"  // Net
            ],
            borderRadius: 8,
            maxBarThickness: 45
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${App.formatCurrency(ctx.parsed.y)}`
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: textColor, font: { weight: "600" } }
            },
            y: {
              grid: { color: gridColor },
              ticks: {
                color: textColor,
                callback: (val) => "₹" + (val >= 1000 ? (val / 1000).toFixed(0) + "k" : val)
              }
            }
          }
        }
      });
    }

    // 2. Category Breakdown Doughnut Chart
    const ctxDoughnut = document.getElementById("dashboardDoughnutChart")?.getContext("2d");
    if (ctxDoughnut) {
      if (this.charts.categoryBreakdown) this.charts.categoryBreakdown.destroy();

      const categories = data.expense_breakdown.map(i => i.category);
      const amounts = data.expense_breakdown.map(i => i.amount);

      const colorPalette = [
        "#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899",
        "#8b5cf6", "#14b8a6", "#f97316", "#e11d48", "#84cc16"
      ];

      if (categories.length === 0) {
        // Empty placeholder state for doughnut chart
        this.charts.categoryBreakdown = new Chart(ctxDoughnut, {
          type: "doughnut",
          data: {
            labels: ["No Expenses This Month"],
            datasets: [{
              data: [1],
              backgroundColor: [isDark ? "#1f2937" : "#e2e8f0"]
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "bottom", labels: { color: textColor } },
              tooltip: { enabled: false }
            }
          }
        });
      } else {
        this.charts.categoryBreakdown = new Chart(ctxDoughnut, {
          type: "doughnut",
          data: {
            labels: categories,
            datasets: [{
              data: amounts,
              backgroundColor: colorPalette.slice(0, categories.length),
              borderWidth: 2,
              borderColor: isDark ? "#111827" : "#ffffff"
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  color: textColor,
                  padding: 12,
                  boxWidth: 12,
                  font: { size: 11 }
                }
              },
              tooltip: {
                callbacks: {
                  label: (ctx) => ` ${ctx.label}: ${App.formatCurrency(ctx.parsed)}`
                }
              }
            }
          }
        });
      }
    }
  }
};
