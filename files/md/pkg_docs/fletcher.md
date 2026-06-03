# Fletcher: LLM Reference Guide

> Fletcher is a Typst package for drawing diagrams made of **nodes** and **edges (arrows)**, built on top of CeTZ. Use it for commutative diagrams, flow charts, state machines, block diagrams, graphs, and similar figures.
>
> Package: `@preview/fletcher:0.5.8` ( github.com/Jollywatt/typst-fletcher )

This document is written so a model can generate correct fletcher code without seeing any rendered images. Every example includes a plain-text description of what it draws. When you generate a diagram, reason about coordinates and layout from these descriptions rather than expecting to "see" output.

---

## 1. Setup and mental model

### Import

```typst
#import "@preview/fletcher:0.5.8" as fletcher: diagram, node, edge
```

Do **not** import with `*`, because many internal functions are also exported and would pollute the namespace. Import `diagram`, `node`, `edge`, and pull shapes from the submodule when needed:

```typst
#import fletcher.shapes: diamond, pill, hexagon, brace, bracket, parallelogram, trapezium, triangle, house, chevron, octagon, cylinder, ellipse, rect, circle, paren
```

### The three building blocks

- `diagram(..)` is the container. It lays nodes and edges out on a flexible grid (a CeTZ canvas).
- `node(coord, label, ..options)` is content centered at a coordinate. Nodes auto-size to their label.
- `edge(..vertices, marks, label, ..options)` connects two or more coordinates with a line, arc, or polyline, optionally with arrowheads and a label.

### Two ways to author a diagram

**Code mode** (most flexible, supports variables, loops, conditionals):

```typst
#diagram(
  node((0,0), $A$),
  node((1,0), $B$),
  edge((0,0), (1,0), $f$, "->"),
)
```

