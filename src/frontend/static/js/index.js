/**
 * Точка входа клиентских ES-модулей: подгружает модули интеракций
 * с учётом версии ассетов и инициализирует их.
 */

const assetVersion = document.documentElement.dataset.assetVersion || "dev";

const importModule = (path) => import(`${path}?v=${assetVersion}`);

const boot = async () => {
  const [
    { initBatchPolling },
    { initChoiceGroups },
    { initHintToggles },
    { initPendingForms },
    { initPromptChips },
    { initThemeToggle },
    { initWordChips },
  ] = await Promise.all([
    importModule("./batch/index.js"),
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
  initBatchPolling();
};

void boot();