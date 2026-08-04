"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const {
  applyDrag,
  isWindowDisplayed,
  mergeAfterSectionSave,
  snapValue,
} = require("../ui-tools/studio/studio-model.js");

test("snapValue rounds to the nearest grid line", () => {
  assert.equal(snapValue(11, 8), 8);
  assert.equal(snapValue(13, 8), 16);
  assert.equal(snapValue(-5, 8), -8);
  assert.equal(snapValue(13, Number.NaN), 16);
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