**Math mode** (compact, nodes separated by `&`, rows by `\`):

```typst
#diagram($
  G edge(f, ->) edge("d", pi, ->>) & im(f) \
  G slash ker(f) edge("ur", tilde(f), "hook-->")
$)
```
*Draws: top-left node `G`, top-right node `im(f)`, bottom-left node `G/ker(f)`. An arrow labeled `f` goes right from `G` to `im(f)`; an arrow labeled `pi` (with a two-headed tip) goes down to `G/ker(f)`; a hooked dashed arrow labeled `f-tilde` goes up-right from the bottom node to `im(f)`.*

In math mode, each `&`-separated entry is a node at the next column; `\` starts a new row. `edge(..)` written inside a math cell attaches to that cell as its starting node.

You can mix node and edge results freely: each `node(..)` / `edge(..)` call can be a separate positional argument to `diagram(..)`, or grouped inside a `{ ... }` code block where you can use loops and scripting.

```typst
#diagram(
  node((0, 0), $A$),
  node((1, 0), $B$),
  {
    node((2, 0), $C$)
    node((3, 0), $D$)
  },
  for x in range(4) { node((x, 1), [#x]) },
)
```

---

## 2. Coordinates

Fletcher supports two coordinate kinds plus CeTZ-style expressions.

### Elastic (uv) coordinates: row/column numbers

Written as `(u, v)`. By default `u` increases to the right (`→`) and `v` increases **downward** (`↓`). So `(0,0)` is top-left, `(1,0)` is one column right, `(0,1)` is one row down.

- The grid grows like a table: placing a node makes its row and column large enough to fit it.
- Coordinates can be **fractional** (e.g. `(0.5, 1)`), which positions a node partway between columns and proportionally splits the column widths.
- `cell-size` sets the minimum row/column size; `spacing` sets the gutter between rows/columns.
- Elastic coordinates **affect layout**: node positions and sizes determine row/column sizes.

Change axis orientation with the `axes` option of `diagram()`:
- `axes: (ltr, ttb)` (default): u goes right, v goes down.
- `axes: (ltr, btt)`: v goes **up** the page.
- `axes: (ttb, ltr)`: matrix convention (row, column).

### Absolute (xy) coordinates: physical lengths

Written with units, e.g. `(10mm, 5mm)`. These are physical offsets independent of row/column sizes. Absolutely positioned nodes are **floating**: they never affect the layout of other nodes. Use them to place things exactly.

| Elastic / uv, e.g. `(2, 1)`      | Absolute / xy, e.g. `(10mm, 5mm)` |
| -------------------------------- | --------------------------------- |
| Dimensionless row/column numbers | Physical lengths                  |
| Depend on row/column sizes       | Independent of row/column sizes   |
| Affect diagram layout            | Floating, never affect layout     |

### Coordinate expressions (CeTZ-style)

You can combine coordinate systems with expressions:

- Relative: `(rel: (1, 2))` or `(rel: (1, 2), to: <name>)`
- Polar: `(45deg, 1cm)` (angle, radius)
- Interpolation: `(<P>, 80%, <Q>)` (80% of the way from P to Q)
- Perpendicular: `(<X>, "|-", <Y>)`
- Node anchors: `<A.north>` or `(name: "A", anchor: "north")`

Example placing nodes in a polar ring around a named origin:

```typst
#diagram(
  node((1, 0), name: <origin>),          // elastic coordinate
  for θ in range(16).map(i => i/16*360deg) {
    node((rel: (θ, 10mm), to: <origin>), $ * $, inset: 1pt)  // absolute polar offset
    edge(<origin>)
  }
)
```
*Draws: a center node, with 16 asterisk nodes arranged evenly in a circle 10mm around it, each connected back to the center by an edge.*

### Relative coordinate shorthands (strings)

A string of direction letters is shorthand for a relative offset `(rel: (du, dv))`. Letters: `l`/`w` (left/west), `r`/`e` (right/east), `u`/`t`/`n` (up/top/north), `d`/`b`/`s` (down/bottom/south). Combine with commas for multi-segment poly edges.

- `"u"` = up, `"sw"` = down-left, `"rr"` = two columns right.
- `"d,r,ur"` = down, then right, then up-right (three segments).

These work for any edge vertex except the first.

### Node anchors

If a node has a `name` (a label, not a string), you can reference anchor points on its outline, just like CeTZ: `<A.north>`, `<A.south-east>`, `<A.center>`, etc. `<A.north>` and `(name: "A", anchor: "north")` are equivalent. Anchors count as **absolute** coordinates, so nodes positioned by an anchor are floating.

```typst
#diagram(
  node((0,0), $A$, name: <A>),
  node((1,0.6), $B$, name: <B>),
  edge(<A>, <B>, "->"),
  node((rel: (1, 0), to: <B>), $C$)   // C placed one unit right of B
)
```
*Draws: A at top-left, B lower and to the right, an arrow A to B, and C one column to the right of B.*

---

## 3. Nodes

```
node(coord, label, ..options)
```

Nodes are content centered at a coordinate, auto-fitting to the label plus an `inset`. You can override `width`, `height`, or `radius`, and set `stroke` and `fill`.

### Basic examples

```typst
#diagram(
  spacing: (5pt, 4em),
  node((0,0), $f$),                                  // bare label, no outline
  node((1,0), $f$, stroke: 1pt),                     // outlined (circle/rect auto)
  node((2,0), $f$, stroke: blue, shape: rect),       // forced rectangle
  node((3,0), $f$, stroke: 1pt, radius: 6mm, extrude: (0, 3)),  // double outline
  node((0,1), `xyz`, fill: blue.lighten(70%)),
  node((1,1), `xyz`, stroke: (paint: blue, dash: "dashed"), inset: 1em),
  node((2,1), `xyz`, fill: blue.lighten(70%), stroke: blue, extrude: (0, -2)),
  node((3,1), `xyz`, fill: blue.lighten(70%), height: 5em, corner-radius: 5pt),
)
```
*Draws two rows of small nodes demonstrating: no outline, thin outline, rectangle, double-stroked rounded node; then a filled node, a dashed-outline node with large inset, a double-stroked filled node, and a tall rounded filled node.*

Key takeaways:
- `extrude: (0, 3)` draws a second outline offset outward by 3 (multiples of stroke thickness), giving a double-stroke effect. `(0, -2)` offsets inward.
- `inset` is padding between label and outline; `outset` is extra margin used only for where edges attach (does not affect layout).
- `corner-radius` rounds rectangle corners.

### Node shapes

By default a node is a circle or rectangle depending on label aspect ratio. Override with `shape:`. Accepts `rect`, `circle`, a shape from `fletcher.shapes`, or a custom function.

```typst
#import fletcher.shapes: pill, parallelogram, diamond, hexagon, brace
#diagram(
  node-fill: gradient.radial(white, blue, radius: 200%),
  node-stroke: blue,
  (
    node((0,0), [Blue Pill], shape: pill),
    node((1,0), [_Slant_], shape: parallelogram.with(angle: 20deg)),
    node((0,1), [Choice], shape: diamond),
    node((1,1), [Stop], shape: hexagon, extrude: (-3, 0), inset: 10pt),
  ).intersperse(edge("o--|>")).join(),
  node(enclose: ((0,0), (1,1)), shape: brace.with(label: [Group]))
)
```
*Draws four shaped nodes (pill, parallelogram, diamond, hexagon) connected in sequence by edges that have a small circle tail and an arrowhead, all surrounded by a brace labeled "Group".* The `.intersperse(edge(..)).join()` pattern places an edge between each consecutive pair of nodes.

Predefined shapes (all in `fletcher.shapes`, many configurable via `.with(..)`):

`rect`, `circle`, `ellipse`, `pill`, `parallelogram`, `trapezium`, `house`, `diamond`, `triangle`, `chevron`, `hexagon`, `octagon`, `cylinder`, plus the "glyph" shapes `stretched-glyph`, `brace`, `bracket`, `paren` (drawn along one edge of a node, great with `enclose`).

To set a parameter: `shape: hexagon.with(angle: 45deg)`. See Section 7 for each shape's parameters.

Custom shapes: pass a function `(node, extrude, ..parameters) => (..)` returning CeTZ objects. You must handle outline extrusion yourself.

### Node groups via `enclose`

Give `enclose:` an array of coordinates or node names and the node resizes to surround them. The node's `pos` (center) no longer affects its own position when `enclose` is set, but still affects connecting edges.

```typst
#diagram(
  node-stroke: 0.6pt,
  node($Sigma$, enclose: ((1,1), (1,2)),   // spans two coordinates
    inset: 10pt, stroke: teal, fill: teal.lighten(90%), name: <bar>),
  node((2,1), [X]),
  node((2,2), [Y]),
  edge((1,1), "r", "->", snap-to: (<bar>, auto)),
  edge((1,2), "r", "->", snap-to: (<bar>, auto)),
)
```
*Draws: a tall teal box labeled Σ enclosing the cells (1,1) and (1,2); X and Y to its right; two arrows from the Σ box to X and Y.*

Enclose by name to group existing nodes:

```typst
#diagram(
  node-stroke: 0.6pt, node-fill: white,
  node((0,1), [X]),
  edge("->-", bend: 40deg),
  node((1,0), [Y], name: <y>),
  node($Sigma$, enclose: ((0,1), <y>),
    stroke: teal, fill: teal.lighten(90%),
    snap: -1,         // lower snap priority so edges prefer inner nodes
    name: <group>),
  edge(<group>, <z>, "->"),
  node((2.5,0.5), [Z], name: <z>),
)
```
*Draws: a teal group box around X and Y, with an edge from the group to a node Z on the right.* Set a lower `snap` so edges snap to the enclosed nodes first.

### Full `node()` option reference

```
node(
  pos: coordinate,                 // default auto; center coordinate (uv, xy, or expression)
  name: label | string | none,     // default none; label to reference this node (labels, e.g. <A>)
  label: content,                  // default none; content shown inside
  inset: length,                   // default auto -> diagram node-inset (6pt); padding label..outline
  outset: length,                  // default auto -> diagram node-outset (0pt); edge-attach margin, no layout effect
  fill: paint,                     // default auto -> diagram node-fill (none)
  stroke: stroke,                  // default auto -> diagram node-stroke (none)
  extrude: array,                  // default (0,); offsets for multi-stroke outlines
  width: length | auto,            // default auto (fit label)
  height: length | auto,           // default auto (fit label)
  radius: length,                  // circle/rounded radius
  enclose: array,                  // default (); coords/names to surround
  corner-radius: length,           // default auto -> diagram node-corner-radius (none)
  shape: rect | circle | function, // default auto -> diagram node-shape
  defocus: number,                 // default auto -> diagram node-defocus (0.2)
  snap: number | false,            // default 0; edge-snapping priority (false = manual only)
  layer: number,                   // default auto; higher draws on top
  post: function,                  // default x => x; intercept cetz objects before drawing
  ..args,                          // first positional is pos, second is label
)
```

Notes on specific options:
- **`name`** must be a label like `<A>` (not a string) so it cannot collide with positional string args to `edge`. Strings are auto-converted.
- **`extrude`**: e.g. `(0,)` single stroke, `(0, 2)` and `(2, 0)` double strokes offset outward, `(0, -2.5, 2mm)` triple. Fill is drawn inside the first offset.
- **`width`/`height` not auto**: wrap the label in `align(..)` to control placement, e.g. `node((0,0), align(bottom + left)[¡Hola!], width: 3cm, height: 2cm)`.
- **`defocus`** (0 to 1, default 0.2): for wide/tall nodes, spreads incoming edges out instead of pointing them all at the exact center. Set `defocus: 0` to aim every edge at the center.
- **`snap`**: higher priority means edges snap here preferentially when nodes overlap. `false` means edges only snap if you set `snap-to` manually. A group node enclosing others defaults to `layer: -1`.
- **`post`** / `fletcher.hide(..)`: hide elements without affecting layout (used for Touying animations).

---

## 4. Edges

```
edge(..vertices, marks, label, ..options)
```

An edge connects two or more coordinates. By default it snaps to the bounding shapes of nodes at its first and last vertices (after applying each node's `outset`). It can carry a label, bend into an arc, turn corners, and display arrowheads (marks).

### Specifying vertices

The leading positional arguments are vertices. There can be two or more. Vertices may be any coordinate expression (uv, xy, anchors, `rel`, polar, etc.). Only the first and last vertices auto-snap to nodes.

```typst
#diagram(
  edge((0,0), (1,1), "->", `line`),                    // two vertices -> line
  edge((2,0), (3,1), "->", bend: -30deg, `arc`),       // bend -> arc
  edge((4,0), (4,1), (5,1), (6,0), "->", `poly`),      // 3+ vertices -> poly
)
```
*Draws three labeled edges: a straight diagonal line, a curved arc, and a multi-segment polyline.*

`()` refers to the **previous vertex** of the same edge, useful for chained relative coordinates.

```typst
#diagram(edge-stroke: 1pt, node-stroke: 1pt, {
  node((0,0), name: <x>)[Input, $arrow(x)$]
  node((0,1), name: <y>)[Ground truth, $arrow(y)$]
  node((1,0.5), name: <out>)[MSE]
  let verts = (                       // () == this edge's previous vertex
    ((), "-|", (<y.east>, 50%, <out.west>)),
    ((), "|-", <out>), <out>)
  edge(<x>, ..verts, "->")            // first () == <x>
  edge(<y>, ..verts)                  // first () == <y>
})
```
*Draws: Input and Ground truth nodes on the left, an MSE node on the right, and two arrows routed with right-angle turns into MSE.*

### `auto` vertices and implicit coordinates

- If the first or last vertex is `auto`, the **previous** or **next** node (in argument order) is used.
- A single vertex `edge(to)` means `edge(auto, to)`.
- With no vertices, `edge(..)` connects the nearest nodes on either side.

```typst
#diagram(
  node((0,0), [London]),
  edge("..|>", bend: 20deg),    // connects London (prev) to Paris (next)
  edge("<|--", bend: -20deg),
  node((1,1), [Paris]),
)
```
*Draws: London and Paris connected by two curved edges (a dotted arrow and a dashed arrow), bending opposite ways.*

Handy in math mode: `#diagram($ L edge("->", bend: #30deg) & P $)` draws L and P with a curved arrow between them.

