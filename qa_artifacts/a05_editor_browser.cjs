const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const origin = process.env.QA_ORIGIN;
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1365, height: 900 }, reducedMotion: 'reduce' });
    await context.addCookies([{ name: 'sessionid', value: process.env.QA_SESSION, url: origin }]);
    const page = await context.newPage();
    await page.goto(origin + '/backoffice/content/mediaasset/', { waitUntil: 'domcontentloaded' });
    if (!await page.locator('img[src*="thumb=1"]').count()) throw new Error('La miniatura no aparece en la biblioteca.');
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-media-admin-desktop.png'), fullPage: true });

    await page.goto(origin + '/backoffice/content/article/add/', { waitUntil: 'domcontentloaded' });
    await page.locator('.ql-editor').waitFor();
    await page.locator('#id_title').pressSequentially('PRUEBA — Editor visual');
    if (!await page.locator('#id_slug').inputValue()) throw new Error('El slug automático no se generó.');
    await page.locator('#id_summary').fill('Contenido sintético para verificar el editor visual.');
    await page.locator('#id_category').selectOption('finance');
    await page.locator('.ql-editor').fill('Texto sintético para prueba editorial.');
    await page.getByRole('button', { name: 'Insertar imagen de la biblioteca' }).click();
    await page.getByRole('button', { name: /PRUEBA — Gráfico editorial/ }).click();
    if (!await page.locator('.ql-editor img[alt="Gráfico sintético de prueba"]').count()) throw new Error('La imagen no se insertó en el editor.');
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-editor-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    const editorOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-editor-mobile.png'), fullPage: true });
    if (editorOverflow) throw new Error('Desbordamiento horizontal en el editor móvil.');
    await page.setViewportSize({ width: 1365, height: 900 });
    await page.locator('input[name="_save"]').first().click();
    await page.waitForURL(origin + '/backoffice/content/article/');
    const articleLink = page.locator('#result_list').getByRole('link', { name: 'PRUEBA — Editor visual' }).first();
    await articleLink.click();
    const preview = page.getByRole('link', { name: /Vista previa del artículo guardado/ });
    if (!await preview.count()) throw new Error('Falta la vista previa.');
    const previewPage = await context.newPage();
    await previewPage.goto(origin + await preview.getAttribute('href'), { waitUntil: 'domcontentloaded' });
    if (!await previewPage.getByText('Vista previa editorial').count()) throw new Error('La vista previa no está protegida.');
    await previewPage.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-preview-desktop.png'), fullPage: true });
    await previewPage.close();

    await page.locator('#id_status').selectOption('published');
    await page.locator('input[name="_save"]').first().click();
    await page.waitForURL(origin + '/backoffice/content/article/');
    await articleLink.click();
    const savedSlug = await page.locator('#id_slug').inputValue();
    if (!savedSlug) throw new Error('El artículo quedó sin slug.');
    await page.goto(origin + '/backoffice/content/article/', { waitUntil: 'domcontentloaded' });
    const publicPage = await context.newPage();
    const publicResponse = await publicPage.goto(origin + `/blog/${savedSlug}/`, { waitUntil: 'domcontentloaded' });
    if (!await publicPage.locator('.article-body img').count()) throw new Error(`La imagen no aparece en el artículo público. Slug ${savedSlug}; HTTP ${publicResponse.status()}; lista editorial ${await page.locator('#result_list').innerText()}; página ${((await publicPage.locator('body').innerText()) || '').slice(0, 350)}`);
    await publicPage.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-article-desktop.png'), fullPage: true });
    await publicPage.setViewportSize({ width: 390, height: 844 });
    const overflow = await publicPage.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    if (overflow) throw new Error('Desbordamiento horizontal en el artículo móvil.');
    await publicPage.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-article-mobile.png'), fullPage: true });
    await publicPage.close();

    await articleLink.click();
    await page.locator('#id_summary').fill('Resumen sintético revisado.');
    await page.locator('#id_status').selectOption('retired');
    await page.locator('input[name="_save"]').first().click();
    await page.waitForURL(origin + '/backoffice/content/article/');
    const retired = await page.request.get(origin + `/blog/${savedSlug}/`);
    if (retired.status() !== 404) throw new Error('El artículo retirado sigue público.');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(origin + '/backoffice/content/mediaasset/', { waitUntil: 'domcontentloaded' });
    const mediaOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT, 'a05-media-admin-mobile.png'), fullPage: true });
    if (mediaOverflow) throw new Error('Desbordamiento horizontal en la biblioteca móvil.');
    console.log(`Editor, biblioteca, vista previa, publicación, edición y retiro: OK (slug ${savedSlug})`);
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error.message); process.exitCode = 1; });
