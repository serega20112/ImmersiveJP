export const initThemeToggle = () => {
  const root = document.documentElement;
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const savedTheme = localStorage.getItem("immersjp-theme");

  if (savedTheme) {
    root.setAttribute("data-theme", savedTheme);
  }

  if (!themeToggle) {
    return;
  }

  themeToggle.addEventListener("click", () => {
    const nextTheme =
      root.getAttribute("data-theme") === "night" ? "paper" : "night";
    root.setAttribute("data-theme", nextTheme);
    localStorage.setItem("immersjp-theme", nextTheme);
  });
};
