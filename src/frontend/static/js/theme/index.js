/**
 * Переключатель тем оформления: три состояния по кругу.
 *
 * Порядок цикла: «Эдо» (по умолчанию, тёмная) → «Сакура» (светлая) →
 * «Неон Эдо» (тёмная) → снова «Эдо».
 *
 * Контракт, который сохраняется намеренно:
 *   * атрибут `data-theme` на `<html>` — источник правды для CSS;
 *   * ключ localStorage `immersjp-theme-v2` — выбор переживает перезагрузку;
 *   * хуки в разметке `[data-theme-toggle]`, `[data-theme-toggle-name]`,
 *     `[data-theme-toggle-hint]`.
 *
 * Значения прошлой двухтемной версии (`paper`/`night`) больше не валидны и
 * игнорируются при чтении из localStorage — вместо них берётся тема по умолчанию.
 */

const STORAGE_KEY = "immersjp-theme-v2";

const DEFAULT_THEME = "edo";

const THEME_CYCLE = ["edo", "sakura", "neon"];

const THEME_COPY = {
  edo: {
    name: "Эдо",
    hint: "далее · сакура",
    aria: "Тема «Эдо» (тёмная). Нажмите, чтобы переключить на тему «Сакура».",
  },
  sakura: {
    name: "Сакура",
    hint: "далее · неон",
    aria: "Тема «Сакура» (светлая). Нажмите, чтобы переключить на тему «Неон Эдо».",
  },
  neon: {
    name: "Неон Эдо",
    hint: "далее · эдо",
    aria: "Тема «Неон Эдо» (тёмная). Нажмите, чтобы вернуться к теме «Эдо».",
  },
};

const normalizeTheme = (value) => (THEME_CYCLE.includes(value) ? value : null);

export const initThemeToggle = () => {
  const root = document.documentElement;
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const themeName = document.querySelector("[data-theme-toggle-name]");
  const themeHint = document.querySelector("[data-theme-toggle-hint]");

  const syncTheme = (theme) => {
    const copy = THEME_COPY[theme] || THEME_COPY[DEFAULT_THEME];

    root.setAttribute("data-theme", theme);

    if (!themeToggle) {
      return;
    }

    themeToggle.dataset.theme = theme;
    themeToggle.setAttribute("aria-label", copy.aria);
    themeToggle.setAttribute("title", copy.aria);

    if (themeName) {
      themeName.textContent = copy.name;
    }

    if (themeHint) {
      themeHint.textContent = copy.hint;
    }
  };

  const storedTheme = normalizeTheme(localStorage.getItem(STORAGE_KEY));
  const initialTheme =
    storedTheme || normalizeTheme(root.getAttribute("data-theme")) || DEFAULT_THEME;

  syncTheme(initialTheme);

  if (!themeToggle) {
    return;
  }

  themeToggle.addEventListener("click", () => {
    const current =
      normalizeTheme(root.getAttribute("data-theme")) || DEFAULT_THEME;
    const nextTheme =
      THEME_CYCLE[(THEME_CYCLE.indexOf(current) + 1) % THEME_CYCLE.length];

    syncTheme(nextTheme);
    localStorage.setItem(STORAGE_KEY, nextTheme);
  });
};