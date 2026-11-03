// Verificación local con Chrome real y datos sintéticos. No incluye tokens ni capturas.
const { spawn } = require('node:child_process');
const { mkdtempSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');

const origin = 'http://127.0.0.1:8788';
const port = 9229;
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', [
  '--headless=new', '--no-first-run', `--remote-debugging-port=${port}`,
  '--remote-allow-origins=*', `--user-data-dir=${mkdtempSync(join(tmpdir(), 'mp-o08-chrome-'))}`,
], { stdio: 'ignore', windowsHide: true });

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function endpoint(path, options) {
  for (let i = 0; i < 40; i++) {
    try { return await (await fetch(`http://127.0.0.1:${port}${path}`, options)).json(); }
    catch { await delay(250); }
  }
  throw Error('Chrome DevTools no respondió');
}

(async () => {
  let socket;
  try {
    const target = await endpoint(`/json/new?${encodeURIComponent(origin + '/')}`, { method: 'PUT' });
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
    let next = 0;
    const pending = new Map();
    const resourceReferers = [];
    socket.onmessage = ({ data }) => {
      const msg = JSON.parse(data);
      if (msg.method === 'Network.requestWillBeSent' && msg.params.request.url === origin + '/recursos/') {
        resourceReferers.push(msg.params.request.headers.Referer || msg.params.request.headers.referer || '');
      }
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id); pending.delete(msg.id);
        msg.error ? reject(Error(msg.error.message)) : resolve(msg.result);
      }
    };
    function send(method, params = {}) {
      const id = ++next;
      return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        socket.send(JSON.stringify({ id, method, params }));
      });
    }
    async function evalJs(expression) {
      const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (result.exceptionDetails) throw Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
      return result.result.value;
    }
    async function ready(path) {
      for (let i = 0; i < 60; i++) {
        const state = await evalJs('({path: location.pathname, ready: document.readyState})');
        if (state.path === path && state.ready === 'complete') return;
        await delay(100);
      }
      throw Error(`No terminó de cargar ${path}`);
    }
    async function go(path) {
      await send('Page.navigate', { url: origin + path });
      await ready(path);
    }
    async function clickSelector(selector) {
      const doc = await send('DOM.getDocument');
      const link = await send('DOM.querySelector', { nodeId: doc.root.nodeId, selector });
      await send('DOM.scrollIntoViewIfNeeded', { nodeId: link.nodeId });
      const box = await send('DOM.getBoxModel', { nodeId: link.nodeId });
      const x = (box.model.content[0] + box.model.content[2]) / 2;
      const y = (box.model.content[1] + box.model.content[5]) / 2;
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    }
    await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');

    // Navegación real y recargas en una sesión.
    await ready('/');
    await clickSelector('a[href="/herramientas/"]');
    await ready('/herramientas/');
    console.log('Home → Herramientas: OK');

    await send('Network.clearBrowserCookies');
    await go('/');
    await send('Page.reload'); await ready('/');
    await send('Page.reload'); await ready('/');
    console.log('Home → F5 → F5: OK');

    await send('Network.clearBrowserCookies');
    await go('/');
    await evalJs("location.assign('/blog/articulo-a/')"); await ready('/blog/articulo-a/');
    await evalJs("location.assign('/blog/articulo-b/')"); await ready('/blog/articulo-b/');
    console.log('Home → artículo A → artículo B: OK');

    await send('Network.clearBrowserCookies');
    await go('/');
    await clickSelector('[data-home-cta="tools"]');
    await ready('/herramientas/'); await delay(500);
    console.log('Clic CTA con JavaScript: OK');

    await send('Network.clearBrowserCookies');
    await go('/');
    await send('Emulation.setScriptExecutionDisabled', { value: true });
    await clickSelector('a[href="/herramientas/"]');
    await ready('/herramientas/');
    await send('Emulation.setScriptExecutionDisabled', { value: false });
    console.log('Enlace sin JavaScript: OK');

    await send('Network.clearBrowserCookies');
    await go('/herramientas/punto-de-equilibrio/');
    await evalJs("document.querySelector('[name=costs]').value='75000'; document.querySelector('[name=price]').value='1200'; document.querySelector('[name=variable_cost]').value='650'; document.querySelector('form').requestSubmit()");
    await delay(400);
    if (!await evalJs("document.body.innerText.includes('137')")) throw Error('La calculadora no mostró 137');
    console.log('Calculadora con resultado 137: OK');

    await send('Network.clearBrowserCookies');
    await go('/herramientas/');
    await send('Network.setExtraHTTPHeaders', { headers: { Referer: 'http://[' } });
    await go('/recursos/');
    if (resourceReferers.at(-1) !== 'http://[') throw Error('Chrome no envió el Referer inválido; escenario no verificado');
    console.log('Referer inválido: navegación disponible');
    await send('Network.setExtraHTTPHeaders', { headers: {} });
    await send('Network.clearBrowserCookies');
    await go('/recursos/');
    console.log('Referer ausente: navegación disponible');
  } finally {
    socket?.close();
    chrome.kill();
  }
})().catch((error) => { console.error(error.message); process.exitCode = 1; });
