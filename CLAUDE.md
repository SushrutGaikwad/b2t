# b2t: Beamer to Touying Converter

## What this is
A pipeline that converts already-compiled LaTeX Beamer presentations into
accessible Typst Touying presentations (university theme), output as UA-1
tagged PDFs. Built for university faculty. The driving goal is accessibility
for blind and visually impaired readers: Beamer cannot provide tagging, Typst
can.

## Core principles (do not violate)
- No LaTeX, ever. Never install or invoke a LaTeX toolchain. Input decks are
  already compiled; we never recompile Beamer.
- Deterministic first. Anything doable in plain Python without an LLM must be
  done that way. LLMs are only for semantic translation, hard fixes, and
  alt-text. See the boundary below.
- The Typst compiler is ground truth. A conversion is not done until
  `typst compile` succeeds; compile errors feed back into a fix loop.
- Never mutate user input. Treat the uploaded directory as read-only; all work
  happens on a copy.
- No overlays in output. The generated Touying deck must never use
  overlay/pause functionality, regardless of the source.

## Deterministic vs LLM boundary
Deterministic (pure Python, no LLM, must be tested):
- build-file cleanup by extension (.aux .log .out .fls .fdb_latexmk .nav .snm
  .toc .vrb .synctex.gz etc.)
- main-file detection (file containing \documentclass{beamer} and
  \begin{document})
- include-graph parsing (\input \include \subfile \includegraphics
  \graphicspath \addbibresource \bibliography)
- flattening included .tex into one file (latexpand-style expansion or
  equivalent Python; fail loudly, never guess content)
- overlay stripping (\pause \onslide \only \uncover and <...> specs)
- loose package/feature heuristics for choosing which docs to load
  (over-inclusion is fine and cheap)
- citation command mapping, .bib parsing, file copying, invoking typst,
  parsing its errors

LLM only:
- Beamer to Touying semantic translation
- recognizing hand-written notation (manual derivative, unit, chemical
  formula) and routing it to the right package
- non-obvious compile-error fixes
- alt-text generation
- converting messy manually-written bibliographies into .bib

## Target Typst packages (pin these versions)
touying 0.7.3, physica 0.9.8, whalogen 0.3.0, cetz 0.5.2, fletcher 0.5.8,
lilaq 0.6.0, lovelace 0.3.1, theorion 0.6.0, subpar 0.2.2, plotsy-3d 0.2.1,
unify 0.8.1.

Use the preferred package for genuine instances of each feature (judgment, not
blind find-replace):
- physica: derivatives, integrals, vectors
- unify: units
- whalogen: chemistry
- lilaq: data-viz plots
- fletcher: node-and-arrow diagrams, graphs, flowcharts
- plotsy-3d: 3D plots
- lovelace: algorithms / pseudocode
- subpar: subfigures
- theorion: theorem, lemma, corollary, caution, warning, note environments
- cetz: any drawing not coverable by fletcher or lilaq

Docs live in files/md/pkg_docs/. Load on demand into the converter context,
only for detected features. Do NOT paste them into this file.

## Key resources
- files/reference/touying_reference_presentation.typ : the converter's primary
  reference. The converter consults this FIRST, before asking for any package
  docs.
- files/md/guides/math_equations_in_typst.md : Typst math syntax guide, fed to
  the convert node alongside the reference deck.
- files/md/guides/accessibility.md : Typst accessibility docs.
- files/md/guides/ua-1_accessibility_rules.md : hand-written rules for
  making a Touying deck UA-1 accessible (used by the tagging step).

## Stack & conventions
- Python via uv. Run with `uv run ...`; add deps with `uv add ...`. Never use
  pip or touch the venv directly.
- Orchestration: LangGraph. State is a single Pydantic model. HITL pauses use
  interrupts plus a persistent checkpointer (a professor may review hours
  later).
- Prefer structured output (Pydantic) for any LLM step returning more than
  free text.
- Keep every LLM call behind a small mockable interface so deterministic nodes
  never touch the network and tests stay cheap.
- Typst compilation via the `typst` Python package or `typst` CLI. No LaTeX
  dependency.
- A FastAPI browser UI (src/b2t/api/) is a development and testing harness for
  exercising the pipeline and inspecting output, not the end-user product; the
  SaaS UI is roadmap item 7.

## LLM access and prompt versioning
- All model calls go through the `LLMClient` Protocol
  (`complete(system, user, model)`) in src/b2t/llm.py. `OpenRouterClient` calls
  open-weight models via OpenRouter (or any OpenAI-compatible endpoint via
  `B2T_BASE_URL`); `FakeClient` serves tests and the offline UI checkbox. The
  model is chosen per call, never stored on the client.
- Prompts are versioned files at prompts/<node>/<version>.toml (keys:
  `description`, `system`, `user_template`). Templates use `{{token}}` markers
  inside literal `'''` TOML strings, so LaTeX/Typst braces and `$` need no
  escaping. The registry (src/b2t/prompts.py) lists nodes and versions and reads
  the per-node default from prompts/defaults.json.
- Every LLM node is a thin wrapper over `run_prompt(state, node_name, client,
  values)` (src/b2t/nodes/_llm.py): it resolves the node's model and prompt
  version from `state.llm_choices` (falling back to `B2T_MODEL`/`DEFAULT_MODEL`
  and the registry default), renders the template, calls the client, and records
  provenance in `state.llm_runs`. Add a new LLM node by writing a prompt file, a
  prompts/defaults.json entry, and a thin node; the testing UI exposes per-node
  model and prompt-version pickers automatically from /api/llm-nodes.

## Current scope (v0)
Smallest end-to-end pipeline on PLAIN decks only: title, sections, text,
bullet lists, basic math, included images. No viz packages, no tagging, no
HITL, no bibliography yet. Pipeline: copy input, clean build files, detect main
.tex, flatten, strip overlays, convert with one LLM node, write output dir,
compile (errors recorded; no retry loop yet). Prompt versioning and per-node
model + prompt-version selection are already in place as the foundation for the
multi-LLM roadmap, even though `convert` is still the only LLM node. Get a
boring deck all the way through before adding anything.

## Roadmap (one at a time, roughly this order)
1. v0 plain-deck pipeline above, with tests on a sample fixture.
2. Math/units/chem/theorem substitutions (physica, unify, whalogen, theorion).
3. UA-1 tagging + alt-text generation.
4. Human-in-the-loop review (approve / feedback / regenerate).
5. Bibliography normalization (always emit a .bib).
6. Visualization translation (cetz, fletcher, lilaq, plotsy-3d) with a
   dedicated compile-and-fix sub-agent.
7. SaaS wrapper: upload, sandboxed compile, download, plus hardening for
   untrusted archives.

## Workflow notes for Claude Code
- Plan before coding on anything non-trivial; show the plan first.
- Build and commit one node at a time. Deterministic nodes come before LLM
  nodes within each increment.
- Every deterministic node needs a test against tests/fixtures before moving
  on.
- Do not expand scope beyond "Current scope" without being asked.
