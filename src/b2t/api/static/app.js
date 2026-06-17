const TERMINAL = ["succeeded", "compile_failed", "failed"];
const $ = (id) => document.getElementById(id);

let currentJobId = null;
let editor = null;
let graphNodes = null;   // node name -> strip element
let nodeOrder = [];      // pipeline node order from /api/graph
let llmNodes = [];       // from /api/llm-nodes
let models = [];         // from /api/models
let stateNodes = [];     // node names that have a captured snapshot

if (window.CodeMirror) {
  CodeMirror.defineSimpleMode("typst", {
    start: [
      { regex: /\/\/.*/, token: "comment" },
      { regex: /\/\*/, token: "comment", next: "comment" },
      { regex: /"(?:[^\\"]|\\.)*"/, token: "string" },
      { regex: /\$[^$]*\$/, token: "string-2" },
      { regex: /^\s*=+.*/, token: "header" },
      { regex: /#(?:let|set|show|import|include)\b/, token: "keyword" },
      { regex: /#[A-Za-z_][\w.-]*/, token: "variable-2" },
    ],
    comment: [
      { regex: /.*?\*\//, token: "comment", next: "start" },
      { regex: /.*/, token: "comment" },
    ],
    meta: { lineComment: "//" },
  });
  editor = CodeMirror.fromTextArea($("typ"), {
    mode: "typst",
    theme: "material-darker",
    lineNumbers: true,
    lineWrapping: true,
  });
}

function getSource() {
  return editor ? editor.getValue() : $("typ").value;
}

function setSource(text) {
  if (editor) editor.setValue(text);
  else $("typ").value = text;
}

// ----- pipeline strip (custom-rendered, replaces mermaid) -----
async function loadGraph() {
  let data;
  try {
    data = await (await fetch("/api/graph")).json();
  } catch (e) {
    return; // leave graphNodes null; highlightGraph uses the text fallback
  }
  nodeOrder = data.nodes.map((n) => n.name);
  const strip = $("graph");
  strip.innerHTML = "";
  const map = {};
  data.nodes.forEach((n, i) => {
    const box = document.createElement("div");
    box.className = "node" + (n.is_llm ? " llm" : "");
    box.dataset.node = n.name;
    box.textContent = n.name;
    strip.appendChild(box);
    map[n.name] = box;
    box.addEventListener("click", () => inspectNode(n.name));
    if (i < data.nodes.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "arrow";
      arrow.textContent = "→";
      strip.appendChild(arrow);
    }
  });
  graphNodes = map;
  highlightGraph(null, "idle");
}

function highlightGraph(currentNode, status) {
  if (!graphNodes) {
    $("graph").textContent = currentNode ? `Stage: ${currentNode} (${status})` : "";
    return;
  }
  const idx = nodeOrder.indexOf(currentNode);
  const allDone = status === "succeeded";
  nodeOrder.forEach((name, i) => {
    const g = graphNodes[name];
    if (!g) return;
    g.classList.remove("done", "active", "pending");
    if (allDone || (idx >= 0 && i < idx)) g.classList.add("done");
    else if (idx === i) g.classList.add(status === "running" ? "active" : "done");
    else g.classList.add("pending");
  });
}

// ----- LLM node cards with inline prompt preview -----
async function loadLLMNodes() {
  const container = $("llm-nodes");
  container.innerHTML = "";
  try {
    models = (await (await fetch("/api/models")).json()).models;
    llmNodes = (await (await fetch("/api/llm-nodes")).json()).nodes;
  } catch (e) {
    return; // leave empty; submitting with no choices keeps server defaults
  }
  for (const node of llmNodes) container.appendChild(buildCard(node));
}

function buildCard(node) {
  const card = document.createElement("div");
  card.className = "llm-card";

  const title = document.createElement("div");
  title.className = "llm-card-title";
  title.textContent = node.node;
  card.appendChild(title);

  const modelSel = document.createElement("select");
  modelSel.dataset.node = node.node;
  modelSel.className = "model-select";
  for (const m of models) {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.label;
    modelSel.appendChild(opt);
  }

  const verSel = document.createElement("select");
  verSel.dataset.node = node.node;
  verSel.className = "version-select";
  for (const v of node.versions) {
    const opt = document.createElement("option");
    opt.value = v.id;
    opt.textContent = v.label;
    opt.selected = v.id === node.default_version;
    verSel.appendChild(opt);
  }

  const viewBtn = document.createElement("button");
  viewBtn.type = "button";
  viewBtn.className = "view-prompt";
  viewBtn.textContent = "view prompt";

  const modelLabel = document.createElement("label");
  modelLabel.append("model ", modelSel);
  const versionLabel = document.createElement("label");
  versionLabel.append("prompt version ", verSel);

  const controls = document.createElement("div");
  controls.className = "llm-controls";
  controls.append(modelLabel, versionLabel, viewBtn);
  card.appendChild(controls);

  const preview = buildPreview(node.node, () => verSel.value);
  card.appendChild(preview.wrap);

  viewBtn.addEventListener("click", () => {
    const open = preview.wrap.hidden;
    preview.toggle(open);
    viewBtn.textContent = open ? "hide prompt" : "view prompt";
  });
  verSel.addEventListener("change", () => preview.onVersionChange());

  return card;
}

// Render text into a line-numbered gutter, one flex row per line. An optional
// highlight(line) -> html escapes and colors each line (used by the inspector);
// without it, the line is inserted as plain text.
function renderLines(container, text, highlight) {
  container.textContent = "";
  const frag = document.createDocumentFragment();
  text.split("\n").forEach((line, i) => {
    const row = document.createElement("div");
    row.className = "code-row";
    const num = document.createElement("span");
    num.className = "code-ln";
    num.textContent = i + 1;
    const content = document.createElement("span");
    content.className = "code-line";
    if (highlight) content.innerHTML = highlight(line);
    else content.textContent = line;
    row.append(num, content);
    frag.appendChild(row);
  });
  container.appendChild(frag);
}

function buildPreview(nodeName, getVersion) {
  const wrap = document.createElement("div");
  wrap.className = "prompt-preview";
  wrap.hidden = true;

  const tabs = document.createElement("div");
  tabs.className = "preview-tabs";
  const tplTab = document.createElement("button");
  tplTab.type = "button";
  tplTab.textContent = "template";
  tplTab.className = "active";
  const rndTab = document.createElement("button");
  rndTab.type = "button";
  rndTab.textContent = "rendered";
  tabs.append(tplTab, rndTab);

  const note = document.createElement("div");
  note.className = "preview-note";
  const body = document.createElement("div");
  body.className = "preview-body";

  wrap.append(tabs, note, body);

  let view = "template";

  async function showTemplate() {
    note.textContent = "";
    body.textContent = "loading...";
    try {
      const r = await fetch(`/api/prompts/${nodeName}/${getVersion()}`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      renderLines(body, `# system\n${d.system}\n\n# user_template\n${d.user_template}`);
    } catch (e) {
      body.textContent = "(failed to load prompt)";
    }
  }

  async function showRendered() {
    note.textContent = "";
    body.textContent = "loading...";
    if (!currentJobId) {
      note.textContent = "run the pipeline to see the rendered prompt";
      body.textContent = "";
      return;
    }
    try {
      const r = await fetch(`/api/jobs/${currentJobId}/prompt/${nodeName}`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      note.textContent = `as run: ${d.model}, ${d.prompt_version}`;
      renderLines(body, `# system\n${d.system}\n\n# user\n${d.user}`);
    } catch (e) {
      note.textContent = "run the pipeline to see the rendered prompt";
      body.textContent = "";
    }
  }

  function refresh() {
    if (view === "template") showTemplate();
    else showRendered();
  }

  tplTab.addEventListener("click", () => {
    view = "template";
    tplTab.classList.add("active");
    rndTab.classList.remove("active");
    refresh();
  });
  rndTab.addEventListener("click", () => {
    view = "rendered";
    rndTab.classList.add("active");
    tplTab.classList.remove("active");
    refresh();
  });

  return {
    wrap,
    toggle: (open) => {
      wrap.hidden = !open;
      if (open) refresh();
    },
    onVersionChange: () => {
      if (!wrap.hidden && view === "template") refresh();
    },
  };
}

// ----- sample deck picker -----
async function loadSampleDecks() {
  const sel = $("sample-deck");
  try {
    const decks = (await (await fetch("/api/sample-decks")).json()).decks;
    sel.innerHTML = "";
    for (const name of decks) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      sel.appendChild(opt);
    }
  } catch (e) {
    // leave empty; the sample button posts no deck and the server defaults
  }
}

function collectChoices() {
  const choices = {};
  for (const sel of document.querySelectorAll(".model-select")) {
    choices[sel.dataset.node] = { model: sel.value };
  }
  for (const sel of document.querySelectorAll(".version-select")) {
    (choices[sel.dataset.node] ||= {}).prompt_version = sel.value;
  }
  return choices;
}

function commonFields(fd) {
  fd.append("use_fake", $("use-fake").checked ? "true" : "false");
  fd.append("hitl", $("hitl").checked ? "true" : "false");
  fd.append("choices", JSON.stringify(collectChoices()));
  return fd;
}

function setBadge(status) {
  const badge = $("badge");
  badge.textContent = status;
  badge.className = "badge " + status;
}

function setBusy(busy) {
  $("run").disabled = busy;
  $("run-sample").disabled = busy;
}

function refreshPdf(id, hasPdf) {
  $("pdf").src = hasPdf ? `/api/jobs/${id}/pdf?t=${Date.now()}` : "about:blank";
}

async function finish(id, job) {
  setBusy(false);
  const typ = await fetch(`/api/jobs/${id}/typ`);
  setSource(typ.ok ? await typ.text() : "");
  refreshPdf(id, job.has_pdf);
  $("error").textContent = job.error || "(none)";
  $("save").disabled = false;
  $("download").disabled = false;
  const prov = job.llm_runs || {};
  $("provenance").textContent = Object.keys(prov).length
    ? "Ran: " + Object.entries(prov)
        .map(([n, r]) => `${n} (${r.model}, ${r.prompt_version})`)
        .join("; ")
    : "";
}

async function poll(id) {
  currentJobId = id;
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  highlightGraph(job.current_node, job.status);
  stateNodes = job.state_nodes || [];
  markInspectable();
  if (job.status === "awaiting_review") renderReview(id);
  else $("review").hidden = true;
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}

// ----- per-frame review panel -----
async function renderReview(jobId) {
  const r = await fetch(`/api/jobs/${jobId}/review`);
  if (!r.ok) { $("review").hidden = true; return; }
  const review = await r.json();
  $("review-counter").textContent = `${review.frame_index + 1} of ${review.total}`;
  $("review-candidate").value = review.candidate;
  $("review-status").textContent = review.preview_ok
    ? "" : `preview did not compile: ${review.preview_error || ""}`;
  $("review-preview").src = review.preview_ok
    ? `/api/jobs/${jobId}/preview.pdf?ts=${Date.now()}` : "about:blank";
  $("review").hidden = false;
}

// Post the decision; the live poll loop re-renders when the run pauses again.
async function submitReview(action) {
  if (!currentJobId) return;
  const feedback = $("review-feedback").value;
  $("review").hidden = true;
  await fetch(`/api/jobs/${currentJobId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, feedback: feedback || null }),
  });
  $("review-feedback").value = "";
}

$("review-approve").addEventListener("click", () => submitReview("approve"));
$("review-regenerate").addEventListener("click", () => submitReview("regenerate"));

async function start(url, fd) {
  setBusy(true);
  $("save").disabled = true;
  $("download").disabled = true;
  setSource("");
  $("error").textContent = "(none)";
  $("pdf").src = "about:blank";
  hideInspector();
  stateNodes = [];
  markInspectable();
  const res = await fetch(url, { method: "POST", body: fd });
  const data = await res.json();
  poll(data.job_id);
}

$("run").addEventListener("click", () => {
  const files = $("folder").files;
  if (!files.length) { alert("Pick a deck folder first."); return; }
  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.webkitRelativePath);
  start("/api/jobs", commonFields(fd));
});

$("run-sample").addEventListener("click", () => {
  const fd = commonFields(new FormData());
  fd.append("deck", $("sample-deck").value);
  start("/api/jobs/sample", fd);
});

$("save").addEventListener("click", async () => {
  if (!currentJobId) return;
  $("error").textContent = "(saving...)";
  const res = await fetch(`/api/jobs/${currentJobId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: getSource() }),
  });
  const data = await res.json();
  $("error").textContent = data.error || "(none)";
  refreshPdf(currentJobId, data.ok);
});

