# Lilaq Documentation (for LLM context)

> Lilaq is a data visualization / plotting package for the **Typst** typesetting language (version documented here: **0.6.0**). This document is a condensed, text-only reference of the official documentation at https://lilaq.org, prepared so that a language model can translate plotting code from other ecosystems (e.g. matplotlib, pgfplots/TikZ in LaTeX) into equivalent Lilaq + Typst code.
>
> **Note on images:** The original docs contain rendered plot images. Those are omitted here. Every code block below is real, runnable Lilaq/Typst code; rely on the code and parameter descriptions rather than on any visual output.

---

## How to read this document

- All code is **Typst** code. Lines beginning with `#` enter Typst "code mode"; everything else is markup/content mode.
- Lilaq is conventionally imported as `lq`:
  ```typ
  #import "@preview/lilaq:0.6.0" as lq
  ```
- Square brackets `[ ... ]` denote Typst **content** (markup), e.g. `[Hello]`, `[$x^2$]`. Math is written between dollar signs: `$x$`, `$x^2$`, `$alpha$`.
- Function calls use named arguments with `name: value`. Trailing positional arguments after named ones are common (e.g. plot data passed positionally, styling passed by name).
- Arrays/tuples use parentheses: `(1, 2, 3)`. A single-element array is `(1,)`. Dictionaries: `(key: value, ...)`. Empty dictionary: `(:)`.
- `auto`, `none`, `true`, `false` are Typst keywords.
- Lengths: `6cm`, `2pt`, `1em`, `50%`. Colors: `red`, `blue`, `rgb("ff0000")`, etc. (standard Typst).
- Typst's standard library `calc` provides math: `calc.sin`, `calc.cos`, `calc.pow`, `calc.exp`, `calc.log`, `calc.pi`, etc.
- `range(n)` yields `0, 1, ..., n-1`. Arrays have `.map(f)`, `.filter(f)`, `.enumerate()`, `.zip(other)`, `.slice(...)` etc.

---

## Quick-start

Import under the canonical abbreviation `lq`. Because Lilaq has a flat namespace with many definitions, do **not** glob-import (`*`) into the global scope.

```typ
#import "@preview/lilaq:0.6.0" as lq
```

### The first plot

A `diagram` takes any number of plot objects produced by the plotting functions. `plot` makes a 2D line plot from arrays of x and y values.

```typ
#lq.diagram(
  lq.plot((0, 1, 2, 3, 4), (3, 5, 4, 2, 3))
)
```

Adding a second plot, a title, axis labels, marks, and legend labels:

```typ
#let xs = (0, 1, 2, 3, 4)

#lq.diagram(
  title: [Precious data],
  xlabel: $x$,
  ylabel: $y$,

  lq.plot(xs, (3, 5, 4, 2, 3), mark: "s", label: [A]),
  lq.plot(
    xs, x => 2*calc.cos(x) + 3,
    mark: "o", label: [B]
  )
)
```

Key ideas demonstrated:
- Instead of an array, `plot`'s `y` argument may be a **function** evaluated for each x. Equivalent: `xs.map(x => 2*calc.cos(x) + 3)`.
- A **legend appears automatically** when plots are labeled; only labeled plots are listed.
- Consecutive plots get **different colors automatically** via the diagram's style **cycle** (default `petroff10`). Override per-plot with explicit args like `color: green`, or change the whole `cycle`.

### Scales and datetime

- Axis scales: `"linear"` (default), `"log"`, `"symlog"`, `"datetime"`. Set via `xscale`/`yscale` on the diagram.
- Lilaq supports Typst `datetime` coordinates; dedicated tick locators/formatters adapt the axes automatically.

### Anatomy of a diagram

A diagram is composed of these elements (each has its own reference section below): `title`, `diagram`, `xlabel`/`ylabel` (`label`), `xaxis`/`yaxis` (`axis`), `legend`, `tick`, `spine`, `tick-label`, `grid`, plus plot objects such as `plot`, `scatter`, `errorbar`, `bar`, etc.

---

# Reference: Diagram

## `diagram`

```
lq.diagram(width: 6cm, height: 4cm, title: none, legend: (:), xlim: auto,
  ylim: auto, xlabel: none, ylabel: none, grid: auto, xscale: auto,
  yscale: auto, xaxis: (:), yaxis: (:), margin: 6%, aspect-ratio: none,
  cycle: petroff10, fill: none, bounds: "strict", ..children)
```

Creates a new diagram containing all plots passed as arguments. All plots must be wrapped in a diagram to be displayed.

```typ
#lq.diagram(
  title: [Trigonometric Functions],
  xlabel: $x$,
  ylabel: $y$,
  lq.plot(lq.linspace(0, 10), calc.sin),
  lq.plot(lq.linspace(0, 10), x => calc.cos(x) / 2)
)
```

Parameters:
- **width** `length | relative | auto` (default `6cm`): width of the *data area* if a bare `length`; use `0% + length` to include axes/labels/title; a `ratio`/`relative` is relative to the parent (includes everything); `auto` derives it from `aspect-ratio`.
- **height** `length | relative | auto` (default `4cm`): as `width` but vertical.
- **title** `lq.title | str | content | none` (default `none`): diagram title. Use a `title` object for more options.
- **legend** `none | dictionary | lq.legend` (default `(:)`): options passed to the `legend` constructor; `none` hides it; or pass a fully custom legend.
- **xlim / ylim** `auto | array` (default `auto`): data limits as `(min, max)`; either entry may be `auto`.
- **xlabel / ylabel** `lq.label | content` (default `none`): axis labels. Use a `label` object for more options.
- **grid** `auto | none | dictionary | stroke | color | length` (default `auto`): a stroke/color/length sets the grid stroke; a dictionary with keys `stroke`, `stroke-sub`, `z-index` gives fine control; `none` removes the grid.
- **xscale / yscale** `auto | str | lq.scale` (default `auto`): scale object or name of a built-in scale: `"linear"`, `"log"`, `"symlog"`, `"datetime"`. `auto` picks `"datetime"` if any plot uses datetime coords, else `"linear"`.
- **xaxis / yaxis** `none | dictionary` (default `(:)`): dictionary of arguments passed to the `axis` constructor (see `axis`). `none` hides the axis (`axis.hidden: true`).
- **margin** `ratio | dictionary` (default `6%`): automatic margins around data, in percent of the covered range (scaled coords). `0%` makes outermost points touch the edges. Per-side dictionary keys: `left`, `right`, `top`, `bottom`, `x`, `y`, `rest`.
- **aspect-ratio** `none | float` (default `none`): fixes the ratio of data coordinates (one x-unit visually equals one y-unit when `1.0`). Realized either by adjusting the diagram dimensions (set one of `width`/`height` to `auto`) or by adjusting margins (leave both fixed).
- **cycle** `array` (default `petroff10`): style cycle. Elements all `color`, or all `dictionary` (keys `color`, `stroke`, `mark`), or all `function`. See cycles tutorial.
- **fill** `none | color | gradient | tiling` (default `none`): background fill of the data area.
- **bounds** `"relaxed" | "strict" | "data-area"` (default `"strict"`): how the bounding box is computed. `"strict"` = precise bounding box; `"relaxed"` = tick labels may hang into page margins so spines line up with the text body; `"data-area"` = bounds are just the data area.
- **..children** `any`: plot objects (`plot`, `bar`, `scatter`, `contour`, ...) and additional `axis` objects.

---

# Reference: Plotting functions

## `plot`

```
lq.plot(x, y, xerr: none, yerr: none, color: auto, stroke: auto, mark: auto,
  mark-size: auto, mark-color: auto, step: none, smooth: false, every: none,
  tip: none, toe: none, label: none, clip: true, z-index: 2)
```

Standard 2D plotting function: lines and/or marks with optional error bars. Points are given as separate arrays of x and y. `y` may also be a **function** evaluated for each x. Points where x or y is `float.nan` are skipped. By default line/mark style comes from the diagram `cycle`.

```typ
#let x = lq.linspace(0, 10)
#let y = x.map(x => calc.sin(0.1 * x * x))

#lq.diagram(
  lq.plot(x, y),
  lq.plot(x, x => calc.sin(x + 0.541))
)
```

With error bars:

```typ
#lq.diagram(
  lq.plot(
    range(8), (3, 6, 2, 6, 5, 9, 0, 4),
    yerr: (1, 1, .7, .8, .2, .6, .5, 1),
    stroke: none,
    mark: "star",
    mark-size: 6pt
  )
)
```

