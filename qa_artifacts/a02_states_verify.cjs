const { chromium } = require('playwright');
const path = require('path');

const origin = 'http://127.0.0.1:8765';
const route = '/herramientas/punto-de-equilibrio/';
const cases = [
  { name: 'positive', costs: '75000', price: '1200', variable: '650', label: 'Margen positivo', values: ['137', '$164,400.00', '$550.00', '45.8 %'] },
  { name: 'zero', costs: '65000', price: '1200', variable: '1200', label: 'Margen cero', values: ['No aplica', 'No aplica', '$0.00', '0.0 %'] },
  { name: 'negative', costs: '65000', price: '1200', variable: '4500', label: 'Margen negativo', values: ['No aplica', 'No aplica', '-$3,300.00', '-275.0 %'] },
];

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  let failures = 0;
  for (const [width, height] of [[1365, 900], [369, 545], [390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, javaScriptEnabled: false, reducedMotion: 'reduce' });
    for (const item of cases) {
      const page = await context.newPage();
      await page.goto(origin + route);
      await page.locator('#id_costs').fill(item.costs);
      await page.locator('#id_price').fill(item.price);
      await page.locator('#id_variable_cost').fill(item.variable);
      await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
      const actual = await page.locator('.result-card strong').allTextContents();
      const state = await page.locator('#resultado').getAttribute('class');
      const label = await page.locator('.result-state').innerText();
      const details = await page.evaluate(() => {
        const rgb = value => value.match(/[\d.]+/g).slice(0, 3).map(Number);
        const lum = value => rgb(value).map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4).reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0);
        const contrast = element => {
          const style = getComputedStyle(element);
          const background = style.backgroundColor === 'rgba(0, 0, 0, 0)' ? 'rgb(255, 255, 255)' : style.backgroundColor;
          const fg = lum(style.color), bg = lum(background);
          return +((Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05)).toFixed(2);
        };
        const status = document.querySelector('.result-state');
        const explanation = document.querySelector('.result-explanation');
        return {
          overflow: document.documentElement.scrollWidth > innerWidth,
          cardCount: document.querySelectorAll('.result-card').length,
          explanation: explanation.textContent.trim(),
          statusContrast: contrast(status),
          explanationContrast: contrast(explanation),
          resultLabelled: document.querySelector('#resultado')?.getAttribute('aria-labelledby') === 'result-title',
        };
      });
      const ok = actual.map(s => s.trim()).join('|') === item.values.join('|') && state.includes(`result-${item.name}`) && label === item.label && details.cardCount === 4 && !details.overflow && details.statusContrast >= 4.5 && details.explanationContrast >= 4.5 && details.resultLabelled;
      if (!ok) failures++;
      const file = `a02-state-${item.name}-${width}x${height}.png`;
      await page.screenshot({ path: path.join(__dirname, file), fullPage: true });
      console.log(JSON.stringify({ viewport: `${width}x${height}`, state: item.name, ok, values: actual.map(s => s.trim()), label, ...details, file }));
      await page.close();
    }
    await context.close();
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
