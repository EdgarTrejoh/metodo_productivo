const { chromium } = require('playwright');
const path = require('path');

const origin = 'http://127.0.0.1:8766';

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  try {
    for (const [width, height] of [[1365, 900], [369, 545], [390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height }, javaScriptEnabled: false, deviceScaleFactor: 1, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const response = await page.goto(origin + '/contacto/');
      await page.keyboard.press('Tab');
      const state = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth > innerWidth,
        activeNav: document.querySelector('.site-nav [aria-current="location"]')?.textContent.trim(),
        breadcrumb: document.querySelector('.breadcrumb [aria-current="page"]')?.textContent.trim(),
        focus: document.activeElement?.classList.contains('skip-link') && getComputedStyle(document.activeElement).outlineStyle !== 'none',
        fields: document.querySelectorAll('.contact-panel input:not([type="hidden"]),.contact-panel select,.contact-panel textarea').length,
      }));
      if (response.status() !== 200 || state.overflow || state.activeNav !== 'Contacto' || state.breadcrumb !== 'Contacto' || !state.focus || state.fields !== 4) throw new Error(JSON.stringify({ width, height, state }));
      await page.evaluate(() => document.activeElement.blur());
      await page.screenshot({ path: path.join(__dirname, `a07-contact-${width}x${height}.png`), fullPage: true });
      await page.locator('#id_category').selectOption('request');
      await page.locator('#id_message').fill('Solicitud sintética de verificación visual A-07');
      await page.getByRole('button', { name: 'Enviar mensaje' }).click();
      if (!(await page.locator('#email-error').isVisible())) throw new Error('Falta error de correo en solicitud.');
      if (width === 369) await page.screenshot({ path: path.join(__dirname, 'a07-contact-error-369x545.png'), fullPage: true });
      if (width === 1365) {
        await page.locator('#id_name').fill('Persona sintética A-07');
        await page.locator('#id_email').fill('prueba-a07@example.invalid');
        await page.getByRole('button', { name: 'Enviar mensaje' }).click();
        if (!(await page.getByRole('status').getByText('Recibimos tu mensaje').isVisible())) throw new Error('Falta confirmación.');
        await page.screenshot({ path: path.join(__dirname, 'a07-contact-confirmation-1365x900.png'), fullPage: true });
      }
      console.log(JSON.stringify({ width, height, ...state, validation: true }));
      await context.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
