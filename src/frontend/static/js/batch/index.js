/**
 * Опрос состояния партии карточек: страница не ждёт генерацию, а подменяет
 * список по мере появления новых карточек.
 */

const POLL_INTERVAL_MS = 2000;
const MAX_BACKOFF_MS = 10000;
const MAX_FAILURES = 5;

const stillGenerating = (root) => Boolean(root.querySelector("[data-batch-generating]"));

export const initBatchPolling = () => {
  const containers = document.querySelectorAll("[data-batch-status-url]");

  containers.forEach((container) => {
    const url = container.dataset.batchStatusUrl;

    if (!url || !stillGenerating(container)) {
      return;
    }

    let failures = 0;
    let delay = POLL_INTERVAL_MS;

    const schedule = () => {
      window.setTimeout(step, delay);
    };

    const finish = () => {
      container.removeAttribute("data-batch-status-url");
    };

    const step = async () => {
      try {
        const response = await fetch(url, { credentials: "same-origin" });

        if (!response.ok) {
          throw new Error(`batch status responded ${response.status}`);
        }

        container.innerHTML = await response.text();
        failures = 0;
        delay = POLL_INTERVAL_MS;

        if (!stillGenerating(container)) {
          finish();
          return;
        }
      } catch {
        failures += 1;
        delay = Math.min(delay * 2, MAX_BACKOFF_MS);

        if (failures >= MAX_FAILURES) {
          finish();
          return;
        }
      }

      schedule();
    };

    schedule();
  });
};
