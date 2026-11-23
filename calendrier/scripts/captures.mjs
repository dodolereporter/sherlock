// Captures de contrôle (Playwright, horloge pilotée pour des instants précis malgré le rendu logiciel).
// Usage : npm run build && npm run preview  (dans un autre terminal), puis  npm run captures [-- --extra]
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const BASE = process.env.CAPTURE_URL ?? 'http://localhost:4173/';
const OUT = new URL('../captures/', import.meta.url).pathname;
const EXTRA = process.argv.includes('--extra');
const ONLY = process.argv.find((a) => a.startsWith('--only='))?.slice(7);
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});
const report = { stats: {}, console: [] };

async function open(name, viewport, query, options = {}) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    reducedMotion: options.reducedMotion ?? 'no-preference',
    hasTouch: options.touch ?? false,
    isMobile: options.touch ?? false,
  });
  const page = await context.newPage();
  page.on('console', (m) => {
    if (m.type() === 'error' || (m.type() === 'warning' && !m.text().includes('GL Driver Message')))
      report.console.push(`[${name}] ${m.type()}: ${m.text()}`);
  });
  page.on('pageerror', (e) => report.console.push(`[${name}] pageerror: ${e.message}`));
  // Horloge figée : seul fastForward fait avancer le temps (une image par pas).
  const start = new Date('2026-11-23T18:00:00');
  await page.clock.install({ time: start });
  await page.clock.pauseAt(new Date(start.getTime() + 200));
  await page.goto(BASE + query);
  return { page, context };
}

/** Avance l'horloge par pas : chaque pas déclenche une image. */
async function advance(page, ms, step = 120) {
  for (let t = 0; t < ms; t += step) {
    await page.clock.fastForward(Math.min(step, ms - t));
    await page.waitForTimeout(5);
  }
}

async function until(page, selector, max = 120) {
  for (let i = 0; i < max; i++) {
    if (await page.$(selector)) return;
    await page.clock.fastForward(150);
    await page.waitForTimeout(150);
  }
  throw new Error(`Délai dépassé : ${selector}`);
}

async function shot(page, file, statsKey) {
  await page.clock.fastForward(16);
  await page.waitForTimeout(30);
  await page.screenshot({ path: OUT + file });
  if (statsKey) {
    await advance(page, 600, 100);
    report.stats[statsKey] = await page.evaluate(() => globalThis.__debugStats ?? null);
  }
  console.log('✓', file);
}

async function centerOf(page, day) {
  const box = await page.locator(`.proxy[data-day="${day}"]`).boundingBox();
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

async function press(page, touch, point) {
  if (touch) await page.touchscreen.tap(point.x, point.y);
  else await page.mouse.click(point.x, point.y);
}

async function run(label, viewport, touch) {
  // Introduction puis vue principale.
  {
    const { page, context } = await open(`${label}-intro`, viewport, '?demo=1&debug=1', { touch });
    await until(page, '.app--intro');
    await advance(page, 2600);
    await shot(page, `${label}-01-intro-milieu.png`);
    await advance(page, 2900);
    await shot(page, `${label}-02-intro-fin.png`);
    await until(page, '.app--idle');
    await advance(page, 1500);
    await shot(page, `${label}-03-vue-principale.png`, `${label}-principale`);
    // Survol (souris) ou focus clavier (tactile).
    if (touch) {
      await page.keyboard.press('Tab');
      for (let i = 0; i < 6; i++) await page.keyboard.press('Tab');
    } else {
      const c = await centerOf(page, 7);
      await page.mouse.move(c.x, c.y, { steps: 4 });
    }
    await advance(page, 700);
    await shot(page, `${label}-04-survol.png`);
    if (!touch) await page.mouse.move(5, 5);
    await advance(page, 600);
    // Ouverture d'une case (objet 3D).
    const c2 = await centerOf(page, 2);
    await press(page, touch, c2);
    await advance(page, 1050, 70);
    await shot(page, `${label}-05-ouverture-milieu.png`);
    await advance(page, 2600);
    await shot(page, `${label}-06-case-ouverte.png`, `${label}-ouverte`);
    await page.keyboard.press('Escape');
    await until(page, '.app--idle');
    await advance(page, 800);
    // Final.
    const c24 = await centerOf(page, 24);
    await press(page, touch, c24);
    await advance(page, 2400);
    await shot(page, `${label}-07-final-anticipation.png`);
    await advance(page, 1150, 60);
    await shot(page, `${label}-08-final-eclat.png`);
    await advance(page, 4200);
    await shot(page, `${label}-09-final.png`, `${label}-final`);
    await context.close();
  }
  // Mouvement réduit.
  {
    const { page, context } = await open(`${label}-reduit`, viewport, '?demo=1', { reducedMotion: 'reduce', touch });
    await until(page, '.app--idle');
    await advance(page, 800);
    await shot(page, `${label}-10-reduit-vue.png`);
    const c = await centerOf(page, 4);
    await press(page, touch, c);
    await advance(page, 2600);
    await shot(page, `${label}-11-reduit-case-ouverte.png`);
    await context.close();
  }
  // Case verrouillée (date simulée).
  {
    const { page, context } = await open(`${label}-refus`, viewport, '?date=2026-12-05&intro=0', { touch });
    await until(page, '.app--idle');
    await advance(page, 800);
    const c = await centerOf(page, 20);
    await press(page, touch, c);
    await advance(page, 420, 60);
    await shot(page, `${label}-12-case-verrouillee.png`);
    await context.close();
  }
}

async function extras() {
  const days = [1, 4, 5, 6, 8, 10, 12, 14, 16, 20, 23, 7, 11, 15, 19, 3, 18];
  const { page, context } = await open('extra', { width: 1440, height: 900 }, '?demo=1&intro=0');
  await until(page, '.app--idle');
  await advance(page, 800);
  for (const day of days) {
    const c = await centerOf(page, day);
    await page.mouse.click(c.x, c.y);
    await advance(page, day === 10 ? 3300 : 4200);
    await shot(page, `extra-case-${String(day).padStart(2, '0')}.png`);
    await page.keyboard.press('Escape');
    await until(page, '.app--idle');
    await advance(page, 300);
  }
  await context.close();
}

if (!ONLY || ONLY === 'desktop') await run('1440', { width: 1440, height: 900 }, false);
if (!ONLY || ONLY === 'mobile') await run('390', { width: 390, height: 844 }, true);
if (EXTRA || ONLY === 'extra') await extras();
await browser.close();
writeFileSync(OUT + 'rapport.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
