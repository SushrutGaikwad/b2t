# Rules for Making a Typst Touying Presentation PDF/UA-1 Accessible

These rules tell you how to take any Typst presentation built with the **Touying** package and rewrite it so that it compiles to a **PDF/UA-1** compliant file. Apply every rule that is relevant to the source file. Do not change the visual appearance, the wording of body text, or the structure of slides beyond what these rules require.

---

## 0. Background you must understand first

PDF/UA-1 is the "Universal Access" PDF standard. In Typst it is turned on at export time:

```sh
typst compile --pdf-standard ua-1 presentation.typ
```

(or via the "Export as PDF" dialog in the web app). Key facts that drive every rule below:

1. Typst **fails the compile and produces no PDF** if a critical accessibility issue is found. Missing alternative descriptions are critical issues. So the rewrite must be complete, not partial.
2. PDF/UA-1 **enforces alternative descriptions for every image and every piece of mathematics**, requires a document title, requires a declared document language, and requires a correct heading hierarchy and properly structured tables.
3. Typst writes accessibility tags automatically from its **semantic elements** (headings, `figure`, `table`, `list`, `enum`, `link`, etc.). The job of the rewrite is therefore narrow: keep using real semantic elements, and **supply the descriptions Typst cannot generate by itself**, which are alt text for math, images, and drawn graphics.
4. `math.equation.alt`, `figure.alt`, and `image.alt` are the parameters that carry these descriptions. They require a recent Typst version (the `math.equation` `alt` parameter needs Typst 0.14 or newer). Assume the user has a compatible compiler.

**The single most important rule:** every `$...$` math expression and every image or drawn graphic must carry a human-language `alt` description after the rewrite. Nothing is too small to skip, not even a lone `$x$`.

---

## 1. Document-level requirements

1.1. **A title must be set.** Confirm `config-info(...)` inside the theme call contains a non-empty `title:`. If it is missing, add one. The title becomes the PDF document title that UA-1 requires.

1.2. **A language must be set.** Confirm `#set text(... lang: "en", region: "US")` (or the correct language and region) exists. If absent, add `lang`. UA-1 requires the document's natural language to be declared.

1.3. Do not disable tagging. Never add `--no-pdf-tags`. Never replace semantic elements with manually positioned boxes that lose their meaning.

---

## 2. Mathematics (the largest and most important change)

Every mathematical expression, whether displayed or inline, must be wrapped so it carries an `alt` description. A bare `$...$` is **not** accessible on its own.

### 2.1. The transformation

Replace every bare equation with a `#math.equation(...)` call that supplies `alt` and the correct `block` value.

**Displayed (block) equations** use `block: true`:

```typst
// BEFORE
$ a^2 + b^2 = c^2. $

// AFTER
#math.equation(
  alt: "a squared plus b squared equals c squared",
  block: true,
  $ a^2 + b^2 = c^2. $
)
```

**Inline equations** use `block: false`:

```typst
// BEFORE
Inline math equation: $a^2 + b^2 = c^2$.

// AFTER
Inline math equation: #math.equation(alt: "a squared plus b squared equals c squared", block: false, $ a^2 + b^2 = c^2 $).
```

### 2.2. Rules that apply to every equation

- **Wrap all of them, no exceptions.** Even single symbols such as `$X$`, `$a$`, `$x$`, `$-1$` must become `#math.equation(alt: "...", block: false, $...$)`. In algorithms and prose these tiny inline bits are the easiest to miss; do not miss them.
- **Match `block` to the original rendering.** If the original used display math (`$ ... $` on its own line, or any equation you want centered and on its own line), use `block: true`. If it was inline within a sentence, use `block: false`.
- **Preserve labels.** If the original equation had a label such as `<eq:pythagorean_theorem>`, keep that label immediately after the closing `)` of the `#math.equation(...)` call, exactly where it was relative to the equation.
- **Preserve surrounding context blocks.** Numbering wrappers like `#[ #set math.equation(numbering: "(1)") ... ]` stay in place; only the inner `$...$` is converted to `#math.equation(...)`.
- **Keep the math source byte-for-byte.** Do not "clean up" or re-typeset the actual Typst math markup. Only add the wrapper.

### 2.3. Writing good math alt text

Read the equation the way a person would say it out loud. Be accurate but natural; do not produce a literal token dump.

