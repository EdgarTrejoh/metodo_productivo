const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const older = await context.newPage();
    const newer = await context.newPage();
    const origin = process.env.QA_ORIGIN;
    await older.goto(origin + '/check-pyme/');
    await older.getByRole('button', { name: 'Iniciar Check PyME' }).click();
    const oldExecution = await older.locator('input[name="execution"]').inputValue();
    await newer.goto(origin + '/check-pyme/');
    await newer.getByRole('button', { name: 'Iniciar Check PyME' }).click();
    const newExecution = await newer.locator('input[name="execution"]').inputValue();
    if (oldExecution === newExecution) throw new Error('El inicio nuevo no reemplazó la ejecución.');
    await older.locator('input[name="answer"][value="2"]').check();
    await older.getByRole('button', { name: 'Continuar' }).click();
    if (!await older.getByText('Este formulario pertenece a un Check anterior').count()) throw new Error('La pestaña antigua no fue rechazada.');
    await older.screenshot({ path: path.join(process.env.QA_OUTPUT, 'c01-stale-tab.png'), fullPage: true });
    await newer.reload();
    if (await newer.locator('input[name="answer"]:checked').count()) throw new Error('La respuesta antigua afectó la ejecución nueva.');
    await newer.goto(origin + '/privacidad/');
    await newer.goBack();
    if (await newer.locator('input[name="execution"]').inputValue() !== newExecution) throw new Error('Privacidad revocó la ejecución vigente.');
    await newer.locator('input[name="answer"][value="2"]').check();
    await newer.getByRole('button', { name: 'Continuar' }).click();
    if (!newer.url().endsWith('/check-pyme/pregunta/2/')) throw new Error('La ejecución nueva no puede continuar.');
    await newer.screenshot({ path: path.join(process.env.QA_OUTPUT, 'c01-current-tab.png'), fullPage: true });
    console.log('C-01: dos pestañas, formulario obsoleto rechazado; nueva ejecución intacta y privacidad sin revocación.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
