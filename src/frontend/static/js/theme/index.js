const THEME_COPY = {
  paper: {
    name: "Бумага",
    hint: "переключить на ночь",
    aria: "Текущая тема: бумага. Нажми, чтобы включить ночной режим.",
  },
  night: {
    name: "Ночь",
    hint: "переключить на бумагу",
    aria: "Текущая тема: ночь. Нажми, чтобы включить светлый режим.",
  },
};

export const initThemeToggle = () => {
  const root = document.documentElement;
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const themeName = document.querySelector("[data-theme-toggle-name]");
  const themeHint = document.querySelector("[data-theme-toggle-hint]");
  const savedTheme = localStorage.getItem("immersjp-theme");

  const syncTheme = (theme) => {
    const copy = THEME_COPY[theme] || THEME_COPY.paper;

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

  syncTheme(savedTheme || root.getAttribute("data-theme") || "paper");

  if (!themeToggle) {
    return;
  }

  themeToggle.addEventListener("click", () => {
    const nextTheme =
      root.getAttribute("data-theme") === "night" ? "paper" : "night";
    syncTheme(nextTheme);
    localStorage.setItem("immersjp-theme", nextTheme);
  });
};
