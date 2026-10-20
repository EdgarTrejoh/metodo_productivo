const { chromium } = require('playwright');
const path = require('path');

const origin = 'http://127.0.0.1:8765';
const synthetic = process.argv.includes('--synthetic');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  let failures = 0;
  for (const [width, height] of [[1365, 900], [369, 545], [390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const thirdPartyRequests = [];
    page.on('request', request => { if (request.url().includes('youtube-nocookie.com')) thirdPartyRequests.push(request.url()); });
    const response = await page.goto(origin + '/blog/', { waitUntil: 'domcontentloaded' });
    const file = `a05a06-${synthetic ? 'synthetic' : 'empty'}-${width}x${height}.png`;
    await page.screenshot({ path: path.join(__dirname, file), fullPage: true });
    await page.keyboard.press('Tab');
    const state = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > innerWidth,
      activeNav: document.querySelector('.site-nav [aria-current="location"]')?.textContent.trim(),
      breadcrumb: document.querySelector('.breadcrumb [aria-current="page"]')?.textContent.trim(),
      categories: document.querySelectorAll('.editorial-area').length,
      articles: document.querySelectorAll('.article-card').length,
      videos: document.querySelectorAll('.video-card').length,
      iframeCount: document.querySelectorAll('iframe').length,
      focus: document.activeElement?.classList.contains('skip-link') && getComputedStyle(document.activeElement).outlineStyle !== 'none',
    }));
    const initialThirdPartyRequests = thirdPartyRequests.length;
    let detailOk = true;
    let clickToLoad = null;
    if (synthetic) {
      const article = await page.locator('.article-card h3 a').first();
      const href = await article.getAttribute('href');
      const detail = await page.goto(origin + href, { waitUntil: 'domcontentloaded' });
      detailOk = detail.status() === 200 && await page.locator('link[rel="canonical"]').count() === 1 && await page.locator('meta[property="og:type"]').count() === 1 && await page.locator('.article-cta .button').count() === 1 && await page.locator('iframe').count() === 0;
      const detailFile = `a05a06-detail-${width}x${height}.png`;
      await page.screenshot({ path: path.join(__dirname, detailFile), fullPage: true });
      const trigger = page.locator('.video-activate').first();
      await trigger.click({ force: true });
      clickToLoad = await page.locator('iframe[src^="https://www.youtube-nocookie.com/embed/"]').count() === 1;
    }
    const ok = response.status() === 200 && !state.overflow && state.activeNav === 'Contenidos' && state.breadcrumb === 'Contenidos' && state.categories === 4 && state.iframeCount === 0 && initialThirdPartyRequests === 0 && state.focus && (synthetic ? state.articles === 1 && state.videos === 1 && detailOk && clickToLoad : state.articles === 0 && state.videos === 0);
    if (!ok) failures++;
    console.log(JSON.stringify({ viewport: `${width}x${height}`, synthetic, ok, ...state, initialThirdPartyRequests, detailOk, clickToLoad, file }));
    await context.close();
  }
  await browser.close();
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 1; });
