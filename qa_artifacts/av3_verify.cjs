const { chromium } = require('playwright');
const path = require('path');

const origin = 'http://127.0.0.1:8765';
const sections = [
  ['home', '/', null],
  ['tools', '/herramientas/', 'Herramientas'],
  ['content', '/blog/', 'Contenidos'],
  ['resources', '/recursos/', 'Recursos'],
  ['contact', '/contacto/', 'Contacto'],
  ['check', '/check-pyme/', 'Check PyME'],
];
const viewports = [[1365, 900], [369, 545], [390, 844]];
const rect = element => {
  const { x, y, width, height } = element.getBoundingClientRect();
  return { x, y, width, height };
};

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  let failures = 0;
  const desktopHeaders = [];
  for (const [width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
    for (const [name, url, label] of sections) {
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.goto(origin + url, { waitUntil: 'networkidle' });
      const m = await page.evaluate(rect => {
        const getRect = selector => {
          const e = document.querySelector(selector);
          if (!e) return null;
          const { x, y, width, height } = e.getBoundingClientRect();
          return { x, y, width, height };
        };
        return {
          scrollWidth: document.documentElement.scrollWidth,
          viewportWidth: innerWidth,
          dpr: devicePixelRatio,
          header: getRect('.site-header'),
          logo: getRect('.brand img'),
          menu: getRect('.site-nav'),
          breadcrumb: getRect('.breadcrumb'),
          breadcrumbName: document.querySelector('.breadcrumb [aria-current="page"]')?.textContent.trim() ?? null,
          breadcrumbHome: document.querySelector('.breadcrumb a')?.getAttribute('href') ?? null,
          activeSection: document.querySelector('.site-nav [aria-current="location"]')?.textContent.trim() ?? null,
          footerBlog: [...document.querySelectorAll('.site-footer a')].some(a => a.textContent.trim() === 'Blog'),
          entryGap: (() => {
            const card = document.querySelector('.check-entry-card');
            const button = card?.querySelector('button');
            return card && button ? Math.round(card.getBoundingClientRect().bottom - button.getBoundingClientRect().bottom) : null;
          })(),
          navMinHeight: Math.min(...[...document.querySelectorAll('.site-nav a')].map(e => e.getBoundingClientRect().height)),
        };
      });
      const expectedCrumb = label === null ? m.breadcrumb === null : m.breadcrumbName === label && m.breadcrumbHome === '/';
      const ok = response.status() === 200 && m.scrollWidth <= width && m.dpr === 1 && expectedCrumb &&
        m.activeSection === label && !m.footerBlog && m.navMinHeight >= 40 && errors.length === 0 &&
        (name !== 'check' || m.entryGap < 70);
      if (!ok) failures++;
      const file = `av3-${name}-${width}x${height}.png`;
      await page.screenshot({ path: path.join(__dirname, file), fullPage: true });
      if (width === 1365) {
        desktopHeaders.push({ name, header: m.header, logo: m.logo, menu: m.menu, breadcrumb: m.breadcrumb });
        await page.screenshot({ path: path.join(__dirname, `av3-top-${name}-1365x900.png`), clip: { x: 0, y: 0, width, height: 265 } });
      }
      console.log(JSON.stringify({ name, viewport: `${width}x${height}`, status: response.status(), ok, ...m, errors, file }));
      await page.close();
    }
    if (width === 369) {
      const page = await context.newPage();
      await page.goto(origin + '/herramientas/');
      await page.keyboard.press('Tab');
      const skip = await page.locator(':focus').getAttribute('class');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      const focus = await page.locator(':focus').evaluate(el => ({ text: el.textContent.trim(), outline: getComputedStyle(el).outlineStyle }));
      if (skip !== 'skip-link' || focus.text !== 'Herramientas' || focus.outline !== 'solid') failures++;
      console.log(JSON.stringify({ keyboard: { skip, focus } }));
      await page.close();
    }
    await context.close();
  }
  const baseline = desktopHeaders[0];
  const sameHeader = desktopHeaders.every(item => ['header', 'logo', 'menu'].every(key => JSON.stringify(item[key]) === JSON.stringify(baseline[key])));
  if (!sameHeader) failures++;
  console.log(JSON.stringify({ sameDesktopHeader: sameHeader, desktopHeaders }));
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(origin);
  const links = await page.locator('a[href^="/"]').evaluateAll(els => [...new Set(els.map(el => el.getAttribute('href')))]);
  for (const href of links) {
    const response = await page.request.get(origin + href);
    if (response.status() !== 200) failures++;
    console.log(JSON.stringify({ href, status: response.status() }));
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
