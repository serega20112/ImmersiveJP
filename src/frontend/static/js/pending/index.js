export const initPendingForms = () => {
  const pendingForms = document.querySelectorAll("[data-pending-form]");

  pendingForms.forEach((form) => {
    form.addEventListener("submit", () => {
      const pendingButton = form.querySelector("[data-pending-button]");
      const pendingLabel = form.dataset.pendingLabel;
      const pendingNote = form.querySelector("[data-pending-note]");

      if (pendingButton && pendingLabel) {
        pendingButton.dataset.originalText = pendingButton.textContent.trim();
        pendingButton.textContent = pendingLabel;
        pendingButton.disabled = true;
        pendingButton.classList.add("is-disabled");
      }

      if (pendingNote) {
        pendingNote.hidden = false;
      }

      form.classList.add("is-pending");
    });
  });
};
