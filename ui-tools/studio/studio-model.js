"use strict";

(function initializeStudioModel(root) {
  function normalizeGridSize(value) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed >= 1 && parsed <= 256 ? parsed : 8;
  }

  function snapValue(value, gridSize) {
    const size = normalizeGridSize(gridSize);
    return Math.round(value / size) * size;
  }

  function applyDrag(start, dx, dy, options = {}) {
    const gridSize = normalizeGridSize(options.gridSize);
    const snapEnabled = options.enabled !== false && options.bypass !== true;
    const minimumSize = Number.isFinite(options.minimumSize)
      ? Math.max(1, options.minimumSize)
      : 16;

    if (options.resize) {
      const rawRight = start.x + Math.max(minimumSize, start.width + dx);
      const rawBottom = start.y + Math.max(minimumSize, start.height + dy);
      const right = snapEnabled ? snapValue(rawRight, gridSize) : rawRight;
      const bottom = snapEnabled ? snapValue(rawBottom, gridSize) : rawBottom;
      return {
        x: start.x,
        y: start.y,
        width: Math.max(minimumSize, right - start.x),
        height: Math.max(minimumSize, bottom - start.y),
      };
    }

    const x = start.x + dx;
    const y = start.y + dy;
    return {
      x: snapEnabled ? snapValue(x, gridSize) : x,
      y: snapEnabled ? snapValue(y, gridSize) : y,
      width: start.width,
      height: start.height,
    };
  }

  function isWindowDisplayed(windowData, filter, showHidden) {
    if (!windowData.visible && !showHidden) return false;
    return String(windowData.section)
      .toLowerCase()
      .includes(String(filter || "").toLowerCase());
  }

  function mergeAfterSectionSave(currentWindows, loadedWindows, savedSection) {
    const currentBySection = new Map(
      currentWindows.map((windowData) => [windowData.section, windowData]),
    );
    return loadedWindows.map((windowData) =>
      windowData.section === savedSection
        ? windowData
        : currentBySection.get(windowData.section) || windowData,
    );
  }

  const model = Object.freeze({
    applyDrag,
    isWindowDisplayed,
    mergeAfterSectionSave,
    snapValue,
  });
  root.PlazmicStudioModel = model;
  if (typeof module !== "undefined" && module.exports) module.exports = model;
})(globalThis);