- Powers: `x^2` -> "x squared", `x^3` -> "x cubed", `e^(-x)` -> "e to the minus x".
- Roots: `sqrt(...)` -> "the square root of ...".
- Subscripts: `x_i` -> "x sub i" or "x subscript i". When upper and lower case matter, say so: `F_X (x)` -> "capital f sub capital x of small x".
- Greek letters and named operators by name: `sum` -> "the sum", `product` -> "the product", `integral` -> "the integral", `lim` -> "the limit", `nabla` -> "the gradient", `nabla^2` (used as a Hessian) -> "the Hessian", `partial` -> "partial derivative".
- Relations and arrows: `=` -> "equals", `<=` -> "less than or equal to", `->` -> "goes to", `<-` (assignment) -> "gets", `mid(|)` -> "given" or "such that" depending on meaning.
- Distributions: `X tilde cal(N)(mu, sigma^2)` -> "x is a normal pdf with a mean of mu and variance of sigma squared".
- **Multi-line or multi-equation displays:** describe each line or equation in order, separated by semicolons, and optionally open with a framing phrase. Examples that match the reference style: a derivation chain begins "Step by step: ..."; three stacked unrelated equations begin "Three equations: ...".
- For a very long equation that only differs by a repeated pattern, it is acceptable to summarize: "f of x 1 through x 12 equals a 1 x 1 plus a 2 x 2 and so on through a 12 x 12 plus b".

### 2.4. Chemical formulae (whalogen `#ce(...)`)

Chemistry rendered by `#ce(...)` is glyph-based content that screen readers cannot interpret, so it must be treated as mathematics: place it inside math mode and wrap it in `#math.equation` with `alt`.

```typst
// BEFORE
This is the formula for water: #ce("H2O")

// AFTER
This is the formula for water: #math.equation(alt: "H 2 O", block: false, $#ce("H2O")$)
```

Apply the same pattern to reactions, charges, isotopes, and aligned reaction blocks. For aligned multi-line `#ce(...)` that was already inside `$ ... $`, wrap the whole display in `#math.equation(alt: "...", block: true, $ ... $)` and describe each reaction in the alt text.

### 2.5. Units (unify `#unit(...)` / `#qty(...)`)

Units rendered in math by `#unit(...)` or `#qty(...)` are also math glyphs. Wrap them:

```typst
// BEFORE
[Density (#unit("g/cm^3"))],

// AFTER
[Density (#math.equation(alt: "grams per centimeter cubed", block: false, $#unit("g/cm^3")$))],
```

---

## 3. Images

Add an `alt` description to every `image(...)` call.

```typst
// BEFORE
#image("graphics/example_image.png", width: 50%)

// AFTER
#image("graphics/example_image.png", width: 50%, alt: "Short description of what the image shows")
```

- This applies whether the image stands alone, sits inside a `#figure(...)`, sits inside a column, or sits inside a `subpar.grid` subfigure. In every case the `alt` goes on the `image(...)` call.
- The description should convey the image's purpose and content, not its file name. For a genuine placeholder image, a short label such as "Placeholder example image" is acceptable.

---

## 4. Drawn graphics: diagrams and plots (cetz, fletcher, lilaq)

Graphics drawn by code (fletcher diagrams, lilaq `lq.diagram` plots, cetz canvases) contain no `image` element, so the alt text goes on the enclosing **`#figure(...)`** via `figure.alt`.

```typst
// BEFORE
#figure(
  fletcher-diagram( ... ),
  caption: [A simple flowchart.],
) <fig:flowchart>

// AFTER
#figure(
  fletcher-diagram( ... ),
  caption: [A simple flowchart.],
  alt: "A flowchart with four boxes. Input connects by an arrow to Process. Process connects to Output. Output connects downward to Feedback. Feedback connects back around to Input, forming a loop.",
) <fig:flowchart>
```

- Add `alt:` as an argument of `#figure(...)`. Keep the existing `caption:` and the trailing label unchanged.
- This covers `fletcher-diagram(...)`, `fletcher.diagram(...)`, `lq.diagram(...)`, and `cetz`/`cetz-canvas(...)` content alike.

### 4.1. Writing good alt text for diagrams and plots

The alt text must do more than repeat the caption.

