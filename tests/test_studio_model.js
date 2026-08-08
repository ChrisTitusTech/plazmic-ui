"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const {
  DEFAULT_GRID_SIZE,
  anchoredPosition,
  applyDrag,
  applyGroupDrag,
  applyGroupLayout,
  emptySelection,
  isWindowDisplayed,
  mergeAfterSectionSave,
  mergeAfterSectionsSave,
  positionPercent,
  snapValue,
} = require("../ui-tools/studio/studio-model.js");

test("snapValue rounds to the nearest grid line", () => {
  assert.equal(snapValue(11, 8), 8);
  assert.equal(snapValue(13, 8), 16);
  assert.equal(snapValue(-5, 8), -8);
  assert.equal(DEFAULT_GRID_SIZE, 16);
  assert.equal(snapValue(24, Number.NaN), 32);
});

test("BagInv8 center anchor remains stable across serialization", () => {
  const x = anchoredPosition("center", -9.980500, 97, 2560);
  const y = anchoredPosition("top", 17.777800, 195, 1440);

  assert.equal(x, 1103.7496);
  assert.equal(y, 256.00032);
  assert.equal(positionPercent("center", x, 97, 2560).toFixed(6), "-9.980500");
  assert.equal(positionPercent("top", y, 195, 1440).toFixed(6), "17.777800");
});

test("empty selection clears both primary and grouped sections", () => {
  const selection = emptySelection();

  assert.equal(selection.primary, null);
  assert.equal(selection.sections.size, 0);
});

test("moving snaps the top-left corner and preserves the size", () => {
  assert.deepEqual(
    applyDrag(
      { x: 13, y: 21, width: 100, height: 80 },
      6,
      9,
      { enabled: true, gridSize: 8 },
    ),
    { x: 16, y: 32, width: 100, height: 80 },
  );
});

test("resizing snaps the lower-right edge and respects the minimum size", () => {
  assert.deepEqual(
    applyDrag(
      { x: 10, y: 20, width: 100, height: 80 },
      13,
      11,
      { enabled: true, gridSize: 8, resize: true },
    ),
    { x: 10, y: 20, width: 110, height: 92 },
  );
  assert.deepEqual(
    applyDrag(
      { x: 10, y: 20, width: 100, height: 80 },
      -500,
      -500,
      { enabled: true, gridSize: 8, minimumSize: 16, resize: true },
    ),
    { x: 10, y: 20, width: 16, height: 20 },
  );
});

test("disabled and bypassed snapping preserve free movement", () => {
  const start = { x: 13, y: 21, width: 100, height: 80 };
  const expected = { x: 19, y: 30, width: 100, height: 80 };
  assert.deepEqual(applyDrag(start, 6, 9, { enabled: false, gridSize: 8 }), expected);
  assert.deepEqual(
    applyDrag(start, 6, 9, { enabled: true, bypass: true, gridSize: 8 }),
    expected,
  );
});

test("the display predicate applies visibility and filter together", () => {
  const visible = { section: "ChatWindow", visible: true };
  const hidden = { section: "HiddenChatWindow", visible: false };
  assert.equal(isWindowDisplayed(visible, "chat", false), true);
  assert.equal(isWindowDisplayed(visible, "PLAYER", false), false);
  assert.equal(isWindowDisplayed(hidden, "chat", false), false);
  assert.equal(isWindowDisplayed(hidden, "chat", true), true);
  assert.equal(isWindowDisplayed(visible, "", false), true);
});

test("saving one section preserves unsaved sibling window state", () => {
  const current = [
    { section: "ChatWindow", x: 48, y: 80 },
    { section: "MapWindow", x: 96, y: 120 },
  ];
  const loaded = [
    { section: "ChatWindow", x: 16, y: 32 },
    { section: "MapWindow", x: 104, y: 128 },
  ];

  assert.deepEqual(mergeAfterSectionSave(current, loaded, "MapWindow"), [
    current[0],
    loaded[1],
  ]);
});

test("saving a group reloads selected sections and preserves outside state", () => {
  const current = [
    { section: "ChatWindow", x: 48 },
    { section: "MapWindow", x: 96 },
    { section: "InventoryWindow", x: 144 },
  ];
  const loaded = [
    { section: "ChatWindow", x: 56 },
    { section: "MapWindow", x: 104 },
    { section: "InventoryWindow", x: 16 },
  ];
  assert.deepEqual(
    mergeAfterSectionsSave(current, loaded, ["ChatWindow", "MapWindow"]),
    [loaded[0], loaded[1], current[2]],
  );
});

test("group dragging snaps the primary and preserves relative offsets", () => {
  const group = [
    { section: "Primary", x: 13, y: 21, width: 100, height: 80 },
    { section: "Sibling", x: 43, y: 61, width: 120, height: 90 },
  ];
  assert.deepEqual(
    applyGroupDrag(group, "Primary", 6, 9, { enabled: true, gridSize: 8 }),
    [
      { section: "Primary", x: 16, y: 32, width: 100, height: 80 },
      { section: "Sibling", x: 46, y: 72, width: 120, height: 90 },
    ],
  );
});

test("group layout matches primary size and aligns primary edges", () => {
  const windows = [
    { section: "Primary", x: 24, y: 32, width: 100, height: 80 },
    { section: "Sibling", x: 200, y: 180, width: 140, height: 120 },
    { section: "Outside", x: 400, y: 300, width: 90, height: 60 },
  ];
  const selected = ["Primary", "Sibling"];
  const sized = applyGroupLayout(windows, selected, "Primary", "match-size");
  assert.deepEqual(sized[1], {
    section: "Sibling",
    x: 200,
    y: 180,
    width: 100,
    height: 80,
  });
  assert.equal(sized[2], windows[2]);

  const left = applyGroupLayout(windows, selected, "Primary", "align-left");
  assert.equal(left[1].x, 24);
  const top = applyGroupLayout(windows, selected, "Primary", "align-top");
  assert.equal(top[1].y, 32);
});

test("group layout distributes mixed sizes with equal gaps", () => {
  const windows = [
    { section: "First", x: 0, y: 0, width: 40, height: 20 },
    { section: "Middle", x: 80, y: 100, width: 20, height: 40 },
    { section: "Last", x: 180, y: 180, width: 60, height: 60 },
  ];
  const selected = windows.map((windowData) => windowData.section);
  const horizontal = applyGroupLayout(
    windows,
    selected,
    "First",
    "distribute-horizontal",
  );
  assert.deepEqual(horizontal.map((windowData) => windowData.x), [0, 100, 180]);
  const vertical = applyGroupLayout(
    windows,
    selected,
    "First",
    "distribute-vertical",
  );
  assert.deepEqual(vertical.map((windowData) => windowData.y), [0, 80, 180]);
});
