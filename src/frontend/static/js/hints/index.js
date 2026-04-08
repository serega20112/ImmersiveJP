export const initHintToggles = () => {
  const hintButtons = document.querySelectorAll("[data-hint-toggle]");

  hintButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetKey = button.dataset.hintTarget;
      const hintIndex = button.dataset.hintIndex;
      const hintItem = document.querySelector(
        `[data-hint-item="${targetKey}"][data-hint-index="${hintIndex}"]`
      );

      if (!hintItem) {
        return;
      }

      const wasHidden = hintItem.hidden;
      hintItem.hidden = !hintItem.hidden;
      button.classList.toggle("is-open", !hintItem.hidden);

      if (wasHidden && !button.dataset.hintUsed) {
        const counterId = button.dataset.hintCounter;
        const counterInput = counterId ? document.getElementById(counterId) : null;

        if (counterInput) {
          const current = Number(counterInput.value || "0");
          counterInput.value = String(current + 1);
        }

        button.dataset.hintUsed = "true";
      }
    });
  });
};
