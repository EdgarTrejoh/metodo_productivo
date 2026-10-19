const { chromium } = require('playwright');
const path = require('path');

const origin = 'http://127.0.0.1:8765';

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  let failures = 0;
  for (const [width, height] of [[1365, 900], [369, 545], [390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height }, javaScriptEnabled: false, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const response = await page.goto(origin + '/herramientas/punto-de-equilibrio/');
    const ready = response.status() === 200 && await page.locator('form').count() === 1;
    await page.keyboard.press('Tab');
    const keyboardOk = await page.evaluate(() => document.activeElement?.classList.contains('skip-link') && getComputedStyle(document.activeElement).outlineStyle !== 'none');
    await page.locator('#id_costs').fill('75000');
    await page.locator('#id_price').fill('1200');
    await page.locator('#id_variable_cost').fill('650');
    await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
    const metrics = await page.evaluate(() => ({
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
      units: document.querySelector('.result-card:nth-child(1) strong')?.textContent.trim(),
      income: document.querySelector('.result-card:nth-child(2) strong')?.textContent.trim(),
      margin: document.querySelector('.result-card:nth-child(3) strong')?.textContent.trim(),
      percentage: document.querySelector('.result-card:nth-child(4) strong')?.textContent.trim(),
      activeNav: document.querySelector('.site-nav [aria-current="location"]')?.textContent.trim(),
    }));
    const ok = ready && keyboardOk && !metrics.horizontalOverflow && metrics.units === '137' && metrics.income === '$164,400.00' && metrics.margin === '$550.00' && metrics.percentage === '45.8 %' && metrics.activeNav === 'Herramientas';
    if (!ok) failures++;
    const file = `a02-calculator-${width}x${height}.png`;
    await page.screenshot({ path: path.join(__dirname, file), fullPage: true });
    console.log(JSON.stringify({ viewport: `${width}x${height}`, ok, keyboardOk, ...metrics, file }));
    await context.close();
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
