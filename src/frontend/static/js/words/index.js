export const initWordChips = () => {
  const wordChips = document.querySelectorAll("[data-word-chip]");

  wordChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const targetId = chip.dataset.wordTarget;
      const value = (chip.dataset.wordValue || "").trim();
      const target = targetId ? document.getElementById(targetId) : null;

      if (!target || !value) {
        return;
      }

      const existingItems = target.value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      const hasValue = existingItems.some(
        (item) => item.toLowerCase() === value.toLowerCase()
      );

      if (!hasValue) {
        existingItems.push(value);
        target.value = existingItems.join(", ");
      }

      chip.classList.add("is-used");
      target.focus();
    });
  });
};
