# Open-Source Models via OpenRouter Design

Date: 2026-06-05
Status: Approved (design), pending implementation plan

## Overview

Replace the proprietary OpenAI models with open-source models served through
OpenRouter. The university deploying b2t will run an open-source LLM on its
local cluster behind an OpenAI-compatible endpoint; developing against open
models avoids overfitting the conversion prompt to a proprietary family. The
dropdown in the testing frontend lists the open-source families US
universities most commonly self-host (Llama, gpt-oss, Qwen, Gemma, Mistral),
each labelled with its complexity, strength, and reasoning level so the user
knows roughly what to expect.

This builds on the existing converter seam (`ConverterLLM` Protocol in
`src/b2t/llm.py`) and the model dropdown
(`docs/superpowers/specs/2026-06-04-model-dropdown-design.md`).

## Goals

- All conversion calls go to OpenRouter using `OPENROUTER_API_KEY` (already in
  `.env`).
- The dropdown lists open-source models only, each labelled with complexity
  (size/architecture), strength (tier), and reasoning level.
- Use Chat Completions, the dialect every host and every campus vLLM/Ollama
  endpoint speaks, instead of the OpenAI-only Responses API.
- One env var (`B2T_BASE_URL`) is the future migration path to the
  university's own cluster endpoint.

## Non-goals

- No Groq integration (key stays in `.env`, unused) and no per-model provider
  routing; OpenRouter is the single provider.
- No live fetching of the OpenRouter catalogue; the list is static in
  `config.py`.
- No pricing display, no token accounting, no streaming.
- No change to the pipeline graph, the `/api/jobs` flow, or `FakeConverter`.

## Model catalog

Ordered strongest first. IDs verified against the live OpenRouter API
(2026-06-05). Default: `openai/gpt-oss-120b`.

| OpenRouter ID | Complexity | Strength | Reasoning |
|---|---|---|---|
| `openai/gpt-oss-120b` (default) | 120B MoE | frontier | high |
| `qwen/qwen3-32b` | 32B dense | strong | hybrid |
| `meta-llama/llama-3.3-70b-instruct` | 70B dense | strong | none |
| `meta-llama/llama-4-scout` | 109B MoE | strong | none |
| `google/gemma-4-26b-a4b-it` | 26B MoE | capable | none |
| `mistralai/mistral-small-2603` | 24B dense | capable | none |
| `openai/gpt-oss-20b` | 21B MoE | capable | medium |
| `meta-llama/llama-3.1-8b-instruct` | 8B dense | basic | none |

The 8B Llama stays deliberately: it shows what a weak model does to
conversion quality and is the cheapest real-network smoke test.

## Approved decisions

1. OpenRouter only. One key, one base URL; it carries every family above,
   including Gemma and Mistral, which Groq does not host.
2. All metadata in the dropdown option label, for example
   `gpt-oss-120b - frontier, high reasoning, 120B MoE`. No extra UI panel.
3. Minimal in-place swap: rename `OpenAIConverter` to `OpenRouterConverter`,
   keep the OpenAI SDK (pointed at OpenRouter), keep the `ConverterLLM`
   Protocol. No provider registry, no new abstraction.
4. The catalog includes the most common open-source families US universities
   self-host, kept to eight entries.

## Architecture

- `src/b2t/config.py`: replace `DEFAULT_OPENAI_MODEL` and `OPENAI_MODELS`
  with:
  - `class ModelInfo(BaseModel)`: `id`, `complexity`, `strength`,
    `reasoning`, and a `label` property composing
    `"<short-name> - <strength>, <reasoning> reasoning, <complexity>"`
    (reasoning `none` renders as `no reasoning`). Short name is the ID minus
    the author prefix.
  - `OPEN_MODELS: tuple[ModelInfo, ...]` with the eight entries above.
  - `DEFAULT_MODEL = OPEN_MODELS[0].id`.
  - `OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"`.
- `src/b2t/llm.py`: `OpenAIConverter` becomes `OpenRouterConverter`:
  - `OpenAI(base_url=os.getenv("B2T_BASE_URL", OPENROUTER_BASE_URL),
    api_key=os.environ["OPENROUTER_API_KEY"])`; a missing key raises
    `KeyError` at construction, surfacing in the job error field.
  - Model fallback chain: constructor arg, then `B2T_MODEL` env var, then
    `DEFAULT_MODEL`.
  - `convert()` uses `chat.completions.create` with `_INSTRUCTIONS` as the
    system message and the same composed reference/guides/source user
    message; returns `choices[0].message.content`.
  - `_INSTRUCTIONS` and `FakeConverter` unchanged.
- `src/b2t/api/schemas.py`: `ModelsView` becomes
  `models: list[ModelOption]` plus `default: str`, where `ModelOption` is
  `{id: str, label: str}`.
- `src/b2t/api/app.py`: `_make_converter` constructs `OpenRouterConverter`;
  `GET /api/models` serves the catalog as `ModelOption`s.
- `src/b2t/api/static/app.js`: `loadModels()` sets option `value` to the id
  and text to the label, appending ` (default)` to the default entry. The
  leading empty `(default)` option and `commonFields` stay as they are.
- `src/b2t/app.py`: `convert_deck` defaults to `OpenRouterConverter()`.
- `README.md`: setup instructions name `OPENROUTER_API_KEY` and the optional
  `B2T_MODEL` / `B2T_BASE_URL` overrides; the OpenAI references go away.

## Data flow

1. Page loads, JS fetches `/api/models`, builds the dropdown from
   `{id, label}` pairs.
2. The user picks a model (or leaves `(default)`); `commonFields` submits the
   id exactly as before.
3. `_make_converter` passes a non-empty id to `OpenRouterConverter(model=...)`;
   empty keeps the env-var/config-default chain.
4. `convert_node` calls `llm.convert(...)`, which sends one Chat Completions
   request to OpenRouter.

## Error handling

- Missing `OPENROUTER_API_KEY`: construction raises immediately with a clear
  message; the job records `failed` and the UI shows it. No retry logic.
- OpenRouter/HTTP errors propagate as exceptions from the SDK and land in the
  same job error field, as today.
- No pre-validation of model ids; an invalid id surfaces as the provider's
  error.

## Testing approach

- `test_config.py`: catalog is non-empty, ids are unique, default is the
  first entry, every entry has the three metadata fields, label composition
  matches the agreed format.
- `test_llm.py`: with a mocked OpenAI client, `OpenRouterConverter.convert`
  sends the system instructions and composed user message and returns the
  message content; model fallback chain (arg beats env beats default);
  missing key raises. No network.
- `test_api_app.py`: `GET /api/models` returns the new shape with labels and
  the default id; page-serves test unchanged.
- All existing pipeline and node tests keep using `FakeConverter` and stay
  green.

## Future seams

- University cluster: set `B2T_BASE_URL` to the campus vLLM/Ollama endpoint
  and `B2T_MODEL` to whatever it serves; `OPENROUTER_API_KEY` then carries
  that endpoint's token. Rename to a neutral env var at that point if it
  bothers anyone.
- New models: edit the one `OPEN_MODELS` tuple.
- The compile-fix loop (roadmap) will reuse the same converter seam.