Relative shorthand + implicit coords:
```typst
#diagram($ A edge("rr", ->, #[jump!], bend: #30deg) & B & C $)
```
*Draws: A, B, C in a row, with a labeled "jump!" arc skipping from A two columns right to C.*

### Edge types: line, arc, poly

Three `kind`s: `"line"`, `"arc"`, `"poly"`. If unspecified, `kind` is inferred: `bend` implies `"arc"`; a `corner` or more than two vertices implies `"poly"`. These poly edges are equivalent:

```typst
edge((4,0), (5,1), (6,1), (7,0), "->", `poly`)
edge((4,0), (rel: (0,1)), (rel: (1,0)), (rel: (1,-1)), "->", `poly`)
edge((4,0), "d", "r", "ur", "->", `poly`)
edge((4,0), "d,r,ur", "->", `poly`)
```

### Adjusting where edges connect

- **`outset`** on the target node: larger outset means the edge stops farther from the node boundary.
- **Fractional vertex coordinates**: nudge an endpoint along the boundary, e.g. `edge((-0.1,0), (-0.4,1))`.
- **`shift`**: move the whole edge sideways by an absolute length or coordinate delta, perpendicular to its direction. A pair `(from, to)` shifts each end independently; a single value shifts both.

```typst
#diagram($A edge(->, shift: #3pt) edge(<-, shift: #(-3pt)) & B$)
```
*Draws two parallel arrows between A and B (one pointing each way), offset 3pt apart.*

For multi-vertex edges, `shift` only affects the first and last segments.

- **`defocus`** (on nodes): edges incident at an angle are slightly fanned out for wide/tall nodes by default. See node `defocus`.

### Loops and corners

- **`bend`** (angle): curvature. `0deg` straight; positive bends clockwise. Larger magnitudes bow out more.
- **`loop-angle`**: for a self-loop (same start and end point with a large bend like `120deg`), the angle around the node where the loop sticks out.
- **`corner`**: `left` or `right` makes a right-angled corner. `corner-radius` rounds it (`none` is distinct from `0pt`).