Parameters:
- **x** `array`: x coordinates (`int`/`float`).
- **y** `array | function`: y coordinates, or a function `x => y`. Lengths of x and y must match.
- **xerr / yerr** `none | array | dictionary` (default `none`): uncertainties. Symmetric: a constant (`xerr: 1.5`) or an array matching `x`. Asymmetric: dict with keys `p` (plus) and `m` (minus), each a constant or array (`xerr: (p: 1, m: 2)`), or an array of `(p:, m:)` dicts. Styled via `errorbar`.
- **color** `auto | color` (default `auto`): combined color for line and marks. `stroke` and `mark-fill` take precedence if set.
- **stroke** `auto | stroke` (default `auto`): line style. A non-auto color component overrides `color`.
- **mark** `auto | none | lq.mark | str` (default `auto`): mark for data points; a mark object (e.g. `lq.marks.x`) or a registered mark string. See `mark`.
- **mark-size** `auto | length` (default `auto`): mark size. For variable-size marks use `scatter`.
- **mark-color** `auto | color` (default `auto`): mark color, overrides `color`.
- **step** `none | "start" | "end" | "center"` (default `none`): step/stair drawing. `none` = straight lines; `start` = interval (x_{i-1}, x_i] takes value x_i; `center` = switches halfway; `end` = [x_i, x_{i+1}) takes value x_i.
- **smooth** `bool` (default `false`): interpolate with Bézier splines instead of straight lines (linear if <=2 points).
- **every** `none | int | array | dictionary` (default `none`): which marks to draw (lines still drawn between all points). `int` = every n-th; `array` = given indices; `dictionary` with keys `n`, `start`, `end` (negative end counts from the end).
- **tip / toe** `none | tiptoe.mark` (default `none`): arrow tip/tail on the line (from the Tiptoe package).
- **label** `any` (default `none`): legend label; omitted plots do not appear in the legend.
- **clip** `bool` (default `true`): clip the plot to the data area (also clips marks lying on an axis).
- **z-index** `int | float` (default `2`): render order. Axes have z-index `20`; use e.g. `2.01` to layer above other plots but below axes.

## `scatter`

```
lq.scatter(x, y, size: auto, color: auto, map: color.map.viridis, min: auto,
  max: auto, norm: "linear", mark: auto, stroke: auto, alpha: 100%,
  label: none, clip: true, z-index: 2)
```

Scatter plot where **mark size and color can vary per point** (this distinguishes it from `plot`).

```typ
#lq.diagram(
  lq.scatter(
    x, y,
    size: sizes.map(size => 200 * size),
    color: colors,
    map: color.map.magma
  )
)
```

Parameters:
- **x / y** `array`: coordinates (matching lengths).
- **size** `auto | array` (default `auto`): per-point scale; mark **area** scales proportionally with these numbers (linear dimension scales with sqrt(size)).
- **color** `auto | color | array` (default `auto`): single color overrides cycle fill; a per-point array of `color`s is used directly (ignoring `map`); a per-point array of `float`s is normalized and passed through `map`.
- **map** `array | gradient` (default `color.map.viridis`): color map sampled when `color` is a float array.
- **min / max** `auto | int | float` (default `auto`): data values mapped to first/last color; default to min/max of `color`.
- **norm** `lq.scale | str | function` (default `"linear"`): normalization applied to float colors before mapping. A scale, a built-in scale name, or a function like `x => calc.log(x)`.
- **mark** `auto | lq.mark | str` (default `auto`): see `plot.mark`.
- **stroke** `stroke` (default `auto`): mark stroke.
- **alpha** `ratio | array` (default `100%`): fill opacity.
- **label** `content` (default `none`): legend label.
- **clip** `bool` (default `true`), **z-index** `int | float` (default `2`): see `plot`.

> A `colorbar` can visualize the color mapping of a `scatter` or `colormesh`.

## `bar`

```
lq.bar(x, y, fill: auto, stroke: none, align: center, width: 80%, offset: 0,
  base: 0, label: none, clip: true, z-index: 2)
```

Vertical bar plot from bar positions `x` and heights `y`.

```typ
#lq.diagram(
  xaxis: (subticks: none),
  lq.bar((1, 2, 3, 4, 5, 6), (1, 2, 3, 2, 5, 3))
)
```

Useful idiom: **categorical / rotated tick labels** via `axis.ticks` (array of `(location, label)` tuples; `.enumerate()` produces them) plus a show rule rotating tick labels 45 degrees:

```typ
#show: lq.show_(
  lq.tick-label.with(kind: "x"),
  it => box(width: 0pt, align(right, rotate(-45deg, reflow: true, it))),
)

#lq.diagram(
  xaxis: (
    ticks: ("Apples", "Bananas", "Kiwis", "Mangos", "Papayas").enumerate(),
    subticks: none,
  ),
  lq.bar(range(5), (5, 3, 4, 2, 1))
)
```

Parameters:
- **x** `array`: bar positions.
- **y** `array | function`: bar heights (array or `x => y`).
- **fill** `none | color | gradient | tiling | array` (default `auto`): single fill or per-bar array.
- **stroke** `auto | none | color | length | stroke | gradient | tiling | dictionary` (default `none`): like `std.rect` stroke; a dictionary strokes individual sides.
- **align** `left | center | right` (default `center`): bar alignment at x values.
- **width** `ratio | int | float | duration | array` (default `80%`): `ratio` = relative to min spacing between bars; `float`/`int` = width in data coords (constant or per-bar array); `duration` for datetime x.
- **offset** `int | float | duration | array` (default `0`): shift applied to all x (equivalent to `x.map(x => x + offset)`); useful for grouped bars side by side; per-bar array allowed.
- **base** `int | float | array` (default `0`): y baseline of the bars (constant or per-bar); enables stacked/floating bars.
- **label** `content` (default `none`), **clip** `bool` (default `true`), **z-index** `int | float` (default `2`): see `plot`.

> To make **grouped bars**, plot several `bar`s with a small `width` and shifted `offset`. To make **stacked bars**, set `base` of upper series to the cumulative heights below.

## `fill-between`

```
lq.fill-between(x, y1, y2: none, stroke: none, fill: auto, step: none,
  smooth: false, label: none, z-index: 2)
```

Fills the area between two graphs, or between one graph and the x-axis.

```typ
#let xs = lq.linspace(-1, 2)
#lq.diagram(
  lq.fill-between(xs, xs.map(calc.sin), y2: xs.map(calc.cos))
)
```

Area between a curve and the x-axis (omit `y2`):

```typ
#let xs = lq.linspace(0, 3, num: 80)
#lq.diagram(
  lq.fill-between(
    label: [Maxwell-distribution],
    xs, xs.map(x => x*x*calc.exp(-x*x*1.3))
  )
)
```

Parameters:
- **x** `array`: x coordinates.
- **y1** `array | function`: first boundary (array or `x => y`).
- **y2** `none | array | function` (default `none`): second boundary; if `none`, fills between `y1` and the x-axis.
- **stroke** `auto | none | stroke` (default `none`): outline stroke.
- **fill** `auto | none | color | gradient | tiling` (default `auto`).
- **step** `none | start | end | center` (default `none`): see `plot.step`.
- **smooth** `bool` (default `false`): Bézier interpolation.
- **label** `content` (default `none`), **z-index** `int | float` (default `2`).

## `stem`

```
lq.stem(x, y, color: auto, stroke: auto, mark: auto, mark-size: auto,
  base: 0, base-stroke: red, label: none, clip: true, z-index: 2)
```

Vertical stem plot (lollipop / discrete signal plot): a vertical line from a baseline to each point, with a mark at the tip.

```typ
#let x = lq.linspace(0, 10, num: 30)
#lq.diagram(
  lq.stem(x, x.map(calc.cos), color: orange, mark: "d",
    base: -0.25, base-stroke: black)
)
```

Parameters:
- **x** `array`, **y** `array | function`.
- **color** `auto | color` (default `auto`): combined line+mark color.
- **stroke** `auto | stroke` (default `auto`): line style (overrides color).
- **mark** `auto | none | lq.mark | str` (default `auto`), **mark-size** `auto | length` (default `auto`).
- **base** `int | float` (default `0`): y of the baseline.
- **base-stroke** `stroke` (default `red`): baseline stroke.
- **label** / **clip** / **z-index**: see `plot`.

## Horizontal variants: `hbar`, `hstem`, `hboxplot`, `hviolin`

Each `h`-prefixed function is the horizontal counterpart of its vertical version, with the roles of the x and y axes swapped (e.g. `hbar(y, x, ...)` draws horizontal bars whose lengths come from the second argument). Parameters mirror the vertical version (`hbar` mirrors `bar`, `hstem` mirrors `stem`, `hboxplot` mirrors `boxplot`, `hviolin` mirrors `violin`). Use them when categories sit on the vertical axis.

```typ
#lq.diagram(
  yaxis: (subticks: none),
  lq.hbar((1, 2, 3, 4), (3, 5, 2, 4))   // horizontal bars
)
```

## `boxplot`

```
lq.boxplot(..data, x: auto, whisker-pos: 1.5, width: 50%, fill: none,
  stroke: 1pt + black, median: 1pt + orange, mean: none, whisker: auto,
  cap: auto, cap-length: 0.25, outliers: "o", outlier-size: 5pt,
  outlier-fill: none, outlier-stroke: black, label: none, clip: true, z-index: 2)
```

Computes and draws one or more boxplots. Each dataset becomes a box. Uses the Komet package internally to compute statistics.

```typ
#lq.diagram(
  lq.boxplot(
    stroke: blue.darken(50%),
    (1, 2, 3, 4, 5, 6, 7, 8, 9, 21, 19),
    range(1, 30),
    (1, 28, 25, 30),
    (1, 2, 3, 4, 5, 6, 32),
  )
)
```

Precomputed stats (for large data, computed externally):

```typ
#lq.diagram(
  lq.boxplot(
    (median: 4.4, q1: 2, q3: 8, outliers: (12, 13),
     whisker-low: 0, whisker-high: 10)
  )
)
```

