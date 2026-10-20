/**
 * SpendWise - Analytics & Reports Controller
 * Financial reports, multi-period trends, category distributions, top expenses, and CSV exports.
 */

const Analytics = {
  state: {
    fromDate: "",
    toDate: ""
  },

  charts: {
    categoryPie: null,
    monthlyCompare: null,
    dailyLine: null
  },

  async load() {
    this.setupListeners();
    // Default to last 90 days if not set
    if (!this.state.fromDate || !this.state.toDate) {
      this.setPreset("3months");
    } else {
      await this.fetchAnalytics();
    }
  },

  setupListeners() {
    if (this._listenersBound) return;
    this._listenersBound = true;

    // Preset buttons
    document.querySelectorAll(".analytics-preset-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".analytics-preset-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.setPreset(btn.dataset.preset);
      });
    });

    // Custom date inputs
    const fromInput = document.getElementById("analyticsFromDate");
    const toInput = document.getElementById("analyticsToDate");

    const onDateChange = () => {
      if (fromInput.value && toInput.value) {
        if (fromInput.value > toInput.value) {
          App.showToast("Start date cannot be after end date", "warning");
          return;
        }
        this.state.fromDate = fromInput.value;
        this.state.toDate = toInput.value;
        // Clear active preset button
        document.querySelectorAll(".analytics-preset-btn").forEach(b => b.classList.remove("active"));
        this.fetchAnalytics();
      }
    };

    if (fromInput && toInput) {
      fromInput.addEventListener("change", onDateChange);
      toInput.addEventListener("change", onDateChange);
    }

    // CSV Export Button
    const exportBtn = document.getElementById("analyticsExportCsvBtn");
    if (exportBtn) {
      exportBtn.addEventListener("click", () => this.triggerCsvExport());
    }
  },

  setPreset(preset) {
    const today = new Date();
    let from = new Date();
    let to = new Date();

    if (preset === "month") {
      from = new Date(today.getFullYear(), today.month ? today.getMonth() : today.getMonth(), 1);
      to = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (preset === "last_month") {
      from = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      to = new Date(today.getFullYear(), today.getMonth(), 0);
    } else if (preset === "3months") {
      from = new Date();
      from.setDate(today.getDate() - 90);
    } else if (preset === "6months") {
      from = new Date();
      from.setDate(today.getDate() - 180);
    } else if (preset === "year") {
      from = new Date(today.getFullYear(), 0, 1);
      to = new Date(today.getFullYear(), 11, 31);
    }

    const formatDate = (d) => d.toISOString().slice(0, 10);
    this.state.fromDate = formatDate(from);
    this.state.toDate = formatDate(to);

    const fromInput = document.getElementById("analyticsFromDate");
    const toInput = document.getElementById("analyticsToDate");
    if (fromInput) fromInput.value = this.state.fromDate;
    if (toInput) toInput.value = this.state.toDate;

    this.fetchAnalytics();
  },

  async fetchAnalytics() {
    try {
      const data = await API.getAnalytics(this.state.fromDate, this.state.toDate);
      this.renderSummaryKPIs(data);
      this.renderCharts(data);
      this.renderTopCategories(data.top_spending_categories, data.total_expenses);
      this.renderHighestExpenses(data.highest_expense_transactions);
    } catch (err) {
      App.showToast(`Error fetching analytics: ${err.message}`, "error");
    }
  },

  renderSummaryKPIs(data) {
    const incEl = document.getElementById("analyticsTotalIncome");
    const expEl = document.getElementById("analyticsTotalExpenses");
    const netEl = document.getElementById("analyticsNetSavings");
    const rateEl = document.getElementById("analyticsSavingsRate");

    if (incEl) incEl.textContent = App.formatCurrency(data.total_income);
    if (expEl) expEl.textContent = App.formatCurrency(data.total_expenses);
    if (netEl) {
      netEl.textContent = App.formatCurrency(data.net_savings);
      netEl.style.color = data.net_savings >= 0 ? "var(--income-color)" : "var(--expense-color)";
    }
    if (rateEl) {
      rateEl.textContent = `${data.savings_rate.toFixed(1)}%`;
      rateEl.style.color = data.savings_rate >= 20 ? "var(--income-color)" : "var(--text-primary)";
    }
  },

  renderCharts(data) {
    if (typeof Chart === "undefined") return;

    const isDark = App.state.theme === "dark";
    const textColor = isDark ? "#94a3b8" : "#475569";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";

    // 1. Category Distribution
    const ctxPie = document.getElementById("analyticsCategoryChart")?.getContext("2d");
    if (ctxPie) {
      if (this.charts.categoryPie) this.charts.categoryPie.destroy();

      const labels = data.expense_breakdown.map(i => i.category);
      const values = data.expense_breakdown.map(i => i.amount);
      const colors = [
        "#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899",
        "#8b5cf6", "#14b8a6", "#f97316", "#e11d48", "#84cc16"
      ];

      this.charts.categoryPie = new Chart(ctxPie, {
        type: "doughnut",
        data: {
          labels: labels.length ? labels : ["No Expenses"],
          datasets: [{
            data: values.length ? values : [1],
            backgroundColor: values.length ? colors.slice(0, labels.length) : [isDark ? "#1f2937" : "#e2e8f0"],
            borderWidth: 2,
            borderColor: isDark ? "#111827" : "#ffffff"
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "right",
              labels: { color: textColor, boxWidth: 12, padding: 12 }
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

    // 2. Monthly Comparison (Income vs Expense)
    const ctxMonthly = document.getElementById("analyticsMonthlyChart")?.getContext("2d");
    if (ctxMonthly) {
      if (this.charts.monthlyCompare) this.charts.monthlyCompare.destroy();

      const months = data.monthly_trends.map(t => t.month);
      const incomes = data.monthly_trends.map(t => t.income);
      const expenses = data.monthly_trends.map(t => t.expense);

      this.charts.monthlyCompare = new Chart(ctxMonthly, {
        type: "bar",
        data: {
          labels: months.length ? months : ["No Data"],
          datasets: [
            {
              label: "Income",
              data: incomes,
              backgroundColor: "#10b981",
              borderRadius: 6
            },
            {
              label: "Expenses",
              data: expenses,
              backgroundColor: "#f43f5e",
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: textColor } },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${ctx.dataset.label}: ${App.formatCurrency(ctx.parsed.y)}`
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: textColor }
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

    // 3. Daily Spending Trend
    const ctxDaily = document.getElementById("analyticsDailyChart")?.getContext("2d");
    if (ctxDaily) {
      if (this.charts.dailyLine) this.charts.dailyLine.destroy();

      const dates = data.daily_spending.map(d => d.date);
      const amounts = data.daily_spending.map(d => d.amount);

      this.charts.dailyLine = new Chart(ctxDaily, {
        type: "line",
        data: {
          labels: dates.length ? dates : ["No Data"],
          datasets: [{
            label: "Daily Spend",
            data: amounts,
            borderColor: "#6366f1",
            backgroundColor: "rgba(99, 102, 241, 0.1)",
            fill: true,
            tension: 0.3,
            borderWidth: 2,
            pointRadius: dates.length > 30 ? 1 : 3,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => ` Spend: ${App.formatCurrency(ctx.parsed.y)}`
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: {
                color: textColor,
                maxTicksLimit: 10
              }
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
  },

  renderTopCategories(categories, totalExpenses) {
    const container = document.getElementById("analyticsTopCategoriesList");
    if (!container) return;

    if (!categories || categories.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted); font-size:0.9rem;">No expense data for this period.</div>`;
      return;
    }

    container.innerHTML = categories.map((cat, idx) => {
      return `
        <div style="margin-bottom: 14px;">
          <div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-bottom: 6px;">
            <span><strong>#${idx + 1} ${App.escapeHtml(cat.category)}</strong> (${cat.count} txns)</span>
            <span><strong>${App.formatCurrency(cat.amount)}</strong> (${cat.percentage}%)</span>
          </div>
          <div class="progress-track" style="height: 8px;">
            <div class="progress-fill ok" style="width: ${cat.percentage}%; background: var(--accent-primary);"></div>
          </div>
        </div>
      `;
    }).join("");
  },

  renderHighestExpenses(transactions) {
    const tbody = document.getElementById("analyticsHighestExpenseTableBody");
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No expense transactions in this period.</td></tr>`;
      return;
    }

    tbody.innerHTML = transactions.map(t => {
      return `
        <tr>
          <td>${t.date}</td>
          <td><strong>${App.escapeHtml(t.description)}</strong></td>
          <td><span class="badge badge-expense">${App.escapeHtml(t.category)}</span></td>
          <td style="font-weight:700; color:var(--expense-color);">
            -${App.formatCurrency(t.amount)}
          </td>
        </tr>
      `;
    }).join("");
  },

  triggerCsvExport() {
    const exportUrl = API.getExportUrl({
      from_date: this.state.fromDate,
      to_date: this.state.toDate
    });
    App.showToast("Preparing CSV download...", "info");
    // Trigger download
    const link = document.createElement("a");
    link.href = exportUrl;
    link.setAttribute("download", "");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};
