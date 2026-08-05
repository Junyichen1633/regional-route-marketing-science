import fs from "node:fs/promises";
import path from "node:path";

import {
  Presentation,
  PresentationFile,
} from "/Users/chenjunyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const PROJECT_ROOT = "/Users/chenjunyi/Desktop/Regional-Air-Route-Marketing-Science";
const WORK_DIR = path.join(PROJECT_ROOT, "work", "deck_build");
const RENDER_DIR = path.join(WORK_DIR, "rendered");
const FINAL_PPTX = path.join(
  PROJECT_ROOT,
  "presentations",
  "regional_route_marketing_science_case_study.pptx",
);

const COLORS = {
  ink: "#000000",
  muted: "#5F666C",
  panel: "#F2F2F2",
  panel2: "#EDEDED",
  rule: "#B8BCC4",
  accent: "#3D8DFF",
  accentLight: "#6DCBF4",
  teal: "#227C70",
  amber: "#C8842B",
  purple: "#7E63A6",
  white: "#FFFFFF",
};

const slideSize = { width: 1280, height: 720 };
const page = { left: 48, top: 42, width: 1184, height: 622 };

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (inQuotes) {
      if (ch === '"' && next === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        field += ch;
      }
      continue;
    }
    if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (ch !== "\r") {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }

  const [headers, ...records] = rows.filter((r) => r.some((v) => v !== ""));
  return records.map((record) =>
    Object.fromEntries(headers.map((header, index) => [header, record[index] ?? ""])),
  );
}

async function readCsv(relativePath) {
  const text = await fs.readFile(path.join(PROJECT_ROOT, relativePath), "utf8");
  return parseCsv(text);
}

function num(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function fmtCad(value) {
  return `CAD ${Math.round(value).toLocaleString("en-US")}`;
}

function fmtK(value) {
  return `${Math.round(value / 1000)}K`;
}

function pct(value) {
  return `${Math.round(value * 100)}%`;
}

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: options.fontSize ?? 22,
    bold: options.bold ?? false,
    color: options.color ?? COLORS.ink,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
  };
  return shape;
}

function addTitle(slide, title, subtitle, slideNo) {
  addText(slide, title, { left: page.left, top: page.top, width: page.width, height: 96 }, {
    fontSize: 38,
    bold: false,
    name: `slide-${slideNo}-title`,
  });
  if (subtitle) {
    addText(slide, subtitle, { left: page.left, top: 136, width: 1000, height: 42 }, {
      fontSize: 20,
      color: COLORS.muted,
      name: `slide-${slideNo}-subtitle`,
    });
  }
  addText(slide, String(slideNo), { left: 1180, top: 662, width: 50, height: 20 }, {
    fontSize: 13,
    alignment: "right",
    color: COLORS.ink,
    name: `slide-${slideNo}-footer`,
  });
}