- **Flowcharts and graphs:** name the nodes and describe the connections and the direction of flow, including any edge labels (for example "an arrow labeled fail curves down to Retry") and any loops.
- **Commutative diagrams:** name the objects and their positions, describe each arrow with its label and direction, and state that the diagram commutes.
- **Plots:** state the axis labels and their ranges, then describe each curve by its meaning, color, line style (solid, dashed), overall shape, and notable points (intercepts, where curves meet, minima or maxima). Example: "A line plot with the horizontal axis labeled x from -3 to 3 and the vertical axis labeled f of x from -25 to 25. A solid blue curve for x squared forms an upward parabola ... A dashed red curve for x cubed rises from about -27 at the left to about 27 at the right ...". This matters specially because UA-1 forbids relying on color alone, so the line style and shape must be described, not just the color.

---

## 5. Subfigures (`subpar.grid`)

A `subpar.grid` contains several inner `figure(...)` entries. Add a description to **each inner figure**, using the same image-versus-figure rule as above:

- Inner subfigure wrapping an `image(...)` -> put `alt` on the inner `image(...)`.
- Inner subfigure wrapping a drawn diagram or plot -> put `alt:` on the inner `figure(...)`.

Leave the grid's own `columns:`, outer `caption:`, and outer `label:` unchanged. Each subfigure should get its own distinct description (for example "Placeholder example image, subfigure A", "... subfigure B", "... subfigure C").

---

## 6. The image-alt versus figure-alt decision rule

Use this rule whenever you are unsure where the `alt` belongs:

- If the visual is a raster/vector **`image(...)`** element, put `alt` on the **image**.
- If the visual is **drawn by code** (cetz, fletcher, lilaq) with no `image` element, put `alt` on the **`figure`**.

Do not put alt text in two places for the same visual.

---

## 7. Tables

Tables are made accessible by **structure**, not by alt text. Do not add an `alt` to a table.

7.1. **Header cells must be marked.** Every table must wrap its header row in `table.header(...)`. If a source table lists header cells as plain `[...]` cells in the first row without `table.header`, move them into `table.header(...)`.

7.2. **Spanning cells must use real spans.** Multi-row or multi-column headers must use `table.cell(rowspan: n)` and `table.cell(colspan: n)` (as in the multi-row example), so the relationship is encoded rather than faked with blank cells.

7.3. **Keep using the real `table` element.** Never simulate a table with stacks, grids of boxes, or manual columns; Typst can only tag a real `table`.

7.4. **Captions and labels must describe content, not appearance.** Rewrite any caption that names only the visual styling. For example a caption "Table with colored rows" should become a content caption such as "Sample data across three categories for four records." This follows the UA-1 principle that meaning must not be carried by color or layout alone. Decorative `fill:` colors and `stroke:` lines can stay; they are handled automatically and convey no meaning that the caption now omits.

---

## 8. Headings and document structure

8.1. **Use real headings with a correct hierarchy.** Keep using `=` (section) and `==` (subsection) as Touying intends. Do not skip levels (no jumping from `=` straight past `==`). Never fake a heading with bold text such as `#text(weight: "bold")[...]` where a real heading is meant; UA-1 checks heading hierarchy.

8.2. **Remove redundant hidden duplicate headings.** A heading marked `<touying:hidden>` is hidden visually but can still emit a heading into the tag tree, which can create an empty or duplicated structure element. In the reference rewrite, a redundant hidden subsection placed immediately before the bibliography (`== References <touying:hidden>`) was removed, leaving the bibliography directly under its section heading. Remove such redundant hidden duplicate headings; keep genuinely needed hidden headings (for example the hidden Outline slides) only where they carry real content.

8.3. **Be careful with show rules and counter manipulation that alter heading structure.** In the reference rewrite, the `#show: appendix` rule was removed before the appendix headings. Show rules that restart or relabel heading counters can disturb the heading hierarchy that UA-1 validates. Treat this as a likely-needed change but verify by compiling: if `--pdf-standard ua-1` reports a heading-hierarchy error around the appendix, remove or adjust the offending show rule. (Lower confidence: confirm against your own compile output rather than applying blindly.)

---

## 9. Elements that need NO change

Do not wrap or alter these; Typst already tags them correctly from their semantic markup. Changing them adds noise and risks breaking the layout.

- Body text, `#emph[...]`, `#strong[...]`, `#strike[...]`.
- Bullet lists `#list(...)` and numbered lists `#enum(...)`. (Either calling style is fine.)
- Hyperlinks `#link(...)`, raw URLs, inline raw code `` `...` ``, and fenced code blocks (```` ```python ... ``` ````).
- Footnotes `#footnote[...]`, block quotes `#quote(...)`, citations `#cite(...)`, cross references `@label`, and the `#bibliography(...)`.
- Theorem-like environments from theorion that contain only text: `#theorem`, `#lemma`, `#corollary`, `#definition`, `#example`, `#remark-block`, `#caution-block`. Leave the environment itself untouched, but **still convert any `$...$` math inside it** per Rule 2.

