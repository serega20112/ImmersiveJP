export const initPromptChips = () => {
  const promptChips = document.querySelectorAll("[data-prompt-chip]");

  promptChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const targetId = chip.dataset.promptTarget;
      const value = (chip.dataset.promptValue || "").trim();
      const target = targetId ? document.getElementById(targetId) : null;

      if (!target || !value) {
        return;
      }

      target.value = value;
      target.focus();
    });
  });
};
