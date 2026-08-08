"use strict";

(function initializeStudioModel(root) {
  const DEFAULT_GRID_SIZE = 16;

  function normalizeGridSize(value) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed >= 1 && parsed <= 256
      ? parsed
      : DEFAULT_GRID_SIZE;
  }

  function snapValue(value, gridSize) {
    const size = normalizeGridSize(gridSize);
    return Math.round(value / size) * size;
  }

  function anchoredPosition(reference, percent, size, extent) {
    const offsetExtent = reference === "center" ? extent / 2 : extent;
    const offset = offsetExtent * percent / 100;
    if (reference === "right" || reference === "bottom") {
      return extent - offset - size;
    }
    if (reference === "center") return extent / 2 + offset - size / 2;
    return offset;
  }

  function positionPercent(reference, position, size, extent) {
    if (reference === "right" || reference === "bottom") {
      return (extent - position - size) * 100 / extent;
    }
    if (reference === "center") {
      return (position + size / 2 - extent / 2) * 100 / (extent / 2);
    }
    return position * 100 / extent;
  }

  function emptySelection() {
    return { primary: null, sections: new Set() };
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

  function applyGroupDrag(startWindows, primarySection, dx, dy, options = {}) {
    const primary = startWindows.find(
      (windowData) => windowData.section === primarySection,
    );
    if (!primary) throw new Error("primary window is not selected");
    const movedPrimary = applyDrag(primary, dx, dy, {
      ...options,
      resize: false,
    });
    const movedX = movedPrimary.x - primary.x;
    const movedY = movedPrimary.y - primary.y;
    return startWindows.map((windowData) => ({
      ...windowData,
      x: windowData.x + movedX,
      y: windowData.y + movedY,
    }));
  }

  function applyGroupLayout(windows, selectedSections, primarySection, action) {
    const selected = new Set(selectedSections);
    const group = windows.filter((windowData) => selected.has(windowData.section));
    if (group.length < 2) return windows;
    const primary = group.find((windowData) => windowData.section === primarySection) || group[0];
    const updates = new Map();

    if (action === "match-size") {
      for (const windowData of group) {
        updates.set(windowData.section, {
          width: primary.width,
          height: primary.height,
        });
      }
    } else if (action === "align-left") {
      for (const windowData of group) updates.set(windowData.section, { x: primary.x });
    } else if (action === "align-top") {
      for (const windowData of group) updates.set(windowData.section, { y: primary.y });
    } else if (action === "distribute-horizontal") {
      const ordered = [...group].sort(
        (left, right) => left.x - right.x || left.section.localeCompare(right.section),
      );
      const start = Math.min(...ordered.map((windowData) => windowData.x));
      const end = Math.max(...ordered.map((windowData) => windowData.x + windowData.width));
      const content = ordered.reduce((total, windowData) => total + windowData.width, 0);
      const gap = (end - start - content) / (ordered.length - 1);
      let cursor = start;
      for (const windowData of ordered) {
        updates.set(windowData.section, { x: cursor });
        cursor += windowData.width + gap;
      }
    } else if (action === "distribute-vertical") {
      const ordered = [...group].sort(
        (top, bottom) => top.y - bottom.y || top.section.localeCompare(bottom.section),
      );
      const start = Math.min(...ordered.map((windowData) => windowData.y));
      const end = Math.max(...ordered.map((windowData) => windowData.y + windowData.height));
      const content = ordered.reduce((total, windowData) => total + windowData.height, 0);
      const gap = (end - start - content) / (ordered.length - 1);
      let cursor = start;
      for (const windowData of ordered) {
        updates.set(windowData.section, { y: cursor });
        cursor += windowData.height + gap;
      }
    } else {
      throw new Error(`unknown group layout action: ${action}`);
    }

    return windows.map((windowData) =>
      updates.has(windowData.section)
        ? { ...windowData, ...updates.get(windowData.section) }
        : windowData,
    );
  }

  function isWindowDisplayed(windowData, filter, showHidden) {
    if (!windowData.visible && !showHidden) return false;
    return String(windowData.section)
      .toLowerCase()
      .includes(String(filter || "").toLowerCase());
  }

  function mergeAfterSectionsSave(currentWindows, loadedWindows, savedSections) {
    const currentBySection = new Map(
      currentWindows.map((windowData) => [windowData.section, windowData]),
    );
    const saved = new Set(savedSections);
    return loadedWindows.map((windowData) =>
      saved.has(windowData.section)
        ? windowData
        : currentBySection.get(windowData.section) || windowData,
    );
  }

  function mergeAfterSectionSave(currentWindows, loadedWindows, savedSection) {
    return mergeAfterSectionsSave(currentWindows, loadedWindows, [savedSection]);
  }

  const model = Object.freeze({
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
  });
  root.PlazmicStudioModel = model;
  if (typeof module !== "undefined" && module.exports) module.exports = model;
})(globalThis);
