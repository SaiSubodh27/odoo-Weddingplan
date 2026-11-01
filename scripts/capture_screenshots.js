const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOTS_DIR = path.join(__dirname, '..', 'docs', 'screenshots');
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function capture() {
  console.log('[*] Launching browser via Playwright channel "msedge"...');
  let browser;
  try {
    browser = await chromium.launch({ channel: 'msedge', headless: true });
  } catch (err) {
    console.log('[*] Falling back to channel "chrome"...');
    browser = await chromium.launch({ channel: 'chrome', headless: true });
  }

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();

  // Helper function to capture a screenshot
  async function take(url, filename, setupFn) {
    console.log(`[*] Navigating to ${url} for ${filename}...`);
    if (setupFn) {
      await page.goto('http://localhost:5173/login');
      await setupFn(page);
    }
    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2000);
    const savePath = path.join(SCREENSHOTS_DIR, filename);
    await page.screenshot({ path: savePath, fullPage: false });
    console.log(`[OK] Captured ${filename}`);
  }

  // 1. Client Agreement Signing Gate
  await take('http://localhost:5173/agreement', 'client-agreement-signing.png', async (p) => {
    await p.evaluate(() => {
      localStorage.setItem('the_royal_knot_token_v1', 'trk_token_client');
      localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
        email: 'aarav.meera@heritage-singhania.com',
        role: 'client',
        name: 'Aarav Singhania',
        clientId: 'CL-HERO-001'
      }));
      localStorage.setItem('the_royal_knot_client_id_v1', 'CL-HERO-001');
      localStorage.setItem('the_royal_knot_details_completed', 'true');
    });
  });

  // 2. Client Intake Dossier
  await take('http://localhost:5173/client-intake', 'client-intake.png', async (p) => {
    await p.evaluate(() => {
      localStorage.setItem('the_royal_knot_token_v1', 'trk_token_client');
      localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
        email: 'aarav.meera@heritage-singhania.com',
        role: 'client',
        name: 'Aarav Singhania',
        clientId: 'CL-HERO-001'
      }));
    });
  });

  // 3. Employee Enquiries Management
  await take('http://localhost:5173/enquiries', 'employee-enquiries.png', async (p) => {
    await p.evaluate(() => {
      localStorage.setItem('the_royal_knot_token_v1', 'trk_token_employee');
      localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
        email: 'gayatri@theroyalknot.com',
        role: 'employee',
        name: 'Maharani Gayatri Singh'
      }));
    });
  });

  // 4. Employee Operational Weddings
  await take('http://localhost:5173/weddings', 'employee-weddings.png', async (p) => {
    await p.evaluate(() => {
      localStorage.setItem('the_royal_knot_token_v1', 'trk_token_employee');
      localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
        email: 'gayatri@theroyalknot.com',
        role: 'employee',
        name: 'Maharani Gayatri Singh'
      }));
    });
  });

  // 5. Employee Big Day Live Schedule with Late Alerts
  await take('http://localhost:5173/weddings/PRJ-LIVE-005/big-day', 'employee-big-day.png', async (p) => {
    await p.evaluate(() => {
      localStorage.setItem('the_royal_knot_token_v1', 'trk_token_employee');
      localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
        email: 'raghav@theroyalknot.com',
        role: 'employee',
        name: 'Raghav Sharma'
      }));
    });
  });

  // 6. Vendor Portal Login & RFQ Dashboard
  await take('http://localhost:5173/vendor-portal', 'vendor-portal.png', async (p) => {
    await p.evaluate(() => {
      localStorage.removeItem('the_royal_knot_token_v1');
      localStorage.removeItem('the_royal_knot_user_v1');
    });
  });

  // 7. Founder Season Overview & Profit Radar
  await take('http://localhost:5173/founder-portal', 'founder-season.png', async (p) => {
    await p.evaluate(() => {
      localStorage.setItem('the_royal_knot_token_v1', 'trk_token_founder');
      localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
        email: 'founder@theroyalknot.com',
        role: 'founder',
        name: 'Vikramaditya Rathore'
      }));
    });
  });

  // 8. Mobile view of Big Day Live Schedule
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 }, // iPhone 14 dimensions
    deviceScaleFactor: 2,
    isMobile: true,
  });
  const mobilePage = await mobileContext.newPage();
  await mobilePage.goto('http://localhost:5173/login');
  await mobilePage.evaluate(() => {
    localStorage.setItem('the_royal_knot_token_v1', 'trk_token_employee');
    localStorage.setItem('the_royal_knot_user_v1', JSON.stringify({
      email: 'raghav@theroyalknot.com',
      role: 'employee',
      name: 'Raghav Sharma'
    }));
  });
  await mobilePage.goto('http://localhost:5173/weddings/PRJ-LIVE-005/big-day', { waitUntil: 'networkidle' }).catch(() => {});
  await mobilePage.waitForTimeout(2000);
  await mobilePage.screenshot({ path: path.join(SCREENSHOTS_DIR, 'mobile-big-day.png') });
  console.log('[OK] Captured mobile-big-day.png');
  await mobileContext.close();

  await browser.close();
  console.log('\n[SUCCESS] All screenshots captured successfully in docs/screenshots/!');
}

capture().catch((err) => {
  console.error('[ERROR] Screenshot capture failed:', err);
  process.exit(1);
});
