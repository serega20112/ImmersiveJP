const root = document.documentElement;
const themeToggle = document.querySelector('[data-theme-toggle]');
const savedTheme = localStorage.getItem('immersjp-theme');
const choiceGroups = document.querySelectorAll('[data-choice-group]');
const pendingForms = document.querySelectorAll('[data-pending-form]');
const wordChips = document.querySelectorAll('[data-word-chip]');

if (savedTheme) {
  root.setAttribute('data-theme', savedTheme);
}

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const nextTheme = root.getAttribute('data-theme') === 'night' ? 'paper' : 'night';
    root.setAttribute('data-theme', nextTheme);
    localStorage.setItem('immersjp-theme', nextTheme);
  });
}

choiceGroups.forEach((group) => {
  const hiddenInput = group.querySelector('[data-choice-input]');
  const buttons = group.querySelectorAll('[data-choice-value]');

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      const selectedValue = button.dataset.choiceValue || '';

      if (hiddenInput) {
        hiddenInput.value = selectedValue;
      }

      buttons.forEach((item) => {
        const isPressed = item === button;
        item.classList.toggle('is-pressed', isPressed);
        item.setAttribute('aria-pressed', isPressed ? 'true' : 'false');
      });
    });
  });
});

pendingForms.forEach((form) => {
  form.addEventListener('submit', () => {
    const pendingButton = form.querySelector('[data-pending-button]');
    const pendingLabel = form.dataset.pendingLabel;
    const pendingNote = form.querySelector('[data-pending-note]');

    if (pendingButton && pendingLabel) {
      pendingButton.dataset.originalText = pendingButton.textContent.trim();
      pendingButton.textContent = pendingLabel;
      pendingButton.disabled = true;
      pendingButton.classList.add('is-disabled');
    }

    if (pendingNote) {
      pendingNote.hidden = false;
    }

    form.classList.add('is-pending');
  });
});

wordChips.forEach((chip) => {
  chip.addEventListener('click', () => {
    const targetId = chip.dataset.wordTarget;
    const value = (chip.dataset.wordValue || '').trim();
    const target = targetId ? document.getElementById(targetId) : null;

    if (!target || !value) {
      return;
    }

    const existingItems = target.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    const hasValue = existingItems.some((item) => item.toLowerCase() === value.toLowerCase());

    if (!hasValue) {
      existingItems.push(value);
      target.value = existingItems.join(', ');
    }

    chip.classList.add('is-used');
    target.focus();
  });
});
