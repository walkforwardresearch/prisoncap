const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';   // 13.33 x 7.5

// palette: deep slate dominant, off-white, brick accent for the critical number, muted grey
const C = { slate: '1F2933', ink: '323F4B', light: 'F5F6F4', white: 'FFFFFF', brick: 'B03A2E',
            grey: '7B8794', pale: 'E4E7EB', amber: 'C8963E', moss: '5B7F5B' };
const HF = 'Cambria', BF = 'Calibri';

function titleBar(s, t, dark = false) {
  s.background = { color: dark ? C.slate : C.white };
  s.addText(t, { x: 0.6, y: 0.35, w: 12.1, h: 1.1, fontFace: HF, fontSize: 30, bold: true,
                 color: dark ? C.white : C.slate, isTextBox: true, margin: 0, valign: 'top' });
}
function foot(s, t, dark = false) {
  s.addText(t, { x: 0.6, y: 7.0, w: 12.1, h: 0.3, fontFace: BF, fontSize: 9, color: dark ? C.pale : C.grey,
                 isTextBox: true, margin: 0 });
}
function stat(s, x, y, w, big, label, color = C.slate, bigSize = 48) {
  s.addText(big, { x, y, w, h: 0.9, fontFace: HF, fontSize: bigSize, bold: true, color, isTextBox: true, margin: 0 });
  s.addText(label, { x, y: y + 0.9, w, h: 0.6, fontFace: BF, fontSize: 12, color: C.grey, isTextBox: true, margin: 0, valign: 'top' });
}
function body(s, x, y, w, h, items, size = 14) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
            { x, y, w, h, fontFace: BF, fontSize: size, color: C.ink, isTextBox: true, margin: 0, valign: 'top' });
}
function card(s, x, y, w, h, head, text, headColor = C.slate) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: C.light }, line: { color: C.light } });
  s.addText(head, { x: x + 0.25, y: y + 0.2, w: w - 0.5, h: 0.45, fontFace: HF, fontSize: 16, bold: true, color: headColor, isTextBox: true, margin: 0 });
  s.addText(text, { x: x + 0.25, y: y + 0.7, w: w - 0.5, h: h - 0.9, fontFace: BF, fontSize: 12.5, color: C.ink, isTextBox: true, margin: 0, valign: 'top' });
}
const chartBase = (title) => ({
  showTitle: true, title, titleFontFace: HF, titleFontSize: 13, titleColor: C.slate,
  catAxisLabelColor: C.grey, valAxisLabelColor: C.grey, catAxisLabelFontFace: BF, valAxisLabelFontFace: BF,
  catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
  valGridLine: { color: C.pale, size: 0.5 }, catGridLine: { style: 'none' },
  legendFontFace: BF, legendFontSize: 10, legendColor: C.ink, legendPos: 'b',
});