Parameters:
- **..data** `array | dictionary`: one or more datasets. Either an array of raw values (stats computed automatically) or a dictionary with mandatory keys `median`, `q1`, `q3`, `whisker-low`, `whisker-high` and optional `mean`, `outliers`.
- **x** `auto | int | float | array` (default `auto`): x positions; `auto` places boxes at integers starting at 1.
- **whisker-pos** `int | float` (default `1.5`): whisker length at most `whisker-pos * (q3 - q1)` (Tukey convention), clipped to actual data points.
- **width** `ratio | int | float | duration | array` (default `50%`): box width in x data coords (see `bar.width`).
- **fill** `none | color | gradient | tiling` (default `none`).
- **stroke** (default `1pt + black`): general box stroke.
- **median** (default `1pt + orange`): median line stroke.
- **mean** `none | lq.mark | str | stroke` (default `none`): show the mean as a mark or line.
- **whisker** `auto | ...stroke` (default `auto`): whisker stroke (inherits `stroke`).
- **cap** `auto | ...stroke` (default `auto`): whisker cap stroke.
- **cap-length** `int | float` (default `0.25`): cap length in x data coords.
- **outliers** `none | lq.mark | str` (default `"o"`): outlier marker.
- **outlier-size** `length` (default `5pt`), **outlier-fill** `none | auto | color` (default `none`), **outlier-stroke** `stroke` (default `black`).
- **label** / **clip** / **z-index**: see `plot`.

> `hboxplot` is the horizontal version. `violin-boxplot` overlays a violin and a boxplot.

## `violin`

```
lq.violin(..data, x: auto, width: 50%, bandwidth: auto, fill: 30%, stroke: auto,
  color: auto, median: "o", mean: none, extrema: false, side: "both",
  boxplot: (:), whisker-pos: 1.5, num-points: 80, trim: true, label: none,
  clip: true, z-index: 2)
```

Violin plot per dataset, using kernel density estimation (KDE) to show the distribution. Like a boxplot but shows the density shape.

```typ
#lq.diagram(
  lq.violin(
    (0, 2, 3, 4, 5, 6, 7, 8, 3, 4, 4, 2, 12),
    (1, 3, 4, 5, 5, 5, 5, 6, 7, 12),
    (0, 3, 4, 5, 6, 7, 8, 9),
  )
)
```

Parameters:
- **..data** `array`: one or more numeric datasets.
- **x** `auto | int | float | array` (default `auto`): positions; `auto` = integers from 1.
- **width** `ratio | int | float | duration | array` (default `50%`): see `bar.width`.
- **bandwidth** `auto | int | float` (default `auto`): KDE bandwidth; `auto` uses Scott's rule.
- **fill** `auto | none | color | gradient | tiling | ratio` (default `30%`): a `ratio` lightens (<100%) or darkens (>100%) the cycle color (`0%` white, `200%` black).
- **stroke** (default `auto`): outline stroke.
- **color** `auto | color` (default `auto`): base color from which fill/stroke and the inner boxplot inherit.
- **median** `none | lq.mark | str | color | stroke | length` (default `"o"`): show median as a mark or horizontal line.
- **mean** (default `none`): like `median`.
- **extrema** `bool` (default `false`): mark min/max with horizontal lines (configure via `set-violin-extremum`).
- **side** `"both" | "low" | "high"` (default `"both"`): which side to draw the KDE (use `"low"`/`"high"` to compare two distributions back-to-back).
- **boxplot** `dictionary | none` (default `(:)`): args forwarded to the inner `violin-boxplot`; `none` removes it.
- **whisker-pos** `int | float` (default `1.5`), **num-points** `int` (default `80`, KDE resolution), **trim** `bool` (default `true`).
- **label** / **clip** / **z-index**: see `plot`.

Related: `hviolin` (horizontal), `violin-boxplot` (the boxplot drawn inside a violin; style globally with `lq.set-violin-boxplot(...)` in a show rule, or per-plot via the `boxplot:` argument).

## `colormesh`

```
lq.colormesh(x, y, z, map: color.map.viridis, min: auto, max: auto,
  excess: "clamp", norm: "linear", align: center + horizon,
  interpolation: "pixelated", label: none, z-index: 2)
```

Rectangular color mesh / **heatmap**. If `x` and `y` are both evenly spaced, an image is drawn (smaller, faster); otherwise individual rectangles.

```typ
#lq.diagram(
  width: 4cm, height: 4cm,
  lq.colormesh(
    lq.linspace(-4, 4, num: 10),
    lq.linspace(-4, 4, num: 10),
    (x, y) => x * y,
    map: color.map.magma
  )
)
```

Parameters:
- **x / y** `array`: 1D coordinate arrays.
- **z** `array | function`: heights for each (x, y). Either a 2D array (row-major, one row per y) of dimensions `y.len() x x.len()` (mapped one-to-one, alignment via `align`) or `(y.len()-1) x (x.len()-1)` (coords treated as cell edges, `align` ignored); or a function `(x, y) => z`; or `content` (e.g. an `image(...)`), in which case set `min`/`max`/`map` manually. Use `float.nan` to mask cells.
- **map** `array | gradient` (default `color.map.viridis`).
- **min / max** `auto | int | float` (default `auto`): data range mapped to first/last color.
- **excess** `"clamp" | "mask"` (default `"clamp"`): out-of-range handling; `"clamp"` to endpoints, `"mask"` transparent.
- **norm** `lq.scale | str | function` (default `"linear"`): normalization (e.g. `"log"`).
- **align** `alignment` (default `center + horizon`): how cells align at coordinates (ignored in edges mode).
- **interpolation** `"pixelated" | "smooth"` (default `"pixelated"`): smoothing (only for evenly spaced x/y).
- **label** / **z-index**: see `plot`.

> Pair with `lq.colorbar(mesh)` to show the color scale. The helper `mesh` (see Math) generates rectangular meshes.

## `contour`

```
lq.contour(x, y, z, levels: 10, fill: false, stroke: 0.7pt,
  map: color.map.viridis, min: auto, max: auto, norm: "linear",
  label: none, z-index: 2)
```

Contour plot of a 3D mesh: cuts through the surface at given `levels` drawn as contour lines (optionally filled per level).

```typ
#lq.diagram(
  width: 4cm, height: 4cm,
  lq.contour(
    lq.linspace(-5, 5, num: 12),
    lq.linspace(-5, 5, num: 12),
    (x, y) => x * y,
    map: color.map.icefire,
    fill: true   // set false (default) for line contours
  )
)
```

Parameters:
- **x / y** `array`: 1D coordinate arrays.
- **z** `array | function`: 2D `m x n` array (m = len(y), n = len(x)) or a function `(x, y) => z`.
- **levels** `int | array` (default `10`): number of auto levels, or an explicit array of z values.
- **fill** `bool` (default `false`): fill between levels vs. stroked contour lines.
- **stroke** `stroke` (default `0.7pt`): contour stroke when `fill: false`; a color here overrides the map.
- **map** `array | gradient` (default `color.map.viridis`), **min / max** `auto | int | float`, **norm** `lq.scale | str | function` (default `"linear"`).
- **label** / **z-index**: see `plot`.

## `quiver`

```
lq.quiver(x, y, directions, stroke: auto, scale: auto, pivot: end,
  tip: tiptoe.stealth.with(length: 400%), toe: none, color: black,
  map: color.map.viridis, min: auto, max: auto, norm: "linear",
  label: none, z-index: 2)
```

Quiver plot of a vector field over a rectangular grid. Arrow lengths/strokes auto-scale to grid density.

```typ
#lq.diagram(
  lq.quiver(
    lq.arange(-2, 3),
    lq.arange(-2, 3),
    (x, y) => (x + y, y - x)
  )
)
```

Parameters:
- **x / y** `array`: 1D grid coordinates.
- **directions** `array | function`: 2D `m x n` array of `(u, v)` vectors, or a function `(x, y) => (u, v)`. `float.nan` masks.
- **stroke** `auto | stroke` (default `auto`): overrides `color`; auto thins small arrows.
- **scale** `auto | int | float` (default `auto`): uniform arrow length scaling.
- **pivot** `start | center | end` (default `end`): which part of the arrow sits on the grid point.
- **tip / toe** `none | tiptoe.mark`: arrow head/tail (Tiptoe package).
- **color** `color | array | function` (default `black`): single color, a 2D array, or a function `(x, y, u, v) => scalar | color` (e.g. `color: (x, y, u, v) => calc.norm(u, v)` to color by magnitude).
- **map** `array | gradient` (default `color.map.viridis`), **min / max**, **norm** (default `"linear"`).
- **label** / **z-index**: see `plot`.

## Primitive drawing functions

These draw shapes/annotations into the data area. Coordinates can be **data coordinates** (`int`/`float`), **absolute** lengths from the top-left of the data area (`length`), **relative** to the data area (`ratio`, `0%` = left/top, `100%` = right/bottom), a `relative` combination, or `datetime`. They can be mixed, e.g. `(1, 100%)`.

### `line`

```
lq.line(start, end, stroke: stroke(), label: none, tip: none, toe: none,
  clip: true, z-index: 2)
```

Draws a line between two points.

```typ
#lq.diagram(width: 3cm, height: 3cm, lq.line((1, 2), (5, 4)))

// Diagonal across the whole data area, mixed coordinates, dashed:
#lq.diagram(
  lq.line(stroke: (paint: blue, dash: "dashed"), (1, 100%), (4, 10pt))
)
```

- **start / end** `array`: endpoints (see coordinate types above).
- **stroke** `stroke` (default `stroke()`).
- **label** `content`; **tip / toe** `none | tiptoe.mark` (arrow head/tail via Tiptoe); **clip** `bool` (default `true`); **z-index** (default `2`).

