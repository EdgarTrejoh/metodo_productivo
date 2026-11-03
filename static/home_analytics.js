// Medición opcional: los enlaces funcionan igual sin JavaScript o si falla el POST.
const analyticsScript = document.querySelector('script[data-analytics-url]');
const ctaUrl = analyticsScript?.dataset.analyticsUrl;
const csrfToken = document.cookie.split('; ').find((part) => part.startsWith('csrftoken='))?.slice(10);

if (ctaUrl && csrfToken && window.crypto?.randomUUID) {
  document.querySelectorAll('[data-home-cta]').forEach((link) => {
    link.addEventListener('click', () => {
      const body = new URLSearchParams({
        cta: link.dataset.homeCta,
        operation: crypto.randomUUID(),
        csrfmiddlewaretoken: decodeURIComponent(csrfToken),
      });
      fetch(ctaUrl, {
        method: 'POST',
        body,
        credentials: 'same-origin',
        keepalive: true,
      }).catch(() => {});
    });
  });
}
