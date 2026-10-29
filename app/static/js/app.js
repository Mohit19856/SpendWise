/* ===========================================================================
   SpendWise - shared UI behaviour
     * mobile sidebar toggle
     * automatic dismissal of success messages
   =========================================================================== */
(function () {
  "use strict";

  // -------------------- mobile sidebar --------------------
  var sidebar = document.getElementById("sidebar");
  var toggle = document.getElementById("sidebarToggle");
  var backdrop = document.getElementById("sidebarBackdrop");

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("show");
  }

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("open");
    if (backdrop) backdrop.classList.add("show");
  }

  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
    });
  }
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeSidebar();
  });

  // -------------------- auto-hide success alerts --------------------
  document.querySelectorAll(".flash-stack .alert-success").forEach(function (alert) {
    window.setTimeout(function () {
      if (window.bootstrap && window.bootstrap.Alert) {
        window.bootstrap.Alert.getOrCreateInstance(alert).close();
      }
    }, 5000);
  });

  // -------------------- client-side sanity check for amounts --------------------
  var amountInput = document.getElementById("amount");
  if (amountInput) {
    amountInput.addEventListener("blur", function () {
      var value = parseFloat(amountInput.value);
      if (!isNaN(value) && value > 0) {
        amountInput.value = value.toFixed(2);
      }
    });
  }
})();
