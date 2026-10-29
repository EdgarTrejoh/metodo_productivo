const { chromium } = require('playwright');
const { spawnSync } = require('child_process');
const path = require('path');

const origin = 'http://127.0.0.1:8767';
const output = __dirname;

async function complete(page) {
  await page.goto(origin + '/check-pyme/');
  await page.getByRole('button', { name: 'Iniciar Check PyME' }).click();
  for (let number = 1; number <= 8; number++) {
    await page.locator(`input[name="answer"][value="${number === 8 ? 'e' : '2'}"]`).check();
    await page.getByRole('button', { name: number === 8 ? 'Terminar cuestionario' : 'Continuar' }).click();
  }
  await page.locator('#id_name').fill('Persona Sintética C02');
  await page.locator('#id_email').fill(`c02-${Date.now()}@example.com`);
  await page.locator('#id_company').fill('Empresa Sintética C02');
  await page.locator('#id_service').check();
  await page.getByRole('button', { name: 'Ver mi informe' }).click();
  if (!page.url().endsWith('/check-pyme/resultado/')) throw new Error('No se obtuvo el resultado.');
}

async function expectDenied(context, route) {
  const response = await context.request.get(origin + route);
  if (response.status() !== 410 || !response.headers()['cache-control']?.includes('no-store')) {
    throw new Error(`Acceso no denegado o cacheable en ${route}: ${response.status()}`);
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  try {
    const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    await expectDenied(context, '/check-pyme/resultado/');
    await expectDenied(context, '/check-pyme/informe.pdf');
    await complete(page);
    const resultResponse = await page.reload();
    if (resultResponse.status() !== 200 || !resultResponse.headers()['cache-control']?.includes('no-store')) throw new Error('Resultado no autorizado o cacheable.');
    await page.screenshot({ path: path.join(output, 'c02-result.png'), fullPage: true });
    const otherTab = await context.newPage();
    await otherTab.goto(origin + '/check-pyme/resultado/');
    if (!await otherTab.getByText('100 / 100').count()) throw new Error('Otra pestaña de la sesión no accede al resultado.');
    const separate = await browser.newContext();
    await expectDenied(separate, '/check-pyme/resultado/');
    await expectDenied(separate, '/check-pyme/informe.pdf');
    await separate.close();
    for (let attempt = 0; attempt < 2; attempt++) {
      const [download] = await Promise.all([
        page.waitForEvent('download'),
        page.getByRole('link', { name: 'Descargar informe PDF' }).click(),
      ]);
      if (download.suggestedFilename() !== 'check-pyme.pdf') throw new Error('Nombre del PDF incorrecto.');
    }
    const pdfResponse = await context.request.get(origin + '/check-pyme/informe.pdf');
    if (pdfResponse.status() !== 200 || !pdfResponse.headers()['cache-control']?.includes('no-store')) throw new Error('PDF no autorizado o cacheable.');
    await page.getByRole('button', { name: 'Salir del diagnóstico' }).click();
    const history = await page.goBack();
    if (!history || history.status() !== 410 || await page.getByText('100 / 100').count()) throw new Error('Atrás restauró el resultado sensible.');
    await page.screenshot({ path: path.join(output, 'c02-expired.png'), fullPage: true });
    await expectDenied(context, '/check-pyme/resultado/');
    await expectDenied(context, '/check-pyme/informe.pdf');
    await otherTab.reload();
    if (await otherTab.getByText('100 / 100').count()) throw new Error('Otra pestaña conservó acceso tras la salida.');

    await complete(page);
    const cookie = (await context.cookies(origin)).find(item => item.name === 'sessionid');
    if (!cookie) throw new Error('No hay sesión técnica para simular el vencimiento.');
    const python = "import sys,time; from django.contrib.sessions.backends.db import SessionStore; s=SessionStore(session_key=sys.stdin.read().strip()); c=s['check']; c['last_activity']=time.time()-1800; s['check']=c; s.save()";
    const expired = spawnSync('docker', ['compose', '--env-file', '.env.docker', '-f', 'compose.yaml', '-f', 'compose.private.yaml', 'exec', '-T', 'web', 'python', 'manage.py', 'shell', '-c', python], { input: cookie.value, encoding: 'utf8', cwd: process.cwd() });
    if (expired.status !== 0) throw new Error('No se pudo simular el vencimiento de la sesión de prueba.');
    const expiryResponse = await page.reload();
    if (expiryResponse.status() !== 410 || await page.getByText('100 / 100').count()) throw new Error('Resultado accesible tras 30 minutos de inactividad.');
    await expectDenied(context, '/check-pyme/informe.pdf');
    console.log('C-02 navegador: captura protegida, dos descargas, otra pestaña, navegador separado, salida, historial y vencimiento correctos.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
