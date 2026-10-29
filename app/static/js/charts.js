/* ===========================================================================
   SpendWise - Chart.js integration (dashboard)

   The server renders the numbers into data-chart="..." attributes as JSON.
   This script only converts those numbers into charts, so the charts always
   show the logged-in user's own data and nothing is hard-coded.
   =========================================================================== */
(function () {
  "use strict";

  if (typeof Chart === "undefined") {
    console.warn("Chart.js was not loaded (no internet connection?). Charts are skipped.");
    return;
  }

  var inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });
  var rupee = "\u20b9";

  function readData(id) {
    var canvas = document.getElementById(id);
    if (!canvas) return null;
    try {
      return JSON.parse(canvas.getAttribute("data-chart") || "null");
    } catch (error) {
      console.error("Invalid chart data for #" + id, error);
      return null;
    }
  }

  Chart.defaults.font.family = '"Segoe UI", system-ui, sans-serif';
  Chart.defaults.color = "#64748b";

  var tooltipMoney = {
    callbacks: {
      label: function (context) {
        var value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
        return context.dataset.label + ": " + rupee + inr.format(value / 100);
      }
    }
  };

  // -------------------- 1. Monthly income vs expense (bar chart) --------------------
  var monthly = readData("monthlyChart");
  if (monthly) {
    new Chart(document.getElementById("monthlyChart"), {
      type: "bar",
      data: {
        labels: monthly.labels,
        datasets: [
          {
            label: "Income",
            data: monthly.income.map(function (paise) { return paise / 100; }),
            backgroundColor: "rgba(16, 185, 129, 0.85)",
            borderRadius: 6,
            maxBarThickness: 34
          },
          {
            label: "Expense",
            data: monthly.expense.map(function (paise) { return paise / 100; }),
            backgroundColor: "rgba(239, 68, 68, 0.85)",
            borderRadius: 6,
            maxBarThickness: 34
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8 } },
          tooltip: {
            callbacks: {
              label: function (context) {
                return context.dataset.label + ": " + rupee + inr.format(context.parsed.y);
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: function (value) { return rupee + inr.format(value); } },
            grid: { color: "rgba(226, 232, 240, 0.7)" }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // -------------------- 2. Category-wise expenses (doughnut) --------------------
  var categories = readData("categoryChart");
  if (categories && categories.labels && categories.labels.length) {
    new Chart(document.getElementById("categoryChart"), {
      type: "doughnut",
      data: {
        labels: categories.labels,
        datasets: [
          {
            data: categories.values.map(function (paise) { return paise / 100; }),
            backgroundColor: categories.colors,
            borderWidth: 2,
            borderColor: "#fff"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                var total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                var percent = total ? ((context.parsed / total) * 100).toFixed(1) : "0";
                return " " + context.label + ": " + rupee + inr.format(context.parsed) + " (" + percent + "%)";
              }
            }
          }
        }
      }
    });
  }

  window.spendwiseTooltipMoney = tooltipMoney;
})();
