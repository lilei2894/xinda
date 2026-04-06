const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, '..', 'jacar_beijing_results');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    locale: 'ja-JP',
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  const pdfUrls = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('.pdf') && url.includes('/content/item/')) {
      pdfUrls.push(url);
    }
  });

  const documentIds = process.argv.slice(2);
  if (documentIds.length === 0) {
    console.log('Usage: node download.js <document_id> [document_id ...]');
    console.log('Example: node download.js B02030535600 A07040002700');
    await browser.close();
    return;
  }

  for (let i = 0; i < documentIds.length; i++) {
    const docId = documentIds[i];
    console.log(`\n[${i + 1}/${documentIds.length}] Downloading: ${docId}`);
    pdfUrls.length = 0;

    try {
      const imageUrl = `https://www.jacar.archives.go.jp/das/image/${docId}`;
      await page.goto(imageUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(8000);

      if (pdfUrls.length > 0) {
        const pdfUrl = [...new Set(pdfUrls)][0];
        const blobData = await page.evaluate(async (url) => {
          const resp = await fetch(url);
          const blob = await resp.blob();
          const reader = new FileReader();
          return new Promise((resolve) => {
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
          });
        }, pdfUrl);

        if (blobData && blobData.startsWith('data:')) {
          const base64Data = blobData.split(',')[1];
          const savePath = path.join(OUTPUT_DIR, `${docId}.pdf`);
          fs.writeFileSync(savePath, Buffer.from(base64Data, 'base64'));
          console.log(`  Saved: ${savePath}`);
        }
      } else {
        console.log(`  No PDF found`);
      }
    } catch (error) {
      console.log(`  Error: ${error.message}`);
    }

    await page.waitForTimeout(2000);
  }

  await browser.close();
})();