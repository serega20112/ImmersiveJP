const STORAGE_KEY = "immersjp-theme-v2";

const THEME_COPY = {
  paper: {
    name: "Свет",
    hint: "переключить на ночь",
    aria: "Текущая тема: свет. Нажми, чтобы включить ночной режим.",
  },
  night: {
    name: "Ночь",
    hint: "переключить на свет",
    aria: "Текущая тема: ночь. Нажми, чтобы включить светлый режим.",
  },
};

export const initThemeToggle = () => {
  const root = document.documentElement;
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const themeName = document.querySelector("[data-theme-toggle-name]");
  const themeHint = document.querySelector("[data-theme-toggle-hint]");
  const savedTheme = localStorage.getItem(STORAGE_KEY);

  const syncTheme = (theme) => {
    const copy = THEME_COPY[theme] || THEME_COPY.night;

    root.setAttribute("data-theme", theme);

    if (!themeToggle) {
      return;
    }

    themeToggle.dataset.theme = theme;
    themeToggle.setAttribute("aria-label", copy.aria);

    if (themeName) {
      themeName.textContent = copy.name;
    }

    if (themeHint) {
      themeHint.textContent = copy.hint;
    }
  };

  syncTheme(savedTheme || root.getAttribute("data-theme") || "night");

  if (!themeToggle) {
    return;
  }

  themeToggle.addEventListener("click", () => {
    const nextTheme =
      root.getAttribute("data-theme") === "night" ? "paper" : "night";
    syncTheme(nextTheme);
    localStorage.setItem(STORAGE_KEY, nextTheme);
  });
};
