# Appendix Handling and `<touying:hidden>` - Design

Date: 2026-06-20
Status: proposed

## 1. Motivation

Beamer marks the start of backup material with `\appendix`. By convention every
frame after `\appendix` is an appendix slide and is kept out of the table of
contents. b2t does not understand `\appendix` today: the deterministic splitter
ignores the command, so the appendix frames are filed under whatever the last
`\section` was and they show up in the outline like ordinary content. The
`deck3` fixture already exhibits this: its `Backup: Additional Material` frame
(after `\appendix`, with no section of its own) currently lands under the `Math`
section.

Touying's equivalent of `\appendix` is a one-time `#show: appendix`, and the
convention of keeping a heading out of the outline is expressed by labelling it
`<touying:hidden>`. This design makes b2t:

- detect the `\appendix` region and render the appendix frames after the
  references slide, introduced by `#show: appendix`;
- apply `<touying:hidden>` to titles the author meant to keep out of the table
  of contents, judged from deterministic Beamer signals.

## 2. Scope

In scope:

- Detect `\appendix` in the document body and tag every frame after it as an
  appendix frame.
- Assemble the appendix frames after the references / bibliography / thank-you
  block, introduced by a single `#show: appendix`.
- Apply `<touying:hidden>` to appendix section headings (`=`) and appendix frame
  titles (`==`); synthesize a single `= Appendix <touying:hidden>` wrapper when
  the appendix frames carry no `\section` of their own.
- Apply `<touying:hidden>` to a body section heading that came from a starred
  `\section*` (Beamer already keeps starred sections out of the TOC); this is the
  only other deterministic "hide from TOC" signal, and realizes the general rule.

Out of scope (deliberately deferred):

- Any LLM judgment about which titles to hide. All hiding is deterministic from
  `\appendix` and `\section*`.
- `\subsection` / `\subsection*` mapping to their own headings (b2t does not emit
  subsection structure today).
- Restructuring the convert / preview / review cycle. Appendix frames are
  converted and reviewed exactly like body frames; only assembly reorders and
  decorates them.
- Appendix-specific numbering packages (`appendixnumberbeamer` in deck3). The
  preamble is passed to the model as context only and needs no translation.

## 3. Decisions already made (with rationale)

| Decision | Choice | Why |
| --- | --- | --- |
| Hidden-TOC logic | Purely deterministic from `\appendix` and starred `\section*`; no LLM | Those two signals fully express the author's TOC intent in the source; keeps the rule testable and aligns with the project's deterministic-first boundary |
| Appendix frame routing | Keep appendix frames in the single `frames` list, tagged with `is_appendix`; `assemble` reorders and decorates them | The convert / preview / review cycle and the `frames` / `converted_frames` index parallelism stay untouched; appendix slides are still reviewed like any frame |
| Order relative to references | References + bibliography + `Thank you!` first, then `#show: appendix` and the appendix frames | Matches the usual talk convention that backup slides live past the closing slide; the reviewer answered this directly |
| No appendix section in source | Synthesize one `= Appendix <touying:hidden>` wrapper | Touying appendix slides read better under a section heading, and it matches the canonical example; deck3 needs exactly this |
| Appendix frame titles | Hide the `==` title as well as the `=` section | The convention is that the whole appendix is out of the TOC; the canonical example hides both levels |
| Body frame titles | Leave visible; only the `=` section heading of a starred section is hidden | Beamer frame titles are never in the TOC anyway and are slide-level in Touying; only sections appear in the outline |

## 4. Architecture overview

The graph is unchanged:

```
... -> split_deck -> convert -> preview -> review (cycle over frames)
   -> assemble -> write_output -> compile -> END
```

`\appendix` detection is added to the deterministic splitter (`latex/split.py`),
two facts are added to `FrameUnit`, and all the new rendering lives in the
deterministic assembler (`typst_scaffold.py`). No node wiring, no prompt, and no
LLM behavior changes. Because `preview` reuses `typst_scaffold.assemble`, the
appendix ordering and hiding appear in the review preview for free.

## 5. State model (`src/b2t/state.py`)

`FrameUnit` gains two fields:

```python
class FrameUnit(BaseModel):
    raw: str
    section: str | None = None
    is_appendix: bool = False      # frame appears after \appendix
    section_starred: bool = False  # the enclosing section was \section*
```

`PipelineState` is unchanged: the new facts ride on `FrameUnit`, which already
flows through `split_deck`, the convert cycle, and `assemble`. `converted_frames`
stays parallel to `frames` by index.

## 6. Components

### 6.1 Split (`src/b2t/latex/split.py`)

`split_frames(body) -> (frames, has_toc)` keeps its signature. Changes inside:

1. Extend the token regex so it also matches `\appendix` and captures a section's
   optional `*`:
   - section alternative captures `star` (`\section(?P<star>\*)?\{...\}`) and the
     name;
   - a new `appendix` alternative matches `\appendix` at a word boundary, so it
     does not match `\appendixnumberbeamer` (and the preamble is not scanned
     anyway).
2. Walk the body tracking `in_appendix` (starts `False`), the current section,
   and whether that section was starred.
   - On the `\appendix` token: set `in_appendix = True` and reset the current
     section to `None`, so appendix sections start fresh and a pre-appendix
     section never carries into the appendix.
   - On a section token: set the current section name and `section_starred =
     bool(star)`.
   - On a frame token: build `FrameUnit(raw, section=current_section,
     is_appendix=in_appendix, section_starred=section_starred)`. Existing
     exclusions (`\titlepage`, `\tableofcontents`, `\printbibliography`) are
     unchanged.

