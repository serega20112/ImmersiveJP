const assetVersion =
  document.documentElement.dataset.assetVersion || "dev";

const importModule = (path) => import(`${path}?v=${assetVersion}`);

const boot = async () => {
  const [
    { initChoiceGroups },
    { initHintToggles },
    { initPendingForms },
    { initPromptChips },
    { initThemeToggle },
    { initWordChips },
  ] = await Promise.all([
    importModule("./choices/index.js"),
    importModule("./hints/index.js"),
    importModule("./pending/index.js"),
    importModule("./prompts/index.js"),
    importModule("./theme/index.js"),
    importModule("./words/index.js"),
  ]);

  initThemeToggle();
  initChoiceGroups();
  initPendingForms();
  initPromptChips();
  initWordChips();
  initHintToggles();
};

void boot();
