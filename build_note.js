const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType,
        AlignmentType, ImageRun, ShadingType, BorderStyle, LevelFormat, PageNumber, Footer, TabStopType } = require('docx');

const INK = '1F2933', GREY = '7B8794', BRICK = 'B03A2E', PALE = 'F5F6F4', RULE = 'C4CBD2';
const W = 9026;   // usable A4 width in DXA with 1" margins

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 160, line: 276 }, alignment: opts.align,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === 'string'
    ? new TextRun({ text: t, font: 'Calibri', size: opts.size ?? 22, color: opts.color ?? INK, bold: opts.bold, italics: opts.italics })
    : t),
});
const R = (text, o = {}) => new TextRun({ text, font: 'Calibri', size: o.size ?? 22, color: o.color ?? INK, bold: o.bold, italics: o.italics });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text: t, font: 'Cambria', size: 30, bold: true, color: INK })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text: t, font: 'Cambria', size: 25, bold: true, color: INK })] });
const bullet = t => new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { after: 100, line: 276 }, children: [new TextRun({ text: t, font: 'Calibri', size: 22, color: INK })] });
const caption = t => new Paragraph({ spacing: { before: 60, after: 240 }, children: [new TextRun({ text: t, font: 'Calibri', size: 18, color: GREY, italics: true })] });

function table(header, rows, widths, opts = {}) {
  const cell = (t, i, isHead, shade) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: isHead ? { type: ShadingType.CLEAR, fill: INK, color: 'auto' } : (shade ? { type: ShadingType.CLEAR, fill: PALE, color: 'auto' } : undefined),
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    borders: { top: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE }, left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' } },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, spacing: { after: 0 },
      children: [new TextRun({ text: String(t), font: 'Calibri', size: opts.size ?? 19, bold: isHead || (opts.boldCol === i), color: isHead ? 'FFFFFF' : ((opts.redCol === i) ? BRICK : INK) })] })],
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }),
           ...rows.map((r, k) => new TableRow({ children: r.map((c, i) => cell(c, i, false, k % 2 === 1)) }))],
  });
}
const img = (path, w, h) => new Paragraph({ spacing: { before: 120, after: 60 }, children: [new ImageRun({ type: 'png', data: fs.readFileSync(path), transformation: { width: w, height: h } })] });

