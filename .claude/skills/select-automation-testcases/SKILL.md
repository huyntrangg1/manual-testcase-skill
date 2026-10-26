---
name: select-automation-testcases
description: Use when turning a full manual test case workbook (kit v2 xlsx with a "Test Case #" header, e.g. manual-tc/<ten-du-an>/<feature>.xlsx) into automation test cases, or when small cases each reinstall the app and should run back-to-back instead.
---
# Select automation test cases

## Overview

- Pick the cases to automate from a full manual workbook.
- **Keep every original TC as its own automation TC**, with the same ID and its own checks. Never merge TCs.
- Order the TCs so they run back-to-back on one install. Reinstall the app only when a TC needs a fresh start state.
- Output: one xlsx **per feature sheet**, in the automation v2 format (TestCases + TestData, the v2 style).
- **Stop after writing the files.** The user reviews them, and no spec code is written.

## Setup

The scripts run with Node 18+ and use `exceljs` from this skill folder. Paths below are relative to the skill folder (`<skill>` = the folder holding this SKILL.md).

- If `<skill>/node_modules/exceljs` is missing, run `npm install --prefix <skill>` once.

## Steps

1. **Extract.** Run `node <skill>/scripts/extract.mjs <kit.xlsx> --out <scratch>/cases.json`. It reads every functional sheet, skips the RTM sheets, and marks `selected` = High, Medium, or Low with Test Type Positive. Never re-filter by hand.
2. **Read every selected case:** scenario, steps, expected, pre-condition.
3. **Set aside cases that stay manual**, each with a reason. They stay in the original file and are not written to the output.
   - Google/Apple OAuth or other third-party popups.
   - Turning network on/off, opening a page outside the app.
   - Colour, animation, pixel or chart checks.
   - Text drawn inside a custom view that locators cannot read.
   - Cases blocked by an open Q&A.

   Before setting cases aside for an open Q&A or a missing value (text, locator), ask the user with AskUserQuestion. Ask every open point, not just 4: the tool takes 4 questions per call, so send several calls in a row. Record answers in the Q&A file as `Đã chốt (user, <date>): …`. Expected results follow the spec: if the user says the app behaves differently, keep the spec's expected result and let the test fail.
4. **Order the automated TCs, one feature sheet at a time.** Never mix sheets.
   - Follow the app's screen order. Each TC starts from the state the previous TC left.
   - Data that can be changed inside the app (Back, then choose Male; edit a field) stays in the same run. No reinstall.
   - Set `fresh: true` (reinstall) **only** when the TC needs a state that cannot be reached from where the previous TC ends:

     - never onboarded;
     - an account already exists, or the app is still logged in;
     - a permission was already asked;
     - kill and relaunch;
     - data that cannot be undone.

     The first TC of each sheet is always `fresh: true`.
   - When the previous TC ends on a different screen, put plain navigation steps (no checks) in `pre`.
5. **Write each TC as v2 rows** (see the format below). Then run `node <skill>/scripts/write.mjs plan.json cases.json <out-dir>` (default `automation-tc/<ten-du-an>/`, same project name as the manual file). Fix the plan until it prints `Độ phủ + format v2: OK`.
6. **Report in chat and stop.** Include:
   - for each output file: TCs, manual cases, installs, and installs before (1 per TC);
   - the manual list with reasons;
   - points to review: assumed data, fixed emails that only work once, device date, open Q&A, values that don't fit the keyword list.

## Output (written by write.mjs)

- `<sheet>-automation.xlsx` with two sheets: **TestCases** and **TestData**. The style copies the v2 template: dark-blue header, Case rows blue, Nav light blue, Check yellow, borders, frozen first column and row, filter, and dropdowns on Kind / Keyword / Compare / Platform.
- **TestCases columns:** `TC ID | Title | Priority | Pre-condition | Data Set | Step | Screen | Kind | Keyword | Target | Value | Compare | Platform | Check label | Test Result | Last Run`.
  - Each TC is one **Case** row (ID, title and priority from the original), followed by its Action / Nav / Check rows.
  - Pre-condition line 1 is `Cài lại app` or `Tiếp nối <previous TC>`. **The order of TCs in the sheet is the run order.**

## plan.json

```json
{
  "testcases": [{
    "id": "TC_SEX_001", "fresh": true, "pre": ["Welcome → bấm \"Continues as guest\""],
    "rows": [
      { "step": 1, "screen": "Sex", "kind": "Nav", "keyword": "Verify screen", "target": "Sex" },
      { "step": 1, "screen": "Sex", "kind": "Check", "keyword": "Verify disabled", "target": "Continue", "label": "Continue disable khi chưa chọn giới tính" }
    ]
  }],
  "testdata": [],
  "manual": [{ "tc": "TC_WEL_005", "reason": "Đăng nhập Google: popup OAuth bên thứ 3" }]
}
```

- **Order:** list `testcases` in run order. `fresh` is required. Do not write the `Cài lại app` / `Tiếp nối` line yourself; the script adds it.
- **Kind / Keyword:**
  - Action: Launch fresh, Relaunch app, Tap, Enter, Clear, Set ruler, Select date, Scroll to, Swipe, Back, Hide keyboard.
  - Nav: Verify screen. Add one whenever the flow reaches a new screen.
  - Check: Verify displayed, Verify not displayed, Verify text, Verify value, Verify enabled, Verify disabled, Verify selected.
- **Compare:** empty, equals, number, unit, date:DD/MM/YYYY, all-on, contains.
- **Platform:** All (default), iOS, Android.
- **Check label:** every Check row needs a short Vietnamese label naming what is checked, never the data value. The test report uses it as the bug label.
- **Step:** the TC's own step number. An Action and the Nav / Check rows that follow it share the number.
- **Data:** use concrete values. Use `dataSet` + `testdata` only when a TC really runs several times with different data.
- Notes and assumptions go into `pre` (for example `Ghi chú bước 3: giả định onboarding-qna #14`), not into Target or Value.
