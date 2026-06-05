const NODES = [
  "copy_input", "clean_build", "detect_main", "flatten",
  "strip_overlays", "convert", "write_output", "compile",
];
const TERMINAL = ["succeeded", "compile_failed", "failed"];

const $ = (id) => document.getElementById(id);

function renderNodes(currentNode, status) {
  const list = $("nodes");
  list.innerHTML = "";
  const idx = NODES.indexOf(currentNode);
  const allDone = status === "succeeded";
  NODES.forEach((name, i) => {
    const li = document.createElement("li");
    li.textContent = name;
    if (allDone || (idx >= 0 && i < idx)) li.classList.add("done");
    else if (idx === i) li.classList.add(status === "running" ? "active" : "done");
    list.appendChild(li);
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

async function finish(id, job) {
  setBusy(false);
  const typ = await fetch(`/api/jobs/${id}/typ`);
  $("typ").textContent = typ.ok ? await typ.text() : "(no typst output)";
  $("pdf").src = job.has_pdf ? `/api/jobs/${id}/pdf` : "about:blank";
  $("error").textContent = job.error || "(none)";
}

async function poll(id) {
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  renderNodes(job.current_node, job.status);
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}

function commonFields(fd) {
  fd.append("use_fake", $("use-fake").checked ? "true" : "false");
  fd.append("model", $("model").value);
  return fd;
}

async function start(url, fd) {
  setBusy(true);
  $("typ").textContent = "(running)";
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
