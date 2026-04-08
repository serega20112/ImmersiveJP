const setDiagnosticLevel = (level) => {
  const diagnosticPanels = document.querySelectorAll("[data-diagnostic-panel]");

  diagnosticPanels.forEach((panel) => {
    const isActive = panel.dataset.diagnosticPanel === level;
    panel.hidden = !isActive;
    panel.classList.toggle("is-active", isActive);
  });
};

export const initChoiceGroups = () => {
  const choiceGroups = document.querySelectorAll("[data-choice-group]");

  choiceGroups.forEach((group) => {
    const hiddenInput = group.querySelector("[data-choice-input]");
    const buttons = group.querySelectorAll("[data-choice-value]");

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const selectedValue = button.dataset.choiceValue || "";

        if (hiddenInput) {
          hiddenInput.value = selectedValue;
        }

        buttons.forEach((item) => {
          const isPressed = item === button;
          item.classList.toggle("is-pressed", isPressed);
          item.setAttribute("aria-pressed", isPressed ? "true" : "false");
        });

        if (group.hasAttribute("data-diagnostic-level-group")) {
          setDiagnosticLevel(selectedValue);
        }
      });
    });
  });

  const initialDiagnosticLevel = document.querySelector(
    "[data-diagnostic-level-input]"
  )?.value;
  if (initialDiagnosticLevel) {
    setDiagnosticLevel(initialDiagnosticLevel);
  }
};