```typst
#diagram(
  edge((0,0), "..|>", corner: right),  // 90-degree dotted arrow turning right
)
```

### Labels on edges

- **`label`**: content (positional `$f$` works too).
- **`label-side`**: `left`, `right`, or `center`. `auto` puts it above straight lines / outside arcs. `center` puts it on the line and turns on a background fill.
- **`label-pos`**: `0` (start) to `1` (end), default `50%`. Lengths like `100% - 1em` work. For poly edges, an integer fraction `k/n` lands on vertices; or pass `(segment, position)`.
- **`label-sep`**: gap between edge and label (default from diagram `label-sep`, 0.4em).
- **`label-angle`**: rotate label; `auto`, `left`, `right`, `top`, `bottom`, or an angle.
- **`label-anchor`**: CeTZ anchor like `"north-east"`; `auto` chooses based on side/angle.
- **`label-fill`**: `true` uses `crossing-fill`; `false`/`none` no fill; `auto` fills only when `label-side: center`.
- **`label-wrapper`**: function `e => content` to box/style the label, e.g. `label-wrapper: e => circle(e.label, fill: e.label-fill)`.

### Crossings (lines passing over each other)

Set `crossing: true` (or pass `"crossing"` positionally) to draw a background-colored backdrop so the edge appears to cross over others. `crossing-fill` (default white) is the backdrop color; `crossing-thickness` (default 5) is its width in stroke multiples.

### Decorations and dashes

- **`dash`**: stroke dash style, e.g. `"dashed"`, `"dotted"`. Some marks set this automatically (e.g. `"<..>"` implies dotted).
- **`decorations`**: `"wave"`, `"zigzag"`, `"coil"` (also accepted as positional flags), or a CeTZ decoration function such as `cetz.decorations.wave.with(amplitude: .4)`.

```typst
#diagram($
  A edge("wave") & B edge("zigzag") & C edge("coil") & D
$)
```
*Draws A B C D in a row connected by a wavy, a zigzag, and a coiled line respectively.*

### Extrude (parallel strokes)

`extrude: (-1.5, 1.5)` draws two parallel strokes; `(-2, 0, 2)` three. Endpoints auto-adjust to the mark cap. Same idea as node extrude but for the line.

### Floating edges

`floating: true` wraps the edge so it does not affect the diagram's bounding box. Useful for decorative arrows that should not enlarge the canvas.

### String positional flags

Some options can be passed as bare strings: `"dashed"`, `"dotted"`, `"double"`, `"triple"`, `"crossing"`, `"wave"`, `"zigzag"`, `"coil"`. So `edge((0,0),(1,0), $f$, "wave", "crossing")` equals `edge((0,0),(1,0), $f$, decorations: "wave", crossing: true)`.

Marks vs label are disambiguated by type, so these are all equivalent:
```typst
edge((0,0), (1,0), $f$, "->")
edge((0,0), (1,0), "->", $f$)
edge((0,0), (1,0), $f$, marks: "->")
edge((0,0), (1,0), "->", label: $f$)
edge((0,0), (1,0), label: $f$, marks: "->")
```

### Positional argument grammar

```
edge(..<coords>, ..<marklabel>, ..<options>)
<coords>    = ()  |  (to)  |  (from, to)  |  (from, ..vertices, to)
<marklabel> = (marks, label) | (label, marks) | (marks) | (label) | ()
<options>   = any number of string flags
```
- `edge(to)` == `edge(auto, to)` (start snaps to previous node)
- `edge()` == `edge(auto, auto)` (snaps to previous and next nodes)
- `edge(from, "->", to)` is allowed: for exactly two vertices the marks string may sit between them.

### Full `edge()` option reference

```
edge(
  vertices: array,                 // default (); or pass as leading positionals
  label: content,                  // default none
  label-side: left|right|center,   // default auto
  label-pos: float|ratio|relative|array,  // default 50%
  label-sep: length,               // default diagram label-sep (0.4em)
  label-angle: angle|left|right|top|bottom|auto,  // default 0deg
  label-anchor: anchor,            // default auto
  label-fill: bool|paint,          // default auto
  label-size: auto|length,         // default diagram label-size (1em)
  label-wrapper: auto|function,    // default diagram label-wrapper
  stroke: stroke,                  // default auto -> diagram edge-stroke (0.048em, matches font arrows)
  dash: string,                    // default none
  decorations: none|string|function,  // default none
  extrude: array,                  // default (0,)
  shift: length|number|pair,       // default 0pt
  kind: string,                    // default auto ("line"|"arc"|"poly")
  bend: angle,                     // default 0deg
  loop-angle: angle,               // default none
  corner: none|left|right,         // default none
  corner-radius: length|none,      // default diagram edge-corner-radius (2.5pt)
  marks: array,                    // default ()
  mark-scale: percent,             // default diagram mark-scale (100%)
  crossing: bool,                  // default false
  crossing-thickness: number,      // default diagram crossing-thickness (5)
  crossing-fill: paint,            // default diagram crossing-fill (white)
  snap-to: pair,                   // default (auto, auto); (start, end) node/coord/none
  layer: number,                   // default 0; higher draws on top
  floating: bool,                  // default false
  post: function,                  // default x => x
  ..args,                          // vertices first, then marks/label, then flags
)
```

- **`snap-to`**: override automatic snapping when many nodes are close. Each entry is a position, a node name, or `none` (disable snapping at that end).

---

## 5. Marks and arrows

### Shorthand strings

Specify marks like `edge(a, b, "-->")` or `marks: "-->"`. A shorthand has the form `M1 L M2` (or `M1 L M2 L M3 ...`), where each `Mi` is a mark name and `L` is a line style.

**Line styles** (`L`): `-` (solid), `=` (double), `==` (heavy double), `--` (dashed), `..` (dotted), `~` (wavy).