### 9.1. The one theorem-like exception: `proof`

The `#proof(...)` environment was the only theorion environment that needed wrapping in the reference rewrite. Wrap the whole proof in a `#figure(...)` with an `alt` that restates its content:

```typst
// BEFORE
#proof(title: "Proof Name")[
  This is an example of a proof.
]

// AFTER
#figure(
  proof(title: "Proof Name")[
    This is an example of a proof.
  ],
  alt: "Proof Name: This is an example of a proof."
)
```

Reason: a proof emits a generated end-of-proof (QED) marker and structure that Typst does not auto-describe, so it is given a single figure-level description. If a future Typst version tags proofs automatically this wrapping may become unnecessary; rely on the compiler's error output to decide.

---

## 10. Purely decorative graphics

If the presentation contains a standalone graphic that carries no meaning (a divider flourish, a background shape that is not an `image` and not inside a `figure`), wrap it in `pdf.artifact[...]` so screen readers skip it. Do not mark meaningful content as an artifact. (The reference files did not need this, but include it whenever decorative-only graphics appear.)

---

## 11. Final checklist

Before declaring a file done, verify each item:

- [ ] `config-info` has a non-empty `title:`.
- [ ] `#set text(...)` declares `lang` (and `region` if relevant).
- [ ] Every displayed equation is `#math.equation(alt: ..., block: true, $...$)`.
- [ ] Every inline equation is `#math.equation(alt: ..., block: false, $...$)`, including single symbols inside prose, algorithms, captions, and table cells.
- [ ] Every `#ce(...)` is in math mode and wrapped with `alt`.
- [ ] Every `#unit(...)` / `#qty(...)` is wrapped with `alt`.
- [ ] Every `image(...)` has `alt`.
- [ ] Every figure that draws a cetz / fletcher / lilaq graphic has `figure.alt`.
- [ ] Every inner figure inside every `subpar.grid` has its own description (image alt or figure alt as appropriate).
- [ ] Every table uses `table.header(...)`; spans use `table.cell(rowspan/colspan)`; captions describe content not color.
- [ ] Heading hierarchy is correct; redundant hidden duplicate headings removed; suspect heading-altering show rules checked.
- [ ] Equation labels, captions, and cross references are all preserved in their original positions.
- [ ] The file compiles with `typst compile --pdf-standard ua-1 ...` and produces a PDF with no accessibility errors. If it errors, the message names the exact missing description or structural problem; fix that spot and recompile until it passes.

---

## 12. Compact before-and-after reference

| Source construct                                     | Accessible form                                                                                      |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `$ a^2 + b^2 = c^2 $` (displayed)                    | `#math.equation(alt: "a squared plus b squared equals c squared", block: true, $ a^2 + b^2 = c^2 $)` |
| `$X$` (inline)                                       | `#math.equation(alt: "x", block: false, $X$)`                                                        |
| `#ce("H2O")`                                         | `#math.equation(alt: "H 2 O", block: false, $#ce("H2O")$)`                                           |
| `#unit("O m")`                                       | `#math.equation(alt: "ohm meter", block: false, $#unit("O m")$)`                                     |
| `image("a.png", width: 50%)`                         | `image("a.png", width: 50%, alt: "...")`                                                             |
| `#figure(fletcher-diagram(...), caption: [...])`     | add `alt: "..."` to the `#figure(...)`                                                               |
| `#figure(lq.diagram(...), caption: [...])`           | add `alt: "..."` to the `#figure(...)`                                                               |
| `#proof(title: "...")[...]`                          | `#figure(proof(title: "...")[...], alt: "...")`                                                      |
| table with plain first row                           | wrap first row in `table.header(...)`                                                                |
| `caption: [Table with colored rows.]`                | content caption, e.g. `caption: [Sample data across three categories for four records.]`             |
| `== References <touying:hidden>` before bibliography | remove the redundant hidden heading                                                                  |
| `#show: appendix` before appendix headings           | remove if it breaks the UA-1 heading check                                                           |

Apply these rules in one pass over the file, then compile with `--pdf-standard ua-1` and resolve any remaining error the compiler reports.
