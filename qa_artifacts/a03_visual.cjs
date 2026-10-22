const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  for (const [width, height, label] of [[1365, 900, 'desktop'], [390, 844, 'mobile']]) {
    const page = await browser.newPage({ viewport: { width, height }, javaScriptEnabled: false });
    const response = await page.goto('http://127.0.0.1:8767/recursos/mapa-de-caja-pyme/', { waitUntil: 'domcontentloaded', timeout: 10000 });
    const result = await page.evaluate(() => ({
      title: document.querySelector('h1')?.textContent,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
      blocked: document.body.textContent.includes('temporalmente deshabilitada'),
      breadcrumb: document.querySelector('nav[aria-label="Ruta de navegación"]')?.textContent.trim(),
    }));
    await page.screenshot({ path: `qa_artifacts/a03-resource-${process.env.QA_FORM ? 'form-' : ''}${label}.png`, fullPage: true });
    console.log(JSON.stringify({ label, status: response.status(), ...result }));
    await page.close();
  }
  await browser.close();
})().catch(error => { console.error(error); process.exitCode = 1; });
