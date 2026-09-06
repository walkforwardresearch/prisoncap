const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
const C = { slate: '1F2933', ink: '323F4B', light: 'F5F6F4', white: 'FFFFFF', brick: 'B03A2E', grey: '7B8794', pale: 'E4E7EB', amber: 'C8963E', moss: '5B7F5B' };
const HF = 'Cambria', BF = 'Calibri';

const title = (s, t, dark = false) => { s.background = { color: dark ? C.slate : C.white };
  s.addText(t, { x: 0.6, y: 0.35, w: 12.1, h: 1.0, fontFace: HF, fontSize: 30, bold: true, color: dark ? C.white : C.slate, isTextBox: true, margin: 0, valign: 'top' }); };
const foot = (s, t) => s.addText(t, { x: 0.6, y: 7.0, w: 12.1, h: 0.3, fontFace: BF, fontSize: 9, color: C.grey, isTextBox: true, margin: 0 });
const box = (s, x, y, w, h, text, o = {}) => {
  s.addShape(o.round ? pres.ShapeType.roundRect : pres.ShapeType.rect, { x, y, w, h, fill: { color: o.fill ?? C.light }, line: { color: o.line ?? (o.fill ?? C.light), width: 1 }, rectRadius: o.round ? 0.08 : undefined });
  s.addText(text, { x: x + 0.1, y, w: w - 0.2, h, fontFace: BF, fontSize: o.size ?? 12, bold: o.bold, color: o.color ?? C.ink, align: o.align ?? 'center', valign: 'middle', isTextBox: true, margin: 0 });
};
const arrow = (s, x1, y1, x2, y2, o = {}) => s.addShape(pres.ShapeType.line, {
  x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.01, h: Math.abs(y2 - y1) || 0.01,
  flipH: x2 < x1, flipV: y2 < y1, line: { color: o.color ?? C.grey, width: o.width ?? 2, endArrowType: 'triangle', dashType: o.dash ? 'dash' : 'solid' } });
const label = (s, x, y, w, h, t, o = {}) => s.addText(t, { x, y, w, h, fontFace: BF, fontSize: o.size ?? 11, color: o.color ?? C.ink, bold: o.bold, align: o.align ?? 'left', valign: o.valign ?? 'top', isTextBox: true, margin: 0, italic: o.italic });
const big = (s, x, y, w, n, t, color = C.brick, size = 40) => { s.addText(n, { x, y, w, h: 0.75, fontFace: HF, fontSize: size, bold: true, color, isTextBox: true, margin: 0 });
  s.addText(t, { x, y: y + 0.75, w, h: 0.55, fontFace: BF, fontSize: 11, color: C.grey, isTextBox: true, margin: 0, valign: 'top' }); };

