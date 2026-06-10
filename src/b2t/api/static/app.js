const NODES = [
  "copy_input", "clean_build", "detect_main", "flatten",
  "strip_overlays", "convert", "write_output", "compile",
];
const TERMINAL = ["succeeded", "compile_failed", "failed"];

const $ = (id) => document.getElementById(id);

let currentJobId = null;
let editor = null;
let graphNodes = null;

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

async function loadGraph() {
  let def;
  try {
    def = (await (await fetch("/api/graph")).json()).mermaid;
  } catch (e) {
    return;  // leave graphNodes null; highlightGraph uses the text fallback
  }
  if (!window.mermaid) return;
  try {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "default" });
    const { svg } = await window.mermaid.render("pipelineGraph", def);
    $("graph").innerHTML = svg;
    const map = {};
    $("graph").querySelectorAll("g.node").forEach((g) => {
      map[g.textContent.trim()] = g;
    });
    graphNodes = map;
    highlightGraph(null, "idle");
  } catch (e) {
    graphNodes = null;
  }
}

function highlightGraph(currentNode, status) {
  if (!graphNodes) {
    $("graph").textContent = currentNode ? `Stage: ${currentNode} (${status})` : "";
    return;
  }
  const idx = NODES.indexOf(currentNode);
  const allDone = status === "succeeded";
  NODES.forEach((name, i) => {
    const g = graphNodes[name];
    if (!g) return;
    g.classList.remove("done", "active", "pending");
    if (allDone || (idx >= 0 && i < idx)) g.classList.add("done");
    else if (idx === i) g.classList.add(status === "running" ? "active" : "done");
    else g.classList.add("pending");
  });
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
  currentJobId = id;
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
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  highlightGraph(job.current_node, job.status);
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}

function commonFields(fd) {
  fd.append("use_fake", $("use-fake").checked ? "true" : "false");
  fd.append("choices", JSON.stringify(collectChoices()));
  return fd;
}

let llmNodes = [];

async function loadLLMNodes() {
  const container = $("llm-nodes");
  container.innerHTML = "";
  let models = [];
  try {
    models = (await (await fetch("/api/models")).json()).models;
    llmNodes = (await (await fetch("/api/llm-nodes")).json()).nodes;
  } catch (e) {
    return; // leave empty; submitting with no choices keeps server defaults
  }
  for (const node of llmNodes) {
    const row = document.createElement("div");
    row.className = "llm-node";
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
    row.append(`${node.node}: model `, modelSel, " version ", verSel);
    container.appendChild(row);
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

async function start(url, fd) {
  setBusy(true);
  $("save").disabled = true;
  $("download").disabled = true;
  setSource("");
  $("error").textContent = "(none)";
  $("pdf").src = "about:blank";
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
  start("/api/jobs/sample", commonFields(new FormData()));
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

loadLLMNodes();
document.addEventListener("mermaid-ready", loadGraph);
