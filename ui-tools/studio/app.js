"use strict";

const token = document.querySelector('meta[name="plazmic-token"]').content;
const studioModel = globalThis.PlazmicStudioModel;
const state = {
  data: null,
  selected: null,
  selectedSections: new Set(),
  drag: null,
  filter: "",
  showHidden: false,
  snapEnabled: true,
  snapSize: studioModel.DEFAULT_GRID_SIZE,
};
const fields = {
  xRef: document.querySelector("#x-ref"),
  yRef: document.querySelector("#y-ref"),
  xPos: document.querySelector("#x-pos"),
  yPos: document.querySelector("#y-pos"),
  width: document.querySelector("#width"),
  height: document.querySelector("#height"),
  alpha: document.querySelector("#alpha"),
  fadeAlpha: document.querySelector("#fade-alpha"),
  bgType: document.querySelector("#bg-type"),
  bgColor: document.querySelector("#bg-color"),
  visible: document.querySelector("#visible"),
  locked: document.querySelector("#locked"),
  fades: document.querySelector("#fades"),
};
const editableSettingKeys = new Set([
  "XRef", "YRef", "XPos", "YPos", "Width", "Height", "Alpha",
  "FadeToAlpha", "Fades", "Locked", "Show", "BGType", "BGTint.red",
  "BGTint.green", "BGTint.blue",
]);
const mutationControls = [...document.querySelectorAll("#save-window, #save-xml, #load-button, #publish-button, #group-tools button")];
let mutationActive = false;

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Plazmic-Token": token, ...(options.headers || {}) },
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `${response.status} ${response.statusText}`);
  return result;
}

function status(message, kind = "") {
  const element = document.querySelector("#status");
  element.textContent = message;
  element.className = kind;
}

function selectedWindow() {
  return state.data?.windows.find((window) => window.section === state.selected) || null;
}

function selectedWindows() {
  return state.data?.windows.filter((window) => state.selectedSections.has(window.section)) || [];
}

function numeric(value, fallback) {
  const parsed = Number.parseFloat(String(value ?? "").replace("%", ""));
  return Number.isFinite(parsed) ? parsed : fallback;
}

function validatedNumber(field, label, minimum, maximum, integer = false) {
  const text = field.value.trim();
  const value = Number(text);
  if (text === "" || !Number.isFinite(value) || value < minimum || value > maximum || (integer && !Number.isInteger(value))) {
    throw new Error(`${label} must be ${integer ? "an integer " : ""}between ${minimum} and ${maximum}.`);
  }
  return value;
}

function beginMutation() {
  if (mutationActive) return false;
  mutationActive = true;
  for (const control of mutationControls) control.disabled = true;
  return true;
}

function endMutation() {
  mutationActive = false;
  for (const control of mutationControls) control.disabled = !state.data;
  document.querySelector("#save-window").disabled = !selectedWindow();
  updateGroupControls();
}

function updateSelectedFromFields() {
  const window = selectedWindow();
  if (!window) return false;
  let values;
  try {
    values = {
      xPos: validatedNumber(fields.xPos, "X position", -200, 200),
      yPos: validatedNumber(fields.yPos, "Y position", -200, 200),
      width: validatedNumber(fields.width, "Width", 1, 8192, true),
      height: validatedNumber(fields.height, "Height", 1, 8192, true),
      alpha: validatedNumber(fields.alpha, "Alpha", 0, 255, true),
      fadeAlpha: validatedNumber(fields.fadeAlpha, "Fade alpha", 0, 255, true),
      bgType: validatedNumber(fields.bgType, "Background type", 0, 3, true),
    };
  } catch (error) {
    status(error.message, "error");
    return false;
  }
  window.values.XRef = fields.xRef.value;
  window.values.YRef = fields.yRef.value;
  window.values.XPos = `${values.xPos.toFixed(6)}%`;
  window.values.YPos = `${values.yPos.toFixed(6)}%`;
  window.width = values.width;
  window.height = values.height;
  window.values.Width = String(values.width);
  window.values.Height = String(values.height);
  window.values.Alpha = String(values.alpha);
  window.values.FadeToAlpha = String(values.fadeAlpha);
  window.values.BGType = String(values.bgType);
  const color = fields.bgColor.value.match(/[0-9a-f]{2}/gi) || ["ff", "ff", "ff"];
  [window.values["BGTint.red"], window.values["BGTint.green"], window.values["BGTint.blue"]] = color.map((part) => String(Number.parseInt(part, 16)));
  window.values.Show = fields.visible.checked ? "1" : "0";
  window.values.Locked = fields.locked.checked ? "1" : "0";
  window.values.Fades = fields.fades.checked ? "1" : "0";
  window.visible = fields.visible.checked;
  setPixelPosition(window);
  renderList();
  renderStage();
  return true;
}

