const { chromium } = require('playwright');
const path = require('path');

const rows = [
  ['Mes', 'Pedidos', 'Variación'],
  ['Enero', '80', '—'],
  ['Febrero', '92', '+15.0 %'],
  ['Marzo', '86', '-6.5 %'],
];
const check = (actual, expected, label) => {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error(`${label}: ${JSON.stringify(actual)}`);
};
async function grid(page, selector) {
  return page.locator(selector).first().evaluate(table =>
    [...table.rows].map(row => [...row.cells].map(cell => cell.textContent.trim()))
  );
}
async function action(page, category, label) {
  const menu = page.locator(`.ql-table-dropdown[data-category="${category}"]`);
  if (!await menu.isVisible()) {
    const state = await page.evaluate(() => {
      const quill = Quill.find(document.querySelector('#article-visual-editor'));
      return { selection: quill.getSelection(), tools: document.querySelector('.ql-table-menus-container')?.className, html: quill.root.querySelector('table')?.outerHTML.slice(-500) };
    });
    throw new Error(`Menú ${category} oculto: ${JSON.stringify(state)}`);
  }
  await menu.evaluate(element => element.click());
  await menu.locator('li').filter({ hasText: label }).first().evaluate(element => element.click());
}

(async () => {
  const origin = process.env.QA_ORIGIN;
  const output = process.env.QA_OUTPUT;
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1365, height: 900 }, reducedMotion: 'reduce' });
    await context.addCookies([{ name: 'sessionid', value: process.env.QA_SESSION, url: origin }]);
    const page = await context.newPage();
    await page.goto(origin + '/backoffice/content/article/add/', { waitUntil: 'domcontentloaded' });
    await page.locator('.ql-editor').waitFor();
    await page.locator('#id_title').fill('PRUEBA — Tabla editorial');
    await page.locator('#id_slug').fill('prueba-tabla-editorial');
    await page.locator('#id_summary').fill('Artículo sintético de verificación.');
    await page.locator('#id_category').selectOption('data');
    await page.locator('.ql-editor').click();
    await page.keyboard.insertText('Las decisiones financieras necesitan datos claros y comparables.');
    await page.keyboard.press('Enter');
    await page.evaluate(() => Quill.find(document.querySelector('#article-visual-editor')).getModule('table-better').insertTable(4, 3));
    if (await page.locator('.ql-editor table tr').count() !== 4) throw new Error('No se insertaron cuatro filas.');
    for (let r = 0; r < rows.length; r++) {
      for (let c = 0; c < rows[r].length; c++) {
        await page.locator('.ql-editor table tr').nth(r).locator('td,th').nth(c).click();
        await page.keyboard.insertText(rows[r][c]);
      }
    }
    check(await grid(page, '.ql-editor table'), rows, 'Editor inicial');
    await page.locator('.ql-editor table tr').nth(1).locator('td').nth(1).click();
    await page.evaluate(() => Quill.find(document.querySelector('#article-visual-editor')).format('align', 'right'));
    if (!await page.locator('.ql-editor table tr').nth(1).locator('td').nth(1).locator('.ql-align-right').count()) throw new Error('No se aplicó alineación a la cifra.');
    await page.locator('.ql-editor table tr').first().locator('td').first().click();
    await action(page, 'row', 'Header row');
    if (await page.locator('.ql-editor table tr').first().locator('th').count() !== 3) throw new Error('No se aplicaron encabezados.');
    await page.locator('.ql-editor table tr').last().locator('td').last().click();
    await action(page, 'row', 'Insert row below');
    if (await page.locator('.ql-editor table tr').count() !== 5) throw new Error('No se insertó fila.');
    await page.locator('.ql-editor table tr').last().locator('td').last().click();
    await action(page, 'row', 'Delete row');
    await page.locator('.ql-editor table tr').nth(1).locator('td').last().click();
    await action(page, 'column', 'Insert column right');
    if (await page.locator('.ql-editor table tr').last().locator('td,th').count() !== 4) throw new Error('No se insertó columna.');
    await page.locator('.ql-editor table tr').nth(1).locator('td,th').last().click();
    await page.keyboard.insertText('Temporal');
    await page.evaluate(() => {
      const module = Quill.find(document.querySelector('#article-visual-editor')).getModule('table-better');
      const cell = module.quill.root.querySelector('table tr:nth-child(2) td:last-child');
      module.cellSelection.setSelected(cell, false);
      module.showTools();
      const menu = document.querySelector('.ql-table-dropdown[data-category="column"]');
      menu.click();
      [...menu.querySelectorAll('li')].find(item => item.textContent === 'Delete column').click();
    });
    check(await grid(page, '.ql-editor table'), rows, 'Edición de filas y columnas');
    await page.screenshot({ path: path.join(output, 'a05-table-editor-desktop.png'), fullPage: true });
    await page.locator('input[name="_save"]').first().click();
    await page.waitForURL(origin + '/backoffice/content/article/');
    await page.locator('#result_list').getByRole('link', { name: 'PRUEBA — Tabla editorial' }).click();
    check(await grid(page, '.ql-editor table'), rows, 'Borrador reabierto');
    if (!await page.locator('.ql-editor table .ql-align-right').count()) throw new Error('Se perdió la alineación al reabrir.');
    const savedSlug = await page.locator('#id_slug').inputValue();
    if (await page.locator('.ql-editor table th').count() !== 3) throw new Error('Encabezados perdidos al reabrir.');
    const previewUrl = await page.getByRole('link', { name: /Vista previa del artículo guardado/ }).getAttribute('href');
    const preview = await context.newPage();
    await preview.goto(origin + previewUrl, { waitUntil: 'domcontentloaded' });
    check(await grid(preview, '.article-body table'), rows, 'Vista previa');
    await preview.screenshot({ path: path.join(output, 'a05-table-preview-desktop.png'), fullPage: true });
    await preview.close();
    await page.locator('#id_status').selectOption('published');
    await page.locator('input[name="_save"]').first().click();
    await page.waitForURL(origin + '/backoffice/content/article/');
    const article = await context.newPage();
    const publicResponse = await article.goto(origin + `/blog/${savedSlug}/`, { waitUntil: 'domcontentloaded' });
    if (publicResponse.status() !== 200) throw new Error(`Publicación HTTP ${publicResponse.status()}, slug ${savedSlug}; estado admin ${await page.locator('#id_status').inputValue()}`);
    check(await grid(article, '.article-body table'), rows, 'Publicado');
    if (!await article.locator('.article-body table .ql-align-right').count()) throw new Error('Se perdió la alineación publicada.');
    await article.screenshot({ path: path.join(output, 'a05-table-public-desktop.png'), fullPage: true });
    for (const width of [369, 390]) {
      await article.setViewportSize({ width, height: width === 369 ? 545 : 844 });
      const size = await article.evaluate(() => {
        const wrapper = document.querySelector('.article-table-scroll');
        const overflowing = [...document.querySelectorAll('body *')].filter(el => el.scrollWidth > el.clientWidth + 1).slice(0, 12).map(el => ({ tag: el.tagName, className: el.className, scroll: el.scrollWidth, client: el.clientWidth, text: el.tagName === 'P' ? el.outerHTML.slice(0, 180) : null, whiteSpace: getComputedStyle(el).whiteSpace }));
        return { page: document.documentElement.scrollWidth, body: document.body.scrollWidth, viewport: innerWidth, wrapper: wrapper.clientWidth, scroll: wrapper.scrollWidth, overflowing };
      });
      if (size.page > size.viewport) throw new Error(`Artículo móvil ${width}px: ${JSON.stringify(size)}`);
      await article.screenshot({ path: path.join(output, `a05-table-public-${width}.png`), fullPage: true });
    }
    await article.close();
    const wide = await context.newPage();
    for (const width of [1365, 369, 390]) {
      await wide.setViewportSize({ width, height: width === 369 ? 545 : 844 });
      await wide.goto(origin + '/blog/prueba-tabla-ancha/', { waitUntil: 'domcontentloaded' });
      const size = await wide.evaluate(() => {
        const wrapper = document.querySelector('.article-table-scroll');
        return { page: document.documentElement.scrollWidth, viewport: innerWidth, wrapper: wrapper.clientWidth, scroll: wrapper.scrollWidth };
      });
      if (size.page > size.viewport || (width < 500 && size.scroll <= size.wrapper)) throw new Error(`Tabla ancha ${width}px: ${JSON.stringify(size)}`);
      if (width < 500) await wide.screenshot({ path: path.join(output, `a05-table-wide-${width}.png`), fullPage: true });
    }
    await wide.close();
    await page.locator('#result_list').getByRole('link', { name: 'PRUEBA — Tabla editorial' }).click();
    check(await grid(page, '.ql-editor table'), rows, 'Editar publicado');
    await page.locator('#id_status').selectOption('retired');
    await page.locator('input[name="_save"]').first().click();
    await page.waitForURL(origin + '/backoffice/content/article/');
    const retired = await page.request.get(origin + `/blog/${savedSlug}/`);
    if (retired.status() !== 404) throw new Error('El artículo retirado sigue público.');
    console.log('Tabla 4×3: edición, borrador, vista previa, publicación y retiro correctos; móvil 369/390 sin desbordamiento de página.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; });