Common arrowhead shorthands and what they resemble:
- `"->"` plain arrow (matches → in the font)
- `"=>"` double-line arrow (⇒)
- `"==>"` heavy double arrow (⇛)
- `"|->"` bar then arrow (↦)
- `"->>"` two-headed arrow (↠)
- `"hook->"` hooked tail then arrow (↪)

Marks can appear anywhere along an edge and combine freely, e.g. `">>-->"`, `"||-/-|>"`, `"o..O"`, `"hook'-x-}>"`, `"-*-harpoon"`.

Append `'` to a mark name to **flip** it across the edge (e.g. `"hook'"`, `"harpoon'"`).

```typst
#diagram(edge("harpoon'-hook", stroke: 1pt))
#diagram(edge("hook'-harpoon", stroke: 1pt))
```

### Default mark names (Table of marks)

All built-in marks live in the state variable `fletcher.MARKS`. Access with `context fletcher.MARKS.get()`. Names:

`head`, `doublehead`, `triplehead`, `harpoon`, `straight`, `solid`, `stealth`, `latex`, `cone`, `circle`, `square`, `diamond`, `bar`, `cross`, `bracket`, `parenthesis`, `hook`, `hooks`,
and the symbol shorthands:
`>`, `<`, `>>`, `<<`, `>>>`, `<<<`, `|>`, `<|`, `}>`, `<{`, `|`, `||`, `|||`, `/`, `\`, `x`, `X`, `o`, `O`, `*`, `@`, `[]`, `<>`, `]`, `[`, `)`, `(`, `crowfoot`, `n`, `n!`, `n?`, `1`, `1!`, `1?`.

Each mark's size, angle, spacing, or fill can be adjusted. Flip with a trailing `'`.

`fletcher.LINE_ALIASES = { -, =, ==, --, .., ~ }`.

Example: `edge(p1, p2, "=>")` expands to `edge(p1, p2, marks: (none, "head"), "double")`.

### `mark-scale`

Scales arrowheads relative to stroke thickness: `100%`, `150%`, `200%`. Default arrowheads already scale up automatically for double/triple strokes (`->`, `=>`, `==>`).

---

## 6. Custom marks

### Passing mark objects

`marks:` can take an array of **mark objects** (dictionaries). Minimum requirement: a `draw` entry of CeTZ objects, centered at `(0,0)`, scaled so one unit equals the stroke thickness.

```typst
#import cetz.draw
#let my-mark = (
  size: 2,
  draw: mark => draw.circle((0,0), radius: mark.size, fill: none),
)
#diagram(
  edge((0,0), (1,0), stroke: 1pt, marks: (my-mark, my-mark), bend: 30deg),
  edge((0,1), (1,1), stroke: 3pt + orange, marks: (none, my-mark)),
)
```
*Draws two edges, each ending (and the first also starting) with a small hollow circle mark.*

Parameters can be functions of other parameters: `draw: mark => draw.circle((0,0), radius: mark.size)`. Change size without touching `draw`: `my-mark + (size: 4)`.

### Inheriting from existing marks

```typst
#let my-mark = (
  inherit: "stealth",   // base on fletcher.MARKS.stealth
  fill: red,
  stroke: none,
  extrude: (0, -3),
)
#diagram(edge("rr", stroke: 2pt, marks: (my-mark, my-mark + (fill: blue))))
```

Mix several mark objects on one edge:
```typst
#diagram(
  edge-stroke: 1.5pt, spacing: 28mm,
  edge((0,1), (-0.1,0), bend: -8deg, marks: (
    (inherit: ">>", size: 6, delta: 70deg, sharpness: 65deg),
    (inherit: "head", rev: true, pos: 0.8, sharpness: 0deg, size: 17),
    (inherit: "bar", size: 1, pos: 0.3),
    (inherit: "solid", size: 12, rev: true, stealth: 0.1, fill: red.mix(purple)),
  ), stroke: green.darken(50%)),
)
```

To see how a shorthand expands, inspect `context fletcher.interpret-marks-arg("|=>")`.

### Special mark properties

| Property                     | Meaning                                                                                            | Default |
| ---------------------------- | -------------------------------------------------------------------------------------------------- | ------- |
| `inherit`                    | Name of a mark in `fletcher.MARKS` to inherit from (e.g. `"<"` is `(inherit: "head", rev: true)`). |         |
| `draw`                       | Final CeTZ objects, centered at (0,0), 1 unit = stroke thickness.                                  |         |
| `pos`                        | Position along edge, 0 (start) to 1 (end).                                                         | auto    |
| `fill` / `stroke`            | Default fill/stroke. `none` = unfilled; `auto` = inherit edge stroke.                              | auto    |
| `rev`                        | Reverse the mark to point backwards.                                                               | false   |
| `flip`                       | Reflect across the edge (a trailing `'` in the name does this).                                    | false   |
| `scale`                      | Overall scaling factor.                                                                            | 100%    |
| `extrude`                    | Duplicate the mark at each offset, e.g. `(-5, 0, 5)`.                                              | (0,)    |
| `tip-origin` / `tail-origin` | x-coordinate of the mark point when acting as a tip vs a tail.                                     | 0       |
| `tip-end` / `tail-end`       | x-coordinate where the edge stroke terminates.                                                     | 0       |
| `cap-offset`                 | Function `(mark, y) => x` for where the stroke ends vs y (for extruded edges).                     |         |

A mark has up to four distinct center points (tip-origin, tail-origin, tip-end, tail-end) controlling how it joins the target point and the stroke. Use `fletcher.mark-debug(mark)` to visualize them.

### Example: a straight arrowhead implementation

```typst
#import cetz.draw
#let straight = (
  size: 8,
  sharpness: 20deg,
  tip-origin: mark => 0.5/calc.sin(mark.sharpness),
  tail-origin: mark => -mark.size*calc.cos(mark.sharpness),
  fill: none,
  draw: mark => {
    draw.line(
      (180deg + mark.sharpness, mark.size),   // polar cetz coordinate
      (0, 0),
      (180deg - mark.sharpness, mark.size),
    )
  },
  cap-offset: (mark, y) => calc.tan(mark.sharpness + 90deg)*calc.abs(y),
)
```

### Defining mark shorthands

Mark shorthands such as `"hook->"` look up names in `fletcher.MARKS`. Modify that state to add or redefine shorthands:

```typst
#fletcher.MARKS.update(m => m + (
  "<": (inherit: "stealth", rev: true),
  ">": (inherit: "stealth", rev: false),
  "multi": (
    inherit: "straight",
    draw: mark => fletcher.cetz.draw.line(
      (0, +mark.size*calc.sin(mark.sharpness)),
      (-mark.size*calc.cos(mark.sharpness), 0),
      (0, -mark.size*calc.sin(mark.sharpness)),
    ),
  ),
))

#diagram(spacing: 2cm, edge("multi->-multi", stroke: 1pt + eastern))

// Restore defaults afterward so you do not affect the rest of the document:
#fletcher.MARKS.update(fletcher.DEFAULT_MARKS)
```

---

## 7. Shapes reference (`fletcher.shapes`)

Import: `#import fletcher: shapes` then `shape: shapes.hexagon`, or `#import fletcher.shapes: hexagon`. Configure with `.with(..)`. All shapes respect `stroke`, `fill`, `width`, `height`, and `extrude`.

- **`rect`** / **`circle`**: standard rectangle / circle. Strings `"rect"`, `"circle"` or the element functions also work.
- **`ellipse(scale: number)`**: `scale` (default 1) multiplies radii.
- **`pill`**: capsule (rounded ends).
- **`parallelogram(angle: 20deg, fit: 0.8)`**: slanted rectangle. Do not use 90deg.
- **`trapezium(dir: top, angle: 20deg, fit: 0.8)`**: isosceles trapezium; `dir` is which side has the shorter parallel edge.
- **`diamond(fit: 0.5)`**: rhombus.
- **`triangle(dir: top, angle: auto, aspect: auto, fit: 0.8)`**: isosceles triangle pointing `dir`. Give `angle` OR `aspect`, not both.
- **`house(dir: top, angle: 10deg)`**: pentagon (house with a roof); `dir` is the roof direction, `angle` the roof slant.
- **`chevron(dir: right, angle: 30deg, fit: 0.8)`**: arrow-like chevron pointing `dir`.
- **`hexagon(angle: 30deg, fit: 0.8)`**: irregular hexagon; `angle` is half the exterior angle (0deg = rectangle).
- **`octagon(truncate: 0.5)`**: rectangle with truncated corners; `truncate` is a multiple of the smaller dimension, or a length.
- **`cylinder(fit: 0.6, tilt: 8deg, rings: ())`**: 3D cylinder; `tilt` controls perspective (0deg side-on), `rings` is an array of vertical positions to draw arcs (often for databases), e.g. `rings: (10%, 20%)` or `rings: 4pt`.

`fit` (0 to 1) on most shapes controls how tightly the shape hugs the label's bounding box.

### Glyph shapes (stretched glyphs along a node edge)

`stretched-glyph` draws a stretchable glyph (brace, bracket, paren, etc.) along one side of a node. Especially useful with `enclose`. Convenience shapes: `brace`, `bracket`, `paren`.

```typst
#import fletcher.shapes: brace, bracket
#diagram(
  spacing: 1cm,
  node-stroke: teal,
  node((0,0), $A$, name: <A>),
  node((1,0), $B$, name: <B>),
  node((1,1), $C$, name: <C>),
  node(enclose: (<A>, <B>), shape: bracket.with(dir: top, size: 2em)),
  node(enclose: (<B>, <C>), shape: brace.with(dir: right, length: 100% - 1em, sep: 10pt, label: $B C$)),
)
```
*Draws: nodes A, B (top row) and C (below B); a bracket spanning A and B on top; a brace on the right spanning B and C, labeled BC.*

`stretched-glyph` parameters:
```
stretched-glyph(
  node, extrude,
  glyph: symbol|content,  // default sym.brace.b; works best with stretchable glyphs
  dir: direction,         // default bottom; side to place the glyph (match the glyph to dir)
  sep: length,            // default 0pt; gap between glyph and node edge
  length: relative,       // default 100%; size, e.g. 100% + 5pt, 150%
  label: content,         // default none; placed beside the glyph per dir
  label-sep: length,      // default 0.25em
  ..args,                 // passed to text() for the glyph (color, font size)
)
```
Choose the glyph to match `dir`: top uses an over-brace, bottom an under-brace, left/right the curly braces, etc.

---

## 8. CeTZ integration and Bezier edges

Fletcher exposes a `render` hook on `diagram()` so you can draw with CeTZ directly using computed layout data. `render` receives `(grid, nodes, edges, options)`. The default is:

```typst
(grid, nodes, edges, options) => {
  cetz.canvas(fletcher.draw-diagram(grid, nodes, edges, debug: options.debug))
}
```

`cetz` is re-exported as `fletcher.cetz`. You can find computed nodes by coordinate and anchor edges to them. Example drawing a Bezier curve between two nodes:

```typst
#diagram(
  node((0,1), $A$, stroke: 1pt, shape: fletcher.shapes.diamond),
  node((2,0), [Bézier], fill: purple.lighten(80%)),
  render: (grid, nodes, edges, options) => {
    cetz.canvas({
      fletcher.draw-diagram(grid, nodes, edges, debug: options.debug)  // default render
      let n1 = fletcher.find-node-at(nodes, (0,1))
      let n2 = fletcher.find-node-at(nodes, (2,0))
      let out-angle = 45deg
      let in-angle = -110deg
      fletcher.get-node-anchor(n1, out-angle, p1 => {
        fletcher.get-node-anchor(n2, in-angle, p2 => {
          let c1 = (to: p1, rel: (out-angle, 10mm))
          let c2 = (to: p2, rel: (in-angle, 20mm))
          cetz.draw.bezier(p1, p2, c1, c2, mark: (end: ">"))  // cetz-style mark
        })
      })
    })
  }
)
```
*Draws: a diamond node A and a "Bézier" node, joined by a custom Bezier curve with a CeTZ arrowhead.*

Useful helpers when using `render`:
- `fletcher.draw-diagram(grid, nodes, edges, debug: ..)` renders the standard diagram.
- `fletcher.find-node-at(nodes, (u,v))` retrieves a computed node by coordinate.
- `fletcher.get-node-anchor(node, angle, callback)` gives the outline point at an angle.

---

## 9. Touying integration (animated/incremental slides)

For incrementally-revealed diagrams in Touying presentations, redefine `diagram` to use a `touying-reducer` so Touying primitives (`pause`, `uncover`, `only`, ...) are understood:

```typst
#import "@preview/touying:0.5.5": *
#show: themes.simple.simple-theme.with(aspect-ratio: "16-9")
#let diagram = touying-reducer.with(reduce: fletcher.diagram, cover: fletcher.hide)

#slide(repeat: 6, self => {
  let (uncover, only, alternatives) = utils.methods(self)
  diagram(
    node((0, 0), name: <A>)[$A$],
    pause,
    edge("->"),
    node((1, 0), name: <B>)[$B$],
    pause,
    edge("->"),
    node((2, 0), name: <C>)[$C$],
    only("4,6", edge(<A>, "~", <B>, bend: 40deg, stroke: red)),
    only("5,6", edge(<B>, "~", <C>, bend: 40deg, stroke: green)),
    only("6", edge(<C>, "~", <A>, bend: 40deg, stroke: blue)),
  )
})
```
*Builds a 6-step animation: reveal A, then arrow to B, then arrow to C, then progressively add three colored curved edges among A, B, C.*

---

## 10. `diagram()` full reference

```
diagram(
  debug: bool|1|2|3,                     // default false; 1/true = grid, higher = boxes/anchors
  axes: pair of directions,              // default (ltr, ttb); orientation of uv axes
  spacing: length | pair,                // default 3em; gutter between rows/cols; (x, y) or d
  cell-size: length | pair,              // default 0pt; minimum row/col size
  edge-stroke: stroke,                   // default 0.048em (matches font arrows); folded with edge stroke
  node-stroke: stroke|none,              // default none
  edge-corner-radius: length|none,       // default 2.5pt
  node-corner-radius: length|none,       // default none
  node-inset: length|pair,               // default 6pt
  node-outset: length|pair,              // default 0pt
  node-shape: rect|circle|function,      // default auto
  node-fill: paint,                      // default none
  node-defocus: number,                  // default 0.2
  label-sep: length,                     // default 0.4em
  label-size: length,                    // default 1em
  label-wrapper: function,               // default boxes the label with small inset/radius/fill
  mark-scale: percent,                   // default 100%
  crossing-fill: paint,                  // default white
  crossing-thickness: number,            // default 5
  render: function,                      // hook into layout (see CeTZ integration)
  ..args: array,                         // the nodes and edges (positional, blocks, or math mode)
)
```

Notes:
- **Strokes are folded**: if `edge-stroke` is `1pt` and an edge's stroke is `red`, the result is `1pt + red`. Same for `node-stroke`.
- **`spacing`** ensures adjacent nodes are at least that far apart (measured between bounding boxes). `(x, y)` sets horizontal/vertical gutters separately.
- **`axes`** examples: `(ltr, ttb)` default; `(ltr, btt)` y increases up; `(ttb, ltr)` matrix (row, column) convention.
- **`label-wrapper` default**:
  ```typst
  edge => box([#edge.label], inset: .2em, radius: .2em, fill: edge.label-fill)
  ```
- **`render`** is called after layout with `(grid, nodes, edges, options)`; `grid` holds row/column widths and positions, `nodes`/`edges` are dictionaries with computed sizes and physical coordinates.

---

## 11. Internal/advanced functions (for `render` hooks and custom marks)

You usually do not need these for ordinary diagrams, but they are available for advanced work.

**Coordinates (`coords.typ`)**: `uv-to-xy(grid, uv)`, `xy-to-uv(grid, xy)`, `duv-to-dxy(grid, uv, duv)`, `dxy-to-duv(grid, xy, dxy)`, `vector-polar-with-xy-or-uv-length(grid, xy, target-length, θ)`, `resolve(ctx, update, ..coords)` (CeTZ coordinate resolver extended for elastic uv coords; `ctx.target-system` is `"uv"` or `"xyz"`, `ctx.grid` optional).

**Marks (`marks.typ`)**: `cap-offset(mark, shift)`, `resolve-mark(mark, defaults)` (applies inheritance and evaluates closures), `draw-mark(mark, stroke, origin, angle, debug)`, `mark-debug(mark, stroke, show-labels, show-offsets, offset-range)` (visualizes tip/tail origin/end points).

**Diagram layout (`diagram.typ`)**: `interpret-axes(axes)`, `expand-fractional-rects(rects)` (splits fractional-position rects across integer cells, the core grid algorithm), `compute-cell-sizes(flip, verts, rects)`, `compute-cell-centers(grid)`, `compute-grid(rects, verts, options)`.

**Nodes (`node.typ`)**: `measure-node-size(node)`, `resolve-node-enclosures(nodes, ctx)`, `resolve-node-coordinates(nodes, ctx)` (`()` refers to the previous node's resolved position).

**Edges (`edge.typ`)**: `interpret-marks-arg(arg)` (parses `"->"`, `"<=>"`, or a mark array into edge args), `interpret-edge-args(args, options)` (splits positional args into from/to/marks/label), `apply-edge-shift(grid, edge)`.

**Drawing (`draw.typ`)**: `place-edge-label-on-curve(edge, curve, debug)`, `draw-edge-line(edge, debug)`, `draw-edge-arc(edge, debug)`, `draw-edge-polyline(edge, debug)`, `find-farthest-intersection(objects, target, callback)`, `get-node-anchor(node, θ, callback)`, `defocus-adjustment(node, θ)`, `draw-debug-axes(grid, debug, floating)`, `hide(objects, bounds)` (make contents invisible; `bounds: false` removes them from layout entirely, `true` keeps layout but hides visuals).

**Utils (`utils.typ`)**: `interp(values, index, spacing)`, `interp-inv(values, value, spacing)`, `get-arc-connecting-points(from, to, angle)` (returns center/radius/start/stop for an arc with a given bend), `is-space(el)`.

State variables: `fletcher.MARKS` (dictionary of mark definitions), `fletcher.DEFAULT_MARKS` (restore target), `fletcher.LINE_ALIASES`.

---

## 12. Patterns cookbook (map a figure type to code)

These are ready-to-adapt templates. Pick the closest one and adjust coordinates, labels, and marks.

### Flowchart (top-to-bottom with decision)

```typst
#import "@preview/fletcher:0.5.8" as fletcher: diagram, node, edge
#import fletcher.shapes: diamond, pill

#diagram(
  node-stroke: 1pt,
  spacing: (10mm, 12mm),
  node((0,0), [Start], shape: pill, name: <s>),
  edge("-|>"),
  node((0,1), [Do work], name: <w>),
  edge("-|>"),
  node((0,2), [OK?], shape: diamond, name: <d>),
  edge("-|>", [yes]),
  node((0,3), [End], shape: pill, name: <e>),
  edge(<d>, (1,2), "r,d", "-|>", [no], label-side: left),
  node((1,3), [Handle error], name: <err>),
  edge(<err>, <w>, "-|>", bend: 30deg),   // loop back
)
```
*A vertical flow Start -> Do work -> decision OK? -> End, with a "no" branch going right to "Handle error" and looping back up to "Do work".*

### Commutative diagram (math mode)

```typst
#diagram($
  A edge(f, ->) edge(g, ->, "d") & B edge(h, ->, "d") \
  C edge(k, ->) & D
$)
```
*A 2x2 square: A (top-left) to B via f, A down to C via g, B down to D via h, C to D via k.*

### State machine (with self-loop)

```typst
#diagram(
  node-stroke: 1pt,
  node((0,0), [q0], name: <q0>, shape: fletcher.shapes.circle, extrude: (0, -3)),
  edge(<q0>, <q1>, "-|>", [a]),
  node((1,0), [q1], name: <q1>, shape: fletcher.shapes.circle),
  edge(<q1>, <q1>, "-|>", [b], bend: 130deg, loop-angle: 90deg),
  edge(<q1>, <q0>, "-|>", [c], bend: 30deg),
)
```
*Two circular states q0 and q1; arrow a from q0 to q1; a self-loop b on q1; arrow c back from q1 to q0.*

### Block diagram (architecture, fixed boxes)

```typst
#diagram(
  node-stroke: 1pt, node-corner-radius: 3pt,
  spacing: (12mm, 8mm),
  node((0,1), [input], name: <in>),
  node((1,1), [memory unit (MU)], name: <mu>),
  node((1,0), [control unit (CU)], name: <cu>),
  node((1,2), [arithmetic & logic\ unit (ALU)], name: <alu>),
  node((2,1), [output], name: <out>),
  edge(<in>, <mu>, "<|-|>"),
  edge(<mu>, <cu>, "<|-|>"),
  edge(<mu>, <alu>, "<|-|>"),
  edge(<mu>, <out>, "<|-|>"),
)
```
*A classic von Neumann-style block diagram: input and output flank a central memory unit, which connects to a control unit above and an ALU below, all with double-headed arrows.*

### Two parallel arrows between the same nodes (with 2-cell / natural transformation)

```typst
#diagram(spacing: 2cm, {
  let (A, B) = ((0,0), (1,0))
  node(A, $cal(A)$)
  node(B, $cal(B)$)
  edge(A, B, $F$, "->", bend: +35deg)
  edge(A, B, $G$, "->", bend: -35deg)
  let h = 0.2
  edge((.5,-h), (.5,+h), $alpha$, "=>")   // vertical double arrow between the two arcs
})
```
*Categories A and B with two functors F (upper arc) and G (lower arc); a double arrow α between them representing a natural transformation.*

### Routed edges with right-angle corners

```typst
#diagram(
  spacing: (10mm, 5mm),
  node-stroke: 1pt,
  edge((-2,0), "r,u,r", "-|>", $f$, label-side: left),
  edge((-2,0), "r,d,r", "..|>", $g$),
  node((0,-1), $F(s)$),
  node((0,+1), $G(s)$),
  edge((0,+1), (1,0), "..|>", corner: left),
  edge((0,-1), (1,0), "-|>", corner: right),
  node((1,0), text(white, $ plus.circle $), inset: 2pt, fill: black),
  edge("-|>"),
)
```
*A signal-flow style figure: two inputs route with right-angle turns into F(s) and G(s), which feed a summing node (a black circle with a plus), then continue right.*

### Inline diagram inside text

```typst
An equation $f: A -> B$ and an inline diagram
#diagram($A edge(->, text(#0.8em, f)) & B$).
```
*Renders a tiny A -> B arrow diagram inline within a sentence.*

---

## 13. Quick checklist for generating fletcher code

1. Decide layout in elastic coordinates first: assign each node a `(col, row)` with `(0,0)` top-left, columns increasing right, rows increasing down (unless you set `axes`).
2. Name nodes with labels (`name: <a>`) whenever an edge needs to refer to them or you want anchors.
3. Connect with `edge(from, to, marks, label)`. Use `"->"` for a plain arrow; add `bend:` for arcs, `corner:` or multiple vertices/`"d,r"` shorthands for routed lines, `"-|>"`, `"<|-|>"`, `"=>"`, `"..|>"` etc. for different heads/line styles.
4. Choose shapes via `shape:` for flowchart semantics (`diamond` = decision, `pill` = terminal, `rect` = process, `cylinder` = data store, `parallelogram` = input/output).
5. Style globally on `diagram(node-stroke: 1pt, edge-stroke: 1pt, spacing: ..)` rather than per-node when possible.
6. For self-loops use `edge(<n>, <n>, bend: 130deg, loop-angle: ..)`.
7. For lines that visually cross, add `"crossing"`.
8. Remember: absolute coordinates and anchors are floating and do not change layout; elastic coordinates do.
