const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  try {
    for (const [width, height] of [[1365, 900], [390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
      await context.addCookies([{ name: 'sessionid', value: process.env.QA_SESSION, url: process.env.QA_ORIGIN }]);
      const page = await context.newPage();
      const response = await page.goto(process.env.QA_ORIGIN + '/backoffice/leads/contactsubmission/', { waitUntil: 'domcontentloaded' });
      const summary = await page.locator('.contact-summary strong').allTextContents();
      const state = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth > innerWidth,
        rows: document.querySelectorAll('#result_list tbody tr').length,
      }));
      if (response.status() !== 200 || summary.join(',') !== '3,2' || state.rows !== 3 || state.overflow) {
        throw new Error(JSON.stringify({ width, height, status: response.status(), summary, state }));
      }
      await page.screenshot({ path: path.join(process.env.QA_OUTPUT, `a07-inbox-${width}x${height}.png`), fullPage: true });
      if (width === 1365) {
        await page.getByRole('link', { name: /Remitente de prueba/ }).click();
        if (!(await page.getByText('Comentario sintético completo para comprobar el detalle.').isVisible())) throw new Error('No aparece el mensaje completo.');
        await page.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a07-inbox-detail-1365x900.png'), fullPage: true });
      }
      console.log(JSON.stringify({ width, height, summary, ...state }));
      await context.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
