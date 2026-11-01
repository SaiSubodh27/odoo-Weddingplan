const fs = require('fs');
const path = require('path');
const { marked } = require('marked');
const { chromium } = require('playwright');

const ROOT_DIR = path.join(__dirname, '..');
const MANUAL_MD_PATH = path.join(ROOT_DIR, 'docs', 'USER_MANUAL.md');
const MANUAL_PDF_PATH = path.join(ROOT_DIR, 'docs', 'USER_MANUAL.pdf');
const SCREENSHOTS_DIR = path.join(ROOT_DIR, 'docs', 'screenshots');

async function compilePdf() {
  console.log('[*] Reading USER_MANUAL.md...');
  let mdContent = fs.readFileSync(MANUAL_MD_PATH, 'utf-8');

  // Replace relative screenshot paths with base64 data URIs so they render reliably in headless PDF
  mdContent = mdContent.replace(/screenshots\/([\w\-]+)\.png/g, (match, filename) => {
    const imgPath = path.join(SCREENSHOTS_DIR, `${filename}.png`);
    if (fs.existsSync(imgPath)) {
      const base64Data = fs.readFileSync(imgPath).toString('base64');
      return `data:image/png;base64,${base64Data}`;
    }
    return match;
  });

  const bodyHtml = marked.parse(mdContent);

  const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>The Royal Knot — User Manual</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    @page {
      size: A4;
      margin: 18mm 18mm 20mm 18mm;
      @bottom-right {
        content: counter(page);
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 8pt;
        color: #888;
      }
    }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 10pt;
      line-height: 1.6;
      color: #1a1a1a;
      background-color: #fff;
      margin: 0;
      padding: 0;
    }
    h1, h2, h3, h4 {
      font-family: 'Cormorant Garamond', Georgia, serif;
      color: #1b2a4a;
      margin-top: 1.5em;
      margin-bottom: 0.5em;
      font-weight: 700;
      page-break-after: avoid;
    }
    h1 {
      font-size: 24pt;
      border-bottom: 2px solid #c5a880;
      padding-bottom: 6px;
      color: #111e38;
      text-align: center;
      margin-top: 0;
    }
    h2 {
      font-size: 17pt;
      border-bottom: 1px solid #e2d7c5;
      padding-bottom: 4px;
      margin-top: 2em;
    }
    h3 {
      font-size: 13pt;
      color: #8c6d3b;
    }
    p, li {
      color: #2c3e50;
    }
    img {
      max-width: 100%;
      height: auto;
      border: 1px solid #ddd;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      margin: 12px 0;
      display: block;
      page-break-inside: avoid;
    }
    blockquote {
      border-left: 4px solid #c5a880;
      margin: 1em 0;
      padding: 8px 16px;
      background-color: #faf7f2;
      font-style: italic;
    }
    code {
      font-family: Consolas, monospace;
      font-size: 9pt;
      background-color: #f4f0ea;
      padding: 2px 5px;
      border-radius: 4px;
      color: #7b241c;
    }
    hr {
      border: none;
      border-top: 1px solid #e2d7c5;
      margin: 2em 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1em 0;
      page-break-inside: avoid;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px 10px;
      text-align: left;
    }
    th {
      background-color: #f8f5ef;
      color: #1b2a4a;
      font-weight: 600;
    }
  </style>
</head>
<body>
  ${bodyHtml}
</body>
</html>`;

  console.log('[*] Launching browser to compile PDF...');
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
  } catch (err) {
    browser = await chromium.launch({ channel: 'chrome', headless: true });
  }

  const page = await browser.newPage();
  await page.setContent(fullHtml, { waitUntil: 'load' });
  await page.waitForTimeout(1000);

  console.log(`[*] Generating PDF at ${MANUAL_PDF_PATH}...`);
  await page.pdf({
    path: MANUAL_PDF_PATH,
    format: 'A4',
    margin: {
      top: '18mm',
      bottom: '20mm',
      left: '18mm',
      right: '18mm',
    },
    printBackground: true,
  });

  await browser.close();
  console.log(`[SUCCESS] docs/USER_MANUAL.pdf generated successfully!`);
}

compilePdf().catch((err) => {
  console.error('[ERROR] PDF compilation failed:', err);
  process.exit(1);
});
