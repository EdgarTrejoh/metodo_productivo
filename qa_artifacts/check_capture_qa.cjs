const { chromium } = require('playwright');
const path = require('path');

async function reachCapture(page, origin) {
  await page.goto(origin + '/check-pyme/');
  await page.getByRole('button', { name: 'Iniciar Check PyME' }).click();
  for (let number = 1; number <= 8; number++) {
    await page.locator(`input[name="answer"][value="${number === 8 ? 'e' : '2'}"]`).check();
    await page.getByRole('button', { name: number === 8 ? 'Terminar cuestionario' : 'Continuar' }).click();
  }
  if (!page.url().endsWith('/check-pyme/datos/')) throw new Error('No se alcanzó la captura.');
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--no-sandbox'],
  });
  try {
    const closeResults = [];
    for (const [width, height, label] of [[1365, 900, 'desktop'], [390, 844, 'mobile-390'], [369, 545, 'mobile-369']]) {
      const context = await browser.newContext({ viewport: { width, height } });
      const page = await context.newPage();
      await reachCapture(page, process.env.QA_ORIGIN);
      const link = page.getByRole('link', { name: /Consultar aviso de privacidad integral/ });
      if (await link.getAttribute('href') !== '/privacidad/?desde=check') throw new Error('Ruta de privacidad incorrecta.');
      if (await link.getAttribute('target') !== '_blank') throw new Error('Privacidad debe abrir nueva pestaña.');
      if (await page.locator('input[type="checkbox"]:checked').count()) throw new Error('Consentimiento preseleccionado.');
      const checkboxOrder = await page.locator('.check-capture-consent label').evaluateAll(labels => labels.map(label => {
        const box = label.querySelector('input[type="checkbox"]');
        return Boolean(box && label.firstElementChild === box && box.getBoundingClientRect().left < label.querySelector('span').getBoundingClientRect().left);
      }));
      if (!checkboxOrder.every(Boolean)) throw new Error('Checkbox fuera de su etiqueta o a la derecha.');
      const overflows = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (overflows) throw new Error(`Desbordamiento horizontal en ${label}.`);
      await page.screenshot({ path: path.join(process.env.QA_OUTPUT, `check-capture-${label}.png`), fullPage: true });
      if (label === 'desktop' || label === 'mobile-390') {
        await page.locator('#id_name').fill('Persona de prueba');
        await page.locator('#id_email').fill('prueba@example.com');
        await page.locator('#id_company').fill('Empresa Ficticia');
        const execution = await page.locator('input[name="execution"]').inputValue();
        const [privacy] = await Promise.all([context.waitForEvent('page'), link.click()]);
        await privacy.waitForLoadState();
        if (!privacy.url().endsWith('/privacidad/?desde=check')) throw new Error('El enlace no abrió privacidad desde el Check.');
        if (!await privacy.getByText('Texto legal no publicable').count()) throw new Error('Falta aviso de estado provisional.');
        if (!await privacy.getByRole('button', { name: 'Cerrar esta pestaña y continuar con mi Check' }).count()) throw new Error('Falta la acción de cierre.');
        if (!await privacy.getByText('Si el navegador no permite cerrarla automáticamente').count()) throw new Error('Falta alternativa de cierre.');
        if (await privacy.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) throw new Error('Privacidad desborda el viewport.');
        await privacy.screenshot({ path: path.join(process.env.QA_OUTPUT, `privacy-check-${label}.png`), fullPage: true });
        await privacy.getByRole('button', { name: 'Cerrar esta pestaña y continuar con mi Check' }).click();
        await privacy.waitForEvent('close', { timeout: 2000 }).catch(() => {});
        closeResults.push(`${label}: ${privacy.isClosed() ? 'cierre automático' : 'cierre manual indicado'}`);
        if (!privacy.isClosed()) await privacy.close();
        if (await page.locator('#id_name').inputValue() !== 'Persona de prueba') throw new Error('Se perdió el nombre capturado.');
        if (await page.locator('#id_email').inputValue() !== 'prueba@example.com') throw new Error('Se perdió el correo capturado.');
        if (await page.locator('input[name="execution"]').inputValue() !== execution) throw new Error('Privacidad reemplazó la ejecución.');
        await page.locator('label[for="id_service"]').click();
        if (!await page.locator('#id_service').isChecked()) throw new Error('La etiqueta no activa el consentimiento.');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Shift+Tab');
        const focus = await page.locator('#id_service').evaluate(el => getComputedStyle(el).outlineStyle);
        if (focus === 'none') throw new Error('Sin foco visible.');
        await page.getByRole('button', { name: 'Ver mi informe' }).click();
        if (!page.url().endsWith('/check-pyme/resultado/')) throw new Error('No se pudo continuar el Check tras cerrar privacidad.');
      }
      await context.close();

      if (label === 'desktop' || label === 'mobile-390') {
        const otherContext = await browser.newContext({ viewport: { width, height } });
        const otherPage = await otherContext.newPage();
        await otherPage.goto(process.env.QA_ORIGIN + '/herramientas/');
        await otherPage.getByRole('link', { name: 'Privacidad · provisional' }).click();
        const back = otherPage.getByRole('button', { name: 'Volver a la página anterior' });
        if (!await back.isVisible()) throw new Error('Falta retorno desde otra sección.');
        await otherPage.screenshot({ path: path.join(process.env.QA_OUTPUT, `privacy-other-${label}.png`), fullPage: true });
        await back.click();
        if (!otherPage.url().endsWith('/herramientas/')) throw new Error('El retorno no llegó a Herramientas.');
        await otherContext.close();
      }
    }
    const directContext = await browser.newContext();
    const directPage = await directContext.newPage();
    await directPage.goto(process.env.QA_ORIGIN + '/privacidad/');
    if (await directPage.getByRole('button', { name: 'Volver a la página anterior' }).isVisible()) throw new Error('Visita directa ofrece historial inexistente.');
    if (!await directPage.getByRole('link', { name: 'Ir al inicio' }).isVisible()) throw new Error('Visita directa sin enlace al inicio.');
    await directPage.screenshot({ path: path.join(process.env.QA_OUTPUT, 'privacy-direct-desktop.png'), fullPage: true });
    await directContext.close();
    console.log(`Privacidad: ${closeResults.join(', ')}; continuidad del formulario, retorno desde Herramientas y entrada directa; escritorio y móvil sin desbordamiento.`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
