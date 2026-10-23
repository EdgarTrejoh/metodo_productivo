(() => {
  const area = document.querySelector('[data-privacy-return]');
  if (!area) return;

  if (area.dataset.privacyReturn === 'check') {
    area.querySelector('.privacy-return-action').addEventListener('click', () => window.close());
    return;
  }

  const back = area.querySelector('.privacy-back');
  let validPreviousPage = false;
  try {
    const previous = new URL(document.referrer);
    validPreviousPage = previous.origin === window.location.origin
      && previous.pathname !== window.location.pathname
      && window.history.length > 1;
  } catch (_) {
    // Una visita directa o un referrer ausente conserva el enlace seguro al inicio.
  }
  if (validPreviousPage) {
    back.hidden = false;
    back.addEventListener('click', () => window.history.back());
  }
})();
