# b2t

Converts compiled LaTeX Beamer decks into accessible Typst Touying PDFs.

## Develop

```bash
uv run pytest
```

Typst integration tests are skipped unless the `typst` CLI is installed.

## Run (v0)

Requires `OPENAI_API_KEY` in `.env` and the `typst` CLI on PATH.

```bash
uv run python -c "from b2t.app import convert_deck; convert_deck('tests/fixtures/sample_deck', 'out')"
```

Output is written to `out/` (`main.typ`, copied images, and `main.pdf` on success).
