# b2t v0 Pipeline Design

Date: 2026-06-03
Status: Approved (design), pending implementation plan

## Overview

v0 is the smallest end-to-end pipeline that takes an already-compiled Beamer
deck directory and produces a Typst Touying deck compiled to PDF. It handles
PLAIN decks only: title, sections, text, bullet lists, basic math, and included
images. It runs as a linear LangGraph with one LLM call for the Beamer to
Touying translation; everything else is deterministic Python.

This document captures the approved module layout, the single Pydantic state
model, and the LangGraph node graph. It does not contain implementation code.

## Scope

In scope for v0:
- Copy the input directory to a working copy (input is read-only).
- Remove build files by extension.
- Detect the main `.tex` file.
- Parse the include graph and flatten includes into one LaTeX source.
- Strip overlays.
- Convert to Typst with a single LLM call.
- Write the output directory (Typst source plus copied images).
- Compile once with the `typst` CLI and report the result.

Out of scope for v0 (later roadmap items):
- LLM-based compile-error fixing / fix loop.
- Visualization packages (cetz, fletcher, lilaq, plotsy-3d).
- UA-1 tagging and alt-text generation.
- Human-in-the-loop review and any persistent checkpointer.
- Bibliography normalization.
- Math/units/chem/theorem package substitutions (physica, unify, whalogen,
  theorion).
- The SaaS wrapper.

## Approved decisions

1. No LLM fix loop in v0. Exactly one LLM call (the conversion). Compile runs
   once; on failure the typst error is surfaced and the run stops. This is a
   deliberate, approved deviation from the literal "compile-fix loop" wording in
   CLAUDE.md, deferred to a later increment.
2. Typst is invoked via the `typst` CLI as a subprocess. This matches the
   `typst compile --pdf-standard ua-1` invocation needed later for tagging.
3. v0 is stateless: a plain compiled `StateGraph` with no checkpointer. A
   persistent checkpointer arrives with HITL (roadmap item 4).
4. LLM backend is OpenAI (an `OPENAI_API_KEY` is present in a gitignored
   `.env`), behind a mockable interface so deterministic nodes never touch the
   network.

## Module layout

Pure deterministic logic (`latex/`, no LangGraph, no state, network-free) is
separated from thin node adapters (`nodes/`, state in and state out). This keeps
the deterministic logic isolated and cheaply testable, and supports building and
committing one node at a time.

```
src/b2t/
  __init__.py
  state.py            # PipelineState: the single Pydantic state model
  config.py           # BUILD_FILE_EXTENSIONS, typst package pins, default filenames
  graph.py            # build_graph(llm) -> compiled StateGraph; wires nodes + edges
  app.py              # convert(input_dir, output_dir, llm) entrypoint: seeds state, runs graph
  llm.py              # ConverterLLM protocol + OpenAIConverter + FakeConverter
  typst_runner.py     # compile(typ_path) -> CompileResult, shells out to `typst`, parses errors
  latex/              # pure deterministic logic (tested directly, no state)
    __init__.py
    cleanup.py        # list/remove build files by extension
    detect.py         # find_main_tex (\documentclass{beamer} + \begin{document})
    includes.py       # parse \input \include \includegraphics \graphicspath -> refs
    flatten.py        # expand includes into one LaTeX string; fail loudly if a file is missing
    overlays.py       # strip \pause \onslide \only \uncover and <...> specs
  nodes/              # thin LangGraph adapters: state -> {update}
    __init__.py
    copy_input.py     # copy input dir to a work dir (never mutate input)
    clean_build.py    # -> latex.cleanup
    detect_main.py    # -> latex.detect
    flatten.py        # -> latex.includes + latex.flatten
    strip_overlays.py # -> latex.overlays
    convert.py        # the ONE LLM node -> llm.ConverterLLM
    write_output.py   # create output dir, write main.typ, copy referenced images
    compile.py        # -> typst_runner.compile
```

Dependency injection: `build_graph(llm)` binds the `convert` node to a
`ConverterLLM` via `functools.partial`. Deterministic nodes never import the
LLM, and tests pass a `FakeConverter`.

## State model

A single `PipelineState`, fields grouped by the stage that fills them. v0 is
stateless, so there are no JSON serialization constraints and `Path` is used
directly. Each node returns a partial update, and the explicit per-stage fields
make each increment independently assertable in tests.

```python
class PipelineState(BaseModel):
    # inputs (seeded by app.py)
    input_dir: Path                       # original upload, treated read-only
    output_dir: Path                      # where the final deck is written

    # working copy
    work_dir: Path | None = None          # the mutable copy of input_dir

    # deterministic discoveries
    removed_build_files: list[Path] = []
    main_tex: Path | None = None
    included_tex: list[Path] = []         # resolved \input/\include targets
    image_files: list[Path] = []          # resolved \includegraphics targets
    flattened_tex: str | None = None      # single merged LaTeX source
    stripped_tex: str | None = None       # after overlay removal (LLM input)

    # conversion (the one LLM step)
    typst_source: str | None = None       # LLM output
    typst_path: Path | None = None        # main.typ written into output_dir

    # compile (ground truth)
    compiled: bool = False
    pdf_path: Path | None = None
    compile_error: str | None = None      # set on failure; surfaced, not retried in v0
```

Fatal deterministic conditions (no main `.tex`, a referenced `\input` file
missing) raise rather than setting a field, which is the "fail loudly, never
guess" behavior. `compile_error` is the one non-fatal recorded outcome; `app.py`
decides whether to raise or report it.

## Node graph

Fully linear, no conditional edges and no loop. The Typst source is written to
disk before compile because the `typst` CLI compiles a file.

```
START
  -> copy_input        copy input_dir -> work_dir
  -> clean_build       remove .aux .log .nav .out .toc .snm .vrb ... from work_dir
  -> detect_main       set main_tex
  -> flatten           parse includes (tex + images), merge -> flattened_tex
  -> strip_overlays    flattened_tex -> stripped_tex
  -> convert           [LLM] stripped_tex + reference deck -> typst_source
  -> write_output      mkdir output_dir, write main.typ, copy image_files
  -> compile           `typst compile output_dir/main.typ` -> pdf_path | compile_error
  -> END
```

Edges:

| Edge | From | To |
|------|------|----|
| 1 | START | copy_input |
| 2 | copy_input | clean_build |
| 3 | clean_build | detect_main |
| 4 | detect_main | flatten |
| 5 | flatten | strip_overlays |
| 6 | strip_overlays | convert |
| 7 | convert | write_output |
| 8 | write_output | compile |
| 9 | compile | END |

Notes:
- `flatten` uses `latex/includes.py` to record both `included_tex` (to expand)
  and `image_files` (so `write_output` knows what to copy).
- `convert` consults `files/reference/touying_reference_presentation.typ` first,
  per CLAUDE.md. For v0 it returns a plain Typst string. The step moves to
  structured Pydantic output when it returns more than the source (for example
  alt-text later).

## Testing approach

- One test file per `latex/` module against `tests/fixtures/sample_deck`:
  cleanup, detect, includes, flatten.
- `strip_overlays`: the sample deck has no overlays, so a small dedicated
  fixture (or inline string fixture) with `\pause` and `\only<2>` is added for
  this node.
- `convert`: tested with `FakeConverter` (no network).
- Graph: an end-to-end test with `FakeConverter`.
- `compile`: needs the `typst` binary, so it is marked integration and skipped
  when `typst` is absent.

## Resolved review items

- A small overlay fixture is added so `strip_overlays` can be tested.
- The `convert` output stays a plain string for v0 (single text blob). The
  Pydantic wrapper is introduced when the step returns more than free text.
```
