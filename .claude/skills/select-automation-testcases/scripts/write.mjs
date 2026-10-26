// Ghi test case automation format v2 (mỗi thao tác / điểm kiểm = 1 dòng): giữ TC lẻ, chạy liên tiếp, chỉ cài lại app khi cần.
// Pre-condition dòng 1 = "Cài lại app" hoặc "Tiếp nối <TC trước>"; thứ tự TC trong sheet = thứ tự chạy.
// Mỗi sheet chức năng của file gốc → 1 file riêng: <out-dir>/<sheet>-automation.xlsx (TestCases + TestData), style theo mẫu v2.
// Case test tay chỉ in ra màn hình (vẫn nằm trong file gốc).
//   node scripts/write.mjs <plan.json> <cases.json> <out-dir>
// plan: {
//   testcases: [{ id, fresh: true|false, pre: [], dataSet?: "", rows: [{ step, screen, kind: Action|Nav|Check, keyword, target?, value?, compare?, platform?, label? }] }],
//            (xếp theo thứ tự chạy; fresh = cài lại app trước TC này)
//   testdata?: [{ "Data Set", "Run", ...cột, "Ghi chú"? }],
//   manual: [{ tc, reason }]
// }
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const [planFile, casesFile, outDir] = process.argv.slice(2);
const ExcelJS = createRequire(import.meta.url)('exceljs'); // exceljs cài trong thư mục skill (npm install)
const plan = JSON.parse(fs.readFileSync(planFile, 'utf8'));
const src = JSON.parse(fs.readFileSync(casesFile, 'utf8'));
const original = new Map(src.sheets.flatMap((s) => s.cases.map((c) => [c.id, { ...c, sheet: s.sheet }])));

// ---- Bộ từ khoá v2 (danh sách chọn trong file mẫu + Relaunch app, contains)
const KEYWORDS = {
  Action: ['Launch fresh', 'Relaunch app', 'Tap', 'Enter', 'Clear', 'Set ruler', 'Select date', 'Scroll to', 'Swipe', 'Back', 'Hide keyboard'],
  Nav: ['Verify screen'],
  Check: ['Verify displayed', 'Verify not displayed', 'Verify text', 'Verify value', 'Verify enabled', 'Verify disabled', 'Verify selected'],
};
const COMPARES = ['equals', 'number', 'unit', 'date:DD/MM/YYYY', 'all-on', 'contains'];
const PLATFORMS = ['All', 'iOS', 'Android'];

// ---- Style của file mẫu v2
const HEAD_FILL = 'FF1F4E78';
const KIND_FILL = { Case: 'FFD9E1F2', Nav: 'FFEDF3FA', Check: 'FFFFF2CC' };
const BORDER = Object.fromEntries(['left', 'right', 'top', 'bottom'].map((s) => [s, { style: 'thin', color: { argb: 'FFBFBFBF' } }]));
const list = (items) => ({ type: 'list', allowBlank: true, formulae: [`"${items.join(',')}"`] });
function styleSheet(ws) {
  const n = ws.columnCount;
  const head = ws.getRow(1);
  head.height = 30;
  for (let c = 1; c <= n; c++) {
    Object.assign(head.getCell(c), {
      fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: HEAD_FILL } },
      font: { bold: true, color: { argb: 'FFFFFFFF' } },
      alignment: { vertical: 'middle', wrapText: true },
      border: BORDER,
    });
  }
  ws.eachRow((row, i) => {
    if (i === 1) return;
    for (let c = 1; c <= n; c++) Object.assign(row.getCell(c), { border: BORDER, alignment: { vertical: 'top', wrapText: true } });
  });
  ws.views = [{ state: 'frozen', xSplit: 1, ySplit: 1, topLeftCell: 'B2' }];
  ws.autoFilter = { from: { row: 1, column: 1 }, to: { row: 1, column: n } };
}

// ---- Kiểm
const problems = [];
const auto = new Map(plan.testcases.map((t) => [t.id, t]));
const manual = new Set(plan.manual.map((m) => m.tc));
if (auto.size !== plan.testcases.length) problems.push('Có TC lặp');
for (const c of original.values()) {
  if (!c.selected) continue;
  if (!auto.has(c.id) && !manual.has(c.id)) problems.push(`Chưa xếp: ${c.id} (${c.sheet} · ${c.module})`);
  if (auto.has(c.id) && manual.has(c.id)) problems.push(`Vừa automation vừa Manual: ${c.id}`);
}
for (const id of [...auto.keys(), ...manual]) if (!original.get(id)?.selected) problems.push(`Không có / không thuộc diện chọn: ${id}`);
// TC đầu tiên của mỗi sheet phải cài lại app (chưa có TC trước để tiếp nối)
const firstOfSheet = new Set();
for (const t of plan.testcases) {
  const sh = original.get(t.id)?.sheet;
  if (!firstOfSheet.has(sh)) {
    firstOfSheet.add(sh);
    if (!t.fresh) problems.push(`${t.id}: TC đầu tiên của sheet ${sh} phải có fresh = true`);
  }
}
const dataSets = new Set((plan.testdata || []).map((r) => r['Data Set']));
for (const t of plan.testcases) {
  if (typeof t.fresh !== 'boolean') problems.push(`${t.id}: thiếu fresh (true / false)`);
  if (t.dataSet && !dataSets.has(t.dataSet)) problems.push(`${t.id}: Data Set "${t.dataSet}" không có trong TestData`);
  if (!t.rows?.some((r) => r.kind === 'Check')) problems.push(`${t.id}: không có dòng Check`);
  for (const r of t.rows || []) {
    if (!KEYWORDS[r.kind]?.includes(r.keyword)) problems.push(`${t.id} step ${r.step}: keyword "${r.keyword}" không hợp lệ cho Kind ${r.kind}`);
    if (r.kind === 'Check' && !r.label) problems.push(`${t.id} step ${r.step}: dòng Check thiếu Check label`);
    if (r.compare && !COMPARES.includes(r.compare)) problems.push(`${t.id} step ${r.step}: Compare "${r.compare}" không có trong danh sách`);
    if (r.platform && !PLATFORMS.includes(r.platform)) problems.push(`${t.id} step ${r.step}: Platform "${r.platform}" lạ`);
  }
}

