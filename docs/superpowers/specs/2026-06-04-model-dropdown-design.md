# Model Dropdown Design

Date: 2026-06-04
Status: Approved (design), pending implementation plan

## Overview

Replace the free-text "model override" box in the testing frontend with a
dropdown of known OpenAI model ids, so a typo cannot select a non-existent
model. The list of models is defined once in `config.py` (next to the existing
default) and served to the page by a small endpoint.

This builds on the existing FastAPI testing frontend (`src/b2t/api/`).

## Goals

- Pick the conversion model from a fixed dropdown instead of typing it.
- Keep one source of truth for the model list and the default (in `config.py`).
- Preserve the current behavior of leaving the model unset (fall back to the
  `OPENAI_MODEL` env var, then the config default).

## Non-goals

- No per-model pricing or capability display.
- No live fetching of the model catalogue from the OpenAI API.
- No validation beyond restricting to the fixed list.
- No change to the existing conversion pipeline or the `/api/jobs` flow.

## Current OpenAI text models (June 2026)

The dropdown lists the current GPT-5 family ids, cheapest first:
`gpt-5.4-nano` (default), `gpt-5.4-mini`, `gpt-5.4`, `gpt-5.4-pro`, `gpt-5.5`.

## Approved decisions

1. Config-driven list. `OPENAI_MODELS` lives in `config.py`; a `GET /api/models`
   endpoint serves it plus the default. The page builds the dropdown from that.
2. A plain `<select>` (a fixed list, no free text), so a typo is impossible.
3. A first `(default)` option with an empty value preserves the existing
   fallback chain (env var `OPENAI_MODEL`, then the config default).

## Architecture

- `src/b2t/config.py`: add
  `OPENAI_MODELS = ("gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4", "gpt-5.4-pro", "gpt-5.5")`.
  `DEFAULT_OPENAI_MODEL` stays `"gpt-5.4-nano"` (also the first entry).
- `src/b2t/api/schemas.py`: add a `ModelsView` model
  (`models: list[str]`, `default: str`).
- `src/b2t/api/app.py`: add `GET /api/models` returning
  `ModelsView(models=list(OPENAI_MODELS), default=DEFAULT_OPENAI_MODEL)`,
  registered with the other routes before the static mount.
- `src/b2t/api/static/index.html`: replace the model `<input type="text">` with
  an empty `<select id="model">`.
- `src/b2t/api/static/app.js`: on load, fetch `/api/models` and populate the
  select: first an option labelled `(default)` with value `""`, then one option
  per model id, with the default id labelled `<id> (default)`. The existing
  `commonFields` already reads `$("model").value`, so submission is unchanged.

## Data flow

1. Page loads, JS calls `GET /api/models`, builds the `<select>` options.
2. The user picks a model (or leaves `(default)`).
3. On run, `commonFields` appends `$("model").value` (a model id, or `""`) to the
   form, exactly as the text box did.
4. The backend `_make_converter` passes a non-empty value to
   `OpenAIConverter(model=...)`; an empty value keeps the existing env-var and
   config-default fallback.

## Error handling

- If `GET /api/models` fails (unlikely on localhost), the select stays empty
  except for the `(default)` option the JS can seed before the fetch, so runs
  still work with the default model.

## Testing approach

- Backend: a `TestClient` test that `GET /api/models` returns 200 with `models`
  equal to the configured list and `default` equal to `DEFAULT_OPENAI_MODEL`.
  Offline; no network.
- Static markup: extend the existing page-serves test to assert the page
  contains `<select id="model"`.
- Existing tests stay green.

## Future seams

- When OpenAI ships a new model, update the one `OPENAI_MODELS` tuple.
- A live `/v1/models` fetch could later replace the static list if desired, but
  is out of scope here.