### `vlines` and `hlines`

```
lq.vlines(..x, min: auto, max: auto, stroke: black, label: none, z-index: 2)
lq.hlines(..y, min: auto, max: auto, stroke: black, label: none, z-index: 2)
```

`vlines` draws one or more vertical reference lines at the given x coordinate(s); `hlines` draws horizontal lines at given y coordinate(s) (with `min`/`max` then being x bounds). These are the equivalent of matplotlib's `axvline`/`axhline`.

```typ
#lq.diagram(
  ylim: (0, 7),
  lq.vlines(1, 1.1, stroke: teal, label: "Indefinite"),
  lq.vlines(2, stroke: blue, min: 2, label: "Fixed start"),
  lq.vlines(3, stroke: purple, max: 2, label: "Fixed end"),
  lq.vlines(4, stroke: red, min: 1, max: 3, label: "Fixed"),
)
```

- **..x** (or **..y** for `hlines`) `int | float`: one or more line positions.
- **min / max** `auto | int | float` (default `auto`): the perpendicular extent; `auto` spans the full diagram.
- **stroke** `stroke` (default `black`); **label** `content`; **z-index** (default `2`).

### `rect` and `ellipse`

```
lq.rect(x, y, width: auto, height: auto, align: left + top, fill: none,
  stroke: auto, radius: 0pt, inset: 5pt, outset: 0pt, label: none,
  clip: true, z-index: 2, ..body)
```

Draws a rectangle (or square) with origin `(x, y)`. `ellipse` has an analogous signature and draws an ellipse instead. Coordinates and sizes accept data values, lengths, ratios, relative, or datetime (mixable). `(50%, 50%)` is the data-area center.

```typ
#lq.diagram(
  width: 3cm, height: 3cm,
  lq.rect(2, 2, width: 10, height: 4, fill: yellow),
  lq.rect(10, 4, width: 4, height: 4, fill: red),
  lq.rect(50%, 50%, width: 45%, height: 45%, stroke: blue)
)
```

- **x / y** `float | relative | datetime`: origin.
- **width / height** `auto | float | relative | duration` (default `auto`).
- **align** `alignment` (default `left + top`): alignment at the origin.
- **fill** `none | color | gradient | tiling` (default `none`); **stroke** `auto | none | stroke` (default `auto`).
- **radius** `relative` (default `0pt`, corner rounding); **inset** (default `5pt`); **outset** (default `0pt`).
- **label** / **clip** / **z-index**; **..body**: optional content placed inside.

### `place`

```
lq.place(x, y, body, align: center + horizon, clip: false, z-index: 21)
```

Places arbitrary content (text, boxes, even a nested `lq.diagram`) into the data area. Used for **annotations**. Unlike most plot commands it is not clipped by default and has a high z-index (`21`), so it renders on top.

```typ
#lq.diagram(
  lq.plot((1, 2, 3, 4), (3, 5, 1, 3)),
  lq.place(2, 5, align: left, pad(.7em)[max]),
  lq.place(3, 1, align: right, pad(.7em)[min])
)
```

Use Typst's `pad(..)` to offset the label from the point, and `box(fill: .., inset: ..)` for a background. An inset mini-plot can be placed via a nested `lq.diagram` inside `place`.

- **x / y** `float | relative | datetime`: origin (data, ratio, or length; mixable).
- **body** `any`: content to place.
- **align** `alignment` (default `center + horizon`).
- **clip** `bool` (default `false`); **z-index** `int | float` (default `21`).

### `path`

```
lq.path(..vertices, fill: none, stroke: auto, closed: false, ...)
```