function setPixelPosition(window) {
  const screen = state.data.screen;
  window.x = studioModel.anchoredPosition(
    window.values.XRef,
    numeric(window.values.XPos, 0),
    window.width,
    screen.width,
  );
  window.y = studioModel.anchoredPosition(
    window.values.YRef,
    numeric(window.values.YPos, 0),
    window.height,
    screen.height,
  );
}

function setPercentPosition(window, updateFields = true) {
  const screen = state.data.screen;
  const x = studioModel.positionPercent(
    window.values.XRef,
    window.x,
    window.width,
    screen.width,
  );
  const y = studioModel.positionPercent(
    window.values.YRef,
    window.y,
    window.height,
    screen.height,
  );
  window.values.XPos = `${x.toFixed(6)}%`;
  window.values.YPos = `${y.toFixed(6)}%`;
  window.values.Width = String(Math.round(window.width));
  window.values.Height = String(Math.round(window.height));
  if (updateFields) {
    fields.xPos.value = x.toFixed(6);
    fields.yPos.value = y.toFixed(6);
    fields.width.value = Math.round(window.width);
    fields.height.value = Math.round(window.height);
  }
}

function editableSettings(window) {
  return Object.fromEntries(
    Object.entries(window.values).filter(
      ([key, value]) => value !== "" && editableSettingKeys.has(key),
    ),
  );
}

function colorFor(name) {
  let hash = 0;
  for (const character of name) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
  return `hsl(${Math.abs(hash) % 360} 68% 55%)`;
}

function isWindowDisplayed(window) {
  return studioModel.isWindowDisplayed(window, state.filter, state.showHidden);
}

function updateMockWindowGeometry(element, window) {
  const screen = state.data.screen;
  element.style.left = `${window.x * 100 / screen.width}%`;
  element.style.top = `${window.y * 100 / screen.height}%`;
  element.style.width = `${window.width * 100 / screen.width}%`;
  element.style.height = `${window.height * 100 / screen.height}%`;
}

function renderStage() {
  const stage = document.querySelector("#stage");
  stage.replaceChildren();
  if (!state.data) return;
  const screen = state.data.screen;
  for (const [index, window] of state.data.windows.entries()) {
    if (!isWindowDisplayed(window)) continue;
    const element = document.createElement("div");
    element.className = `mock-window${window.section === state.selected ? " selected" : ""}${state.selectedSections.has(window.section) ? " group-selected" : ""}${window.visible ? "" : " hidden-window"}`;
    element.dataset.section = window.section;
    updateMockWindowGeometry(element, window);
    element.style.opacity = String(Math.max(0.18, numeric(window.values.Alpha, 255) / 255));
    element.style.zIndex = String(index + 1);
    element.style.setProperty("--window-color", colorFor(window.section));
    const label = document.createElement("span");
    label.textContent = window.section;
    element.append(label);
    if (window.section === state.selected) {
      const handle = document.createElement("div");
      handle.className = "resize-handle";
      handle.dataset.resize = "true";
      element.append(handle);
    }
    element.addEventListener("pointerdown", beginDrag);
    stage.append(element);
  }
}

function renderList() {
  const list = document.querySelector("#window-list");
  list.replaceChildren();
  if (!state.data) return;
  for (const window of state.data.windows) {
    if (!isWindowDisplayed(window)) continue;
    const button = document.createElement("button");
    button.textContent = window.section;
    button.className = `${window.section === state.selected ? "active" : ""}${state.selectedSections.has(window.section) ? " group-selected" : ""}${window.visible ? "" : " hidden-window"}`;
    button.type = "button";
    button.setAttribute("aria-current", window.section === state.selected ? "true" : "false");
    button.setAttribute("aria-pressed", state.selectedSections.has(window.section) ? "true" : "false");
    button.addEventListener("click", (event) => handleWindowSelection(window.section, event.shiftKey));
    list.append(button);
  }
}

function rgb(values) {
  const channels = ["BGTint.red", "BGTint.green", "BGTint.blue"].map((key) => Math.max(0, Math.min(255, numeric(values[key], 255))));
  return `#${channels.map((value) => Math.round(value).toString(16).padStart(2, "0")).join("")}`;
}

