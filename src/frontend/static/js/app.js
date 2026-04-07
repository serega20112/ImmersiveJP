const root = document.documentElement;
const themeToggle = document.querySelector('[data-theme-toggle]');
const savedTheme = localStorage.getItem('immersjp-theme');
const choiceGroups = document.querySelectorAll('[data-choice-group]');
const pendingForms = document.querySelectorAll('[data-pending-form]');
const wordChips = document.querySelectorAll('[data-word-chip]');
const diagnosticPanels = document.querySelectorAll('[data-diagnostic-panel]');
const hintButtons = document.querySelectorAll('[data-hint-toggle]');

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

const setDiagnosticLevel = (level) => {
  diagnosticPanels.forEach((panel) => {
    const isActive = panel.dataset.diagnosticPanel === level;
    panel.hidden = !isActive;
    panel.classList.toggle('is-active', isActive);
  });
};

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

      if (group.hasAttribute('data-diagnostic-level-group')) {
        setDiagnosticLevel(selectedValue);
      }
    });
  });
});

const initialDiagnosticLevel = document.querySelector('[data-diagnostic-level-input]')?.value;
if (initialDiagnosticLevel) {
  setDiagnosticLevel(initialDiagnosticLevel);
}

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

hintButtons.forEach((button) => {
  button.addEventListener('click', () => {
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
    button.classList.toggle('is-open', !hintItem.hidden);

    if (wasHidden && !button.dataset.hintUsed) {
      const counterId = button.dataset.hintCounter;
      const counterInput = counterId ? document.getElementById(counterId) : null;

      if (counterInput) {
        const current = Number(counterInput.value || '0');
        counterInput.value = String(current + 1);
      }

      button.dataset.hintUsed = 'true';
    }
  });
});