Draws a custom path through a sequence of vertices given in data coordinates (analogous to Typst's native `path`/`curve`, but in data space). Useful for arbitrary polylines/polygons inside the data area. Pass vertices as coordinate tuples; set `closed: true` to close the shape and `fill`/`stroke` to style it.

# Reference: Diagram elements

## `axis`

```
lq.axis(scale: auto, lim: auto, inverted: false, label: none, kind: "x",
  position: auto, mirror: auto, ticks: auto, subticks: auto,
  tick-distance: auto, offset: auto, exponent: auto,
  auto-exponent-threshold: 3, locate-ticks: auto, format-ticks: auto,
  locate-subticks: auto, format-subticks: none, extra-ticks: (),
  format-extra-ticks: none, tick-args: (:), subtick-args: (:),
  functions: auto, hidden: false, stroke: auto, tip: auto, toe: auto,
  filter: (value, distance) => true, ..plots)
```

A diagram axis: a spine, ticks/subticks with tick labels, and an axis label. **Usually you configure the main axes by passing a dictionary of these parameters to `diagram.xaxis` / `diagram.yaxis`** rather than constructing an `axis` directly:

```typ
#lq.diagram(
  yaxis: (exponent: 0),
  xaxis: (position: top),
  // ...plots
)
```

Adding an `axis` object as a child of the diagram creates an additional (secondary/twin) axis. Built-in tick formatters use the Zero package for number formatting.

Parameters:
- **scale** `auto | str | lq.scale` (default `auto`): `"linear"`, `"log"`, `"symlog"`, `"datetime"`, or a scale object.
- **lim** `auto | array` (default `auto`): `(min, max)`; either may be `auto`. If `min > max` the axis inverts; if equal the range expands.
- **inverted** `bool` (default `false`): swap min/max.
- **label** `content | lq.label` (default `none`).
- **kind** `"x" | "y"` (default `"x"`).
- **position** `auto | alignment | float | relative | dictionary` (default `auto`): a side (`top`/`bottom` for x, `left`/`right` for y), a coordinate on the other axis, a length/relative, or a dict `(align:, offset:)`.
- **mirror** `auto | bool | dictionary` (default `auto`): show ticks on the opposite side; dict keys `ticks`, `tick-labels`. `auto` disables mirrors when a secondary axis exists or position is non-standard.
- **ticks** `auto | array | dictionary | none` (default `auto`): explicit tick locations. Array of locations, array of `(location, label)` tuples, or a dict `(ticks:, labels:)` with equal-length arrays. `none` hides ticks; `auto` uses the locator.
- **subticks** `auto | none | int` (default `auto`): subtick count between major ticks; `none` to disable.
- **tick-distance** `auto | float` (default `auto`): spacing between major ticks (linear locator).
- **offset** `auto | int | float | content | none` (default `auto`): a value subtracted from all ticks and shown at the axis end (reduces long labels); `content`/`none` just displays without affecting data.
- **exponent** `auto | none | int | "inline"` (default `auto`): divide all ticks by 10^exponent and show the factor at the axis end (scientific-notation control). With log locators, `none` writes out full numbers.
- **auto-exponent-threshold** `int` (default `3`).
- **locate-ticks / locate-subticks** `auto | function`: tick locators (see Tick locators).
- **format-ticks / format-subticks / format-extra-ticks** `auto | none | function`: tick formatters (see Tick formatters).
- **extra-ticks** `array` (default `()`): additional ticks (float values or `tick` instances).
- **tick-args / subtick-args** `dictionary`: args forwarded to the locators.
- **functions** `auto | array` (default `auto`): forward/backward transforms `(forward, backward)` for a dependent secondary axis (e.g. `(x => m*x*x, y => calc.sqrt(y/m))`); the two must be inverses. Mutually exclusive with `..plots` and `lim`.
- **hidden** `bool` (default `false`): hide the axis entirely (logical settings still apply; `diagram.xaxis: none` sets this).
- **stroke** `auto | stroke`: spine stroke. **tip / toe** `auto | none | tiptoe.mark`: arrows on the spine.
- **..plots** `any`: plots to bind to an independent (twin) axis; mutually exclusive with `functions` and `lim`.

## `legend`

```
lq.legend(..children, fill: white.transparentize(20%), inset: 0.3em,
  stroke: 0.5pt + gray, radius: 1.5pt, position: top + right, pad: 2pt,
  dx: 0pt, dy: 0pt, z-index: 25)
```

Legend listing all labeled plots. Appears automatically when plots have `label:`. Configure by passing a dictionary to `diagram.legend` (e.g. `legend: (position: top + left)`); set `legend: none` to hide.

```typ
#lq.diagram(
  legend: (position: top + left),
  lq.plot((1,2,3), (1,2,3), label: [Data A]),
  lq.plot((1,2,3), (2,3,4), label: [Data B]),
)
```

Parameters:
- **..children** `array`: items (filled automatically by `diagram`; provide manually for a fully custom legend).
- **fill** (default `white.transparentize(20%)`); **inset** `relative` (default `0.3em`); **stroke** (default `0.5pt + gray`); **radius** (default `1.5pt`).
- **position** `alignment | array` (default `top + right`): an alignment, or `(x, y)` relative position (lengths/ratios). To place **outside** (e.g. to the right): `position: left + horizon` with `dx: 100%`.
- **pad** `length` (default `2pt`): padding from the data-area edge when `position` is an alignment.
- **dx / dy** `relative` (default `0pt`): displacement from `position`.
- **z-index** `int | float` (default `25`).

## `mark` and available mark shapes

```
lq.mark(size: 4pt, fill: auto, stroke: 0.7pt, shape: ".")
```

A mark for marking data points. Set marks via the `mark:` parameter of plot types (`plot`, `scatter`, `stem`, ...). Specify a mark in two ways: a **string name** (e.g. `mark: "o"`) or a **mark object** from `lq.marks` (e.g. `mark: lq.marks.star`, configurable like `lq.marks.star.with(n: 6)`). `mark: none` removes the mark.

Parameters of `lq.mark`:
- **size** `length` (default `4pt`): shapes are tuned to match in optical size.
- **fill** `auto | none | color | gradient | tiling` (default `auto`, inherits from plot).
- **stroke** `stroke` (default `0.7pt`, `auto` inherits).
- **shape** `str | function` (default `"."`): a built-in name or a function `mark => content`.

Built-in mark names (under `lq.marks`, usable as strings):
- `"."` default point, `","` a fixed 1pt point (size-independent).
- `"o"` circle, `"s"` square, `"d"` diamond, `"x"` cross, `"+"` plus (alias of `a4`).
- Triangles: `"^"` (up), `"v"` (down), `"<"` (left), `">"` (right) — specializations of `polygon` (params `n`, `angle`).
- Polygons: `"p5"`, `"p6"`, `"p7"`, `"p8"` (also via `lq.marks.polygon.with(n: .., angle: ..)`).
- Stars: `"star"`, `"s3"`, `"s4"`, `"s5"`, `"s6"` — specializations of `star` (params `n`, `angle`, `inset`).
- Asterisks: `"a3"`, `"a4"`, `"a5"`, `"a6"` — specializations of `asterisk` (= `star.with(inset: 100%)`).
- `text` mark: shows arbitrary content, e.g. `lq.marks.text.with(body: [Y])`.

Custom mark: pass a function receiving a mark object (fields `size`, `fill`, `stroke`) returning content:

```typ
#lq.diagram(
  lq.plot((1,2,3,4), (1,2,3,4), stroke: none,
    mark: mark => place(center + horizon, text(mark.fill)[%]))
)
```

## `errorbar`

```
lq.errorbar(kind: "x", cap: 3pt, stroke: auto, cap-stroke: auto)
```

Configures the look of error bars (the data themselves are supplied via `plot`'s `xerr`/`yerr`). Restyle globally with a show rule `#show: lq.set-errorbar(stroke: 1pt + red, cap: none)`.

- **kind** `"x" | "y"` (default `"x"`): horizontal or vertical bars.
- **cap** `none | length` (default `3pt`): cap length; `none` for no cap.
- **stroke** `auto | stroke` (default `auto`, inherits from plot).
- **cap-stroke** `auto | stroke` (default `auto`, inherits from `stroke`).

## `grid`

```
lq.grid(ticks, sub, kind: "x", stroke: 0.5pt + luma(80%), stroke-sub: none, z-index: 0)
```

Axis grid highlighting tick positions. Grid lines come from the axes' tick locators. Configure per-diagram via `diagram.grid` (e.g. `grid: (stroke: black, stroke-sub: 0.25pt)`, or `grid: none` to disable), or globally with `#show: lq.set-grid(stroke: teal, stroke-sub: 0.5pt + luma(90%))`. Address one axis only with `#show: lq.cond-set(lq.grid.with(kind: "x"), stroke: orange)`.

- **ticks** `array`: tick positions (auto-filled by `diagram`).
- **sub** `bool`: whether the ticks are subticks.
- **kind** `"x" | "y"` (default `"x"`).
- **stroke** `none | stroke` (default `0.5pt + luma(80%)`): main grid line stroke.
- **stroke-sub** `auto | none | stroke` (default `none`): subtick grid stroke (`auto` inherits `stroke`).
- **z-index** `int | float` (default `0`).

## `tick`, `tick-label`, `spine`, `label`, `title`

These elements are usually styled via show rules (`lq.set-tick(...)`, `lq.set-tick-label(...)`, `lq.set-spine(...)`, etc.) or by passing dictionaries to the axis/diagram, rather than constructed directly.

### `tick`

```
lq.tick(value, label: none, sub: false, kind: "x", stroke: auto,
  shorten-sub: 50%, align: right, pad: 0.5em, inset: 4pt, outset: 0pt)
```

A tick mark plus tick label on an axis.
- **value** `float`: position in data coords.
- **label** `content | lq.tick-label` (default `none`).
- **sub** `bool` (default `false`): subtick or not.
- **kind** `"x" | "y"` (default `"x"`).
- **stroke** `auto | stroke` (default `auto`, inherits spine).
- **shorten-sub** `ratio` (default `50%`): subtick length vs. major.
- **align** `left | top | right | bottom` (default `right`).
- **pad** `length` (default `0.5em`): gap between tick and label.
- **inset** `length` (default `4pt`): tick length inside the axis.
- **outset** `length` (default `0pt`): tick length outside the axis. (Set `inset: 0pt, outset: 4pt` for outward-pointing ticks.)

### `tick-label`

A tick label (usually a number). Style globally via `lq.set-tick-label(...)` or target one axis with `lq.tick-label.with(kind: "x")` in a show rule (see the rotated-labels idiom under `bar`). It carries the formatted text content for a tick.

### `spine`

The line drawn along an axis. Parameters include `stroke`, `tip`, `toe` (arrow marks via Tiptoe). Style via `lq.set-spine(stroke: ..., tip: ..., toe: ...)` or through `axis.stroke` / `axis.tip` / `axis.toe`.

### `label`

```
lq.label(body, dist: auto, angle: auto, ...)
```

An axis label (used by `diagram.xlabel`/`ylabel` and `axis.label`). Pass content directly (`xlabel: $x$`) or a `label` object for control over distance from the axis (`dist`) and rotation (`angle`).

### `title`

A diagram title (used by `diagram.title`). Pass content directly (`title: [My plot]`) or a `title` object for more options (e.g. positioning/styling).

## `colorbar`

```
lq.colorbar(plot, orientation: "vertical", thickness: 3mm, label: none, ..args)
```

Creates a colorbar (a slim diagram with a gradient and ticks) for a color-coded plot (`scatter`, `colormesh`, `contour`, `quiver`). It is a separate inline object, placed wherever you put it in the document.

```typ
#show: lq.set-diagram(height: 3.5cm, width: 4cm)

#let mesh = lq.colormesh(
  lq.linspace(-0.3, 1.3),
  lq.linspace(-0.3, 1.3),
  (x, y) => x * y,
  map: gradient.linear(..color.map.icefire).sharp(9)
)

#lq.diagram(mesh)
#lq.colorbar(mesh, thickness: 2mm)
```

- **plot**: the color-coded plot instance.
- **orientation** `"vertical" | "horizontal"` (default `"vertical"`).
- **thickness** `length` (default `3mm`).
- **label** `content` (default `none`).
- **..args**: forwarded to `diagram`. Use a `set-diagram` show rule to give the colorbar and the main diagram the same height. Insert `h(.5em)` between them for spacing.

# Reference: Scale

Scales transform data coordinates into scaled (drawing) coordinates. Set per axis via `diagram.xscale` / `diagram.yscale` / `axis.scale`, using either a name string or a scale object. Built-in scale names: `"linear"`, `"log"`, `"symlog"`, `"datetime"`.

## `scale` (constructor)

```
lq.scale.scale(transform, inverse, name: "", identity: 0,
  locate-ticks: none, locate-subticks: none, ..args)
```

Build a custom scale.
- **transform** `function`: data -> scaled coordinates (ignore absolute coefficients/offsets; e.g. linear is `x => x`, log is `x => calc.log(x)`).
- **inverse** `function`: exact inverse of `transform`.
- **name** `str` (default `""`): used to auto-select a suitable tick locator.
- **identity** `int | float` (default `0`): initial axis value when no limits/plots given; positive-only scales (log) should use `1`.
- **locate-ticks / locate-subticks** `none | function`: default locators for this scale.

## Built-in scales

- `lq.scale.linear` — uniform linear scaling (default).
- `lq.scale.log(base: 10)` — logarithmic scale (positive data only). Use `xscale: "log"` for the common case. Pairs with the log tick locator/formatter for decade ticks like 10^n.
- `lq.scale.symlog(...)` — symmetric log: logarithmic away from zero but linear within a small region around zero, so it handles zero and negative values. Useful for data spanning positive and negative orders of magnitude.
- `lq.scale.datetime` — for `datetime` coordinates; auto-selected when any plot uses datetimes.

Example (log y-axis):

```typ
#lq.diagram(
  yscale: "log",
  lq.plot(lq.linspace(1, 100), x => x*x)
)
```

# Reference: Math helpers

Module `lq` exposes a small math/data library. Common ones for generating plot data:

- **`lq.linspace(start, end, num: 50, include-end: true)`** — array of `num` evenly spaced values over `[start, end]` (or `[start, end)` if `include-end: false`). The go-to way to make x-arrays for function plots.
  ```typ
  #let x = lq.linspace(0, 10)            // 50 points, 0..10 inclusive
  #let x = lq.linspace(0, 1, num: 100)
  ```
- **`lq.arange(start, end, step: 1)`** — numbers spaced by `step` over `[start, end)` (end excluded), like Python's `range`/numpy `arange`. E.g. `lq.arange(-2, 3)` -> `(-2, -1, 0, 1, 2)`.
- **`lq.logspace(start, end, num: 50, base: 10, include-end: true)`** — logarithmically spaced numbers over `[base^start, base^end]`. Handy for log-axis data.
- **`lq.mesh(x, y, f)`** — builds a 2D rectangular mesh by evaluating `f(x, y)` over the grid; returns the 2D array suitable for `colormesh`/`contour`/`quiver` `z`/`directions`.
- **`lq.minmax(array)`** -> `(min, max)`, ignoring `float.nan`. **`lq.cmin(array)`**, **`lq.cmax(array)`** — min/max ignoring `float.nan`.
- **`lq.percentile(data, q)`** — the q-th percentile.
- **`lq.pow10(x)`** -> `10^x` as a float. **`lq.sign(x)`** -> sign of a number.
- **`lq.divmod(a, b)`** -> `(quotient, remainder)` with floored division.
- **`lq.decompose-floating-point(x)`** — decomposes into scientific-notation parts.

Beyond these, use Typst's built-in `calc` module for math: `calc.sin`, `calc.cos`, `calc.tan`, `calc.exp`, `calc.log`, `calc.ln`, `calc.pow`, `calc.sqrt`, `calc.abs`, `calc.pi`, `calc.e`, `calc.norm(..)`, `calc.min`, `calc.max`, etc. And array methods: `.map(f)`, `.filter(f)`, `.enumerate()`, `.zip(other)`, `.slice(a, b)`, `.rev()`, `.sum()`.

# Reference: Vec

The `lq.vec` module provides basic vector (array-of-numbers) operations used internally and available for data manipulation: elementwise arithmetic and helpers such as adding/subtracting/scaling arrays and combining them. When transforming data for a plot, you can usually rely on Typst array `.map(..)` and `.zip(..)` instead; reach for `lq.vec.*` for concise elementwise vector math.

# Reference: Color maps

`lq.color.map` contains accessible color maps (CVD-friendly, perceptually uniform and ordered) for color-coded plots (`scatter`, `colormesh`, `contour`, `quiver` via their `map:` parameter). Access as `lq.color.map.<name>` or, in code where `color` is in scope, `color.map.<name>`.

Confirmed/known maps include the sequential maps **viridis** (default for color-coded plots), **magma**, **plasma**, **inferno**, **cividis**; diverging and bi-sequential maps such as **icefire** and **tovu**; plus a set of scientifically designed maps by Crameri (Crameri *et al*). The four categories are:
- **Sequential** — single-direction intensity (e.g. viridis, magma, plasma, inferno, cividis).
- **Diverging** — emphasizes deviation from a center (e.g. icefire).
- **Bi-sequential** — two sequential ramps joined (e.g. tovu).
- **Qualitative** — distinct categorical colors, good for style cycles.

Usage:

```typ
#lq.scatter(x, y, color: values, map: color.map.magma)
#lq.colormesh(x, y, (x, y) => x*y, map: color.map.viridis)
```

A map can also be supplied as a Typst `gradient` or an array of colors. You can post-process a map, e.g. `gradient.linear(..color.map.icefire).sharp(9)` for 9 discrete bands.

The default **style cycle** for line/marker colors across consecutive plots is `petroff10` (a 10-color qualitative palette). Override with `diagram.cycle`.

# Reference: Tick locators and formatters

A **tick locator** decides *where* ticks go; a **tick formatter** decides *how* tick values are rendered as labels. Lilaq auto-selects both based on the axis scale. Override via `axis.locate-ticks` / `axis.format-ticks` (and the subtick variants), or pass arguments to the current locator via `axis.tick-args`.

Built-in tick locators (`lq.tick-locate.*`): `linear`, `log`, `symlog`, `manual`, the subtick variants `subticks-linear` / `subticks-log` / `subticks-symlog`, and datetime locators `years`, `months`, `days`, `hours`, `minutes`, `seconds`.

Built-in tick formatters (`lq.tick-format.*`): `linear`, `log`, `symlog`, `fraction`, `manual`, `datetime`, plus the smart datetime helpers `datetime-smart-format`, `datetime-smart-first`, `datetime-smart-offset`.

## Configuring ticks (practical guide)

**Styling tick marks** with a show rule (`inset` = length inside axis, `outset` = outside; both `0pt` hides the marks but keeps labels):

```typ
#show: lq.set-tick(inset: 0pt, outset: 3pt, shorten-sub: 75%, stroke: blue)
```

**Styling tick labels** (select all tick labels):

```typ
#show lq.selector(lq.tick-label): set text(0.8em)
```

**Hiding tick labels but keeping ticks:** set `format-ticks: none` on the axis.

**Tick density / spacing** (semi-automatic): pass to the locator via `tick-args`, or use shortcuts:

```typ
#lq.diagram(xaxis: (tick-args: (density: 150%)))   // more/fewer ticks (default 100%)
#lq.diagram(xaxis: (tick-distance: 0.25))          // force exact spacing (linear locator)
```

The linear locator also has a `unit` parameter (e.g. mark multiples of pi).

**Manual tick locations** via `axis.ticks` (`none` = no ticks, `auto` = default locator, or an array):

```typ
#lq.diagram(
  xaxis: (ticks: (0.1, 0.4, 0.7, 1.0)),
  yaxis: (ticks: (0.0, 0.2, 0.7, 0.8, 1.0), subticks: none),
)
```

**Custom tick labels** (array of `(location, label)` tuples, often via `.zip` or `.enumerate()`):

```typ
#lq.diagram(
  xlim: (2, 6),
  xaxis: (ticks: range(2, 7).zip(([A], [B], [C], [D], [E])))
)
// or, when locations are 0,1,2,...:
// xaxis: (ticks: ([A], [B], [C], [D], [E]).enumerate())
```

**Subticks** via `axis.subticks`: `none` to remove, or an integer count between major ticks: `#lq.diagram(xaxis: (subticks: 1))`.

**Custom tick formatter:** a function `(ticks, ..) => labels` returning an array of label content, or a dictionary `(labels:, exponent:, offset:)` (last two optional). Reuse a built-in and post-process, or use the built-in's `suffix`:

```typ
#lq.diagram(xaxis: (format-ticks: lq.tick-format.linear.with(suffix: $k$)))
// naive: format-ticks: (ticks, ..) => ticks.map(str)  (beware float rounding)
```

Tick locations are also forwarded to the `grid`; setting `ticks: none` removes grid lines too.

# Reference: Data loading (`load-txt`)

```
lq.load-txt(data, delimiter: ",", comments: "#", skip-rows: 0, usecols: auto,
  header: false, converters: float)
```

Parses CSV/TSV text into **columns** (not rows, unlike Typst's built-in `csv`). Load the file text with Typst's `read(..)` first.

```typ
#let data = lq.load-txt(read("data.csv"))
#lq.diagram(lq.plot(data.at(0), data.at(1)))

// With a header row -> dictionary keyed by column name:
#let d = lq.load-txt(read("data.csv"), header: true)
#lq.diagram(lq.plot(d.time, d.value))
```

- **data** `str`: raw text (from `read(..)`).
- **delimiter** `str` (default `","`): column separator (use `"\t"` for TSV).
- **comments** `str` (default `"#"`): line-comment marker.
- **skip-rows** `int` (default `0`): leading rows to skip.
- **usecols** `auto | array` (default `auto`): indices of columns to keep.
- **header** `bool` (default `false`): if `true`, first line names columns; result is a dictionary.
- **converters** `function | type | dictionary` (default `float`): conversion applied to entries; single function/type for all columns, or a dictionary keyed by column index/header name (with optional `rest` default). Use e.g. `converters: (0: float, 1: str)`.

# Reference: `layout` (subplot grids)

```
lq.layout(body)
```

A show rule that aligns multiple diagrams placed in a Typst `grid` so their axis spines line up across rows/columns, regardless of ticks, labels, titles, or legends.

```typ
#show: lq.set-diagram(width: 4cm, height: 2.2cm)

#figure({
  show: lq.layout  // special layout rule
  grid(
    columns: 2, row-gutter: 1em, column-gutter: 1em,
    lq.diagram(lq.plot((1, 2, 3), (3, 2, 5))),
    lq.diagram(lq.bar((1, 2, 3), (3, 2, 5))),
    lq.diagram(lq.plot((5, 7, 8, 9), (2, 3, 3, 4))),
    lq.diagram(lq.bar((1, 2, 3), (11, 1, 4))),
  )
})
```

# Tutorial: Styling and themes (set / show rules)

Most Lilaq elements (`diagram`, `title`, `legend`, `label`, `grid`, `tick`, `tick-label`, `spine`, `mark`, `errorbar`, ...) are stylable "element functions." Because Typst does not yet support custom element functions natively, Lilaq uses a workaround API instead of native `#set`/`#show`:

| Conceptually (not valid yet)                     | Write this instead                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| `#set lq.diagram(width: 10cm)`                   | `#show: lq.set-diagram(width: 10cm)`                                     |
| `#show lq.diagram: set text(0.8em)`              | `#show lq.selector(lq.diagram): set text(0.8em)`                         |
| `#show lq.label.where(kind: "x"): set text(red)` | `#show: lq.show_(lq.label.with(kind: "x"), it => { set text(red); it })` |

Key helpers:
- **`lq.set-<element>(..)`** — used in a `#show:` rule to set default parameters for all instances of that element (e.g. `lq.set-diagram`, `lq.set-tick`, `lq.set-grid`, `lq.set-spine`, `lq.set-errorbar`, `lq.set-tick-label`, `lq.set-legend`, ...).
- **`lq.selector(lq.<element>)`** — a selector usable in `#show <sel>: set ...` to apply native set rules (text, align, ...) to those elements.
- **`lq.show_(lq.<element>.with(<filter>), it => ...)`** — apply a transformation/show rule, optionally filtered (e.g. only x labels).
- **`lq.cond-set(lq.<element>.with(<filter>), ..params)`** — conditionally set parameters for a filtered subset (e.g. only the x grid).

Common recipes:

```typ
// Smaller text in all diagrams:
#show lq.selector(lq.diagram): set text(.8em)
// Only legend / tick labels:
#show lq.selector(lq.legend): set text(.8em)
#show lq.selector(lq.tick-label): set text(.8em)

// Align axis labels and title:
#show lq.selector(lq.label): set align(top + right)
#show lq.selector(lq.title): set align(right)

// Default log x-scale for all following diagrams:
#show: lq.set-diagram(xscale: "log")
```

**Reusable theme/preset** = a function applied via a `#show:` rule, scoped with a code block to limit its reach:

```typ
#let spectrum-plot = it => {
  show: lq.set-diagram(
    title: [Spectrum], ylabel: [Intensity], xlabel: [Wavelength],
    yscale: "log", xaxis: (subticks: none)
  )
  show: lq.set-tick(outset: 2pt, inset: 0pt)
  it
}

#{
  show: spectrum-plot
  lq.diagram(lq.plot((1, 3), (1, 100)))
}
```

This is exactly how Lilaq's built-in themes are built.

# Tutorial: Style cycles

A style cycle is a repeating sequence of styles (colors / marks / strokes) applied to consecutive plots so they are distinguishable without manual styling and consistent across diagrams. Set via `diagram.cycle`. Most plot types use it (exceptions: `boxplot`, `colormesh`, `contour`).

Three ways to define a cycle:

```typ
// 1) Array of colors:
#lq.diagram(cycle: (red, teal), ...)

// 2) Array of dictionaries (color/mark/stroke, all optional):
#lq.diagram(
  cycle: ((color: red, mark: "x"), (color: teal, mark: "+")),
  ...
)

// 3) Array of content-transforming functions (full control):
#lq.diagram(
  cycle: (
    it => { set lq.style(fill: red); set lq.mark(align: lq.marks.s3); it },
    it => { set lq.style(fill: teal); set lq.mark(align: lq.marks.s); it },
  ),
  ...
)
```

Style properties (set inside cycle functions):
- `lq.style.fill` — main color (sets line/mark/fill at once; lowest precedence, overridden by explicit non-auto settings).
- `lq.style.stroke` — main stroke for lines and bars (inherits color from `lq.style.fill` if none given).
- `lq.mark.fill` / `lq.mark.stroke` — mark fill/stroke (inherit from `lq.style.fill`).
- `lq.mark.inset` — mark size (temporary name). `lq.mark.align` — the mark shape (temporary name; one of `lq.marks` or a custom function).

Because `plot`/`scatter`/etc. default `stroke`, `mark`, `mark-size` to `auto`, those inherit from the current cycle/style; set them explicitly per plot to override.

Built-in color sequences (under `lq.color.map`): default **`petroff10`** (CVD-optimized, by Petroff), and **`okabe-ito`** (a.k.a. "wong" in Makie.jl). Sequential maps from the color reference can also be used. The `lq.cycle` module has helpers for generating and folding color cycles.

# Tutorial: Datetime support

Most plotting functions accept arrays of Typst `datetime` values as coordinates. When an axis has datetime data, its scale switches to a datetime scale with an adaptive locator (years / months / days / hours / minutes / seconds). `diagram.xlim`/`ylim` also accept datetimes.

```typ
#lq.diagram(
  title: [Source code size], ylabel: [kB], xlabel: [Time],
  lq.plot(
    (
      datetime(year: 2025, month: 3, day: 14),
      datetime(year: 2025, month: 5, day: 14),
      datetime(year: 2026, month: 3, day: 14),
    ),
    (254, 295, 398)
  )
)
```

**Fixed format string** (Typst datetime format syntax) or a `datetime => content` function:

```typ
#lq.diagram(
  xaxis: (
    format-ticks: lq.tick-format.datetime.with(format: "[year]/[month]"),
    tick-args: (density: 80%)
  ),
  ...
)
```

**Rotating long date labels:**

```typ
#show: lq.show_(lq.tick-label.with(kind: "x"), rotate.with(-90deg, reflow: true))
```

**Smart formatter** (default): `tick-format.datetime.format` defaults to `tick-format.datetime-smart-format`, which shortens labels by showing only the changing leading component, promoting the first-of-period to the larger unit, and pushing missing info to an axis **offset**. Configure component formats:

```typ
#show: lq.tick-format.set-datetime-smart-format(month: "[month repr:long]")
#show: lq.tick-format.set-datetime-smart-format(day: "[weekday repr:short]")
#show: lq.tick-format.set-datetime-smart-format(smart-first: false)   // disable promotion
// What to show for the first of a period:
#show: lq.tick-format.set-datetime-smart-first(day: "[day]\n[month repr:short]")
// The axis offset (missing higher-order components):
#show: lq.tick-format.set-datetime-smart-offset(month: "[year] [month repr:long]")
```

Each smart-format/first/offset element has fields `year, month, day, hour, minute, second`, each accepting a format string or `datetime => content`. **Localization:** the built-in `datetime` display is English-only; supply a function to localize, e.g.

```typ
#let french-months = ("Janvier", "Février", "Mars", /* ... */)
#show: lq.tick-format.set-datetime-smart-format(
  month: dt => french-months.at(dt.month() - 1)
)
```

# Translation patterns: matplotlib / pgfplots (LaTeX) to Lilaq

This table maps common plotting concepts to their Lilaq equivalents. Use it when converting existing plot code into Lilaq + Typst.

| Concept                      | matplotlib                     | pgfplots (LaTeX)                | Lilaq                                                                           |
| ---------------------------- | ------------------------------ | ------------------------------- | ------------------------------------------------------------------------------- |
| Figure/axes container        | `fig, ax = plt.subplots()`     | `\begin{axis}...\end{axis}`     | `lq.diagram(...)`                                                               |
| Line plot                    | `ax.plot(x, y)`                | `\addplot coordinates {...}`    | `lq.plot(x, y)`                                                                 |
| Plot a function              | `ax.plot(x, np.sin(x))`        | `\addplot {sin(x)}`             | `lq.plot(x, calc.sin)` or `lq.plot(x, t => calc.sin(t))`                        |
| Scatter                      | `ax.scatter(x, y, s=.., c=..)` | `\addplot[only marks]`          | `lq.scatter(x, y, size: .., color: ..)`                                         |
| Markers only, no line        | `ax.plot(x, y, 'o', ls='')`    | `[only marks, mark=*]`          | `lq.plot(x, y, mark: "o", stroke: none)`                                        |
| Bar chart                    | `ax.bar(x, h)`                 | `\addplot[ybar]`                | `lq.bar(x, h)`                                                                  |
| Horizontal bar               | `ax.barh(y, w)`                | `[xbar]`                        | `lq.hbar(y, w)`                                                                 |
| Stem                         | `ax.stem(x, y)`                | —                               | `lq.stem(x, y)`                                                                 |
| Fill between                 | `ax.fill_between(x, y1, y2)`   | `\addplot fill between`         | `lq.fill-between(x, y1, y2: y2)`                                                |
| Error bars                   | `ax.errorbar(x, y, yerr=..)`   | `[error bars]`                  | `lq.plot(x, y, yerr: ..)`                                                       |
| Histogram-like / boxplot     | `ax.boxplot(data)`             | —                               | `lq.boxplot(data)`                                                              |
| Heatmap                      | `ax.pcolormesh(X, Y, Z)`       | `\addplot[matrix plot]`         | `lq.colormesh(x, y, z, map: ..)`                                                |
| Contour                      | `ax.contour(X, Y, Z)`          | `\addplot3[contour]`            | `lq.contour(x, y, z)`                                                           |
| Vector field                 | `ax.quiver(...)`               | `\addplot[quiver]`              | `lq.quiver(x, y, dirs)`                                                         |
| Title                        | `ax.set_title("T")`            | `title={T}`                     | `title: [T]` (diagram arg)                                                      |
| Axis labels                  | `ax.set_xlabel`, `set_ylabel`  | `xlabel=`, `ylabel=`            | `xlabel: $x$`, `ylabel: $y$`                                                    |
| Axis limits                  | `ax.set_xlim(a, b)`            | `xmin=a, xmax=b`                | `xlim: (a, b)`                                                                  |
| Log scale                    | `ax.set_yscale("log")`         | `ymode=log`                     | `yscale: "log"`                                                                 |
| Invert axis                  | `ax.invert_yaxis()`            | `y dir=reverse`                 | `yaxis: (inverted: true)`                                                       |
| Legend                       | `ax.legend()` + `label=`       | `\legend{}` / `\addlegendentry` | add `label: [..]` to plots (auto legend); position via `legend: (position: ..)` |
| Grid                         | `ax.grid(True)`                | `grid=both`                     | grid is on by default; `grid: none` to remove                                   |
| Tick positions               | `ax.set_xticks([..])`          | `xtick={..}`                    | `xaxis: (ticks: (..))`                                                          |
| Tick labels                  | `ax.set_xticklabels([..])`     | `xticklabels={..}`              | `xaxis: (ticks: locations.zip(labels))`                                         |
| Categorical labels           | `ax.bar(names, vals)`          | `symbolic x coords`             | `xaxis: (ticks: names.enumerate())` + `lq.bar(range(n), vals)`                  |
| Vertical/horizontal ref line | `ax.axvline(x)` / `axhline(y)` | —                               | `lq.vlines(x)` / `lq.hlines(y)`                                                 |
| Text annotation              | `ax.annotate`/`ax.text`        | `\node`                         | `lq.place(x, y, [text])`                                                        |
| Color of a series            | `color="green"`                | `color=green`                   | `color: green` (per plot)                                                       |
| Line style                   | `ls="--"`                      | `dashed`                        | `stroke: (dash: "dashed")`                                                      |
| Line width                   | `lw=2`                         | `line width=2pt`                | `stroke: 2pt` or `stroke: (thickness: 2pt)`                                     |
| Marker size                  | `ms=8`                         | `mark size=`                    | `mark-size: 8pt`                                                                |
| Step plot                    | `ax.step(x, y)`                | `const plot`                    | `lq.plot(x, y, step: center)`                                                   |
| Smooth curve                 | (interp)                       | `smooth`                        | `lq.plot(x, y, smooth: true)`                                                   |
| Figure size                  | `figsize=(w, h)`               | `width=, height=`               | `width: ..cm, height: ..cm` (data-area sizes)                                   |
| Subplots                     | `plt.subplots(r, c)`           | `groupplots`                    | Typst `grid(...)` wrapped in `#show: lq.layout`                                 |
| Colorbar                     | `fig.colorbar(..)`             | `colorbar`                      | `lq.colorbar(plotobj)`                                                          |
| Equal aspect                 | `ax.set_aspect("equal")`       | `axis equal`                    | `aspect-ratio: 1.0`                                                             |

Notes:
- Lilaq `width`/`height` size the **data area** by default (not the whole figure), unlike matplotlib `figsize`. Use `0% + length` to include axes/labels.
- Multiple series: pass multiple plot objects as positional args to one `diagram`. Colors auto-advance via the cycle.
- For repeated styling across many diagrams, prefer a theme (`#show: lq.set-diagram(...)`) over per-plot args.
- Math in labels uses Typst math: `xlabel: $x^2$`, `ylabel: $sqrt(y)$`, `title: [$E = m c^2$]`.

# Complete worked examples

### Multi-series line plot with legend, labels, log y-axis

```typ
#import "@preview/lilaq:0.6.0" as lq

#let x = lq.linspace(1, 100, num: 100)
#lq.diagram(
  title: [Growth comparison],
  xlabel: $t$,
  ylabel: $f(t)$,
  yscale: "log",
  legend: (position: bottom + right),
  lq.plot(x, x.map(t => t), label: [linear]),
  lq.plot(x, x.map(t => t*t), mark: none, label: [quadratic]),
  lq.plot(x, x.map(t => calc.exp(t/20)), mark: none, label: [exponential]),
)
```

### Scatter with color mapping and colorbar

```typ
#let pts = lq.linspace(0, 10, num: 40)
#let s = lq.scatter(
  pts, pts.map(p => calc.sin(p)),
  color: pts, size: pts.map(p => 30 + 10*p), map: color.map.plasma
)
#lq.diagram(s)
#h(.5em)
#lq.colorbar(s, label: [value])
```

### Grouped bar chart with categorical labels and rotated ticks

```typ
#show: lq.show_(
  lq.tick-label.with(kind: "x"),
  it => box(width: 0pt, align(center, rotate(-30deg, reflow: true, it)))
)
#let cats = ("Q1", "Q2", "Q3", "Q4")
#lq.diagram(
  ylabel: [Revenue],
  legend: (position: top + left),
  xaxis: (ticks: cats.enumerate(), subticks: none),
  lq.bar(range(4), (3, 5, 4, 6), width: 0.4, offset: -0.2, label: [2024]),
  lq.bar(range(4), (4, 4, 5, 7), width: 0.4, offset: 0.2, label: [2025]),
)
```

### Function plot with shaded region and annotation

```typ
#let x = lq.linspace(-3, 3, num: 100)
#lq.diagram(
  xlabel: $x$, ylabel: $y$,
  lq.fill-between(x, x.map(t => calc.exp(-t*t)), fill: blue.transparentize(70%)),
  lq.plot(x, x.map(t => calc.exp(-t*t)), mark: none, color: blue),
  lq.vlines(0, stroke: (dash: "dashed", paint: gray)),
  lq.place(0, 1, align: bottom, pad(4pt)[peak]),
)
```

# Secondary, twin, and extra axes

Add an `lq.axis(...)` object as a child of the diagram to create an additional axis (beyond the main x/y set via `xaxis`/`yaxis`).

- **Dependent secondary axis** (same data, different unit/scale): use `axis.functions: (forward, backward)` where the two are inverses. E.g. a top x-axis showing energy when the bottom shows velocity:
  ```typ
  #lq.diagram(
    xlabel: [velocity],
    lq.plot(x, y),
    lq.axis(kind: "x", position: top, label: [energy],
            functions: (v => m*v*v, e => calc.sqrt(e/m)))
  )
  ```
- **Independent / twin axis** (different data range on the same side family): pass plots to the axis via `..plots`; its limits are computed from those plots. Mutually exclusive with `functions` and `lim`.
- **Placement**: `position` accepts `top`/`bottom` (x) or `left`/`right` (y), a coordinate on the other axis, a length/relative, or `(align:, offset:)`. When a secondary axis is added or position is non-standard, `mirror` auto-disables.
- **Mirrors**: by default the main axes mirror their ticks on the opposite side; disable with `mirror: false` or `mirror: (ticks: false, tick-labels: false)`.

# Subplots / plot grids

Place several `lq.diagram(...)` calls in a Typst `grid(...)` and apply `#show: lq.layout` so their spines align across rows/columns regardless of differing ticks/labels/titles. See the `layout` reference above for a full example. The `diagram.bounds` parameter (`"strict"` default, `"relaxed"`, `"data-area"`) controls how bounding boxes are computed, which affects alignment in grids.

# Quick reference: common per-plot styling arguments

- `color: <color>` — series color (line + marks).
- `stroke: <stroke>` — line style; dictionary form `(paint:, thickness:, dash:, cap:, join:)`. `stroke: none` removes the line.
- `mark: "<name>" | none` — marker (see mark shapes list). `mark-size: <length>`.
- `label: [..]` — legend entry (omit to keep out of legend).
- `smooth: true` — Bézier interpolation. `step: start|center|end` — stair plot.
- `z-index: <number>` — draw order (axes are at 20).

Typst color/stroke building blocks: named colors (`red`, `blue`, `green`, `orange`, `purple`, `teal`, `gray`, `black`, `white`, ...), `rgb("RRGGBB")`, `luma(80%)`, `color.darken(50%)`, `color.lighten(..)`, `color.transparentize(..)`; dashes `"solid"`, `"dashed"`, `"dotted"`, `"dash-dotted"`.

# Secondary, twin, and extra axes

Add an `lq.axis(...)` object as a child of the diagram to create an additional axis (beyond the main x/y set via `xaxis`/`yaxis`).

- **Dependent secondary axis** (same data, different unit/scale): use `axis.functions: (forward, backward)` where the two are inverses. E.g. a top x-axis showing energy when the bottom shows velocity:
  ```typ
  #lq.diagram(
    xlabel: [velocity],
    lq.plot(x, y),
    lq.axis(kind: "x", position: top, label: [energy],
            functions: (v => m*v*v, e => calc.sqrt(e/m)))
  )
  ```
- **Independent / twin axis** (different data range on the same side family): pass plots to the axis via `..plots`; its limits are computed from those plots. Mutually exclusive with `functions` and `lim`.
- **Placement**: `position` accepts `top`/`bottom` (x) or `left`/`right` (y), a coordinate on the other axis, a length/relative, or `(align:, offset:)`. When a secondary axis is added or position is non-standard, `mirror` auto-disables.
- **Mirrors**: by default the main axes mirror their ticks on the opposite side; disable with `mirror: false` or `mirror: (ticks: false, tick-labels: false)`.

# Subplots / plot grids

Place several `lq.diagram(...)` calls in a Typst `grid(...)` and apply `#show: lq.layout` so their spines align across rows/columns regardless of differing ticks/labels/titles. See the `layout` reference above for a full example. The `diagram.bounds` parameter (`"strict"` default, `"relaxed"`, `"data-area"`) controls how bounding boxes are computed, which affects alignment in grids.

# Quick reference: common per-plot styling arguments

- `color: <color>` — series color (line + marks).
- `stroke: <stroke>` — line style; dictionary form `(paint:, thickness:, dash:, cap:, join:)`. `stroke: none` removes the line.
- `mark: "<name>" | none` — marker (see mark shapes list). `mark-size: <length>`.
- `label: [..]` — legend entry (omit to keep out of legend).
- `smooth: true` — Bézier interpolation. `step: start|center|end` — stair plot.
- `z-index: <number>` — draw order (axes are at 20).

Typst color/stroke building blocks: named colors (`red`, `blue`, `green`, `orange`, `purple`, `teal`, `gray`, `black`, `white`, ...), `rgb("RRGGBB")`, `luma(80%)`, `color.darken(50%)`, `color.lighten(..)`, `color.transparentize(..)`; dashes `"solid"`, `"dashed"`, `"dotted"`, `"dash-dotted"`.