$("download").addEventListener("click", () => {
  if (!currentJobId) return;
  window.location = `/api/jobs/${currentJobId}/download`;
});

// ----- per-node state inspector -----
let inspectedNode = null;   // node whose snapshot is shown, or null

function markInspectable() {
  if (!graphNodes) return;
  for (const [name, box] of Object.entries(graphNodes)) {
    box.classList.toggle("inspectable", stateNodes.includes(name));
  }
}

function selectNode(node) {
  if (!graphNodes) return;
  for (const box of Object.values(graphNodes)) box.classList.remove("selected");
  if (graphNodes[node]) graphNodes[node].classList.add("selected");
}

function ensureInspector() {
  const panel = $("state-inspector");
  if (panel.dataset.built) return;
  panel.dataset.built = "1";

  const header = document.createElement("div");
  header.className = "inspector-header";
  const title = document.createElement("span");
  title.className = "inspector-title";
  title.id = "inspector-title";
  const hide = document.createElement("button");
  hide.type = "button";
  hide.className = "inspector-hide";
  hide.textContent = "hide";
  hide.addEventListener("click", hideInspector);
  header.append(title, hide);

  const changed = document.createElement("div");
  changed.className = "inspector-changed";
  changed.id = "inspector-changed";

  const viewer = document.createElement("div");
  viewer.id = "inspector-viewer";

  panel.append(header, changed, viewer);
}

