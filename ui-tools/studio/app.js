"use strict";

const token = document.querySelector('meta[name="plazmic-token"]').content;
const studioModel = globalThis.PlazmicStudioModel;
const state = {
  data: null,
  selected: null,
  drag: null,
  filter: "",
  showHidden: false,
  snapEnabled: true,
  snapSize: 8,
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
const mutationControls = ["#save-window", "#save-xml", "#publish-button"].map((selector) => document.querySelector(selector));
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

function numeric(value, fallback) {
  const parsed = Number.parseFloat(String(value || "").replace("%", ""));
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
  for (const control of mutationControls) control.disabled = false;
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
  const xPercent = numeric(window.values.XPos, 0);
  const yPercent = numeric(window.values.YPos, 0);
  const xOffset = screen.width * xPercent / 100;
  const yOffset = screen.height * yPercent / 100;
  window.x = window.values.XRef === "right" ? screen.width - xOffset - window.width : window.values.XRef === "center" ? screen.width / 2 + xOffset - window.width / 2 : xOffset;
  window.y = window.values.YRef === "bottom" ? screen.height - yOffset - window.height : window.values.YRef === "center" ? screen.height / 2 + yOffset - window.height / 2 : yOffset;
}

function setPercentPosition(window) {
  const screen = state.data.screen;
  let x;
  let y;
  if (window.values.XRef === "right") x = (screen.width - window.x - window.width) * 100 / screen.width;
  else if (window.values.XRef === "center") x = (window.x + window.width / 2 - screen.width / 2) * 100 / screen.width;
  else x = window.x * 100 / screen.width;
  if (window.values.YRef === "bottom") y = (screen.height - window.y - window.height) * 100 / screen.height;
  else if (window.values.YRef === "center") y = (window.y + window.height / 2 - screen.height / 2) * 100 / screen.height;
  else y = window.y * 100 / screen.height;
  window.values.XPos = `${x.toFixed(6)}%`;
  window.values.YPos = `${y.toFixed(6)}%`;
  fields.xPos.value = x.toFixed(4);
  fields.yPos.value = y.toFixed(4);
  fields.width.value = Math.round(window.width);
  fields.height.value = Math.round(window.height);
}

function colorFor(name) {
  let hash = 0;
  for (const character of name) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
  return `hsl(${Math.abs(hash) % 360} 68% 55%)`;
}

function isWindowDisplayed(window) {
  return studioModel.isWindowDisplayed(window, state.filter, state.showHidden);
}

function renderStage() {
  const stage = document.querySelector("#stage");
  stage.replaceChildren();
  if (!state.data) return;
  const screen = state.data.screen;
  for (const [index, window] of state.data.windows.entries()) {
    if (!isWindowDisplayed(window)) continue;
    const element = document.createElement("div");
    element.className = `mock-window${window.section === state.selected ? " selected" : ""}${window.visible ? "" : " hidden-window"}`;
    element.dataset.section = window.section;
    element.style.left = `${window.x * 100 / screen.width}%`;
    element.style.top = `${window.y * 100 / screen.height}%`;
    element.style.width = `${window.width * 100 / screen.width}%`;
    element.style.height = `${window.height * 100 / screen.height}%`;
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
    button.className = `${window.section === state.selected ? "active" : ""}${window.visible ? "" : " hidden-window"}`;
    button.type = "button";
    button.setAttribute("aria-current", window.section === state.selected ? "true" : "false");
    button.addEventListener("click", () => selectWindow(window.section));
    list.append(button);
  }
}

function rgb(values) {
  const channels = ["BGTint.red", "BGTint.green", "BGTint.blue"].map((key) => Math.max(0, Math.min(255, numeric(values[key], 255))));
  return `#${channels.map((value) => Math.round(value).toString(16).padStart(2, "0")).join("")}`;
}

function selectWindow(section, renderCanvas = true) {
  state.selected = section;
  const window = selectedWindow();
  if (!window) return;
  document.querySelector("#selected-name").textContent = section;
  fields.xRef.value = window.values.XRef || "left";
  fields.yRef.value = window.values.YRef || "top";
  fields.xPos.value = numeric(window.values.XPos, 0).toFixed(4);
  fields.yPos.value = numeric(window.values.YPos, 0).toFixed(4);
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
  renderList();
  if (renderCanvas) renderStage();
}

function beginDrag(event) {
  event.preventDefault();
  const section = event.currentTarget.dataset.section;
  if (section !== state.selected) selectWindow(section, false);
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
  const next = studioModel.applyDrag(
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
      resize: state.drag.resize,
    },
  );
  Object.assign(window, next);
  setPercentPosition(window);
  const screen = state.data.screen;
  event.currentTarget.style.left = `${window.x * 100 / screen.width}%`;
  event.currentTarget.style.top = `${window.y * 100 / screen.height}%`;
  event.currentTarget.style.width = `${window.width * 100 / screen.width}%`;
  event.currentTarget.style.height = `${window.height * 100 / screen.height}%`;
}

function endDrag(event) {
  event.currentTarget.removeEventListener("pointermove", moveDrag);
  event.currentTarget.removeEventListener("pointerup", endDrag);
  event.currentTarget.removeEventListener("pointercancel", endDrag);
  state.drag = null;
  renderStage();
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

async function loadState(preferredSelection = null, preservedWindows = null) {
  const data = await api("/api/state");
  if (preservedWindows && preferredSelection) {
    data.windows = studioModel.mergeAfterSectionSave(
      preservedWindows,
      data.windows,
      preferredSelection,
    );
  }
  state.data = data;
  const layoutName = document.querySelector("#layout-name");
  layoutName.textContent = data.layout;
  layoutName.title = data.layout;
  document.querySelector("#screen-size").textContent = `${data.screen.width} x ${data.screen.height}`;
  const targetSelect = document.querySelector("#target-ini");
  targetSelect.replaceChildren(...data.targets.map((name) => new Option(name, name)));
  if (data.targets.includes(data.layout)) targetSelect.value = data.layout;
  const xmlSelect = document.querySelector("#xml-file");
  xmlSelect.replaceChildren(...data.xmlFiles.map((name) => new Option(name, name)));
  const candidate = data.windows.find((window) => window.section === preferredSelection) || data.windows.find((window) => window.visible) || data.windows[0];
  if (candidate) selectWindow(candidate.section);
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
    const settings = Object.fromEntries(Object.entries(window.values).filter(([key, value]) => value !== "" && ["XRef", "YRef", "XPos", "YPos", "Width", "Height", "Alpha", "FadeToAlpha", "Fades", "Locked", "Show", "BGType", "BGTint.red", "BGTint.green", "BGTint.blue"].includes(key)));
    await api("/api/layout", { method: "POST", body: JSON.stringify({ section: window.section, settings }) });
    await loadState(window.section, windowsBeforeSave);
    status(`Saved ${window.section} to ${state.data.layout}.`, "success");
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

document.querySelector("#publish-button").addEventListener("click", async () => {
  const targetIni = document.querySelector("#target-ini").value;
  if (!targetIni || !window.confirm(`Replace the installed plazmic-ui skin and write the edited layout into ${targetIni}? Backups will be created.`)) return;
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

loadState().then(() => status("Workspace ready. Changes stay local until you publish.", "success")).catch((error) => status(error.message, "error"));