function updateGroupControls() {
  const count = state.selectedSections.size;
  const tools = document.querySelector("#group-tools");
  tools.hidden = count < 2;
  document.querySelector("#selection-count").textContent = `${count} selected`;
  for (const button of tools.querySelectorAll("button")) {
    const needsThree = button.matches("[data-group-action^='distribute-']");
    button.disabled = mutationActive || !state.data || count < 2 || (needsThree && count < 3);
  }
}

function selectWindow(section, renderCanvas = true, resetSelection = true) {
  state.selected = section;
  if (resetSelection) state.selectedSections = new Set([section]);
  else state.selectedSections.add(section);
  const window = selectedWindow();
  if (!window) return;
  for (const field of Object.values(fields)) field.disabled = false;
  document.querySelector("#save-window").disabled = mutationActive;
  document.querySelector("#selected-name").textContent = section;
  fields.xRef.value = window.values.XRef || "left";
  fields.yRef.value = window.values.YRef || "top";
  fields.xPos.value = numeric(window.values.XPos, 0).toFixed(6);
  fields.yPos.value = numeric(window.values.YPos, 0).toFixed(6);
  fields.width.value = Math.round(window.width);
  fields.height.value = Math.round(window.height);
  fields.alpha.value = numeric(window.values.Alpha, 255);
  fields.fadeAlpha.value = numeric(window.values.FadeToAlpha, 255);
  fields.bgType.value = numeric(window.values.BGType, 1);
  fields.bgColor.value = rgb(window.values);
  fields.visible.checked = window.visible;
  fields.locked.checked = window.values.Locked === "1";
  fields.fades.checked = window.values.Fades !== "0";
  if (window.xmlFile) {
    document.querySelector("#xml-file").value = window.xmlFile;
    loadXml(window.xmlFile);
  }
  updateGroupControls();
  renderList();
  if (renderCanvas) renderStage();
}

function toggleWindowSelection(section) {
  if (state.selectedSections.has(section)) {
    if (state.selectedSections.size === 1) return;
    state.selectedSections.delete(section);
    if (state.selected === section) {
      selectWindow(state.selectedSections.values().next().value, true, false);
      return;
    }
  } else {
    state.selectedSections.add(section);
  }
  updateGroupControls();
  renderList();
  renderStage();
}

function handleWindowSelection(section, extendSelection) {
  if (extendSelection) toggleWindowSelection(section);
  else selectWindow(section);
}

function deselectAllWindows() {
  const selection = studioModel.emptySelection();
  state.selected = selection.primary;
  state.selectedSections = selection.sections;
  document.querySelector("#selected-name").textContent = "Select a window";
  for (const field of Object.values(fields)) field.disabled = true;
  document.querySelector("#save-window").disabled = true;
  updateGroupControls();
  renderList();
  renderStage();
  status("Deselected all windows.", "success");
}

function invalidateEditorState() {
  const selection = studioModel.emptySelection();
  state.data = null;
  state.selected = selection.primary;
  state.selectedSections = selection.sections;
  document.querySelector("#selected-name").textContent = "Reload Studio to continue";
  for (const field of Object.values(fields)) field.disabled = true;
  renderList();
  renderStage();
  updateGroupControls();
}

function beginDrag(event) {
  event.preventDefault();
  const section = event.currentTarget.dataset.section;
  if (event.shiftKey) {
    toggleWindowSelection(section);
    return;
  }
  if (!state.selectedSections.has(section)) selectWindow(section, false);
  const window = selectedWindow();
  const stageRect = document.querySelector("#stage").getBoundingClientRect();
  state.drag = {
    pointerId: event.pointerId,
    resize: event.target.dataset.resize === "true",
    startClientX: event.clientX,
    startClientY: event.clientY,
    startX: window.x,
    startY: window.y,
    startWidth: window.width,
    startHeight: window.height,
    startWindows: selectedWindows().map((selected) => ({
      section: selected.section,
      x: selected.x,
      y: selected.y,
      width: selected.width,
      height: selected.height,
    })),
    scaleX: state.data.screen.width / stageRect.width,
    scaleY: state.data.screen.height / stageRect.height,
  };
  event.currentTarget.setPointerCapture(event.pointerId);
  event.currentTarget.addEventListener("pointermove", moveDrag);
  event.currentTarget.addEventListener("pointerup", endDrag);
  event.currentTarget.addEventListener("pointercancel", endDrag);
}