// ---------------------------------------------------------------- 1 title
{ const s = pres.addSlide(); s.background = { color: C.slate };
  s.addText('Prison capacity in six diagrams', { x: 0.8, y: 2.2, w: 11.5, h: 1.2, fontFace: HF, fontSize: 42, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText('The mechanisms behind fifteen years of flat prisons, failed projections and repeated emergency release', { x: 0.8, y: 3.4, w: 11, h: 0.9, fontFace: BF, fontSize: 18, color: C.pale, isTextBox: true, margin: 0 });
  s.addText('Walk Forward Research, 4 September 2026', { x: 0.8, y: 6.0, w: 11, h: 0.4, fontFace: BF, fontSize: 12, color: C.grey, isTextBox: true, margin: 0 }); }

// ---------------------------------------------------------------- 2 how the scorecard works
{ const s = pres.addSlide(); title(s, '1. How the projections were scored: walk forward, edition by edition');
  // axis
  const x0 = 0.9, x1 = 8.3, yb = 5.3;
  arrow(s, x0, yb, x1 + 0.3, yb, { color: C.grey, width: 1.5 });
  ['2008', '2012', '2016', '2020', '2024'].forEach((t, i) => label(s, x0 + i * 1.85 - 0.25, yb + 0.08, 0.6, 0.3, t, { size: 9, color: C.grey, align: 'center' }));
  // outturn: a wobbly flat line drawn as segments
  const pts = [[0.9, 3.4], [1.8, 3.2], [2.7, 3.55], [3.6, 3.45], [4.5, 3.3], [5.0, 4.4], [5.6, 4.1], [6.4, 3.05], [7.3, 3.15], [8.3, 3.1]];
  for (let i = 1; i < pts.length; i++) s.addShape(pres.ShapeType.line, { x: Math.min(pts[i - 1][0], pts[i][0]), y: Math.min(pts[i - 1][1], pts[i][1]), w: Math.abs(pts[i][0] - pts[i - 1][0]), h: Math.abs(pts[i][1] - pts[i - 1][1]) || 0.01, flipV: pts[i][1] < pts[i - 1][1], line: { color: C.slate, width: 3 } });
  label(s, 8.35, 2.95, 1.6, 0.3, 'Outturn', { size: 10, bold: true, color: C.slate });
  // three editions, each with a rising central path and a dashed no-change line
  [[1.8, 3.2, '2012 edition'], [4.5, 3.3, '2016 edition'], [6.4, 3.05, '2020 edition']].forEach(([ex, ey, name]) => {
    s.addShape(pres.ShapeType.ellipse, { x: ex - 0.08, y: ey - 0.08, w: 0.16, h: 0.16, fill: { color: C.brick }, line: { color: C.brick } });
    arrow(s, ex, ey, ex + 2.0, ey - 1.1, { color: C.brick, width: 2 });
    arrow(s, ex, ey, ex + 2.0, ey, { color: C.grey, width: 1.5, dash: true });
    label(s, ex - 0.4, ey + 0.12, 1.2, 0.3, name, { size: 9, color: C.brick, align: 'center' });
  });
  // error bracket on the 2016 edition
  s.addShape(pres.ShapeType.line, { x: 6.5, y: 2.2, w: 0.01, h: 1.85, line: { color: C.amber, width: 2 } });
  label(s, 6.6, 2.1, 1.6, 0.6, 'error at 3 years: projection minus outturn', { size: 9, color: C.amber });
  label(s, 3.9, 1.5, 3.0, 0.4, 'central path (red) vs no-change (dashed)', { size: 10, color: C.grey, italic: true });
  // right panel
  box(s, 9.0, 1.5, 3.7, 1.15, 'Every edition since 2008. Every published horizon, one to six years. Outturn from the MoJ\u2019s own weekly bulletins, interpolated to the published reference date.', { size: 11, align: 'left' });
  box(s, 9.0, 2.8, 3.7, 1.0, 'Benchmark: a forecaster with no model who carries the current population forward unchanged. Same targets, same information.', { size: 11, align: 'left' });
  big(s, 9.0, 4.05, 1.8, '84%', 'of 75 targets too high');
  big(s, 10.9, 4.05, 1.8, '72%', 'no-change was closer', C.slate);
  box(s, 9.0, 5.5, 3.7, 1.2, 'Structural overshoot about +2% in ordinary years; the COVID and release-scheme years double it. No-change wins at every horizon under every cut.', { size: 11, align: 'left', fill: C.slate, color: C.white });
  foot(s, 'Eighteen editions, 2008 to 2025, 75 scoreable targets. Fifteen of seventeen editions have a positive mean error; thirteen are beaten by the no-change forecast.'); }

// ---------------------------------------------------------------- 3 the self-falsifying cycle
{ const s = pres.addSlide(); title(s, '2. The cycle: the projection creates the policy that falsifies it');
  const cx = 4.3, cy = 4.15, r = 2.35, n = 5, bw = 2.2, bh = 0.95;
  const items = ['MoJ projects the population rising ~3,000 a year', 'Capacity alarm: building programme sized to the projection', 'Estate fills; emergency release cuts the proportion of sentence served', 'Population stays flat; determinate stock falls', 'Projection is falsified. Next edition projects growth again'];
  const pos = items.map((_, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / n; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; });
  pos.forEach(([x, y], i) => box(s, x - bw / 2, y - bh / 2, bw, bh, items[i], { size: 10.5, fill: i === 4 ? C.brick : C.light, color: i === 4 ? C.white : C.ink, round: true }));
  for (let i = 0; i < n; i++) { const [x1, y1] = pos[i], [x2, y2] = pos[(i + 1) % n];
    const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L; const pad = Math.max(bw / 2 * Math.abs(ux), bh / 2 * Math.abs(uy)) + 0.12;
    arrow(s, x1 + ux * pad, y1 + uy * pad, x2 - ux * pad, y2 - uy * pad, { color: C.grey, width: 2.5 }); }
  s.addText('17 editions\n13 with every target too high', { x: cx - 1.3, y: cy - 0.55, w: 2.6, h: 1.1, fontFace: HF, fontSize: 14, bold: true, color: C.slate, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
  box(s, 8.2, 1.55, 4.5, 1.6, 'This is the MoJ\u2019s defence and the problem at once. The projections are conditional on unchanged policy; policy changes; the projection is falsified by design. True, and it means a counterfactual the government itself falsifies each time cannot size a \u00a37bn building programme.', { size: 11, align: 'left' });
  box(s, 8.2, 3.35, 4.5, 1.3, 'The overshoot predates the cycle. In the 2008 to 2014 editions, a decade before any emergency release scheme, no-change was closer on 29 of 40 targets.', { size: 11, align: 'left', fill: C.slate, color: C.white });
  big(s, 8.2, 4.9, 2.2, '+3,000/yr', 'the demand assumption behind 14,000 places by 2031', C.brick, 28);
  big(s, 10.5, 4.9, 2.2, '+246/yr', 'realised growth, 2011 to 2026', C.slate, 28);
  foot(s, 'No five-year window since 2011 has sustained even +2,000 a year. The +3,000 figure is the MoJ\u2019s near-term no-action counterfactual; its own central path with reforms is +1,333 a year.'); }

// ---------------------------------------------------------------- 4 two forces cancel
{ const s = pres.addSlide(); title(s, '3. Two large forces cancel, and the flat line hides both');
  // left force up
  s.addShape(pres.ShapeType.upArrow, { x: 1.2, y: 2.2, w: 1.3, h: 2.6, fill: { color: C.brick }, line: { color: C.brick } });
  label(s, 2.7, 2.2, 3.0, 2.6, 'Sentence inflation\n\nCustodial months imposed by the courts: +21.5%, 2016 to 2026. Average sentence 16.3 to 20.1 months on 1.5% fewer sentences.', { size: 11.5 });
  // right force down
  s.addShape(pres.ShapeType.downArrow, { x: 7.0, y: 2.2, w: 1.3, h: 2.6, fill: { color: C.slate }, line: { color: C.slate } });
  label(s, 8.5, 2.2, 4.2, 2.6, 'Executive release\n\nProportion of sentence served: 63% in 2017, 60% every year to 2023, then 54% by 2026. ECSL, SDS40, then release at one third from October.', { size: 11.5 });
  // flat line result
  s.addShape(pres.ShapeType.line, { x: 1.2, y: 5.35, w: 11.5, h: 0.01, line: { color: C.grey, width: 4 } });
  label(s, 1.2, 5.45, 5.5, 0.4, 'Total population: +1.5% in ten years', { size: 12, bold: true, color: C.slate });
  label(s, 7.0, 5.45, 5.7, 0.4, 'Determinate population: \u221216.5% since 2017', { size: 12, bold: true, color: C.brick, align: 'right' });
  box(s, 1.2, 6.0, 11.5, 0.85, 'Release cuts more than absorbed sentence inflation on the sentenced stock. The total held up only because something else filled the gap (next diagram). Ninety-five percent of the MoJ\u2019s projection error sits in exactly this component.', { size: 11, align: 'left', fill: C.light });
  foot(s, 'CJS quarterly Q5 tables; OMSQ releases 3.Q.3 to 3.Q.5. Sentence inflation itself is well documented (Sentencing Academy 2025: 54% more punitive than 2005); the bridge to prison places is not.'); }

// ---------------------------------------------------------------- 5 the substitution
{ const s = pres.addSlide(); title(s, '4. One prison population swapped for another, 2017 to 2025');
  const scale = 4.6 / 87465; const L = 1.4, R = 9.5, W = 2.0, top = 1.75;
  const parts17 = [['Determinate', 57726, C.slate], ['Remand', 9638, C.brick], ['Recall', 6390, C.amber], ['Other', 12109, C.grey]];
  const parts25 = [['Determinate', 48224, C.slate], ['Remand', 17700, C.brick], ['Recall', 12657, C.amber], ['Other', 8884, C.grey]];
  const draw = (x, parts, tag) => { let y = top; parts.forEach(([n, v, col]) => { const h = v * scale;
      s.addShape(pres.ShapeType.rect, { x, y, w: W, h, fill: { color: col }, line: { color: C.white, width: 1 } });
      s.addText(`${n}\n${v.toLocaleString()}`, { x, y, w: W, h, fontFace: BF, fontSize: 10, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 }); y += h; });
    label(s, x, y + 0.08, W, 0.35, tag, { size: 12, bold: true, color: C.slate, align: 'center' }); };
  draw(L, parts17, 'June 2017: 85,863'); draw(R, parts25, 'Sept 2025: 87,465');
  // flow arrows between
  arrow(s, L + W + 0.15, top + 57726 * scale / 2, R - 0.15, top + 48224 * scale / 2, { color: C.slate, width: 3 });
  label(s, 4.0, 2.55, 5.0, 0.4, '\u22129,502 sentenced prisoners', { size: 13, bold: true, color: C.slate, align: 'center' });
  arrow(s, L + W + 0.15, top + (57726 + 9638 / 2) * scale, R - 0.15, top + (48224 + 17700 / 2) * scale, { color: C.brick, width: 3 });
  label(s, 4.0, 4.55, 5.0, 0.4, '+8,062 remand (+84%)', { size: 13, bold: true, color: C.brick, align: 'center' });
  arrow(s, L + W + 0.15, top + (57726 + 9638 + 6390 / 2) * scale, R - 0.15, top + (48224 + 17700 + 12657 / 2) * scale, { color: C.amber, width: 3 });
  label(s, 4.0, 5.55, 5.0, 0.4, '+6,267 recall (+98%)', { size: 13, bold: true, color: C.amber, align: 'center' });
  box(s, 4.0, 6.05, 5.0, 0.8, 'Near one for one. The break is 2019 to 2020 when the courts stopped; it never reversed.', { size: 10.5 });
  label(s, 11.7, 1.75, 1.5, 3.0, 'Determinate share\n67% \u2192 55%\n\nRemand + recall\n19% \u2192 35%', { size: 11, color: C.ink });
  foot(s, 'MoJ published base-year actuals from the 2017-2022 and 2025-2030 projection editions. Other = indeterminate, non-criminal, fine defaulters.'); }

// ---------------------------------------------------------------- 6 the recall loop
{ const s = pres.addSlide(); title(s, '5. The recall loop: every early release carries its own partial reversal');
  const cx = 3.9, cy = 4.2, r = 2.1, n = 5, bw = 1.9, bh = 0.85;
  const items = ['In custody', 'Released early on licence', 'More people on licence, for longer', 'Breach of licence', 'Recalled to custody'];
  const pos = items.map((_, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / n; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; });
  pos.forEach(([x, y], i) => box(s, x - bw / 2, y - bh / 2, bw, bh, items[i], { size: 10.5, fill: i === 4 ? C.brick : (i === 0 ? C.slate : C.light), color: (i === 4 || i === 0) ? C.white : C.ink, round: true }));
  for (let i = 0; i < n; i++) { const [x1, y1] = pos[i], [x2, y2] = pos[(i + 1) % n]; const dx = x2 - x1, dy = y2 - y1, Lh = Math.hypot(dx, dy), ux = dx / Lh, uy = dy / Lh, pad = Math.max(bw / 2 * Math.abs(ux), bh / 2 * Math.abs(uy)) + 0.12;
    arrow(s, x1 + ux * pad, y1 + uy * pad, x2 - ux * pad, y2 - uy * pad, { color: C.grey, width: 2.5 }); }
  label(s, cx - 1.0, cy - 0.35, 2.0, 0.7, '99.4% of recalls\nreturn to custody', { size: 10, color: C.slate, align: 'center', bold: true });
  // right: the numbers
  big(s, 7.6, 1.5, 2.5, '29 \u2192 85', 'recalls per 100 releases, 2015 to 2025', C.brick, 32);
  big(s, 10.3, 1.5, 2.5, '+125%', 'recalls per year since 2015, to 48,327', C.slate, 32);
  box(s, 7.6, 3.0, 5.2, 1.0, 'Q1 2026: 13,193 recalls against 12,977 determinate releases. More people came back than went out.', { size: 11.5, align: 'left', fill: C.slate, color: C.white });
  box(s, 7.6, 4.2, 5.2, 1.15, 'Contained so far by shortening recalls: inflow +73% in a year, recall population +0.6%, because mean time in custody per recall fell from 5.1 to 3.0 months.', { size: 11, align: 'left' });
  box(s, 7.6, 5.5, 5.2, 1.2, 'Then reversed: from 31 March 2026 a 56-day fixed-term recall replaced the 14 and 28 day ones. Mechanically up to +3,570 places, not yet visible in the data. First measurable in the Apr-Jun OMSQ, due 29 October.', { size: 11, align: 'left', fill: C.brick, color: C.white });
  foot(s, 'OMSQ recall and release tables across six editions. The surge began in Q2 2024 with the ECSL extensions, before SDS40. Composition series breaks at July 2025; totals unaffected.'); }

// ---------------------------------------------------------------- 7 capacity feedback
{ const s = pres.addSlide(); title(s, '6. Capacity follows population, so a release buys about 60% of its face value');
  // two chains
  const chain = (y, col, items) => { let x = 0.8; items.forEach((t, i) => { box(s, x, y, 2.55, 0.95, t, { size: 10.5, fill: i === 0 ? col : C.light, color: i === 0 ? C.white : C.ink, round: true }); if (i < items.length - 1) arrow(s, x + 2.55, y + 0.475, x + 2.95, y + 0.475, { color: col, width: 2.5 }); x += 2.95; }); };
  label(s, 0.8, 1.45, 6, 0.35, 'When the estate is full', { size: 12, bold: true, color: C.brick });
  chain(1.85, C.brick, ['Population rises', 'Cells cannot be taken offline: nowhere to put people', 'Maintenance and fire-safety work deferred', 'Capacity stays high (crowding operated)']);
  label(s, 0.8, 3.15, 6, 0.35, 'When it empties a little', { size: 12, bold: true, color: C.slate });
  chain(3.55, C.slate, ['Population falls (March 2026 release)', 'Deferred work finally starts', 'Places go offline for repair', 'Capacity falls: \u2212900 places, Mar to Jul 2026']);
  // equation and stats
  box(s, 0.8, 5.0, 6.6, 1.0, 'd cap  =  627  \u2212 0.284 \u00d7 headroom(t\u221226)  +  0.386 \u00d7 d pop        t = \u221214, +19   R\u00b2 0.42   n = 791 weeks', { size: 11, fill: C.slate, color: C.white, bold: true });
  big(s, 7.8, 5.0, 2.3, '39%', 'of any population move is matched by capacity', C.brick, 34);
  big(s, 10.3, 5.0, 2.4, '2,203', 'equilibrium headroom when population is flat', C.slate, 34);
  box(s, 0.8, 6.15, 11.9, 0.7, 'The 2026 capacity fall was forecast in the January 2026 Annual Statement as planned maintenance. Staffing does not explain which prisons cut (R\u00b2 0.001); assaults only weakly (R\u00b2 0.02). It is a centrally managed dial, not a local constraint.', { size: 10.5, align: 'left' });
  foot(s, 'Weekly series 2011 to 2026. Population change lagged a further 13 weeks predicts capacity change at t = 13.4, so the direction runs from population to capacity. Feedback is stronger since 2020 (+0.47, R\u00b2 0.58).'); }

// ---------------------------------------------------------------- 7b competing pressures
{ const s = pres.addSlide(); title(s, '7. The competing pressures: five institutions, five levers, no one controlling the total');
  const hdr = (x, t, col) => box(s, x, 1.45, 5.9, 0.45, t, { fill: col, color: C.white, bold: true, size: 12 });
  hdr(0.6, 'Pushing the population UP', C.brick); hdr(6.8, 'Pushing it DOWN', C.slate);
  const rowY = (i) => 2.05 + i * 0.78;
  const item = (x, i, who, what, size, col) => { box(s, x, rowY(i), 1.35, 0.68, who, { fill: col, color: C.white, size: 10, bold: true });
    box(s, x + 1.4, rowY(i), 3.1, 0.68, what, { size: 10, align: 'left' }); box(s, x + 4.55, rowY(i), 1.35, 0.68, size, { size: 10, bold: true, color: col }); };
  const up = [['Parliament, judges', 'Sentence inflation: custodial months imposed', '+21% per decade'], ['Probation, HMPPS', 'Recall intensity: recalls per 100 releases', '29 to 85'],
              ['MoJ', '56-day fixed-term recall from 31 March 2026', 'up to +3,570'], ['Courts', 'Custody deferred by the bail shift, landing 2027-28', '700 to 1,800 prisoner-yrs'], ['Calendar', 'Seasonal peak, August to November', '+800 amplitude']];
  const down = [['Ministers', 'Progression releases, eight dated tranches Oct 26 to Apr 27', '\u22124,050'], ['Judges', 'Bail replacing remand since August 2025, contested by police', '\u2212200 a month'],
                ['HMPPS', 'Capacity feedback: places brought online as headroom tightens', '39% of any move'], ['Courts', 'Case attrition over long delays: fewer convictions', 'unquantified'], ['Calendar', 'Seasonal trough, December to January', '\u2212800 amplitude']];
  up.forEach((r, i) => item(0.6, i, r[0], r[1], r[2], C.brick)); down.forEach((r, i) => item(6.8, i, r[0], r[1], r[2], C.slate));
  box(s, 0.6, 6.05, 12.1, 0.8, 'Supply moves too: planned maintenance takes about 48 places a week offline until May 2027; new prisons add gross places of which 15% have historically survived attrition; Dartmoor holds 689 certified places empty. The net of all of this is a population that has not moved in fifteen years and a headroom figure that reads as a crisis at 2,000.', { size: 10.5, align: 'left', fill: C.light });
  foot(s, 'Every lever is discretionary and each responds to the others. A projection conditional on any one of them holding still has not survived contact with the other four.'); }

// ---------------------------------------------------------------- 7c storing up
{ const s = pres.addSlide(); title(s, '8. Storing it up: bail moves the custody, it does not cancel it');
  // top: two queues
  label(s, 0.6, 1.5, 6, 0.35, 'Open Crown Court trial cases, Q2 2025 to Q1 2026', { size: 12, bold: true, color: C.slate });
  const bar = (y, lab, custody, bail, scale) => { s.addShape(pres.ShapeType.rect, { x: 0.6, y, w: custody * scale, h: 0.55, fill: { color: C.brick }, line: { color: C.white } });
    s.addShape(pres.ShapeType.rect, { x: 0.6 + custody * scale, y, w: bail * scale, h: 0.55, fill: { color: C.grey }, line: { color: C.white } });
    s.addText(`in custody ${custody.toLocaleString()}`, { x: 0.6, y, w: custody * scale, h: 0.55, fontFace: BF, fontSize: 9.5, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(`on bail ${bail.toLocaleString()}`, { x: 0.6 + custody * scale, y, w: bail * scale, h: 0.55, fontFace: BF, fontSize: 9.5, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    label(s, 0.6 + (custody + bail) * scale + 0.1, y, 1.6, 0.55, lab, { size: 10, valign: 'middle', color: C.ink }); };
  const sc = 5.4 / 67419; bar(1.95, 'Q2 2025: 64,388', 17409, 46177, sc); bar(2.65, 'Q1 2026: 67,419', 16285, 50275, sc);
  label(s, 0.6, 3.3, 7.2, 0.9, 'Custody queue \u22121,124. Bail queue +4,098. Open cases +3,031. Nothing was resolved faster: the mean time a bailed case has been open rose from 332 to 353 days, and trial dates are being set for late 2028. The prison remand population fell because defendants moved from the short queue to the long one.', { size: 10.5 });
  // bottom: timeline of deferred custody
  const y = 5.25; s.addShape(pres.ShapeType.line, { x: 0.8, y, w: 11.7, h: 0.01, line: { color: C.pale, width: 3 } });
  [['2025', 'Remanded: time in custody now, credited against sentence, many released at sentencing'], ['2026', 'Bailed instead: remand population falls 2,561. Headroom improves'], ['2027\u201328', 'Trials happen. Convicted defendants start the full custodial portion from sentencing'], ['2028+', 'The deferred custody lands in the years the 14,000-place programme was meant to relieve']].forEach(([d, t], i) => {
    const x = 2.1 + i * 3.05; s.addShape(pres.ShapeType.ellipse, { x: x - 0.11, y: y - 0.11, w: 0.22, h: 0.22, fill: { color: i === 2 ? C.brick : C.amber }, line: { color: C.white } });
    label(s, x - 0.5, y - 0.55, 1.2, 0.4, d, { size: 13, bold: true, color: C.slate, align: 'center' }); label(s, x - 1.45, y + 0.25, 2.9, 1.3, t, { size: 9.5, align: 'center', color: C.ink }); });
  box(s, 8.2, 1.5, 4.5, 2.7, 'Deferred custody from the 4,098 extra bailed cases since Q2 2025, at 80% conviction, 50% custody, 22 months mean, 40% served: about 1,200 prisoner-years, range 700 to 1,800. For scale: the progression programme releases 4,050; headroom is 2,094.\n\nOffsets: acquittals avoid custody altogether, and cases collapse over long delays. Both reduce the number; neither changes the timing.', { size: 10.5, align: 'left', fill: C.slate, color: C.white });
  foot(s, 'Criminal Court Statistics Quarterly, Jan-Mar 2026, Table O2; OMSQ Table 1.A.1. Bailed open cases are 2.6 times the 2019 level. Custody-rate and sentence assumptions are stated and can be changed in build_diagrams.js.'); }

// ---------------------------------------------------------------- 8 robust vs not
{ const s = pres.addSlide(); title(s, 'What holds, what does not, and what cannot be settled');
  const col = (x, head, colr, items) => { box(s, x, 1.5, 3.9, 0.55, head, { fill: colr, color: C.white, bold: true, size: 13 });
    items.forEach((t, i) => box(s, x, 2.2 + i * 0.95, 3.9, 0.85, t, { size: 10.5, align: 'left', fill: C.light })); };
  col(0.6, 'Robust: survives every cut', C.moss, ['Projections too high at every horizon, in ordinary years and shock years alike', 'No-change forecast closer at every horizon, on identical targets, in every era', '15 of 17 editions biased high (p = 0.001)', 'Sentenced prisoners replaced by remand and recall, near one for one', 'Recalls now exceed determinate releases']);
  col(4.7, 'Not robust: do not quote', C.brick, ['The size of the overshoot: +2% structural, +4% with shocks', 'Direction accuracy: 53% at short horizons is noise', 'The underlying population trend: +19/week from 19 weeks of data', 'Any headroom forecast beyond six months', 'Ten-year statements: five-year error is three times total headroom']);
  col(8.8, 'Cannot be settled from these data', C.grey, ['Regime dependence: no-change wins because the population was flat; it would have lost 1993 to 2012', 'Capacity binding through remand, HDC or sentencing could make some pre-2020 overshoot constrained demand', 'Whether FTR56 or seasonality drove the summer 2026 rise, until the Q2 OMSQ', 'How much of recall growth is reclassification before July 2025']);
  foot(s, 'Full robustness table in the scorecard note, section 3. Definitions log: 114 entries, including six corrections made during the build.'); }

// ---------------------------------------------------------------- 9 timeline
{ const s = pres.addSlide(); s.background = { color: C.slate }; title(s, 'What happens next, and when the model gets scored', true);
  const y = 3.6; s.addShape(pres.ShapeType.line, { x: 0.9, y, w: 11.5, h: 0.01, line: { color: C.pale, width: 3 } });
  const ev = [['28 Sep', 'First register score: 2,076 forecast vs bulletin'], ['2 Oct', '2025 edition first live score: 91,400 vs outturn'], ['29 Oct', 'Q2 OMSQ: FTR56 measurable, recall term added'], ['early Dec', '19th projection edition scored on day one'], ['25 Jan 27', 'The bulletin that separates v1, v2, v3 by 3,200'], ['Jan 27', 'Annual Statement 2026: supply path scored']];
  ev.forEach(([d, t], i) => { const x = 1.5 + i * 2.1; s.addShape(pres.ShapeType.ellipse, { x: x - 0.12, y: y - 0.12, w: 0.24, h: 0.24, fill: { color: i === 4 ? C.brick : C.amber }, line: { color: C.white, width: 1 } });
    s.addText(d, { x: x - 1.0, y: y - 0.85, w: 2.0, h: 0.5, fontFace: HF, fontSize: 15, bold: true, color: C.white, align: 'center', isTextBox: true, margin: 0 });
    s.addText(t, { x: x - 1.05, y: y + 0.35, w: 2.1, h: 1.4, fontFace: BF, fontSize: 10.5, color: C.pale, align: 'center', valign: 'top', isTextBox: true, margin: 0 }); });
  box(s, 0.8, 5.6, 5.6, 1.1, 'The scorecard note is ready. Hold it three weeks: a scorecard that has itself been scored once is a different object from one that has not.', { size: 11.5, align: 'left', fill: '2B3944', color: C.white });
  box(s, 6.7, 5.6, 5.8, 1.1, 'Forecasts are lodged, never edited. A superseded model gets a new column. That is the only way a scorecard project can score itself.', { size: 11.5, align: 'left', fill: '2B3944', color: C.white });
  foot(s, ''); }

pres.writeFile({ fileName: '/home/claude/prisoncap/outputs/prison_capacity_diagrams.pptx' }).then(f => console.log('wrote', f));
