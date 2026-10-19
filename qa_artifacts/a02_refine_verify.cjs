const { chromium } = require('playwright');
const path = require('path');

const origin = 'http://127.0.0.1:8765';
const route = '/herramientas/punto-de-equilibrio/';
const browserPath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: browserPath, args: ['--no-sandbox'] });
  let failures = 0;
  for (const [width, height] of [[1365, 900], [369, 545], [390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, javaScriptEnabled: false, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const methods = [];
    page.on('request', request => { if (request.url().startsWith(origin + route)) methods.push(request.method()); });
    await page.goto(origin + route);
    const breadcrumb = await page.locator('.breadcrumb').innerText();
    await page.keyboard.press('Tab');
    const focus = await page.evaluate(() => document.activeElement?.classList.contains('skip-link') && getComputedStyle(document.activeElement).outlineStyle !== 'none');
    await page.locator('#id_costs').fill('75000');
    await page.locator('#id_price').fill('1200');
    await page.locator('#id_variable_cost').fill('650');
    await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
    const positive = await page.locator('.result-card strong').allTextContents();
    const positiveFile = `a02-refined-positive-${width}x${height}.png`;
    await page.screenshot({ path: path.join(__dirname, positiveFile), fullPage: true });

    // Una recarga del documento POST puede pedir confirmación; si el navegador
    // la ejecuta, el servidor redirige por GET sin conservar valores.
    let reloadOutcome = 'completed';
    try { await page.reload({ waitUntil: 'load', timeout: 8000 }); }
    catch (error) { reloadOutcome = error.name; }
    const afterReload = await page.locator('#id_costs').inputValue();
    const reloadHasResult = await page.locator('#resultado').count();

    // Limpiar funciona tanto después de resultado como de errores sin JS.
    await page.goto(origin + route);
    await page.locator('#id_costs').fill('-1');
    await page.locator('#id_price').fill('1200');
    await page.locator('#id_variable_cost').fill('650');
    await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
    const error = await page.locator('#costs-error').innerText();
    const preserved = await page.locator('#id_price').inputValue();
    const errorFile = `a02-refined-error-${width}x${height}.png`;
    await page.screenshot({ path: path.join(__dirname, errorFile), fullPage: true });
    await page.getByRole('link', { name: 'Limpiar' }).click();
    const clean = await page.locator('#id_costs').inputValue() === '' && await page.locator('#id_price').inputValue() === '' && await page.locator('#costs-error').count() === 0 && await page.locator('#resultado').count() === 0;

    await page.locator('#id_costs').fill('0');
    await page.locator('#id_price').fill('100');
    await page.locator('#id_variable_cost').fill('150');
    await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
    const negative = await page.locator('.result-card:nth-child(3) strong').innerText();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    const note = await page.locator('.method-note').evaluate(el => ({ fontSize: getComputedStyle(el).fontSize, lineHeight: getComputedStyle(el).lineHeight }));
    const negativeFile = `a02-refined-negative-${width}x${height}.png`;
    await page.screenshot({ path: path.join(__dirname, negativeFile), fullPage: true });
    await page.getByRole('link', { name: 'Limpiar' }).click();
    const cleanAfterResult = await page.locator('#id_costs').inputValue() === '' && await page.locator('#resultado').count() === 0;
    const validation = [];
    for (const [costs, price, variableCost, selector, expected] of [
      ['', '1200', '650', '#costs-error', 'Ingresa los costos fijos mensuales.'],
      ['100', '0', '20', '#price-error', 'Se requiere un precio positivo'],
      ['100', 'abc', '20', '#price-error', 'Ingresa un importe numérico válido.'],
      ['100.001', '1200', '20', '#costs-error', 'Usa como máximo dos decimales.'],
      ['100', '1200', '-1', '#variable-cost-error', 'El costo variable no puede ser negativo.'],
    ]) {
      await page.goto(origin + route);
      await page.locator('#id_costs').fill(costs);
      await page.locator('#id_price').fill(price);
      await page.locator('#id_variable_cost').fill(variableCost);
      await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
      validation.push((await page.locator(selector).innerText()).includes(expected) && await page.locator('#resultado').count() === 0);
    }
    await page.goto(origin + route);
    await page.locator('#id_costs').fill('999999999.99');
    await page.locator('#id_price').fill('0.02');
    await page.locator('#id_variable_cost').fill('0.01');
    await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
    const large = await page.locator('.result-card:nth-child(1) strong').innerText();
    const largeOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.goto(origin + route);
    await page.locator('#id_costs').fill('0');
    await page.locator('#id_price').fill('0.01');
    await page.locator('#id_variable_cost').fill('999999999.99');
    await page.getByRole('button', { name: 'Calcular equilibrio' }).click({ force: true });
    const negativeLarge = await page.locator('.result-card:nth-child(3) strong').innerText();
    const negativeLargeOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    const ok = breadcrumb.replace(/\s+/g, ' ').includes('Inicio / Herramientas / Punto de equilibrio') && focus && positive.map(s => s.trim()).join('|') === '137|$164,400.00|$550.00|45.8 %' && afterReload === '' && reloadHasResult === 0 && error.includes('no pueden ser negativos') && preserved === '1200' && clean && cleanAfterResult && negative === '-$50.00' && !overflow && validation.every(Boolean) && large === '99,999,999,999' && !largeOverflow && negativeLarge === '-$999,999,999.98' && !negativeLargeOverflow;
    if (!ok) failures++;
    console.log(JSON.stringify({ viewport: `${width}x${height}`, ok, focus, positive, reloadOutcome, afterReload, reloadHasResult, methods, error, preserved, clean, cleanAfterResult, negative, overflow, note, validation, large, largeOverflow, negativeLarge, negativeLargeOverflow, positiveFile, errorFile, negativeFile }));
    await context.close();
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