Pre-appendix frames are tagged `is_appendix=False`; everything after `\appendix`
is `is_appendix=True`. The `split_deck` node is unchanged.

### 6.2 Assemble (`src/b2t/typst_scaffold.py`)

`assemble(meta, aspect_ratio, has_toc, frames, converted, bib_name)` keeps its
signature. It now:

1. Pairs `frames` with `converted` (the existing `zip`, which truncates to the
   shorter list, so the partial lists `preview` passes keep working), then
   partitions the pairs into body pairs (`not is_appendix`) and appendix pairs.
2. Emits, in order:
   - header (unchanged);
   - optional outline when `has_toc` (unchanged);
   - the body, from the body pairs;
   - the references / bibliography / `Thank you!` block when `bib_name` is set
     (unchanged `_bibliography_block`);
   - the appendix block, from the appendix pairs, when there are any.

`_body` change: when a body frame's section changes and that section is starred
(`section_starred`), emit `= <section> <touying:hidden>` instead of
`= <section>`. Body frame titles (`==`) are left as the model produced them.

New `_appendix_block(pairs) -> str`:

- emits `#show: appendix` once, before any appendix heading;
- walks the appendix pairs tracking the current section; on a section change
  emits `= <section> <touying:hidden>`;
- if an appendix frame has no section and no appendix section has been emitted
  yet, emits a single `= Appendix <touying:hidden>` wrapper;
- for each appendix frame, appends ` <touying:hidden>` to its converted body's
  first level-2 heading via a small `_hide_frame_title` helper.

New `_hide_frame_title(typ) -> str`: finds the first line whose stripped text
starts with `==` but not `===`, and appends ` <touying:hidden>` if it is not
already present; returns the text otherwise unchanged. This is the deterministic
way the appendix frame title is hidden without the model having to cooperate.

### 6.3 Unchanged

`convert_frame`, `review`, `preview` (reuses `assemble`), `split_deck`,
`write_output`, `compile`, `graph.py`, the prompts, and the `LLMClient` seam are
all untouched.

## 7. Data flow (one run, deck3)

1. `split_deck` produces `frames` where the `Introduction` and `Math` frames are
   `is_appendix=False` and the `Backup: Additional Material` frame is
   `is_appendix=True` with `section=None`.
2. The convert cycle converts each frame, including the appendix frame, into
   `== Title` + body, appended to `converted_frames` in order.
3. `assemble` emits header, body (the two sections), then the references /
   bibliography / `Thank you!` block, then `#show: appendix`,
   `= Appendix <touying:hidden>`, and the backup frame with its `==` title
   hidden.
4. `write_output` and `compile` run unchanged.

The resulting tail of `main.typ`:

```
= References

== References <touying:hidden>

#bibliography("references.bib", title: none, style: "apa")

#slide(config: (
  page: (header: none, footer: none),
))[
  #set align(center + horizon)
  #text(size: 2.5em)[Thank you!]
]

#show: appendix

= Appendix <touying:hidden>

== Backup: Additional Material <touying:hidden>
...
```

## 8. Error handling

- No new failure modes. `\appendix` is optional; its absence leaves every frame
  `is_appendix=False` and the output identical to today.
- An empty appendix (an `\appendix` with no following frames) yields no appendix
  block; the references / thank-you block is still the deck's end.
- Frame-title hiding is best-effort: if the model emitted no `==` heading for an
  appendix frame, `_hide_frame_title` returns the body unchanged rather than
  raising. The `= ... <touying:hidden>` section still keeps the slide out of the
  TOC.

## 9. Testing

- `tests/test_split.py`: `\appendix` tags every following frame `is_appendix` and
  resets the section; pre-appendix frames stay `is_appendix=False`; a starred
  `\section*` sets `section_starred` while a plain `\section` does not; the
  `\appendix` token does not match `\appendixnumberbeamer`.
- `tests/test_scaffold.py`: the appendix block emits `#show: appendix`, a hidden
  `= Appendix`, and a hidden `==` title, and lands after the bibliography /
  thank-you block; a starred body section heading is hidden while a plain one is
  not; `_hide_frame_title` hides only the first `==` and is idempotent; a deck
  with no appendix is byte-for-byte unchanged from today.
- `tests/test_state.py`: the two new `FrameUnit` fields default correctly.
- End-to-end on `deck3` under `FakeClient` (`tests/test_graph.py` or
  `tests/test_nodes.py`): the assembled deck contains `#show: appendix` after the
  bibliography and the backup frame is no longer under the `Math` section.
- Integration (typst present): deck3 assembles and compiles.

All non-integration tests stay offline via `FakeClient`.

## 10. Known limitations / deferred

- `\subsection*` is not handled (b2t emits no subsection headings yet).
- Mixed appendix sectioning (some appendix frames under a `\section`, some not)
  uses the same "synthesize `= Appendix` until a real appendix section appears"
  rule; the in-scope fixture (deck3) has no appendix sections, so the common case
  is a single synthesized wrapper.
- Hiding non-structural titles that an author "meant" to hide without using
  `\appendix` or `\section*` is out of scope; only those two deterministic
  signals drive hiding.

## 11. Future extensions (not built now)

- LLM-judged hiding for decks that express appendix intent informally (for
  example a section literally named "Backup" without `\appendix`).
- `\subsection` / `\subsection*` heading support, with the same hiding rule.
