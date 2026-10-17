const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  const origin = 'http://127.0.0.1:8765';
  const cases = [
    ['home', '/', 1365, 900], ['tools', '/herramientas/', 1365, 900], ['contact', '/contacto/', 1365, 900],
    ['home', '/', 369, 545], ['home', '/', 390, 844],
    ['tools', '/herramientas/', 369, 545], ['tools', '/herramientas/', 390, 844],
    ['contact', '/contacto/', 390, 844], ['resources', '/recursos/', 390, 844],
    ['blog', '/blog/', 390, 844], ['check', '/check-pyme/', 369, 545],
  ];
  let failures = 0;
  for (const [name, url, width, height] of cases) {
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const response = await page.goto(origin + url, { waitUntil: 'networkidle' });
    const metrics = await page.evaluate(() => ({
      innerWidth, scrollWidth: document.documentElement.scrollWidth,
      dpr: devicePixelRatio,
      h1: document.querySelector('h1')?.innerText,
      logoCount: document.querySelectorAll('.brand img').length,
      fakeMonogram: !!document.querySelector('.section-mark'),
    }));
    const filename = `av2-${name}-${width}x${height}.png`;
    await page.screenshot({ path: path.join(__dirname, filename), fullPage: true });
    const ok = response.status() === 200 && metrics.scrollWidth <= width && !metrics.fakeMonogram && errors.length === 0;
    if (!ok) failures++;
    console.log(JSON.stringify({ name, url, viewport: `${width}x${height}`, status: response.status(), ...metrics, errors, ok, screenshot: filename }));
    if (name === 'home' && width === 369) {
      await page.keyboard.press('Tab');
      const keyboardFirstFocus = await page.locator(':focus').getAttribute('class');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      const nav = await page.evaluate(() => ({
        focused: document.activeElement?.textContent.trim(),
        outline: getComputedStyle(document.activeElement).outlineStyle,
        minTargetHeight: Math.min(...[...document.querySelectorAll('.site-nav a')].map(a => a.getBoundingClientRect().height)),
      }));
      if (keyboardFirstFocus !== 'skip-link' || nav.focused !== 'Herramientas' || nav.outline !== 'solid' || nav.minTargetHeight < 40) failures++;
      console.log(JSON.stringify({ keyboardFirstFocus, nav }));
    }
    await context.close();
  }
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  await page.goto(origin, { waitUntil: 'networkidle' });
  const links = await page.locator('a[href^="/"]').evaluateAll(els => [...new Set(els.map(e => e.getAttribute('href')))]);
  for (const href of links) {
    const response = await page.request.get(origin + href);
    if (response.status() !== 200) failures++;
    console.log(JSON.stringify({ href, status: response.status() }));
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