// ------------------------------------------------------------ 1 title
{
  const s = pres.addSlide();
  s.background = { color: C.slate };
  s.addText('Prison Capacity and Early Release Triggers', { x: 0.8, y: 2.0, w: 11.5, h: 1.2, fontFace: HF, fontSize: 40, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText('Where the model stands, and what it found', { x: 0.8, y: 3.2, w: 11.5, h: 0.7, fontFace: BF, fontSize: 20, color: C.pale, isTextBox: true, margin: 0 });
  s.addText('Walk Forward Research. Status at 3 September 2026, built against the project brief of the same date.', { x: 0.8, y: 5.9, w: 11.5, h: 0.5, fontFace: BF, fontSize: 13, color: C.grey, isTextBox: true, margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: 0.8, y: 4.3, w: 0.9, h: 0.9, fill: { color: C.brick }, line: { color: C.brick } });
  s.addText('2,094', { x: 1.9, y: 4.3, w: 4, h: 0.5, fontFace: HF, fontSize: 26, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText('headroom on 24 August 2026, the latest bulletin', { x: 1.9, y: 4.8, w: 6, h: 0.4, fontFace: BF, fontSize: 12, color: C.pale, isTextBox: true, margin: 0 });
}

// ------------------------------------------------------------ 2 what got built
{
  const s = pres.addSlide();
  titleBar(s, 'The data layer is done and cross-validated');
  stat(s, 0.6, 1.6, 3.0, '787', 'weekly bulletins parsed, January 2011 to date, five layout eras');
  stat(s, 3.9, 1.6, 3.0, '12,038', 'establishment-months of certified accommodation, capacity and population');
  stat(s, 7.2, 1.6, 3.0, '18', 'projection editions, 2008 to 2025, in one scenario-normalised table');
  stat(s, 10.5, 1.6, 2.5, '101', 'entries in the definitions log');
  card(s, 0.6, 3.5, 5.9, 3.2, 'Every series reconciles to every other',
    'Monthly establishment sums minus the operating margin equal weekly useable capacity on the report date: mean gap 0.5 people over 101 months.\n\nProjection editions publish their own base-year actual: it matches the weekly bulletin to within 40 people since 2018.\n\nAnnual Statement 2025 quotes 88,931 useable capacity at 29 September 2025. The weekly series gives 88,931.');
  card(s, 6.8, 3.5, 5.9, 3.2, 'Deterministic routes only',
    'Every input is a gov.uk content API call or an asset URL enumerated from one. No page scraping.\n\nrefresh.sh rebuilds everything from the API, and reads every source Notes sheet before it touches a number. If a definition changed, it stops.\n\nOne-off inputs (release tranche dates, margin steps) live in a hand-maintained CSV with the source cited.');
  foot(s, 'Repo: prisoncap. Sources: MoJ weekly and monthly population bulletins, Prison Population Projections, OMSQ, CJS quarterly, HMPPS workforce, Safety in Custody, Annual Statement on Prison Capacity.');
}

// ------------------------------------------------------------ 3 scorecard
{
  const s = pres.addSlide();
  titleBar(s, 'Q1. A forecaster who assumed nothing would change beat the MoJ at every horizon');
  s.addChart(pres.ChartType.bar, [
    { name: 'MoJ central projection', labels: ['1 yr', '2 yr', '3 yr', '4 yr', '5 yr', '6 yr'], values: [2429, 3923, 3616, 5115, 4778, 3780] },
    { name: 'Naive no-change', labels: ['1 yr', '2 yr', '3 yr', '4 yr', '5 yr', '6 yr'], values: [1679, 2428, 3386, 4053, 3184, 2687] },
  ], { ...chartBase('Mean absolute error in prisoners, by forecast horizon, all editions 2008 to 2025'),
       x: 0.6, y: 1.5, w: 7.4, h: 5.3, barGrouping: 'clustered', chartColors: [C.brick, C.grey],
       showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 9, dataLabelColor: C.ink, showLegend: true });
  stat(s, 8.5, 1.6, 4.2, '14 / 14', 'targets from the 2020-onward editions were too high', C.brick);
  stat(s, 8.5, 3.4, 4.2, '+7.6%', 'mean error of those editions, against +2.3% for 2008 to 2014', C.brick, 40);
  body(s, 8.5, 5.0, 4.2, 1.9, [
    'Bias worsens by era: +2.3%, +4.3%, +7.6%',
    'Nobody outside government scores these. A parliamentary submission calls their low profile "curious"',
  ], 12);
  foot(s, 'Outturn from the weekly bulletin series interpolated to each edition\'s reference date. Naive forecast is the population at the edition\'s own base date carried forward.');
}

// ------------------------------------------------------------ 4 decomposition
{
  const s = pres.addSlide();
  titleBar(s, 'The error is almost entirely in one place, and two errors cancel');
  s.addChart(pres.ChartType.bar, [
    { name: '2015 to 2019 editions', labels: ['Determinate', 'Remand', 'Non-criminal', 'Indeterminate', 'Recall'], values: [900, 851, 465, 307, -47] },
    { name: '2020 onward editions', labels: ['Determinate', 'Remand', 'Non-criminal', 'Indeterminate', 'Recall'], values: [8610, -2862, 254, -126, -361] },
  ], { ...chartBase('Mean projection error by custody type (projected minus actual, people)'),
       x: 0.6, y: 1.5, w: 7.4, h: 5.3, barDir: 'bar', chartColors: [C.grey, C.brick],
       showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 9, dataLabelColor: C.ink, showLegend: true });
  stat(s, 8.5, 1.6, 4.2, '95%', 'of total projection error sits in the determinate sentenced population', C.brick);
  stat(s, 8.5, 3.4, 4.2, '1.9x', 'gross component error over net error. Headline bias understates the modelling failure by half', C.slate, 40);
  body(s, 8.5, 5.1, 4.2, 1.8, [
    'Determinate is over-projected: release rules changed after publication',
    'Remand is under-projected: the court backlog',
    'Both are the same phenomenon seen twice',
  ], 12);
  foot(s, '13 matched pairs where an edition projected a month for which a later edition published the unrounded actual. 19 successive-edition revisions confirm: determinate is 105% of revision movement.');
}

// ------------------------------------------------------------ 5 composition swap
{
  const s = pres.addSlide();
  titleBar(s, 'One prison population has been swapped for another');
  s.addChart(pres.ChartType.bar, [
    { name: 'Determinate', labels: ['June 2017', 'Sept 2025'], values: [57726, 48224] },
    { name: 'Remand', labels: ['June 2017', 'Sept 2025'], values: [9638, 17700] },
    { name: 'Recall', labels: ['June 2017', 'Sept 2025'], values: [6390, 12657] },
    { name: 'Indeterminate', labels: ['June 2017', 'Sept 2025'], values: [10600, 8493] },
    { name: 'Other', labels: ['June 2017', 'Sept 2025'], values: [1509, 391] },
  ], { ...chartBase('Prison population by custody type, MoJ published actuals'),
       x: 0.6, y: 1.5, w: 6.6, h: 5.3, barGrouping: 'stacked', chartColors: [C.slate, C.brick, C.amber, C.grey, C.pale],
       showValue: true, dataLabelPosition: 'ctr', dataLabelFontSize: 9, dataLabelColor: C.white, showLegend: true });
  stat(s, 7.7, 1.6, 2.4, '-16.5%', 'determinate', C.slate, 34);
  stat(s, 10.2, 1.6, 2.4, '+84%', 'remand', C.brick, 34);
  stat(s, 7.7, 3.2, 2.4, '+98%', 'recall', C.brick, 34);
  stat(s, 10.2, 3.2, 2.4, '+1.9%', 'total', C.grey, 34);
  card(s, 7.7, 4.9, 5.0, 1.9, 'Near one-for-one substitution',
    '12,664 sentenced, indeterminate and non-criminal prisoners out. 14,329 remand and recall prisoners in. The break is 2019 to 2020 when courts stopped; it never reversed. Recall then rises every period with no step, so it is not a reclassification.');
  foot(s, 'Base-year actuals published in the 2017-2022 and 2025-2030 projection editions. Determinate share of the population 67% to 55%; remand plus recall 19% to 35%.');
}

// ------------------------------------------------------------ 6 time served
{
  const s = pres.addSlide();
  titleBar(s, 'Sentences got longer and people served the extra time, until 2022');
  const labels = ['2017 Q1', '2018 Q1', '2021 Q1', '2022 Q1', '2023 Q2', '2024 Q1', '2025 Q2', '2025 Q4', '2026 Q1'];
  s.addChart(pres.ChartType.line, [
    { name: 'Mean sentence imposed (months)', labels, values: [18.95, 19.99, 26.26, 26.32, 25.41, 25.78, 29.95, 27.56, 26.68] },
    { name: 'Mean time served (months)', labels, values: [11.86, 12.69, 15.96, 15.92, 15.20, 15.52, 15.03, 14.22, 14.52] },
  ], { ...chartBase('Releases from determinate sentences, England and Wales'),
       x: 0.6, y: 1.5, w: 7.4, h: 5.3, chartColors: [C.slate, C.brick], lineSize: 2.5, lineDataSymbol: 'circle', lineDataSymbolSize: 6, showLegend: true });
  stat(s, 8.5, 1.6, 4.2, '63% → 54%', 'proportion of sentence actually served, 2017 to 2026', C.brick, 36);
  card(s, 8.5, 3.3, 4.2, 3.5, 'Two eras, not one trend',
    '2017 to 2022: sentence +39%, time served +34%. The proportion held at 60 to 63%. Sentence inflation passed straight through.\n\n2022 to 2026: sentence +1%, time served -9%. Proportion fell 8.6 points in two years. That is an intervention, not drift: ECSL, then SDS40, then the one-third model.\n\nAt the pre-2022 rate today\'s sentences would mean about 5,800 more determinate places. Headroom is 2,094.');
  foot(s, 'OMSQ prison releases tables 3.Q.3 to 3.Q.5 across four editions. Figures include time on remand. Serious offenders moved the other way (two-thirds release points from 2020), so the mean hides a widening spread.');
}

// ------------------------------------------------------------ 7 recall
{
  const s = pres.addSlide();
  titleBar(s, 'Recalls now exceed releases in the same quarter');
  const labels = ['23 Q1', '23 Q2', '23 Q3', '23 Q4', '24 Q1', '24 Q2', '24 Q3', '24 Q4', '25 Q1', '25 Q2', '25 Q3', '25 Q4', '26 Q1'];
  s.addChart(pres.ChartType.bar, [
    { name: 'Determinate releases', labels, values: [11887, 12132, 12351, 12764, 13289, 13600, 14200, 15000, 13296, 14946, 14038, 14643, 12977] },
    { name: 'Recalls to custody', labels, values: [6824, 6814, 7030, 7152, 7415, 9782, 9975, 10401, 10101, 11041, 12836, 14349, 13193] },
  ], { ...chartBase('Releases from determinate sentences and recalls, per quarter'),
       x: 0.6, y: 1.5, w: 7.4, h: 5.3, barGrouping: 'clustered', chartColors: [C.grey, C.brick], showLegend: true });
  stat(s, 8.5, 1.6, 4.2, '+32%', 'in one quarter, Q1 to Q2 2024: the surge began with the ECSL extensions, before SDS40', C.brick);
  stat(s, 8.5, 3.4, 4.2, '565 → 1,017', 'recalls per 1,000 releases. An intensity effect: releases rose only 12%', C.slate, 30);
  card(s, 8.5, 5.0, 4.2, 1.9, 'A 56-day recall since 31 March 2026',
    'OMSQ note 12: the 56-day fixed-term recall replaced 14 and 28 day recalls. Mechanically up to +3,570 places. Not yet visible in the data on timing grounds. The Apr-Jun 2026 OMSQ, due about 29 October, is the first release that can measure it.');
  foot(s, 'OMSQ Table 5.Q.1 and 3.Q.1 across five editions. 2024 Q2 to Q4 releases are estimated from the annual total (57,277) pending the quarterly split. 99.4% of recalls result in return to custody. Composition series breaks at July 2025 (note 11); totals unaffected.');
}

// ------------------------------------------------------------ 7b long run
{
  const s = pres.addSlide();
  titleBar(s, 'The long run: fewer leave, more come back, and headroom has never been comfortable');
  const yrs = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024'];
  s.addChart(pres.ChartType.line, [
    { name: 'Recalls per 100 releases', labels: yrs, values: [28.8, 29.4, 30.7, 34.9, 42.2, 45.9, 47.0, 50.4, 56.6, 65.6] },
    { name: 'Proportion of sentence served (%)', labels: yrs, values: [60.6, 62.1, 63.7, 63.7, 62.4, 60.8, 60.3, 60.2, 60.2, 55.5] },
  ], { ...chartBase('Two long-run ratios, annual, England and Wales'),
       x: 0.6, y: 1.5, w: 6.4, h: 3.4, chartColors: [C.brick, C.slate], lineSize: 2.5, lineDataSymbol: 'circle', lineDataSymbolSize: 5, showLegend: true });
  card(s, 0.6, 5.1, 6.4, 1.7, 'Releases down 23%, recalls up 125%',
    '74,443 releases in 2015 became 57,277 in 2024. 21,467 recalls became 48,327 in 2025. The proportion served held at 60 to 64% for nine years, then dropped five points in one.');
  stat(s, 7.5, 1.5, 2.5, '10', 'weeks in 15 years with headroom above 5,000. The last was February 2013', C.brick, 44);
  stat(s, 10.2, 1.5, 2.5, '96–99%', 'mean occupancy in every calendar year since 2011', C.slate, 30);
  stat(s, 7.5, 3.3, 2.5, '77 wks', 'longest unbroken run above 2,000 headroom, ending September 2013', C.slate, 30);
  stat(s, 10.2, 3.3, 2.5, '1 in 6', 'weeks since 2011 with headroom at the level the MoJ projects for 2032', C.brick, 30);
  card(s, 7.5, 5.1, 5.2, 1.7, '2026 is the best year for headroom since 2013',
    'Mean 2,927 so far, minimum 2,094. Against 1,130 in 2023 (minimum 557), 1,831 in 2024, 1,838 in 2025. The year described as perma-crisis has had more room than any since 2013.', C.brick);
  foot(s, 'OMSQ 2024 annual tables 3.A.1, 3.A.5, 5.A.2; weekly bulletin series 2011 to 2026. 2024 sentence and time-served means are inflated by the SDS40 cohort; the ratio series shown here are less affected.');
}

// ------------------------------------------------------------ 8 supply gross vs net
{
  const s = pres.addSlide();
  titleBar(s, 'Q3. Fourteen years of building added a few hundred net places');
  s.addChart(pres.ChartType.bar, [
    { name: 'New prisons', labels: ['2022/23', '2023/24', '2024/25', '2025/26', '2026/27 to Jul'], values: [940, 2150, 54, 1177, 126] },
    { name: 'Rest of the estate', labels: ['2022/23', '2023/24', '2024/25', '2025/26', '2026/27 to Jul'], values: [2011, 662, -64, -81, -1026] },
  ], { ...chartBase('Change in operational capacity by financial year (places)'),
       x: 0.6, y: 1.5, w: 7.0, h: 5.3, barGrouping: 'clustered', chartColors: [C.moss, C.brick],
       showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 9, dataLabelColor: C.ink, showLegend: true });
  stat(s, 8.1, 1.6, 4.6, '1,005', 'net places added May 2010 to Sept 2024, per the Public Accounts Committee, against 6,518 gross', C.brick);
  stat(s, 8.1, 3.4, 4.6, '+641', 'net change in operational capacity, Jan 2011 to Aug 2026, from this series', C.slate, 40);
  card(s, 8.1, 5.0, 4.6, 1.9, 'Millsike, the brief\'s first case',
    'Reached 90% of peak in 12 months, faster than Five Wells (20) or Fosse Way (31). But it runs at 1,158 against 1,468 certified: 79%, where older new-builds sit at 97 to 101%. On time, 310 places short.');
  foot(s, 'Monthly by-establishment bulletins, 2018 to 2026. HMPPS Annual Report confirms its new-places figures "do not account for loss of places". Attrition absorbed 85% of gross additions 2010-24.');
}

// ------------------------------------------------------------ 9 capacity endogenous
{
  const s = pres.addSlide();
  titleBar(s, 'Capacity follows population. That halves what a release buys');
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: 1.5, w: 6.4, h: 2.6, fill: { color: C.slate }, line: { color: C.slate } });
  s.addText('d cap  =  627  −  0.284 × headroom(t−26)  +  0.386 × d pop', { x: 0.9, y: 1.7, w: 5.9, h: 0.7, fontFace: 'Courier New', fontSize: 15, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText('13-week changes, weekly data 2011 to 2026. t = −14.4 and +19.4. R² 0.42, n = 791.', { x: 0.9, y: 2.4, w: 5.9, h: 0.5, fontFace: BF, fontSize: 12, color: C.pale, isTextBox: true, margin: 0 });
  s.addText('Survives the clean checks: population change lagged a further 13 weeks predicts capacity change at t = 13.4, with no capacity term on the right-hand side. Coefficient rises to +0.47 (R² 0.58) in the crisis era.', { x: 0.9, y: 2.95, w: 5.9, h: 1.0, fontFace: BF, fontSize: 11, color: C.pale, isTextBox: true, margin: 0, valign: 'top' });
  stat(s, 7.5, 1.5, 2.5, '39%', 'of any population move is matched by capacity moving the same way', C.brick, 40);
  stat(s, 10.2, 1.5, 2.5, '2,203', 'equilibrium headroom with population flat', C.slate, 40);
  card(s, 0.6, 4.4, 6.0, 2.4, 'The 2026 capacity fall was forecast maintenance',
    'Annual Statement 2025 (Jan 2026) projects adult supply falling 89,900 to 88,300 by May 2027 before recovering. Annex B: places offline for fire safety and LTHSE security work plus a dilapidation assumption. A full estate prevents that work; when the population dropped after March, deferred work started.');
  card(s, 6.9, 4.4, 5.8, 2.4, 'Three hypotheses tested and scored',
    'Staffing: rejected. Slope +0.04 places per officer FTE, R² 0.001 on every specification; the full-span correlation is a scale effect.\nStarting crowding: rejected, R² 0.002.\nAssaults: partial. Prisons that cut capacity had a 36% higher assault rate (t = 2.1) but it explains 2% of how much. Self-harm: nothing.');
  foot(s, 'Establishment-level tests use 104 to 111 matched prisons. Officer staffing is 92% of target and falling (1,526 FTE lost since March 2024), but that operates at estate level, not through the prisons that cut.');
}

// ------------------------------------------------------------ 10 benchmarks and long horizons
{
  const s = pres.addSlide();
  titleBar(s, 'Q2. Nothing forecasts this series, and trend extrapolation makes it worse');
  const rows = [
    [{ text: 'Horizon', options: { bold: true, color: C.white, fill: { color: C.slate } } }, { text: 'Naive MAE', options: { bold: true, color: C.white, fill: { color: C.slate } } }, { text: 'Drift, 52-wk trend', options: { bold: true, color: C.white, fill: { color: C.slate } } }, { text: 'Drift, 5-yr trend', options: { bold: true, color: C.white, fill: { color: C.slate } } }, { text: 'Naive MAPE', options: { bold: true, color: C.white, fill: { color: C.slate } } }],
    ['13 weeks', '784', '804', '', '0.9%'], ['1 year', '2,052', '2,887', '2,384', '2.5%'], ['2 years', '3,560', '5,219', '4,226', '4.3%'],
    ['3 years', '4,794', '6,948', '5,824', '5.7%'], ['5 years', '5,541', '12,088', '7,628', '6.6%'], ['7 years', '2,646', '9,538', '4,480', '3.0%'], ['10 years', '1,191', '4,952', '1,416', '1.4%'],
  ].map((r, i) => i === 0 ? r : r.map((c, j) => ({ text: c, options: { color: j === 1 ? C.brick : C.ink, bold: j === 1, fill: { color: i % 2 ? C.light : C.white } } })));
  s.addTable(rows, { x: 0.6, y: 1.5, w: 7.4, colW: [1.4, 1.5, 1.7, 1.5, 1.3], fontFace: BF, fontSize: 12, border: { type: 'solid', color: C.pale, pt: 0.5 }, rowH: 0.42, align: 'center', valign: 'middle' });
  stat(s, 8.5, 1.6, 4.2, '−65 / yr', 'population trend over the full 15.6 years. The sign flips four times across windows', C.slate, 40);
  stat(s, 8.5, 3.4, 4.2, '0%', 'of five-year windows since 2011 reached the +2,000/yr the ten-year plan assumes', C.brick);
  body(s, 8.5, 5.1, 4.2, 1.8, [
    'ETS beats naive by 2.5% at 13 weeks. Reported as the negative result it is',
    'Five-year error is 5,541: nearly three times total headroom',
    'The 7 and 10 year "improvement" is mean reversion on 35 origins, not skill',
  ], 12);
  foot(s, 'Walk-forward on the weekly series, origins 2016 to 2026 for the 13-week row and 2011 to 2026 for the rest. The +3,000 a year figure is the MoJ\'s near-term no-action counterfactual; its own central path with reforms is +1,333 a year.');
}

// ------------------------------------------------------------ 11 model evolution and seasonality
{
  const s = pres.addSlide();
  titleBar(s, 'Q4. Four model versions, each fixing a real error in the last');
  s.addChart(pres.ChartType.bar, [
    { name: 'Seasonal deviation (people)', labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], values: [-407, 74, 126, -173, -198, -257, -55, 183, 163, 340, 365, 13] },
  ], { ...chartBase('The annual cycle I had been extrapolating: deviation from 53-week centred mean, 2011 to 2026'),
       x: 0.6, y: 1.5, w: 6.6, h: 3.3, chartColors: [C.slate], showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 8, dataLabelColor: C.ink, showLegend: false });
  const rows = [
    [{ text: 'Version', options: { bold: true, color: C.white, fill: { color: C.slate } } }, { text: 'What it fixed', options: { bold: true, color: C.white, fill: { color: C.slate } } }, { text: 'Headroom, Jan 2027', options: { bold: true, color: C.white, fill: { color: C.slate } } }],
    ['v1', 'Dated release schedule, capacity extrapolated', '1,042'],
    ['v2', 'Capacity endogenous to population', '1,867'],
    ['grid', 'asfreq bug had flattened the last two years', ''],
    ['v3', 'Seasonality removed; trend +19/wk not +143', '4,210'],
  ].map((r, i) => i === 0 ? r : r.map((c, j) => ({ text: c, options: { color: j === 2 ? C.brick : C.ink, bold: j === 2, fill: { color: i % 2 ? C.light : C.white } } })));
  s.addTable(rows, { x: 7.5, y: 1.5, w: 5.2, colW: [0.8, 3.0, 1.4], fontFace: BF, fontSize: 11.5, border: { type: 'solid', color: C.pale, pt: 0.5 }, rowH: 0.5, valign: 'middle' });
  card(s, 0.6, 5.0, 6.6, 1.8, 'Half the summer rise was the calendar',
    'Of the +770 from April to August, +411 was seasonal. Deseasonalised, the underlying trend is +19 a week. It was fitted over the fastest-rising part of the cycle and extrapolated from just before the November peak.');
  card(s, 7.5, 4.3, 5.2, 2.5, 'The outlook now rests on 19 weeks of data',
    'At +19/wk headroom never enters the historical trigger band. At +40/wk it does by November 2027; at +60/wk by September 2027; at +143/wk by this month. That range is the finding: the near-term outlook is not knowable to the precision at which policy is being made.', C.brick);
  foot(s, 'The earlier validation of "bust before Christmas" is withdrawn: with no releases and the fitted trend, headroom at Christmas 2026 is 2,269. The claim needs about +150 a week.');
}

// ------------------------------------------------------------ 12 register
{
  const s = pres.addSlide();
  titleBar(s, 'The standing forecast, lodged and not to be edited');
  const labels = ['28 Sep', '26 Oct', '30 Nov', '28 Dec', '25 Jan', '1 Mar', '29 Mar', '31 May'];
  s.addChart(pres.ChartType.line, [
    { name: 'v1 exogenous', labels, values: [1139, 1725, 1420, 1206, 1042, 587, 23, -1496] },
    { name: 'v2 endogenous', labels, values: [1183, 1975, 1912, 1827, 1867, 1687, 1442, 735] },
    { name: 'v3 seasonal (central)', labels, values: [2076, 3170, 3509, 4226, 4210, 3957, 4109, 4048] },
    { name: 'Lowest historical trigger, 557', labels, values: [557, 557, 557, 557, 557, 557, 557, 557] },
  ], { ...chartBase('Headroom forecasts by target date, from the 24 August 2026 bulletin'),
       x: 0.6, y: 1.5, w: 7.6, h: 5.3, chartColors: [C.grey, C.amber, C.brick, C.pale], lineSize: 2.5, lineDataSymbol: 'circle', lineDataSymbolSize: 5, showLegend: true });
  card(s, 8.6, 1.5, 4.1, 2.4, 'Why all three columns stay',
    'The scorer never edits a lodged number. A superseded model gets a new column, not a revision. That is the only way a scorecard project can score itself.');
  card(s, 8.6, 4.2, 4.1, 2.6, 'One bulletin settles it',
    'The three agree in September (spread under 1,000) and disagree by 3,200 in January 2027. The September bulletin tests the shared capacity feedback; the January bulletin tests the model. First scoreable target: 28 September 2026.', C.brick);
  foot(s, 'outputs/forecast_register.csv. score_register.py appends a one-line weekly update on every refresh; the brief\'s standing forecast deliverable.');
}

// ------------------------------------------------------------ 13 corrections
{
  const s = pres.addSlide();
  titleBar(s, 'Six corrections made during the build, each of which changed a conclusion');
  const items = [
    ['Weekly grid', 'asfreq anchored on a 2011 Friday; bulletins moved to Mondays in Oct 2024. Two years filled flat. Affected the capacity estimate, destroyed the seasonal analysis.'],
    ['Staffing triple-counted', 'Three aggregate rows inside the establishment column. "4,443 officers lost" was 1,526. Percentages were unaffected; MoJ\'s own 95% figure confirms the corrected series.'],
    ['Seasonality', 'Amplitude 859. The +143/week trend was half calendar. Reversed the outlook and withdrew the validation of a ministerial claim.'],
    ['56-day recall', 'Found in OMSQ note 12 after the analysis. Replaced 14 and 28 day recalls from 31 March 2026. Not yet visible in the data.'],
    ['Recall composition', 'Note 11: series break at July 2025. Totals stand; the fixed-term share does not.'],
    ['Sentence inflation', 'Comprehensively done by the Sentencing Academy (2025): 54% more punitive, 87% genuine. Demoted from finding to mechanism.'],
  ];
  items.forEach(([h, t], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.2, y = 1.5 + row * 1.75;
    s.addShape(pres.ShapeType.ellipse, { x, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: C.brick }, line: { color: C.brick } });
    s.addText(String(i + 1), { x, y: y + 0.05, w: 0.5, h: 0.5, fontFace: HF, fontSize: 14, bold: true, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(h, { x: x + 0.7, y, w: 5.3, h: 0.4, fontFace: HF, fontSize: 15, bold: true, color: C.slate, isTextBox: true, margin: 0 });
    s.addText(t, { x: x + 0.7, y: y + 0.42, w: 5.3, h: 1.2, fontFace: BF, fontSize: 11.5, color: C.ink, isTextBox: true, margin: 0, valign: 'top' });
  });
  foot(s, 'Three of the six were in a Notes sheet read after the numbers. The refresh now diffs every Notes sheet first and stops if one changed.');
}

// ------------------------------------------------------------ 14 what the evidence says and next
{
  const s = pres.addSlide();
  s.background = { color: C.slate };
  titleBar(s, 'What the evidence supports, and what comes next', true);
  const claims = [
    ['Supported', 'The MoJ projections overshoot at every horizon and a naive forecast beats them. The error sits in the component release policy controls. A counterfactual falsified by the publisher\'s own subsequent actions cannot size a £7bn programme.'],
    ['Supported', 'Sentenced prisoners have been replaced by remand and recalled ones near one for one. Recalls now exceed determinate releases. Every early release scheme carries its own partial reversal.'],
    ['Supported', 'Net capacity has been flat for fifteen years. Capacity responds to population, so a release tranche buys about 60% of its face value.'],
    ['Not supported', 'Any ten-year statement about headroom. The five-year forecast error is three times the buffer. The near-term outlook depends on a trend estimated from 19 weeks.'],
  ];
  claims.forEach(([tag, t], i) => {
    const y = 1.5 + i * 1.25;
    const ok = tag === 'Supported';
    s.addShape(pres.ShapeType.rect, { x: 0.6, y, w: 1.6, h: 0.45, fill: { color: ok ? C.moss : C.brick }, line: { color: ok ? C.moss : C.brick } });
    s.addText(tag, { x: 0.6, y, w: 1.6, h: 0.45, fontFace: BF, fontSize: 11, bold: true, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(t, { x: 2.4, y: y - 0.05, w: 10.3, h: 1.1, fontFace: BF, fontSize: 12.5, color: C.pale, isTextBox: true, margin: 0, valign: 'top' });
  });
  s.addText('Next', { x: 0.6, y: 6.05, w: 1.2, h: 0.4, fontFace: HF, fontSize: 15, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText('Run the refresh on the 28 September bulletin and see if the notes gate fires.  Score the January 2027 point.  Add the recall term once the Apr-Jun OMSQ lands on 29 October.  Pull OMSQ receptions and court flows for the full demand-side decomposition.', { x: 1.9, y: 6.05, w: 10.8, h: 0.9, fontFace: BF, fontSize: 11.5, color: C.pale, isTextBox: true, margin: 0, valign: 'top' });
}

pres.writeFile({ fileName: '/home/claude/prisoncap/outputs/prison_capacity_status.pptx' }).then(f => console.log('wrote', f));