function moveDrag(event) {
  if (!state.drag || event.pointerId !== state.drag.pointerId) return;
  const window = selectedWindow();
  const dx = (event.clientX - state.drag.startClientX) * state.drag.scaleX;
  const dy = (event.clientY - state.drag.startClientY) * state.drag.scaleY;
  if (state.drag.resize) {
    Object.assign(
      window,
      studioModel.applyDrag(
        {
          x: state.drag.startX,
          y: state.drag.startY,
          width: state.drag.startWidth,
          height: state.drag.startHeight,
        },
        dx,
        dy,
        {
          enabled: state.snapEnabled,
          bypass: event.altKey,
          gridSize: state.snapSize,
          resize: true,
        },
      ),
    );
    setPercentPosition(window);
  } else {
    const moved = studioModel.applyGroupDrag(
      state.drag.startWindows,
      state.selected,
      dx,
      dy,
      {
        enabled: state.snapEnabled,
        bypass: event.altKey,
        gridSize: state.snapSize,
      },
    );
    const movedBySection = new Map(
      moved.map((windowData) => [windowData.section, windowData]),
    );
    for (const selected of selectedWindows()) {
      Object.assign(selected, movedBySection.get(selected.section));
      setPercentPosition(selected, selected.section === state.selected);
    }
  }
  const rendered = new Map(
    [...document.querySelectorAll(".mock-window")].map((element) => [
      element.dataset.section,
      element,
    ]),
  );
  for (const selected of selectedWindows()) {
    const element = rendered.get(selected.section);
    if (element) updateMockWindowGeometry(element, selected);
  }
}

function endDrag(event) {
  event.currentTarget.removeEventListener("pointermove", moveDrag);
  event.currentTarget.removeEventListener("pointerup", endDrag);
  event.currentTarget.removeEventListener("pointercancel", endDrag);
  state.drag = null;
  renderStage();
}

function applyGroupAction(action) {
  if (state.selectedSections.size < 2) return;
  state.data.windows = studioModel.applyGroupLayout(
    state.data.windows,
    [...state.selectedSections],
    state.selected,
    action,
  );
  for (const window of selectedWindows()) {
    setPercentPosition(window, window.section === state.selected);
  }
  const labels = {
    "match-size": "Matched selected windows to the primary size.",
    "align-left": "Aligned selected windows to the primary left edge.",
    "align-top": "Aligned selected windows to the primary top edge.",
    "distribute-horizontal": "Distributed selected windows evenly across.",
    "distribute-vertical": "Distributed selected windows evenly down.",
  };
  renderStage();
  status(`${labels[action]} Save selected to keep these changes.`, "success");
}

async function loadXml(filename) {
  if (!filename) return;
  try {
    const result = await api(`/api/xml?file=${encodeURIComponent(filename)}`);
    if (document.querySelector("#xml-file").value !== filename) return;
    document.querySelector("#xml-source").value = result.contents;
    status(`Loaded ${filename}.`);
  } catch (error) {
    status(error.message, "error");
  }
}

async function loadState(
  preferredSelection = null,
  preservedWindows = null,
  savedSections = null,
  preferredTarget = null,
) {
  const preservedSelection = preservedWindows ? [...state.selectedSections] : null;
  const data = await api("/api/state");
  if (preservedWindows && preferredSelection) {
    data.windows = studioModel.mergeAfterSectionsSave(
      preservedWindows,
      data.windows,
      savedSections || [preferredSelection],
    );
  }
  state.data = data;
  const layoutName = document.querySelector("#layout-name");
  layoutName.textContent = data.layout;
  layoutName.title = data.layout;
  document.querySelector("#skin-name").textContent = data.skinName;
  document.querySelector("#screen-size").textContent = `${data.screen.width} x ${data.screen.height}`;
  const targetSelect = document.querySelector("#target-ini");
  targetSelect.replaceChildren(...data.targets.map((name) => new Option(name, name)));
  if (preferredTarget && data.targets.includes(preferredTarget)) {
    targetSelect.value = preferredTarget;
  } else if (data.targets.includes(data.layout)) {
    targetSelect.value = data.layout;
  }
  const xmlSelect = document.querySelector("#xml-file");
  xmlSelect.replaceChildren(...data.xmlFiles.map((name) => new Option(name, name)));
  const candidate = data.windows.find((window) => window.section === preferredSelection) || data.windows.find((window) => window.visible) || data.windows[0];
  if (candidate && preservedSelection) {
    const available = new Set(data.windows.map((window) => window.section));
    state.selectedSections = new Set(
      preservedSelection.filter((section) => available.has(section)),
    );
    selectWindow(candidate.section, true, false);
  } else if (candidate) {
    selectWindow(candidate.section);
  }
  renderList();
  renderStage();
}

