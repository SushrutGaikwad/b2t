# b2t

An AI-powered conversion pipeline that turns compiled LaTeX Beamer decks into
accessible Typst Touying PDFs. A deterministic LangGraph workflow does
everything that does not need a model; one LLM step, served by open-source
models (gpt-oss, Llama, Qwen, Gemma, Mistral) via OpenRouter, performs the
Beamer to Typst translation. Built for university faculty, with PDF/UA-1
tagging for blind and visually impaired readers as the driving goal.

## Contents

- [Architecture (v0)](#architecture-v0)
  - [Nodes](#nodes)
- [Models](#models)
- [Getting started](#getting-started)
  - [Requirements](#requirements)
  - [Setup](#setup)
  - [Verify](#verify)
- [Run (v0)](#run-v0)
- [Run the testing UI](#run-the-testing-ui)
- [Logs](#logs)

## Architecture (v0)

The pipeline is a linear LangGraph `StateGraph` over a single Pydantic
`PipelineState`. Everything that can be done without an LLM is done in plain
Python; the one LLM call handles only the Beamer to Touying translation. The
Typst compiler is the final arbiter of success.

```mermaid
flowchart TD
    start([START]) --> copy_input
    copy_input --> clean_build
    clean_build --> detect_main
    detect_main --> flatten
    flatten --> strip_overlays
    strip_overlays --> convert
    convert --> write_output
    write_output --> compile
    compile --> stop([END])

    classDef llm fill:#ffe0f0,stroke:#cc3399,color:#000;
    class convert llm;
```

The shaded `convert` node is the only LLM step; every other node is
deterministic.

### Nodes

1. `copy_input` (deterministic): Copies the read-only input deck into a fresh
   temporary working directory so the original is never mutated.
2. `clean_build` (deterministic): Deletes LaTeX build artifacts (`.aux`,
   `.log`, `.nav`, `.toc`, `.synctex.gz`, and similar) from the working copy.
3. `detect_main` (deterministic): Finds the single `.tex` that declares a
   Beamer document (`\documentclass`, `beamer`, `\begin{document}`). Fails
   loudly unless exactly one is found.
4. `flatten` (deterministic): Parses the include graph (`\input`, `\include`,
   `\includegraphics`), records referenced image files, and expands every
   include into one LaTeX string.
5. `strip_overlays` (deterministic): Removes Beamer overlay constructs
   (`\pause`, `\only`, `\uncover`, `\onslide`, and `<...>` specs) while keeping
   the wrapped content. The output never uses overlays.
6. `convert` (LLM): The single model call. Translates the flattened,
   overlay-free Beamer source into Typst Touying source, using the reference
   presentation and the Typst math guide as context. A markdown code fence
   wrapping the whole answer is stripped deterministically.
7. `write_output` (deterministic): Normalizes `image()` references to the
   copied filenames (with extension), writes `main.typ` to the output
   directory, and copies the referenced images alongside it.
8. `compile` (deterministic): Runs `typst compile` on `main.typ` and records
   the result (PDF path on success, error text on failure). v0 records the
   error but does not yet retry.

## Models

Conversions use open-weight LLMs only, so a university can later self-host the
same families on its own cluster behind any OpenAI-compatible endpoint (vLLM,
Ollama). The catalog in `src/b2t/config.py` lists the strongest open-weight
flagship of each family (Qwen 3.5 397B, Mistral Large 3, Llama 4 Maverick,
Gemma 4 31B) plus the sizes campuses most commonly self-host. The testing UI
shows each model's complexity, strength, and reasoning level in each node's
model dropdown; the default is `openai/gpt-oss-120b`.

## Getting started

### Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/): manages
  Python and all dependencies. Python 3.12 is fetched automatically if needed.
- [Typst CLI](https://github.com/typst/typst#installation) 0.14+ on PATH
  (`winget install Typst.Typst`, `brew install typst`, or
  `cargo install typst-cli`). Verify with `typst --version`.
- An OpenRouter API key, for real conversions. The pipeline runs offline with
  the fake converter (tests and the UI checkbox), but actual Beamer to Typst
  translation calls open-source models via OpenRouter.

No LaTeX installation is needed; input decks are already compiled.

### Setup

```bash
git clone https://github.com/SushrutGaikwad/b2t.git
cd b2t
uv sync
```

Create a `.env` file in the repo root:

```
OPENROUTER_API_KEY=sk-or-...
```

Optionally add `B2T_MODEL=...` to override the default model
(`openai/gpt-oss-120b`), or `B2T_BASE_URL=...` to point at any
OpenAI-compatible endpoint (for example a campus vLLM server).

### Verify

```bash
uv run pytest
```

All tests should pass. Typst integration tests are skipped unless the `typst`
CLI is installed.

## Run (v0)

```bash
uv run python -c "from b2t.app import convert_deck; convert_deck('tests/fixtures/sample_deck', 'out')"
```

Output is written to `out/` (`main.typ`, copied images, and `main.pdf` on
success).

## Run the testing UI

A thin browser UI for converting a deck folder and inspecting the result.

> This UI is for local development and testing only. It is a harness for
> exercising the pipeline and inspecting output, not the end-user product. A
> separate SaaS UI will be built later once the pipeline matures (see the
> roadmap in `CLAUDE.md`).

```bash
uv run uvicorn b2t.api.app:app --reload
```

Open http://127.0.0.1:8000. Click "Use sample deck" for a one-click run, or
pick a deck folder with the folder chooser. For each LLM node you can choose a
model and a prompt version; tick "use fake converter (offline)" to exercise the
pipeline without calling OpenRouter. The page shows per-node progress, the
model and prompt version each node used, the generated `main.typ` in an editor
(save to recompile), the compiled PDF, and any compile error. Click any pipeline
node to inspect the LangGraph state captured after that step (the accumulated
state, with the fields that node changed highlighted).

## Logs

The console shows INFO lines; the full DEBUG trail is written to
`logs/b2t.log` (rotated at 10 MB, kept 10 days, gitignored). Tracebacks omit
variable values so API keys never land in the logs.

---

Keywords: AI document conversion, LLM pipeline, LangGraph, generative AI,
open-source LLM, OpenRouter, gpt-oss, Llama, Qwen, Gemma, Mistral, vLLM,
Typst, Touying, LaTeX, Beamer, accessible PDF, PDF/UA, screen reader,
document accessibility, higher education.