// Color JSON tokens after HTML-escaping, so model/deck text can never inject
// markup. The viewer scrolls natively, so any snapshot size reaches the bottom.
function highlightJson(json) {
  const escaped = json
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g,
    (match) => {
      let cls = "json-number";
      if (match[0] === '"') {
        cls = match.slice(-1) === ":" ? "json-key" : "json-string";
      } else if (match === "true" || match === "false") {
        cls = "json-boolean";
      } else if (match === "null") {
        cls = "json-null";
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

function setViewer(text) {
  const viewer = $("inspector-viewer");
  if (!text) {
    viewer.textContent = "";
    return;
  }
  renderLines(viewer, text, highlightJson);
}

function hideInspector() {
  $("state-inspector").hidden = true;
  inspectedNode = null;
  if (graphNodes) {
    for (const box of Object.values(graphNodes)) box.classList.remove("selected");
  }
}

async function inspectNode(node) {
  if (!currentJobId || !stateNodes.includes(node)) return;
  const panel = $("state-inspector");
  if (inspectedNode === node && !panel.hidden) {
    hideInspector();
    return;
  }
  ensureInspector();
  selectNode(node);
  inspectedNode = node;
  panel.hidden = false;
  $("inspector-title").textContent = `State after: ${node}`;
  $("inspector-changed").textContent = "loading...";
  setViewer("");
  try {
    const r = await fetch(`/api/jobs/${currentJobId}/state/${node}`);
    if (!r.ok) throw new Error();
    const data = await r.json();
    $("inspector-changed").textContent =
      "changed: " + (data.changed.join(", ") || "(nothing)");
    setViewer(JSON.stringify(data.state, null, 2));
  } catch (e) {
    $("inspector-changed").textContent = "(failed to load state)";
    setViewer("");
  }
}

loadGraph();
loadLLMNodes();
loadSampleDecks();