function addRule(slide, left, top, width, color = COLORS.rule, weight = 1) {
  return slide.shapes.add({
    geometry: "line",
    position: { left, top, width, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function addPanel(slide, left, top, width, height, fill = COLORS.panel, line = "none") {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill,
    line: line === "none" ? { style: "solid", fill: "none", width: 0 } : line,
  });
}

function addMetric(slide, left, top, width, value, label, accent = COLORS.ink) {
  addPanel(slide, left, top, width, 112, COLORS.panel);
  addText(slide, value, { left: left + 22, top: top + 22, width: width - 44, height: 42 }, {
    fontSize: 34,
    bold: true,
    color: accent,
  });
  addText(slide, label, { left: left + 22, top: top + 70, width: width - 44, height: 32 }, {
    fontSize: 16,
    color: COLORS.muted,
  });
}

function addSimpleTable(slide, values, options) {
  const {
    left,
    top,
    columnWidths,
    rowHeight = 42,
    headerHeight = 42,
    fontSize = 14,
    headerFontSize = 13,
    headerFill = COLORS.ink,
    border = COLORS.rule,
  } = options;
  const width = columnWidths.reduce((sum, value) => sum + value, 0);
  const height = headerHeight + (values.length - 1) * rowHeight;

  addPanel(slide, left, top, width, height, COLORS.white, {
    style: "solid",
    fill: border,
    width: 1,
  });
  addPanel(slide, left, top, width, headerHeight, headerFill);

  let x = left;
  for (let c = 0; c <= columnWidths.length; c += 1) {
    slide.shapes.add({
      geometry: "line",
      position: { left: x, top, width: 0, height },
      fill: "none",
      line: { style: "solid", fill: border, width: 1 },
    });
    if (c < columnWidths.length) x += columnWidths[c];
  }
  for (let r = 0; r <= values.length; r += 1) {
    const y = top + headerHeight + Math.max(r - 1, 0) * rowHeight;
    if (r === 0) continue;
    addRule(slide, left, y, width, border, 1);
  }

  values.forEach((row, r) => {
    let cellLeft = left;
    row.forEach((cell, c) => {
      const cellTop = r === 0 ? top : top + headerHeight + (r - 1) * rowHeight;
      const cellHeight = r === 0 ? headerHeight : rowHeight;
      addText(
        slide,
        String(cell),
        {
          left: cellLeft + 8,
          top: cellTop + (r === 0 ? 9 : 8),
          width: columnWidths[c] - 16,
          height: cellHeight - 12,
        },
        {
          fontSize: r === 0 ? headerFontSize : fontSize,
          bold: r === 0,
          color: r === 0 ? COLORS.white : COLORS.ink,
        },
      );
      cellLeft += columnWidths[c];
    });
  });
}

function addBulletList(slide, items, left, top, width, lineHeight = 34, fontSize = 22) {
  items.forEach((item, index) => {
    addPanel(slide, left, top + index * lineHeight + 10, 7, 7, COLORS.accent);
    addText(slide, item, { left: left + 24, top: top + index * lineHeight, width, height: lineHeight }, {
      fontSize,
      color: COLORS.ink,
    });
  });
}

function addNotes(slide, lines) {
  slide.speakerNotes.textFrame.setText(lines);
  slide.speakerNotes.setVisible(true);
}

function styleTable(table, headerFill = COLORS.ink, bodyFont = 12, headerFont = 12) {
  table.styleOptions = { headerRow: true, bandedRows: true };
  table.borders.assign({ style: "solid", fill: COLORS.rule, width: 0.8 });
  const rowCount = table.rows?.length ?? 0;
  const colCount = table.columns?.length ?? 0;
  for (let r = 0; r < rowCount; r += 1) {
    for (let c = 0; c < colCount; c += 1) {
      table.getCell(r, c).text.style = {
        fontSize: bodyFont,
        color: COLORS.ink,
      };
    }
  }
  for (let c = 0; c < table.columns.length; c += 1) {
    const cell = table.getCell(0, c);
    cell.fill = headerFill;
    cell.text.style = {
      fontSize: headerFont,
      bold: true,
      color: COLORS.white,
    };
  }
}

function compactAction(text) {
  if (text.includes("Relaunch")) return "Capacity-gated relaunch";
  if (text.includes("Scale")) return "Scale / defend";
  if (text.includes("Run test")) return "Test and learn";
  if (text.includes("Maintain")) return "Maintain";
  if (text.includes("Watchlist")) return "Evidence first";
  return text;
}

function compactBucket(bucket) {
  return {
    scale_defend: "scale",
    test_and_learn: "test",
    relaunch_feasibility: "relaunch",
    maintain: "maintain",
    evidence_first: "evidence",
  }[bucket] ?? bucket.replaceAll("_", " ");
}

function compactDesign(design) {
  return {
    matched_route_geo_lift: "matched geo lift",
    two_stage_capacity_gated_test: "capacity gate",
    incrementality_guardrail_test: "guardrail test",
  }[design] ?? design.replaceAll("_", " ");
}

function compactMetric(metric) {
  if (metric.includes("qualified")) return "qualified signal";
  if (metric.includes("search")) return "booking/search proxy";
  return "booking proxy";
}

function compactReadiness(readiness) {
  if (readiness.startsWith("Feasibility")) return "Feasibility";
  if (readiness.startsWith("Low")) return "Low";
  if (readiness.startsWith("Medium")) return "Medium";
  if (readiness.startsWith("Directional")) return "Directional";
  return readiness.split(";")[0];
}

function addRouteNetwork(slide, allocations, coords) {
  const frame = { left: 702, top: 190, width: 480, height: 360 };
  addPanel(slide, frame.left, frame.top, frame.width, frame.height, "#FAFAFA", {
    style: "solid",
    fill: COLORS.rule,
    width: 1,
  });
  addText(slide, "Funded route network", { left: frame.left + 20, top: frame.top + 18, width: 260, height: 30 }, {
    fontSize: 18,
    bold: true,
  });

  const bounds = { minLon: -124, maxLon: -63, minLat: 42, maxLat: 54 };
  const project = (code) => {
    const c = coords[code];
    const padX = 40;
    const padY = 58;
    const x =
      frame.left + padX + ((c.lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * (frame.width - padX * 2);
    const y =
      frame.top + frame.height - padY - ((c.lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * (frame.height - padY * 2);
    return { x, y };
  };

  for (const row of allocations) {
    const [origin, dest] = row.route_id.split("_");
    const a = project(origin);
    const b = project(dest);
    const bucket = row.decision_bucket;
    const color =
      bucket === "relaunch_feasibility"
        ? COLORS.amber
        : bucket === "maintain"
          ? COLORS.accent
          : COLORS.teal;
    const left = Math.min(a.x, b.x);
    const top = Math.min(a.y, b.y);
    slide.shapes.add({
      geometry: "line",
      position: {
        left,
        top,
        width: Math.max(Math.abs(b.x - a.x), 1),
        height: Math.max(Math.abs(b.y - a.y), 1),
        horizontalFlip: a.x > b.x,
        verticalFlip: a.y > b.y,
      },
      fill: "none",
      line: { style: "solid", fill: color, width: bucket === "relaunch_feasibility" ? 3 : 2 },
    });
  }

  const airports = new Set();
  for (const row of allocations) {
    const [origin, dest] = row.route_id.split("_");
    airports.add(origin);
    airports.add(dest);
  }

  for (const code of airports) {
    const p = project(code);
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: p.x - 6, top: p.y - 6, width: 12, height: 12 },
      fill: COLORS.ink,
      line: { style: "solid", fill: COLORS.white, width: 1.5 },
    });
    addText(slide, code, { left: p.x + 8, top: p.y - 11, width: 48, height: 22 }, {
      fontSize: 12,
      bold: true,
    });
  }
}

async function main() {
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  await fs.mkdir(RENDER_DIR, { recursive: true });

  const [caseRows, allocationRows, routeRows, sensitivityRows, experimentRows, controlRows] =
    await Promise.all([
      readCsv("data/processed/budget_optimization_case_summary_v0.csv"),
      readCsv("data/processed/budget_optimization_allocations_v0.csv"),
      readCsv("data/processed/route_opportunity_score_v0.csv"),
      readCsv("data/processed/marketing_sensitivity_summary_v0.csv"),
      readCsv("data/processed/experiment_design_plan_v0.csv"),
      readCsv("data/processed/experiment_control_matches_v0.csv"),
    ]);

  const recommendedCase = caseRows.find((row) => row.case_id === "portfolio_value_500k");
  const recommendedAllocations = allocationRows
    .filter((row) => row.case_id === "portfolio_value_500k")
    .sort((a, b) => num(b.campaign_budget_cad) - num(a.campaign_budget_cad));
  const topRoutes = routeRows
    .filter((row) => row.model_role !== "benchmark" && row.model_role !== "control")
    .sort((a, b) => num(b.marketing_support_priority_score_v0) - num(a.marketing_support_priority_score_v0))
    .slice(0, 5);

  const sensitivityBySpec = Object.values(
    sensitivityRows.reduce((acc, row) => {
      const spec = row.model_spec;
      if (!acc[spec]) {
        acc[spec] = {
          model_spec: spec,
          top_channel_recovery_rate: 0,
          top2_set_recovery_rate: 0,
          budget_efficiency_ratio: 0,
          channel_rank_corr_mean: 0,
          count: 0,
        };
      }
      acc[spec].top_channel_recovery_rate += num(row.top_channel_recovery_rate);
      acc[spec].top2_set_recovery_rate += num(row.mean_top2_budget_direction_overlap);
      acc[spec].budget_efficiency_ratio += num(row.mean_budget_efficiency_ratio);
      acc[spec].channel_rank_corr_mean += num(row.mean_spearman_rank_corr);
      acc[spec].count += 1;
      return acc;
    }, {}),
  ).map((row) => ({
    ...row,
    top_channel_recovery_rate: row.top_channel_recovery_rate / row.count,
    top2_set_recovery_rate: row.top2_set_recovery_rate / row.count,
    budget_efficiency_ratio: row.budget_efficiency_ratio / row.count,
    channel_rank_corr_mean: row.channel_rank_corr_mean / row.count,
  }));

  const sensitivityOrder = ["controlled_saturation", "controlled_adstock", "naive_raw_spend"];
  const sensitivity = sensitivityOrder.map((spec) =>
    sensitivityBySpec.find((row) => row.model_spec === spec),
  );
  const controlsByRoute = controlRows.reduce((acc, row) => {
    acc[row.treatment_route_id] ??= [];
    acc[row.treatment_route_id].push(row.control_route_id);
    return acc;
  }, {});

  const coords = {
    YKF: { lat: 43.46, lon: -80.38 },
    YHM: { lat: 43.17, lon: -79.93 },
    YXU: { lat: 43.03, lon: -81.15 },
    YXX: { lat: 49.03, lon: -122.36 },
    YLW: { lat: 49.96, lon: -119.38 },
    YVR: { lat: 49.19, lon: -123.18 },
    YYC: { lat: 51.12, lon: -114.01 },
    YEG: { lat: 53.31, lon: -113.58 },
    YHZ: { lat: 44.88, lon: -63.51 },
    YYZ: { lat: 43.68, lon: -79.63 },
  };

  const presentation = Presentation.create({ slideSize });

  // Slide 1
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addText(slide, "Regional Route", { left: 42, top: 40, width: 480, height: 58 }, {
      fontSize: 32,
      color: COLORS.muted,
    });
    addText(slide, "Marketing Science", { left: 42, top: 172, width: 1010, height: 182 }, {
      fontSize: 80,
      color: COLORS.ink,
    });
    addText(slide, "Marketing measurement and route sustainability for Canadian regional air routes", {
      left: 48,
      top: 506,
      width: 780,
      height: 82,
    }, {
      fontSize: 30,
      color: COLORS.ink,
    });
    addRule(slide, 48, 468, 360, COLORS.accent, 4);
    addText(slide, "Portfolio case study | 2026", { left: 48, top: 626, width: 460, height: 34 }, {
      fontSize: 18,
      color: COLORS.muted,
    });
    addNotes(slide, [
      "Open with the business decision: this is a route-support and validation system, not a pure channel attribution exercise.",
      "",
      "[Sources]",
      "Project source: reports/final_portfolio_case_study.md",
    ]);
  }

  // Slide 2
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "The decision is route portfolio support, not channel attribution",
      "The model has to rank routes, allocate a fixed budget, and define how to validate before scaling.",
      2,
    );
    addPanel(slide, 48, 204, 540, 336, COLORS.panel);
    addText(slide, "Decision question", { left: 78, top: 232, width: 420, height: 38 }, {
      fontSize: 24,
      bold: true,
    });
    addText(
      slide,
      "Which regional air routes should receive incremental marketing investment, and how should a fixed budget be allocated to maximize sustainable demand?",
      { left: 78, top: 294, width: 470, height: 160 },
      { fontSize: 27 },
    );

    addPanel(slide, 662, 204, 520, 336, "#FAFAFA", {
      style: "solid",
      fill: COLORS.rule,
      width: 1,
    });
    addText(slide, "Operating constraints", { left: 692, top: 232, width: 440, height: 38 }, {
      fontSize: 24,
      bold: true,
    });
    addBulletList(
      slide,
      [
        "Route-level passengers and bookings are not publicly observed",
        "Marketing spend is simulated, so response is scenario-based",
        "Inactive routes need capacity checks before media scaling",
        "Recommendations must feed test design, not just rankings",
      ],
      696,
      292,
      420,
      48,
      19,
    );
    addNotes(slide, [
      "This slide frames the problem as an ambiguous business decision under incomplete data, with a need to connect analysis to action.",
      "",
      "[Sources]",
      "Project source: reports/final_portfolio_case_study.md",
      "Project source: docs/03_data_strategy.md",
    ]);
  }

  // Slide 3
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "The workflow turns public route evidence into a testable allocation",
      "MMM-style response modeling is one component inside a broader route sustainability system.",
      3,
    );
    const stages = [
      {
        label: "1",
        title: "Root demand and supply",
        body: "Airport context, route-active evidence, movement proxies, hub competition",
      },
      {
        label: "2",
        title: "Marketing response module",
        body: "Scenario curves, adstock/saturation structure, recovery sensitivity",
      },
      {
        label: "3",
        title: "Optimization and validation",
        body: "Constrained budget allocation, matched-route tests, scale / maintain / stop rules",
      },
    ];
    stages.forEach((stage, idx) => {
      const left = 70 + idx * 394;
      addPanel(slide, left, 214, 332, 284, idx === 1 ? "#EBF6FC" : COLORS.panel);
      addText(slide, stage.label, { left: left + 24, top: 234, width: 42, height: 40 }, {
        fontSize: 28,
        bold: true,
        color: idx === 1 ? COLORS.accent : COLORS.ink,
      });
      addText(slide, stage.title, { left: left + 24, top: 300, width: 276, height: 64 }, {
        fontSize: 28,
        bold: true,
      });
      addText(slide, stage.body, { left: left + 24, top: 390, width: 278, height: 82 }, {
        fontSize: 19,
        color: COLORS.muted,
      });
      if (idx < 2) {
        addRule(slide, left + 338, 356, 54, COLORS.ink, 2);
      }
    });
    addText(
      slide,
      "Result: a planning system that can recommend where to spend and what evidence is required next.",
      { left: 70, top: 574, width: 930, height: 40 },
      { fontSize: 24, bold: true },
    );
    addNotes(slide, [
      "This is the core architecture. It keeps MMM from becoming the whole project and makes it one replaceable response module.",
      "",
      "[Sources]",
      "Project source: reports/final_portfolio_case_study.md",
      "Project source: docs/02_project_plan.md",
    ]);
  }

  // Slide 4
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "Opportunity scoring separates active scale bets from relaunch feasibility",
      "The highest-priority route is not automatically a media-scale route when service is inactive.",
      4,
    );
    const values = [
      ["Route", "Status", "Prio", "Sustain", "Decision"],
      ...topRoutes.map((row) => [
        row.route_id.replace("_", "-"),
        row.end_of_period_route_status,
        num(row.marketing_support_priority_score_v0).toFixed(1),
        num(row.route_sustainability_score_v0).toFixed(1),
        compactAction(row.recommendation),
      ]),
    ];
    addSimpleTable(slide, values, {
      left: 54,
      top: 206,
      columnWidths: [112, 104, 68, 80, 226],
      headerHeight: 40,
      rowHeight: 44,
      fontSize: 15,
      headerFontSize: 13,
    });
    addRouteNetwork(slide, recommendedAllocations, coords);
    addText(
      slide,
      "YKF_YVR ranks high but remains a capacity-gated relaunch candidate because the end-of-period route status is inactive.",
      { left: 54, top: 556, width: 760, height: 58 },
      { fontSize: 21, bold: true },
    );
    addNotes(slide, [
      "Call out YKF_YVR: the model respects route status and business feasibility, not just a rank order.",
      "",
      "[Sources]",
      "Project data: data/processed/route_opportunity_score_v0.csv",
      "Project source: reports/phase3_route_opportunity_memo.md",
    ]);
  }

  // Slide 5
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "Sensitivity analysis keeps simulated marketing honest",
      "Budget direction is more stable than exact channel ranking under simulated spend mechanisms.",
      5,
    );
    slide.charts.add("bar", {
      position: { left: 52, top: 176, width: 720, height: 420 },
      categories: ["Controlled saturation", "Controlled adstock", "Naive raw spend"],
      series: [
        {
          name: "Top-channel recovery",
          values: sensitivity.map((row) => Math.round(num(row.top_channel_recovery_rate) * 100)),
          fill: COLORS.accent,
        },
        {
          name: "Budget-efficiency ratio",
          values: sensitivity.map((row) => Math.round(num(row.budget_efficiency_ratio) * 100)),
          fill: COLORS.accentLight,
        },
      ],
      hasLegend: true,
      legend: { position: "bottom", overlay: false, textStyle: { fontSize: 12, fill: COLORS.muted } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 12, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
      plotAreaLine: { style: "solid", fill: COLORS.white, width: 0 },
      yAxis: {
        min: 0,
        max: 100,
        majorUnit: 20,
        numberFormatCode: '0"%"',
        majorGridlines: { style: "solid", fill: COLORS.panel2, width: 1 },
        line: { style: "solid", fill: COLORS.white, width: 0 },
        textStyle: { fontSize: 11, fill: COLORS.muted },
      },
      xAxis: {
        line: { style: "solid", fill: COLORS.rule, width: 1 },
        textStyle: { fontSize: 11, fill: COLORS.muted },
      },
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 80 },
    });
    addPanel(slide, 832, 190, 340, 116, COLORS.panel);
    addText(slide, "58%", { left: 858, top: 214, width: 132, height: 44 }, {
      fontSize: 36,
      bold: true,
      color: COLORS.accent,
    });
    addText(slide, "Top-channel recovery for controlled saturation", {
      left: 998,
      top: 218,
      width: 144,
      height: 58,
    }, { fontSize: 17, color: COLORS.muted });
    addPanel(slide, 832, 334, 340, 116, COLORS.panel);
    addText(slide, "8%", { left: 858, top: 358, width: 132, height: 44 }, {
      fontSize: 36,
      bold: true,
      color: COLORS.ink,
    });
    addText(slide, "Top-channel recovery for naive raw-spend ranking", {
      left: 998,
      top: 362,
      width: 144,
      height: 58,
    }, { fontSize: 17, color: COLORS.muted });
    addText(
      slide,
      "The right claim is directional planning support, not observed causal channel ROI.",
      { left: 832, top: 514, width: 340, height: 72 },
      { fontSize: 22, bold: true },
    );
    addNotes(slide, [
      "This slide answers the user's sensitivity concern directly. The model helps budget direction, but exact channel ranking is fragile.",
      "",
      "[Sources]",
      "Project data: data/processed/marketing_sensitivity_summary_v0.csv",
      "Project source: reports/phase4b_marketing_sensitivity_memo.md",
    ]);
  }

  // Slide 6
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "A CAD 500K portfolio funds seven routes with one capacity-gated relaunch",
      "The recommended case balances route-health lift, passenger proxy, and strategic priority.",
      6,
    );
    addMetric(slide, 54, 188, 250, "CAD 500K", "Total budget", COLORS.ink);
    addMetric(slide, 332, 188, 210, String(Math.round(num(recommendedCase.funded_routes))), "Funded routes", COLORS.ink);
    addMetric(slide, 570, 188, 280, Math.round(num(recommendedCase.incremental_passenger_proxy)).toLocaleString("en-US"), "Incremental passenger proxy", COLORS.accent);
    addMetric(slide, 878, 188, 250, `${num(recommendedCase.incremental_route_health_points).toFixed(1)} pts`, "Route-health lift", COLORS.accent);

    slide.charts.add("bar", {
      position: { left: 58, top: 352, width: 710, height: 266 },
      categories: recommendedAllocations.map((row) => row.route_id.replace("_", "-")),
      series: [
        {
          name: "Campaign budget (CAD K)",
          values: recommendedAllocations.map((row) => num(row.campaign_budget_cad) / 1000),
          fill: COLORS.accent,
          points: recommendedAllocations.map((row, idx) => ({
            idx,
            fill: row.decision_bucket === "relaunch_feasibility" ? COLORS.amber : COLORS.accent,
          })),
        },
      ],
      hasLegend: false,
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 12, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
      xAxis: {
        line: { style: "solid", fill: COLORS.rule, width: 1 },
        textStyle: { fontSize: 11, fill: COLORS.muted },
      },
      yAxis: {
        visible: false,
        max: 120,
        majorGridlines: null,
        line: { style: "solid", fill: COLORS.white, width: 0 },
      },
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 58 },
    });

    const allocValues = [
      ["Route", "Budget", "Bucket"],
      ...recommendedAllocations.map((row) => [
        row.route_id.replace("_", "-"),
        fmtK(num(row.campaign_budget_cad)),
        compactBucket(row.decision_bucket),
      ]),
    ];
    addSimpleTable(slide, allocValues, {
      left: 828,
      top: 340,
      columnWidths: [104, 82, 168],
      headerHeight: 38,
      rowHeight: 32,
      fontSize: 14,
      headerFontSize: 13,
    });
    addNotes(slide, [
      "This is the key recommendation slide for a project walkthrough.",
      "",
      "[Sources]",
      "Project data: data/processed/budget_optimization_case_summary_v0.csv",
      "Project data: data/processed/budget_optimization_allocations_v0.csv",
      "Project source: reports/phase5_budget_optimization_memo.md",
    ]);
  }

  // Slide 7
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "Every recommendation is tied to a validation design",
      "The output is a test plan with matched controls, not a direct instruction to scale spend immediately.",
      7,
    );
    const experiments = experimentRows
      .filter((row) => row.case_id === "portfolio_value_500k")
      .sort((a, b) => num(b.campaign_budget_cad) - num(a.campaign_budget_cad));
    const testAndLearnRoutes = experiments
      .filter((row) => row.decision_bucket === "test_and_learn")
      .map((row) => row.route_id.replace("_", "-"))
      .join(", ");
    const values = [
      ["Group", "Routes", "Design", "Decision rule"],
      ["Scale / defend", "YKF-YEG", "matched geo lift", "Scale only if lift clears target and guardrails hold"],
      ["Test and learn", testAndLearnRoutes, "matched geo lift", "Pool similar routes or extend window where power is directional"],
      ["Relaunch", "YKF-YVR", "capacity gate", "Advance only with qualified demand and capacity interest"],
      ["Maintain", "YXX-YEG, YLW-YVR", "guardrail test", "Keep spend capped unless leakage or retention signal improves"],
    ];
    addSimpleTable(slide, values, {
      left: 54,
      top: 210,
      columnWidths: [168, 248, 220, 474],
      headerHeight: 42,
      rowHeight: 68,
      fontSize: 17,
      headerFontSize: 13,
    });
    addPanel(slide, 54, 570, 1110, 54, "#FAFAFA", {
      style: "solid",
      fill: COLORS.rule,
      width: 1,
    });
    addText(
      slide,
      "Active routes use matched-route or geo-lift designs; relaunch routes require capacity-gated feasibility before passenger lift claims.",
      { left: 78, top: 584, width: 1036, height: 36 },
      { fontSize: 18, bold: true },
    );
    addNotes(slide, [
      "Use this slide to show the system closes the loop from recommendation to measurement design.",
      "",
      "[Sources]",
      "Project data: data/processed/experiment_design_plan_v0.csv",
      "Project data: data/processed/experiment_control_matches_v0.csv",
      "Project source: reports/phase6_experiment_design_memo.md",
    ]);
  }

  // Slide 8
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(
      slide,
      "Meridian is the future MMM component, not a claim in this prototype",
      "The production path is clear, but the current public-data prototype intentionally avoids false causal precision.",
      8,
    );
    addPanel(slide, 62, 206, 500, 284, COLORS.panel);
    addText(slide, "Current prototype", { left: 92, top: 238, width: 400, height: 36 }, {
      fontSize: 26,
      bold: true,
    });
    addBulletList(
      slide,
      [
        "Route-month panel from public evidence",
        "Scenario response curves, not observed channel ROI",
        "Sensitivity analysis to expose recovery limits",
        "Budget optimizer and experiment design",
      ],
      96,
      306,
      390,
      42,
      18,
    );
    addPanel(slide, 650, 206, 500, 284, "#EBF6FC");
    addText(slide, "Future production version", { left: 680, top: 238, width: 400, height: 36 }, {
      fontSize: 26,
      bold: true,
      color: COLORS.accent,
    });
    addBulletList(
      slide,
      [
        "BigQuery stores route, spend, and outcome data",
        "Vertex AI Pipelines rebuild and compare models",
        "Meridian estimates MMM response and ROI/mROI",
        "Looker or dashboard exports planning outputs",
      ],
      684,
      306,
      390,
      42,
      18,
    );
    addText(
      slide,
      "Project caveat: I did not run Meridian because the data does not support a production MMM yet. I designed exactly where it would plug in once real spend and outcomes exist.",
      { left: 72, top: 562, width: 1050, height: 70 },
      { fontSize: 24, bold: true },
    );
    addNotes(slide, [
      "This slide answers the Meridian question directly.",
      "",
      "[Sources]",
      "Google Developers Meridian landing page: https://developers.google.com/meridian",
      "Google Developers Meridian MMM docs: https://developers.google.com/meridian/mmm",
      "GitHub google/meridian README: https://github.com/google/meridian",
      "Project source: docs/18_meridian_vertex_positioning.md",
    ]);
  }

  const sourceNotes = [
    "Regional Route Marketing Science case-study deck",
    "",
    "External sources used:",
    "- Google Developers Meridian landing page: https://developers.google.com/meridian",
    "- Google Developers Meridian MMM docs: https://developers.google.com/meridian/mmm",
    "- GitHub google/meridian README: https://github.com/google/meridian",
    "",
    "Project sources used:",
    "- reports/final_portfolio_case_study.md",
    "- data/processed/route_opportunity_score_v0.csv",
    "- data/processed/marketing_sensitivity_summary_v0.csv",
    "- data/processed/budget_optimization_case_summary_v0.csv",
    "- data/processed/budget_optimization_allocations_v0.csv",
    "- data/processed/experiment_design_plan_v0.csv",
    "- data/processed/experiment_control_matches_v0.csv",
  ].join("\n");
  await fs.writeFile(path.join(WORK_DIR, "source-notes.txt"), sourceNotes, "utf8");

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await writeBlob(path.join(RENDER_DIR, `${stem}.png`), png);
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDER_DIR, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await writeBlob(path.join(RENDER_DIR, "deck-montage.webp"), montage);

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);

  const inspect = await presentation.inspect({
    kind: "slide,textbox,shape,chart,table,notes",
    maxChars: 12000,
  });
  await fs.writeFile(path.join(RENDER_DIR, "deck-inspect.ndjson"), inspect.ndjson, "utf8");

  console.log(
    JSON.stringify(
      {
        pptx: FINAL_PPTX,
        slides: presentation.slides.items.length,
        rendered: RENDER_DIR,
        recommendedCase: recommendedCase.case_id,
        fundedRoutes: recommendedAllocations.length,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
