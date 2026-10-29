/* ===========================================================================
   SpendWise - transaction page behaviour
     * show only the categories that belong to the selected transaction type
     * wire the delete-confirmation modal to the correct record
   =========================================================================== */
(function () {
  "use strict";

  // -------------------- category select depends on the type --------------------
  var typeSelect = document.getElementById("type");
  var categorySelect = document.getElementById("category");

  function filterCategories() {
    if (!typeSelect || !categorySelect) return;

    var wanted = typeSelect.value === "income" ? "income" : "expense";

    Array.prototype.forEach.call(categorySelect.querySelectorAll("optgroup"), function (group) {
      var visible = group.getAttribute("data-type") === wanted;
      group.hidden = !visible;
      group.style.display = visible ? "" : "none";
      Array.prototype.forEach.call(group.querySelectorAll("option"), function (option) {
        option.disabled = !visible;
      });
    });

    // If the selected option is hidden, jump to the first visible option.
    var selected = categorySelect.options[categorySelect.selectedIndex];
    if (selected && selected.disabled) {
      var firstVisible = categorySelect.querySelector("optgroup:not([hidden]) option");
      if (firstVisible) {
        categorySelect.value = firstVisible.value;
      }
    }
  }

  if (typeSelect && categorySelect) {
    typeSelect.addEventListener("change", filterCategories);
    filterCategories();
  }

  // -------------------- delete confirmation modal --------------------
  var deleteModal = document.getElementById("deleteModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", function (event) {
      var button = event.relatedTarget;
      if (!button) return;
      var url = button.getAttribute("data-delete-url");
      var label = button.getAttribute("data-delete-label");

      var form = deleteModal.querySelector("#deleteForm");
      var target = deleteModal.querySelector("#deleteTargetLabel");
      if (form && url) form.setAttribute("action", url);
      if (target) target.textContent = label || "";
    });
  }
})();
