const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const origin = process.env.QA_ORIGIN;
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1365, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    for (const [width, height, label] of [[1365, 900, 'desktop'], [390, 844, 'mobile']]) {
      await page.setViewportSize({ width, height });
      for (const [url, name] of [['/tienda/', 'catalog'], ['/tienda/producto-sintetico-qa/', 'detail']]) {
        const response = await page.goto(origin + url, { waitUntil: 'domcontentloaded' });
        if (response.status() !== 200) throw new Error(`${url}: HTTP ${response.status()}`);
        if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error(`${url}: desbordamiento horizontal a ${width}px`);
        if (name === 'catalog' && await page.getByRole('link', { name: 'Probar compra en Stripe' }).count()) throw new Error('El botón piloto apareció en el catálogo.');
        if (name === 'detail') {
          const pilot = page.getByRole('link', { name: 'Probar compra en Stripe' });
          if (await pilot.getAttribute('href') !== 'https://buy.stripe.com/test_AbC123456789') throw new Error('El botón no usa el enlace TEST del producto.');
          if (!await page.getByText('Pago de prueba. No se realizan cargos reales ni se entregan archivos.').count()) throw new Error('Falta la advertencia de pago de prueba.');
        }
        await page.screenshot({ path: path.join(process.env.QA_OUTPUT, `b01-${name}-${label}.png`), fullPage: true });
        if (name === 'detail' && label === 'desktop') {
          await page.route('https://buy.stripe.com/**', route => route.fulfill({ status: 200, body: 'Destino TEST sintético interceptado' }));
          await page.getByRole('link', { name: 'Probar compra en Stripe' }).click();
          await page.waitForURL('https://buy.stripe.com/test_AbC123456789');
        }
      }
    }
    await context.addCookies([{ name: 'sessionid', value: process.env.QA_SESSION, url: origin }]);
    await page.setViewportSize({ width: 1365, height: 900 });
    const response = await page.goto(origin + '/backoffice/store/digitalproduct/', { waitUntil: 'domcontentloaded' });
    if (response.status() !== 200) throw new Error(`Admin: HTTP ${response.status()}`);
    if (!await page.getByText('Producto sintético de QA').count()) throw new Error('El producto no aparece en el Admin.');
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT, 'b01-admin-desktop.png'), fullPage: true });
    console.log('B-01: botón TEST y destino verificados sin contactar Stripe; catálogo, ficha y Admin OTP visibles; escritorio y móvil sin desbordamiento.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
