const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFile } = require('node:fs/promises');
const { resolve, extname } = require('node:path');
const { chromium } = require('playwright');

test('Een hoofdstukkaart laadt eenmaal nadat de definitieve leestekst klaarstaat', async () => {
    const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH ||
        (process.platform === 'win32' ? 'C:/Program Files/Google/Chrome/Application/chrome.exe' : '/usr/bin/google-chrome') });
    try {
        const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, serviceWorkers: 'block' });
        const maps = [];
        const root = resolve(__dirname, '..');
        await context.route('**/*', async route => {
            const url = new URL(route.request().url());
            if (url.pathname === '/data/opw-begrippen.js') return route.fulfill({ contentType: 'text/javascript',
                body: 'window.OGWReadingTerms={};window.OGWChapterMapCounts={genesis:{4:1,5:1}};' });
            if (url.hostname === 'opengodsword.com' && url.pathname === '/kaart.html') {
                maps.push(url.searchParams.get('hoofdstuk'));
                return route.fulfill({ contentType: 'text/html', body: '<html data-map-ready="true"><body>Kaart</body></html>' });
            }
            if (url.hostname !== 'reader.test') return route.abort();
            if (url.pathname.startsWith('/api/')) return route.fulfill({ contentType: 'application/json', body: '{}' });
            if (url.pathname === '/data/book-images.json') await new Promise(resolve => setTimeout(resolve, 700));
            const file = resolve(root, '.' + url.pathname);
            if (!file.startsWith(root + '/')) {
                if (!file.startsWith(root + '\\')) return route.abort();
            }
            try {
                const type = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
                    '.css': 'text/css', '.svg': 'image/svg+xml' }[extname(file)] || 'application/octet-stream';
                return route.fulfill({ contentType: type, body: await readFile(file) });
            } catch { return route.fulfill({ status: 404, body: '' }); }
        });
        const page = await context.newPage();
        await page.goto('https://reader.test/bijbel/genesis/4.html', { waitUntil: 'networkidle' });
        await page.waitForFunction(() => Navigation._renderedChapter === 'genesis/4');
        assert.deepEqual(maps, ['4']);
        await page.frameLocator('.opw-chapter-map iframe').locator('html[data-map-ready="true"]').waitFor();
        await page.evaluate(() => Navigation.navigateChapter('genesis', 5));
        await page.waitForFunction(() => Navigation._renderedChapter === 'genesis/5');
        await page.frameLocator('.opw-chapter-map iframe').locator('html[data-map-ready="true"]').waitFor();
        assert.deepEqual(maps, ['4', '5']);
        assert.match(await page.locator('.opw-chapter-map iframe').getAttribute('src'), /hoofdstuk=5&embed=1/);
    } finally { await browser.close(); }
});