const doc = new Document({
  styles: { default: { document: { run: { font: 'Calibri', size: 22 } } } },
  numbering: { config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 460, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT], font: 'Calibri', size: 18, color: GREY })] })] }) },
    children: [
      new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: 'How good are the Ministry of Justice prison population projections?', font: 'Cambria', size: 40, bold: true, color: INK })] }),
      new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: 'A walk-forward scorecard of eighteen editions, 2008 to 2025', font: 'Cambria', size: 26, color: GREY })] }),
      new Paragraph({ spacing: { after: 360 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 8 } }, children: [new TextRun({ text: 'Walk Forward Research. Working note, 4 September 2026. Data and code published with this note.', font: 'Calibri', size: 20, color: GREY })] }),

      H1('Summary'),
      bullet('Since 2008 the Ministry of Justice has published eighteen editions of its prison population projections. This note scores every central projection against what happened, at every horizon from one to six years, using the MoJ\u2019s own weekly population bulletins as outturn.'),
      bullet('The central projection has been too high at every horizon. Mean error is +2.4% at one year, +3.8% at two and +5.2% at five. Thirteen of seventeen scoreable editions had every target too high. Fourteen of fourteen targets from editions published since 2020 were too high, by 7.6% on average. Removing the COVID years and the release-scheme years from the targets roughly halves the overshoot, to +2.3%, but does not remove it: the bias is structural, and the shocks doubled it.'),
      bullet('A forecaster who simply assumed the population would not change would have beaten the MoJ at every horizon, scored on identical targets. At two years the no-change error is 42% smaller, and the no-change forecast was closer on 54 of the 75 targets. Nobody outside government appears to run this comparison.'),
      bullet('The projections got the direction of change right 63% of the time overall and 53% at one and two years, barely better than a coin toss at the horizons that matter for capacity planning. They projected a rise in 73% of targets; the population rose in 52%.'),
      bullet('At one and two years, outturn fell below the MoJ\u2019s own low scenario 38% of the time. The published range covered the outcome in half of those targets.'),
      bullet('95% of the error sits in the determinate sentenced population, the component set by release rules. Remand error runs the other way. Because the two partly cancel, gross component error is 1.9 times the net headline error, so the headline bias understates the modelling failure by about half.'),
      bullet('The MoJ can fairly say its projections are conditional on unchanged policy and that policy changed. That is true, and it is also the problem: a projection that is systematically falsified by the publisher\u2019s own subsequent actions is not a basis for sizing a \u00a37 billion building programme.'),

      H1('What was scored, and how'),
      P('The eighteen editions run from Prison Population Projections 2008\u20132015 to 2025\u20132030. Each publishes a central path at annual reference points; earlier editions publish it as one of three scenario columns, later editions as a single path broken down by custody type. The 2008 to 2019 editions sit as attachments on a single rolling gov.uk page; the six recent editions have their own pages. All were parsed into one table with scenario labels normalised to central, low and high.'),
      P('Outturn is the weekly prison population bulletin, 787 bulletins from January 2011 to August 2026, parsed into one series and interpolated to each edition\u2019s published reference date. The reference date matters: it moves between end June, 1 June, end September, 1 July and end November across editions, and horizons are not comparable unless the published dates are used. Targets before January 2011 cannot be scored, so the 2008 and 2009 editions are scored from their second year.'),
      P('Whether the projections are measured on the same basis as the bulletins was tested rather than assumed. Ten editions publish their own unrounded base-year actual. Those match the bulletin total, which includes HMPPS-operated immigration removal centres before 2022, more closely than the prisons-only figure: mean absolute gap 258 against 394. Since 2018 the agreement is within 40 people. The bulletin total is therefore used.'),
      P('The benchmark is a forecaster with no model who, at publication, carries the current population forward unchanged. It is available at the same moment with the same information, and its errors are computed on the same targets. Where an edition publishes no base actual, the bulletin value at 30 June of the edition year is used. For the 2008, 2009 and 2010 editions, whose base years predate the weekly series, the 30 June prison population is taken from the Population in Custody bulletins for June 2009 and June 2010 (83,194, 83,391 and 85,002), so every one of the 75 targets has a like-for-like benchmark.'),
      P('Horizon is the calendar year of the reference date less the edition year, so a 2020 edition\u2019s September 2021 target is one year ahead. Error is projected minus actual; a positive error means the projection was too high.'),

      H1('Results'),
      H2('By horizon'),
      table(['Horizon', 'Mean error', 'Mean abs. % error', 'Share too high', 'MoJ MAE', 'No-change MAE', 'MoJ / no-change', 'No-change closer'],
        [['1 year', '+2.4%', '2.9%', '87%', '2,429', '1,666', '1.46', '73%'], ['2 years', '+3.8%', '4.7%', '87%', '3,923', '2,275', '1.72', '67%'],
         ['3 years', '+3.5%', '4.3%', '86%', '3,616', '3,222', '1.12', '64%'], ['4 years', '+4.6%', '6.1%', '79%', '5,115', '3,595', '1.42', '71%'],
         ['5 years', '+5.2%', '5.7%', '78%', '4,778', '2,630', '1.82', '100%'], ['6 years', '+4.3%', '4.6%', '86%', '3,780', '2,439', '1.55', '57%']],
        [1050, 1050, 1350, 1150, 1050, 1250, 1050, 1076], { redCol: 6 }),
      caption('Table 1. Central projection against outturn, all editions, 75 targets, both forecasts scored on the same targets. MAE in prisoners. The ratio column is MoJ error over no-change error; above 1 means the no-change forecast was more accurate. The final column is the share of targets on which it was closer.'),
      img('/home/claude/prisoncap/outputs/fig2_mae.png', 600, 228),
      caption('Figure 1. Mean absolute error by horizon. The no-change forecast wins at every horizon.'),
      img('/home/claude/prisoncap/outputs/fig1_fan.png', 600, 324),
      caption('Figure 2. Every central path since 2008 against the weekly outturn. Editions from 2020 onward, in red, all project a rise the population has not made.'),

      H2('By era'),
      table(['Editions', 'Mean error', 'Mean abs. % error', 'Share too high', 'MoJ MAE', 'No-change MAE', 'No-change closer'],
        [['2008 to 2014', '+2.3%', '3.4%', '75%', '2,895', '1,623', '29 of 40'], ['2015 to 2019', '+4.3%', '4.9%', '91%', '3,984', '3,212', '15 of 21'], ['2020 to 2025', '+7.6%', '7.6%', '100%', '6,506', '4,703', '10 of 14']],
        [1700, 1150, 1500, 1300, 1100, 1250, 1026], { redCol: 1 }),
      caption('Table 2. The bias has worsened in each era, and the no-change forecast wins in every era, including the 2008 to 2014 editions that predate any emergency release scheme. No target from a 2020-onward edition has been too low.'),

      H2('Direction and range'),
      P('Two further tests do not depend on magnitude. First, direction: did the central path get the sign of the change from the base year right? Across 75 targets it did so 63% of the time, and 53% at both one and two years. The projections called a rise in 73% of targets; the population rose in 52%. At the horizons that bear on capacity decisions, the central path is about as informative on direction as a coin toss, and it is biased toward predicting growth. Second, coverage: forty-five targets have a published low and high scenario. Outturn fell inside that range 67% of the time overall, but only 50% at one and two years, where it fell below the low scenario in 38% of targets. Coverage improves to 86% at five years because the range widens: the mean half-width at three years, 3,343, is about the same as the mean absolute error at three years, 3,616.'),

      H2('By edition'),
      table(['Edition', '1 yr', '2 yr', '3 yr', '4 yr', '5 yr', 'Targets', 'No-change wins', 'All too high'],
        [['2008\u20132015', 'n/a', 'n/a', '+3.0', '+2.7', '+5.7', '5', '4', 'yes'], ['2009\u20132015', 'n/a', '+1.8', '+1.5', '+4.5', '+2.9', '5', '2', 'yes'],
         ['2010\u20132016', '+2.0', '+1.5', '+5.5', '+3.7', '+2.9', '6', '5', 'yes'], ['2011\u20132017', '+0.6', '+3.7', '+2.3', '+2.2', '+4.0', '6', '4', 'yes'],
         ['2012\u20132018', '+0.9', '\u22121.4', '\u22122.0', '\u22120.5', '\u22120.7', '6', '3', 'no'], ['2013\u20132019', '\u22122.5', '\u22124.7', '\u22123.7', '\u22125.0', '\u22121.8', '6', '5', 'no'],
         ['2014\u20132020', '+1.9', '+4.7', '+4.0', '+8.1', '+8.9', '6', '6', 'yes'], ['2015\u20132021', '+1.8', '+1.8', '+6.3', '+7.6', '+12.7', '5', '5', 'yes'],
         ['2016\u20132021', '\u22121.5', '+0.9', '+1.3', '+5.7', '', '4', '1', 'no'], ['2017\u20132022', '+3.8', '+4.7', '+8.5', '+12.0', '', '4', '4', 'yes'],
         ['2018\u20132023', '+1.2', '+5.9', '+8.6', '+6.3', '', '4', '4', 'yes'], ['2019\u20132024', '+3.5', '+3.7', '+0.9', '\u22124.8', '', '4', '1', 'no'],
         ['2020\u20132026', '+5.6', '+8.4', '+5.9', '+10.9', '+11.9', '5', '4', 'yes'], ['2021\u20132026', '+5.0', '+4.2', '+7.0', '+11.6', '', '4', '2', 'yes'],
         ['2022\u20132027', '+1.4', '+8.3', '', '', '', '2', '1', 'yes'], ['2023\u20132028', '+9.8', '+14.2', '', '', '', '2', '2', 'yes'],
         ['2024\u20132029', '+2.0', '', '', '', '', '1', '1', 'yes']],
        [1300, 850, 850, 850, 850, 850, 950, 1300, 1226], { size: 18 }),
      caption('Table 3. Percentage error of the central path at each horizon, by edition. n/a marks a target dated before January 2011, outside the weekly series and not scoreable; a blank means the edition published no target at that horizon. The 2025\u20132030 edition has no scoreable target yet: its first, 30 September 2026, is 91,400 against 86,843 on 24 August, and will be scored against the 28 September bulletin when it publishes in early October. The 2012 and 2013 editions, which projected a fall, are the only two that were too low.'),

      H2('Robustness'),
      P('A hostile reader will ask whether the result is an artefact of two shocks that no projection could have foreseen: the COVID fall of 2020 to 2021, and the emergency releases from October 2023. It is not. The table below re-scores the central path after removing those target years, after removing both, after switching outturn to the prisons-only definition, and after dropping the five largest misses.'),
      table(['Cut', 'Targets', 'Mean error', 'Share too high', 'No-change closer', 'No-change wins at every horizon'],
        [['All targets', '75', '+3.8%', '84%', '72%', 'yes'], ['Excluding COVID targets, Mar 2020 to Dec 2021', '65', '+3.2%', '82%', '72%', 'yes'],
         ['Excluding release-scheme targets, Oct 2023 on', '66', '+3.2%', '82%', '71%', 'yes'], ['Excluding both: normal years only', '56', '+2.3%', '79%', '71%', 'yes'],
         ['Normal years, pre-2020 editions only', '52', '+2.1%', '77%', '73%', 'yes'], ['Prisons-only outturn, IRCs excluded', '58', '+3.9%', '84%', '74%', 'yes'],
         ['Dropping the five largest absolute errors', '70', '+3.2%', '83%', '70%', 'yes'], ['Horizons one to three only', '44', '+3.2%', '86%', '68%', 'yes']],
        [3300, 900, 1100, 1200, 1300, 1226], { size: 18 }),
      caption('Table 5. The headline survives every cut. The magnitude does not: about 40% of the measured overshoot is attributable to the two shock periods, and the structural overshoot in ordinary years is about +2%.'),
      P('Targets within an edition are not independent, so the unit of inference should be the edition. Fifteen of seventeen editions have a positive mean error (one-sided sign test p = 0.001). Thirteen of seventeen have a higher mean absolute error than the no-change forecast (p = 0.02). The mean of edition-level mean errors is +4.2% with a standard deviation of 3.6, t = 4.8 on seventeen observations. Even seventeen overstates independence, because editions share target years and a low outturn year counts against several at once; the honest description is a small, correlated sample that points the same way on every test available.'),
      P('Two objections cannot be settled from these data. First, the no-change forecast wins because the population was flat; in the trending decades before 2011 it would have lost, and the MoJ\u2019s method was built in that era. The scorecard is a statement about the last fifteen years, not about forecasting in general. Second, if capacity binds on the population through channels other than release timing, the pre-2020 overshoot could itself be constrained demand rather than error. The proportion of sentence served held at 60 to 64% throughout 2015 to 2023, which argues against a binding constraint on release, but it does not rule out effects through remand, home detention curfew or sentencing behaviour.'),

      H1('Where the error sits'),
      P('Every edition since 2017 publishes an unrounded base-year actual broken down by custody type: remand, determinate, indeterminate, recall, non-criminal. Where an earlier edition projected that same reference month, the error can be decomposed component by component. Thirteen such pairs exist.'),
      table(['Component', 'Mean error', 'Share of total error', 'Largest contributor in'],
        [['Determinate', '+3,272', '95%', '54% of pairs'], ['Other (non-criminal, fine defaulters)', '+426', '12%', '15%'], ['Indeterminate', '+174', '5%', '0%'],
         ['Recall', '\u2212144', '\u22124%', '0%'], ['Remand', '\u2212292', '\u22128%', '31%']],
        [2400, 2000, 2400, 2226], { boldCol: 0 }),
      caption('Table 4. Component decomposition of projection error, 13 matched pairs. Positive means projected above actual. Non-criminal and fine defaulter prisoners are combined; the non-criminal category fell from 1,422 to 367 over the period and its error is largely definitional churn.'),
      P('Determinate accounts for 95% of the error and recall is never the largest contributor. Remand has a near-zero mean but a mean absolute error of 1,893: a large miss in both directions that averages out. The two biggest components err in opposite directions, so the gross component error, 6,896 on average, is 1.9 times the net error of 3,627. The worst case is the 2022 edition\u2019s November 2023 target: net error 1,165, gross 8,723, a ratio of 7.5. It got the total nearly right by pairing a determinate overshoot of 4,608 with a remand undershoot of 3,086.'),
      P('The composition shifts across eras. Editions from 2015 to 2019 were mildly high on everything: determinate +900, remand +851. Editions from 2020 onward are +8,610 on determinate and \u22122,862 on remand. Nineteen successive-edition revisions of a common target date point the same way: determinate accounts for 105% of revision movement and is revised down, by 2,621 on average, edition after edition.'),
      P('The interpretation is that the determinate overshoot is policy: release points were cut after each edition was published, by ECSL in 2023, SDS40 in 2024 and the progression model in 2026. The remand undershoot is demand: the court backlog. These are separate failures that happen to offset, and reporting a single net bias hides both.'),

      H1('The conditional-projection defence'),
      P('The MoJ\u2019s strongest reply is that the projections are conditional. They model the population under existing release rules; the rules then change in response; the projection is falsified by design. On this reading the overshoot is a measure of the policy response, not of forecasting skill, and a naive forecast wins precisely because it silently assumes the government will act.'),
      P('That is a fair description of what has happened and this note does not dispute it. But it does not rescue the projections for the purpose they are put to. The 10-Year Prison Capacity Strategy commits up to \u00a37 billion to 14,000 places by 2031 against a demand assumption of about 3,000 additional prisoners a year in the absence of further action. The realised growth rate over the fifteen years of weekly data is 246 a year. No five-year window since 2011 has sustained even 2,000 a year. A counterfactual that has been too high in every year since 2020, and that the government itself falsifies each time it is published, cannot carry that weight.'),
      P('There is a second reason the defence is incomplete. The no-change forecast wins in the 2008 to 2014 editions too: closer on 29 of 40 targets, with a mean absolute error of 1,623 against the MoJ\u2019s 2,895, on identical targets. Those editions predate ECSL, SDS40 and the progression model by a decade. The overshoot predates the policy responses that are said to explain it.'),

      H1('Why it matters now'),
      P('Fifteen years of weekly data show a prison estate that has run between 96% and 99% full in every calendar year, with headroom above 5,000 in ten weeks in total. The supply side has delivered a net 641 places since January 2011 on this series, or 1,005 between 2010 and 2024 on the Public Accounts Committee\u2019s figure, against thousands announced. The demand side is planned against a growth rate that has never been sustained. Both halves of the capacity plan rest on numbers that the record does not support, and the demand half has not previously been scored.'),
      P('The 2025\u20132030 edition projects 91,400 for September 2026. The August 2026 bulletin gives 86,843. The nineteenth edition is expected in December 2026 and will be scored on publication.'),

      H1('Data notes and caveats'),
      bullet('Two source defects were found. The 2022\u20132027 edition\u2019s central block stops at November 2024 while its low and high blocks run to 2026; the missing years are recoverable from the monthly appendix. And \u201cScenario 2\u201d is the central path in the 2012 and 2013 editions but the high path in the 2014 edition, so generic scenario labels must be resolved against the explicit central column rather than read by position.'),
      bullet('The 2011\u20132017 edition\u2019s base-year row is a scenario value, not an actual; it is excluded from the calibration test. The 2016\u20132021 edition publishes only four forward years.'),
      bullet('Component decomposition rests on thirteen matched pairs, weighted toward the June reference grid of the 2015 to 2019 editions, and the two most extreme rows come from the same edition. The era contrast rests on fewer independent observations than the row count suggests.'),
      bullet('Reference dates vary between the first and last day of the month across editions; decomposition matches on year and month and the largest day gap used is 29 days.'),
      bullet('The no-change benchmark uses the edition\u2019s own base actual where published, otherwise the bulletin at 30 June of the edition year. This slightly favours the MoJ where their base is a September or November figure and the population was seasonally higher.'),
      bullet('Everything in this note refreshes from the gov.uk content API. Every input is a versioned attachment or an API-enumerable route; there is no page scraping. The refresh reads every source Notes sheet before rebuilding any series and stops if a definition has changed.'),

      H1('Data and code'),
      P('The weekly series (population, capacity, headroom, operating margin, 2011 to date), the establishment panel (2018 to date), the eighteen projection editions in one table, the scorecard by edition, the decomposition and a 106-entry log of definitional changes and corrections are published with this note. The repository includes the refresh script and a standing forecast register, lodged on 3 September 2026, that will be scored against each weekly bulletin without amendment.'),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync('/home/claude/prisoncap/outputs/projection_scorecard_note.docx', buf); console.log('written'); });