document.querySelector("#window-filter").addEventListener("input", (event) => {
  state.filter = event.target.value;
  renderList();
  renderStage();
});
document.querySelector("#show-hidden").addEventListener("change", (event) => { state.showHidden = event.target.checked; renderList(); renderStage(); });
document.querySelector("#snap-enabled").addEventListener("change", (event) => {
  state.snapEnabled = event.target.checked;
});
document.querySelector("#snap-size").addEventListener("change", (event) => {
  const snapSize = Number.parseInt(event.target.value, 10);
  if (!Number.isInteger(snapSize) || snapSize < 1 || snapSize > 256) {
    event.target.value = String(state.snapSize);
    return;
  }
  state.snapSize = snapSize;
});
document.querySelector("#xml-file").addEventListener("change", (event) => loadXml(event.target.value));
for (const field of Object.values(fields)) field.addEventListener("change", updateSelectedFromFields);
document.querySelectorAll("[data-group-action]").forEach((button) => {
  button.addEventListener("click", () => applyGroupAction(button.dataset.groupAction));
});
document.querySelector("#deselect-all").addEventListener("click", deselectAllWindows);

document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".tab, .tab-panel").forEach((element) => element.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((tab) => tab.setAttribute("aria-selected", "false"));
  button.classList.add("active");
  button.setAttribute("aria-selected", "true");
  document.querySelector(`#${button.dataset.tab}`).classList.add("active");
}));

document.querySelector("#save-window").addEventListener("click", async () => {
  const window = selectedWindow();
  if (!window) return;
  if (!beginMutation()) return;
  try {
    if (!updateSelectedFromFields()) return;
    const windowsBeforeSave = state.data.windows;
    const settings = editableSettings(window);
    await api("/api/layout", { method: "POST", body: JSON.stringify({ section: window.section, settings }) });
    await loadState(window.section, windowsBeforeSave);
    status(`Saved ${window.section} to ${state.data.layout}.`, "success");
  } catch (error) {
    status(error.message, "error");
  } finally {
    endMutation();
  }
});

document.querySelector("#save-selected").addEventListener("click", async () => {
  if (state.selectedSections.size < 2 || !beginMutation()) return;
  try {
    if (!updateSelectedFromFields()) return;
    const windowsBeforeSave = state.data.windows;
    const sections = selectedWindows().map((window) => ({
      section: window.section,
      settings: editableSettings(window),
    }));
    await api("/api/layout", {
      method: "POST",
      body: JSON.stringify({ sections }),
    });
    await loadState(
      state.selected,
      windowsBeforeSave,
      sections.map((item) => item.section),
    );
    status(`Saved ${sections.length} selected windows to ${state.data.layout}.`, "success");
  } catch (error) {
    status(error.message, "error");
  } finally {
    endMutation();
  }
});

document.querySelector("#save-xml").addEventListener("click", async () => {
  const filename = document.querySelector("#xml-file").value;
  if (!beginMutation()) return;
  try {
    await api("/api/xml", { method: "POST", body: JSON.stringify({ file: filename, contents: document.querySelector("#xml-source").value }) });
    status(`Validated and saved ${filename}.`, "success");
  } catch (error) {
    status(error.message, "error");
  } finally {
    endMutation();
  }
});

document.querySelector("#load-button").addEventListener("click", async () => {
  const sourceIni = document.querySelector("#target-ini").value;
  if (!sourceIni || !window.confirm(`Discard unsaved Studio positions and load the current ${sourceIni} from EverQuest? The local Studio layout will be backed up first.`)) return;
  if (!beginMutation()) return;
  status(`Loading ${sourceIni} from EverQuest...`);
  try {
    const result = await api("/api/load", { method: "POST", body: JSON.stringify({ sourceIni }) });
    invalidateEditorState();
    await loadState(state.selected, null, null, sourceIni);
    status(`Loaded ${result.source} into ${result.layout}.`, "success");
  } catch (error) {
    status(error.message, "error");
  } finally {
    endMutation();
  }
});

document.querySelector("#publish-button").addEventListener("click", async () => {
  const targetIni = document.querySelector("#target-ini").value;
  if (!targetIni || !window.confirm(`Replace the installed ${state.data.skinName} skin and write the edited layout into ${targetIni}? Backups will be created.`)) return;
  if (!beginMutation()) return;
  status("Publishing the skin and layout to EverQuest...");
  try {
    const result = await api("/api/publish", { method: "POST", body: JSON.stringify({ targetIni }) });
    status(`Published. ${result.instructions}`, "success");
  } catch (error) {
    status(error.message, "error");
  } finally {
    endMutation();
  }
});

loadState().then(() => status("Workspace ready. Changes stay local until you save to game.", "success")).catch((error) => status(error.message, "error"));
