const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 369, height: 545 }, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:8765/check-pyme/');
  await page.getByRole('button', { name: 'Iniciar Check PyME' }).click();
  for (let n = 1; n <= 8; n++) {
    await page.locator(`input[name="answer"][value="${n === 8 ? 'e' : '2'}"]`).check();
    await page.getByRole('button', { name: n === 8 ? 'Terminar cuestionario' : 'Continuar' }).click();
  }
  await page.locator('input[name="name"]').fill('Persona Demo');
  await page.locator('input[name="email"]').fill('av2-demo@example.com');
  await page.locator('input[name="company"]').fill('Empresa Demo');
  await page.locator('input[name="service"]').check();
  await page.getByRole('button', { name: 'Ver y descargar mi informe' }).click();
  const result = await page.evaluate(() => ({ path: location.pathname, scrollWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth, score: document.querySelector('main h1')?.innerText, actions: document.querySelectorAll('main article').length }));
  await page.screenshot({ path: path.join(__dirname, 'av3-check-result-369x545.png'), fullPage: true });
  console.log(JSON.stringify(result));
  await browser.close();
  if (result.path !== '/check-pyme/resultado/' || result.scrollWidth > result.viewportWidth || result.actions !== 3) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