// ---- Ghi: 1 file / sheet chức năng
const slug = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const sheetOf = (id) => original.get(id)?.sheet;
const sheets = [...new Set([...plan.testcases.map((t) => sheetOf(t.id)), ...plan.manual.map((m) => sheetOf(m.tc))])].filter(Boolean);
fs.mkdirSync(outDir, { recursive: true });
const written = [];
for (const sheet of sheets) {
  const wb = new ExcelJS.Workbook();
  const mine = plan.testcases.filter((t) => sheetOf(t.id) === sheet); // giữ thứ tự chạy của plan

  const ws = wb.addWorksheet('TestCases');
  ws.columns = [
    ['TC ID', 16], ['Title', 34], ['Priority', 8], ['Pre-condition', 40], ['Data Set', 13], ['Step', 6], ['Screen', 17], ['Kind', 8],
    ['Keyword', 17], ['Target', 26], ['Value', 30], ['Compare', 14], ['Platform', 9], ['Check label', 32], ['Test Result', 11], ['Last Run', 16],
  ].map(([header, width]) => ({ header, key: header, width }));
  mine.forEach((t, i) => {
    const c = original.get(t.id) || {};
    // Dòng đầu Pre-condition quyết định cách bắt đầu TC; thứ tự TC trong sheet = thứ tự chạy
    const where = t.fresh ? 'Cài lại app' : `Tiếp nối ${mine[i - 1]?.id}`;
    const pre = (t.pre || []).filter((l) => !(t.fresh && /^Cài lại app/i.test(l)));
    ws.addRow({
      'TC ID': t.id, Title: c.description || c.scenario, Priority: c.priority, Kind: 'Case', 'Data Set': t.dataSet || '',
      'Pre-condition': [where, ...pre].map((l, i) => `${i + 1}. ${l}`).join('\n'),
    });
    for (const r of t.rows) {
      ws.addRow({
        Step: r.step, Screen: r.screen, Kind: r.kind, Keyword: r.keyword, Target: r.target ?? '', Value: r.value ?? '',
        Compare: r.compare ?? '', Platform: r.platform || 'All', 'Check label': r.label ?? '',
      });
    }
  });
  styleSheet(ws);
  ws.eachRow((row, i) => {
    if (i === 1) return;
    const kind = row.getCell(8).value;
    if (KIND_FILL[kind]) for (let col = 1; col <= 16; col++) row.getCell(col).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: KIND_FILL[kind] } };
    if (kind === 'Case') row.font = { bold: true };
    row.getCell(8).dataValidation = list(['Case', 'Action', 'Nav', 'Check']);
    row.getCell(9).dataValidation = list([...KEYWORDS.Action, ...KEYWORDS.Nav, ...KEYWORDS.Check]);
    row.getCell(12).dataValidation = list(COMPARES);
    row.getCell(13).dataValidation = list(PLATFORMS);
  });

  const td = wb.addWorksheet('TestData');
  const sets = new Set(mine.map((t) => t.dataSet).filter(Boolean));
  const rows = (plan.testdata || []).filter((r) => sets.has(r['Data Set']));
  const keys = [...new Set(rows.flatMap((r) => Object.keys(r)))].filter((k) => !['Data Set', 'Run', 'Ghi chú'].includes(k));
  td.columns = ['Data Set', 'Run', ...keys, 'Ghi chú', 'Result', 'Bug', 'Last Run'].map((k) => ({ header: k, key: k, width: k === 'Ghi chú' ? 40 : 14 }));
  for (const r of rows) td.addRow(r);
  styleSheet(td);

  const file = path.join(outDir, `${slug(sheet)}-automation.xlsx`);
  await wb.xlsx.writeFile(file);
  const installs = mine.filter((t) => t.fresh).length;
  written.push(`${file}\n  ${sheet}: ${mine.length} TC automation · ${plan.manual.filter((x) => sheetOf(x.tc) === sheet).length} manual · cài app ${installs} lần (trước: ${mine.length})`);
}

const sel = [...original.values()].filter((c) => c.selected).length;
console.log(`Đã ghi:\n${written.join('\n')}`);
console.log(`Case gốc: ${original.size} · chọn ${sel} · automation ${auto.size} · manual ${manual.size} · không chọn ${original.size - sel}`);
// Case test tay vẫn nằm trong file gốc → chỉ liệt kê ở đây, không ghi vào file automation
console.log(`Test tay (giữ trong file gốc):\n${plan.manual.map((m) => `  ${m.tc}: ${m.reason}`).join('\n')}`);
if (problems.length) { console.log(`\nLỖI (${problems.length}):\n- ${problems.slice(0, 40).join('\n- ')}`); process.exit(1); }
console.log('Độ phủ + format v2: OK');
