# CeTZ Reference Manual

CeTZ ("CeTZ, ein Typst Zeichenpaket") is a drawing package for the Typst
typesetting system. Its drawing model is inspired by TikZ/PGF: it uses relative
coordinates, named elements, anchors, marks (arrowheads), styling, grouping and
transformations. This single file is a self-contained reference compiled from
the official CeTZ documentation and source docstrings, intended as context for a
language model translating TikZ/PGF code into CeTZ.

Key facts to keep in mind:

- A drawing lives inside `#cetz.canvas({ import cetz.draw: *; ... })`. The `draw`
  functions are imported inside the canvas body.
- The coordinate system has **up as positive y** (unlike screen coordinates).
  One unit defaults to 1cm.
- Coordinates are usually tuples like `(x, y)` or `(x, y, z)`, but many other
  coordinate systems exist (relative, polar/angle, anchor-relative, intersection,
  interpolation, tangent, perpendicular). See "Coordinate Systems".
- Most shape functions accept `name:` so the element can later be referenced by
  its anchors, e.g. `"label.north"`.
- This document has no rendered images. Every example is shown only as code; read
  the prose around it to understand the visual result.

The examples in the API reference are written as the body of a `canvas` block
(the surrounding `#cetz.canvas({ import cetz.draw: *; ... })` is omitted).

---

# TikZ to CeTZ Quick Mapping

This appendix is a compact orientation for translating TikZ/PGF into CeTZ. It is
not part of the official manual; it summarises equivalences implied by the
reference below. Always confirm details against the relevant section.

General structure:

```typ
// TikZ:  \begin{tikzpicture} ... \end{tikzpicture}
#cetz.canvas({
  import cetz.draw: *
  // ... draw calls go here ...
})
```

Paths and shapes:

- `\draw (0,0) -- (1,1);` becomes `line((0,0), (1,1))`
- `\draw (0,0) -- (1,0) -- (1,1);` becomes `line((0,0), (1,0), (1,1))` (a line strip)
- `\draw (0,0) -- (1,0) -- (0,1) -- cycle;` becomes `line((0,0), (1,0), (0,1), close: true)`
- `\draw (0,0) circle (1);` becomes `circle((0,0), radius: 1)`
- `\draw (0,0) ellipse (2 and 1);` becomes `circle((0,0), radius: (2, 1))`
- `\draw (0,0) rectangle (2,1);` becomes `rect((0,0), (2,1))`
- `\draw (0,0) arc (0:90:1);` becomes `arc((0,0), start: 0deg, stop: 90deg, radius: 1)`
- `\draw (0,0) grid (3,2);` becomes `grid((0,0), (3,2))`
- `\draw (a) .. controls (b) and (c) .. (d);` becomes `bezier((a), (d), (b), (c))`

Nodes and labels:

- `\node at (0,0) {Text};` becomes `content((0,0), [Text])`
- `\node[draw] (n) at (0,0) {A};` becomes `content((0,0), [A], frame: "rect", name: "n")`
- A node placed on a path can be approximated with a separate `content(...)` call.

Coordinates:

- Cartesian `(x,y)` stays `(x, y)`. Remember up is positive y.
- Polar `(30:2)` becomes the angle form `(30deg, 2)`.
- Relative `++(1,0)` becomes `(rel: (1, 0))`; the non-updating `+(1,0)` becomes
  `(rel: (1, 0), update: false)`.
- Anchor reference `(n.north)` becomes the string `"n.north"`.
- A named coordinate `\coordinate (a) at (1,2);` is usually replaced by naming the
  producing element (`name: "a"`) or by a Typst `let a = (1, 2)` binding.

Styling (pass as named args, or set defaults with `set-style(...)`):

- `[red]` or `[draw=red]` becomes `stroke: red`
- `[thick]` / `[line width=2pt]` becomes `stroke: (paint: black, thickness: 2pt)`
  (or simply `stroke: 2pt` for thickness only).
- `[fill=blue]` becomes `fill: blue`
- `[dashed]` becomes `stroke: (dash: "dashed")`
- `\fill[c] ...` is a shape call with `fill: c` and no stroke.
- `[->]`, `[<-]`, `[<->]` arrowheads become `mark: (end: ">")`, `mark: (start: ">")`,
  `mark: (start: ">", end: ">")`.

Scopes and transformations (these affect everything drawn after them, within the
current group):

- `\begin{scope}[...] ... \end{scope}` becomes `group({ set-style(...); ... })`.
- `[xshift=1cm, yshift=1cm]` or `[shift={(1,1)}]` becomes `translate((1, 1))`.
- `[rotate=30]` becomes `rotate(30deg)`.
- `[scale=2]` becomes `scale(2)`.

Loops:

- `\foreach \x in {0,...,4} { ... }` becomes a Typst loop, e.g.
  `for x in range(0, 5) { circle((x, 0), radius: .1) }`.

---

# Part 1: Guide

## Overview

CeTZ, ein Typst Zeichenpaket, is a drawing package for [Typst](https://typst.app/). Its API is similar to Processing but with relative coordinates and anchors from Ti*k*Z. You also won't have to worry about accidentally drawing over other content as the canvas will automatically resize. And remember: up is positive!

These docs are a work in progress! Please submit issues for parts that don't make sense or need improving :)

We are also still trying to find a logo for CeTZ so if you have any ideas please let us know through the Typst Discord server.

---

## Getting Started

### Usage

This is the minimal starting point in a `.typ` file:

```typ
#import "@preview/cetz:0.5.2"
#cetz.canvas({
  import cetz.draw: *
  ...
})
```

Note that draw functions are imported inside the scope of the `canvas` block. This is recommended as some draw functions override Typst's functions such as `line`.

### Examples

From this point on only the code inside the `canvas` block will be shown in examples unless specified otherwise.

```typ
circle((0, 0))
line((0, 0), (2, 1))
```

---

## Basics

The following chapters are about the basic and core concepts of CeTZ. They are recommended reading for basic usage.

---

## Custom Types

Many CeTZ functions expect data in certain formats which we will call types. Note that these are actually made up of Typst primitives.

### `coordinate`

A position on the canvas specified by any coordinate system. See [Coordinate Systems](/basics/coordinate-systems).

### `number`

Any of `float`, `int` or `length`.

### `style`

Represents options passed to draw functions that affect how elements are drawn. They are normally taken in the form of named arguments to the draw functions or sometimes can be a dictionary for a single argument.

---

## The Canvas

The [`canvas`](/api/internal/canvas) function is what handles all of the logic and processing in order to produce drawings. It's usually called with a code block `{...}` as argument. The content of the curly braces is the _body_ of the canvas. Import all the draw functions you need at the top of the body:

```typ
#cetz.canvas({
  import cetz.draw: *

})
```

You can now call the draw functions within the body and they'll produce some graphics! Typst will evaluate the code block and pass the result to the `canvas` function for rendering.

The canvas does not have typical `width` and `height` parameters. Instead its size will grow and shrink to fit the drawn graphic.

By default 1 [coordinate](/basics/coordinate-systems) unit is `1cm`, this can be changed by setting the `length` parameter. If a ratio is given, the length will be the size of the canvas' parent's width!

---

## Styling

You can style draw elements by passing the relevant named arguments to their draw functions. All elements that draw something have stroke and fill styling unless said otherwise.

- `fill` (color,none) = `none`: How to fill the drawn element.
- `stroke` (none,auto,length,color,dictionary,stroke) = `black`: How to stroke the border or the path of the draw element. [See Typst's line documentation for more details.](https://typst.app/docs/reference/visualize/line/#parameters-stroke)
- `fill-rule` (string) = `&quot;non-zero&quot;`: How to fill self-intersecting paths. Can be "non-zero" or "even-odd". [See Typst's path documentation for more details.](https://typst.app/docs/reference/visualize/curve/#parameters-fill-rule)

```typ
// Draws a red circle with a blue border
circle((0, 0), fill: red, stroke: blue)

// Draws a green line
line((0, 0), (1, 1), stroke: green)
```

Instead of having to specify the same styling for each time you want to draw an element, you can use the [`set-style`](/api/draw-functions/styling/set-style) function to change the style for all elements after it, like a Typst `set` rule. You can still pass styling to a draw function to override what has been set with `set-style`. You can also use the [`fill`](/api/draw-functions/styling/fill) and [`stroke`](/api/draw-functions/styling/stroke) functions as a shorthand to set the fill and stroke respectively.

```typ
// Draws an empty square with a black border
rect((-1, -1), (1, 1))

// Sets the global style to have a fill of red and a stroke of blue
set-style(stroke: blue, fill: red)
circle((0,0))

// Draws a green line despite the global stroke being blue
line((), (1,1), stroke: green)
```

When using a dictionary for a style, it is important to note that they update each other instead of overriding the entire option like a non-dictionary value would. For example, if the stroke is set to `(paint: red, thickness: 5pt)` and you pass `(paint: blue)`, the stroke would become `(paint: blue, thickness: 5pt)`.

```typ
// Sets the stroke to red with a thickness of 5pt
set-style(stroke: (paint: red, thickness: 5pt))

// Draws a line with the global stroke
line((0,0), (1,0))

// Draws a blue line with a thickness of 5pt because dictionaries update the style
line((0,0), (1,1), stroke: (paint: blue))

// Draws a yellow line with a thickness of 1pt because other values override the style
line((0,0), (0,1), stroke: yellow)
```

You can also specify styling for each type of element. Note that dictionary values will still update with its global value, the full hierarchy is `function > element type > global`. When the value of a style is `auto`, it will become exactly its parent style.

```typ
set-style(
  // Global fill and stroke
  fill: green,
  stroke: (thickness: 5pt),
  // Stroke and fill for only rectangles
  rect: (stroke: (dash: "dashed"), fill: blue),
)
rect((0,0), (1,1))
circle((2.5, 0.5))
rect((4, 0), (5, 1), stroke: (thickness: 1pt))
```

---

## Coordinate Systems

A `coordinate` is a position on the canvas on which the picture is drawn. They take the form of dictionaries and the following subsections define the key-value pairs for each system. Some systems have a more implicit form as an array of values and CeTZ attempts to infer the system based on the element types.

### XYZ

Defines a point `x` units right, `y` units upward and `z` units away.

- `x` (number) = `0`: The number of units in the `x` direction.

- `y` (number) = `0`: The number of units in the `y` direction.

- `z` (number) = `0`: The number of units in the `z` direction.

The implicit form can be given as an `array` of two or three `number`s, as in `(x, y)` or `(x, y, z)`.

```typ
line((0,0), (x: 1))
line((0,0), (y: 1))
line((0,0), (z: 1))

// Implicit form
line((2, 0), (3, 0))
line((2, 0), (2, 1, 0))
line((2, 0), (2, 0, 1))
```

### Previous

Use this to reference the position of the previous coordinate passed to a draw function. It takes the form of an empty `array` `()` and the previous position initially will be `(0, 0, 0)`. This will never reference the position of a coordinate used to define another coordinate.

```typ
line((0,0), (1, 1))

// Draws a circle at (1,1)
circle(())
```

### Relative

Places the given coordinate relative to the previous coordinate. Or in other words, for the given coordinate, the previous coordinate will be used as the origin. Another coordinate can be given to act as the previous coordinate instead.

- `rel` (coordinate): The coordinate to place relative to the previous coordinate.

- `update` (bool) = `true`: When false, the previous position will not be updated.

- `to` (coordinate) = `()`: The coordinate to treat as the previous coordinate.

In the example below, the red circle is placed one unit to the right of the blue circle. If the blue circle was to be moved to a different position, the red circle would move with the blue circle to stay one unit to the right.

```typ
circle((0, 0), stroke: blue)
circle((rel: (1, 0)), stroke: red)
```

### Polar

Defines a point that is `radius` distance away from the origin at the given angle.

- `angle` (angle): The angle of the coordinate. A value of `0deg` is to the right, a value of `90deg` is upward.

- `radius` (number,array): The distance from the origin. An `array` of `number` can be given, in the form `(x, y)`, to define the `x` and `y` radii of an ellipse instead of a circle.

```typ
line((0, 0), (angle: 30deg, radius: 1))
```

The implicit form is an array of the angle then the radius `(angle, radius)` or `(angle, (x, y))`.

```typ
line(
  (0, 0),
  (30deg, 1),
  (60deg, 1),
  (90deg, 1),
  (120deg, 1),
  (150deg, 1),
  (180deg, 1)
)
```

### Barycentric

In the barycentric coordinate system a point is expressed as the linear combination of multiple vectors. The idea is that you specify vectors $v_1, v_2, ..., v_n$ and numbers $\alpha_1, \alpha_2, ..., \alpha_n$. Then the barycentric coordinate specified by these vectors and numbers is

$$
\frac{\alpha_1 v_1 + \alpha_2 v_2 + \cdots + \alpha_n v_n}{\alpha_1 + \alpha_2 + \cdots + \alpha_n}
$$

- `bary` (dictionary): A dictionary where the key is a named element and the value is a{" "} `float`. The `center` anchor of the named element is used as $v$ and the value is used as $\alpha$.

```typ
circle((90deg, 3), radius: 0, name: "content")
circle((210deg, 3), radius: 0, name: "structure")
circle((-30deg, 3), radius: 0, name: "form")

for (c, a) in (
  ("content", "south"),
  ("structure", "north"),
  ("form", "north")
) {
  content(c, align(center, c + [\ oriented]), padding: .1, anchor: a)
}

stroke(gray + 1.2pt)
line("content", "structure", "form", close: true)

for (c, s, f, cont) in (
  (0.5, 0.1, 1, "PostScript"),
  (1, 0, 0.4, "DVI"),
  (0.5, 0.5, 1, "PDF"),
  (0, 0.25, 1, "CSS"),
  (0.5, 1, 0, "XML"),
  (0.5, 1, 0.4, "HTML"),
  (1, 0.2, 0.8, "LaTeX"),
  (1, 0.6, 0.8, "TeX"),
  (0.8, 0.8, 1, "Word"),
  (1, 0.05, 0.05, "ASCII")
) {
  content(
    (bary: (
      content: c,
      structure: s,
      form: f
    )),
    cont,
    fill: rgb(50, 50, 255, 100),
    stroke: none,
    frame: "circle"
  )
}
```

### Anchor

Defines a point relative to a named element using anchors, see [Anchors](/basics/anchors).

- `name` (str): The name of the element that you wish to use to specify a coordinate.

- `anchor` (str,angle,number,ratio,none) = `none`: The anchor of the element. Strings are named anchors, angles are border anchors and numbers and ratios are path anchors. If not given, the default anchor will be used, on most elements this is `center` but it can be different or not exist at all!

```typ
circle((0,0), name: "circle")
// Anchor at 30 degree
content((name: "circle", anchor: 30deg), box(fill: white, $ 30 degree $))
// Anchor at 30% of the path length
content((name: "circle", anchor: 30%), box(fill: white, $ 30 % $))
// Anchor at 3.14 of the path
content((name: "circle", anchor: 3.14), box(fill: white, $ p = 3.14 $))
```

You can also use implicit syntax of a dot separated string in the form `"name.anchor"` for all anchors.

```typ
line((0, 0), (4, 3), name: "line")
circle("line.75%", name: "circle")
rect("line.start", "circle.east")
```

When using named elements within a group, you can access the element's anchors outside of the group by using the implicit anchor coordinate, e.g. `"a.b.north"`.
```typ
group(name: "a", {
  circle((), name: "b")
})
circle("a.b.south", radius: 0.2)
circle((name: "a", anchor: "b.north"), radius: 0.2)
```

### Tangent

This system allows you to compute the point that lies tangent to a shape. In detail, consider an element and a point. Now draw a straight line from the point so that it "touches" the element (more formally, so that it is _tangent_ to this element). The point where the line touches the shape is the point referred to by this coordinate system.

- `element` (str): The name of the element on whose border the tangent should lie.

- `point` (coordinate): The point through which the tangent should go.

- `solution` (int): Which solution should be used if there are more than one.

A special algorithm is needed in order to compute the tangent for a given shape. Currently it does this by fitting an ellipse to the given center, north and east anchors (see [Anchors](/basics/anchors)), so only circles and ellipses will work correctly.

```typ
grid((0,0), (3,2), help-lines: true)

circle((3,2), name: "a", radius: 2pt)
circle((1,1), name: "c", radius: 0.75)
content("c", $ c $, anchor: "north-east", padding: .1)

line(
  // The starting point or element
  "a",
  // The tangent coordinate
  (element: "c", point: "a", solution: 1),
  // The center of the circle
  "c",
  // The other tangent coordinate
  (element: "c", point: "a", solution: 2),
  "a",
  stroke: red
)
```

### Perpendicular

Can be used to find the intersection of a vertical line going through a point $p$ and a horizontal line going through some other point $q$.

- `horizontal` (coordinate): The coordinate through which the horizontal line passes.

- `vertical` (coordinate): The coordinate through which the vertical line passes.

You can use the implicit syntax of `(horizontal, "|-", vertical)` or `(vertical, "-|", horizontal)`.

```typ
set-style(content: (padding: .05))
content((30deg, 1), $ p_1 $, name: "p1")
content((75deg, 1), $ p_2 $, name: "p2")

line((-0.2, 0), (1.2, 0), name: "xline")
content("xline.end", $ q_1 $, anchor: "west")

line((2, -0.2), (2, 1.2), name: "yline")
content("yline.end", $ q_2 $, anchor: "south")

line("p1.south-east", (horizontal: (), vertical: "xline.end"))
line("p2.south-east", ((), "|-", "xline.end")) // Short form
line("p1.south-east", (vertical: (), horizontal: "yline.end"))
line("p2.south-east", ((), "-|", "yline.end")) // Short form
```

### Interpolation

Use this to linearly interpolate between two coordinates `a` and `b` with a given distance `number`. If `number` is a `number` the position will be at the absolute distance away from `a` towards `b`, a `ratio` can be given instead to be the relative distance between `a` and `b`. An `angle` can also be given for the general meaning: "First consider the line from `a` to `b`. Then rotate this line by `angle` around point `a`. Then the two endpoints of this line will be `a` and some point `c`. Use the point `c` for the subsequent computation."

- `a` (coordinate): The coordinate to interpolate from.

- `b` (coordinate): The coordinate to interpolate to.

- `number` (ratio,number): The distance between `a` and `b`. A `ratio` will be the relative distance between the two points, a `number` will be the absolute distance between the two points.

- `angle` (angle) = `0deg`: Angle between $\vec{AB}$ and $\vec{AP}$, where $P$ is the resulting coordinate. This can be used to get the _normal_ for a tangent between two points.

Can be used implicitly as an array in the form `(a, number, b)` or `(a, number, angle, b)`.

```typ
grid((0,0), (3,3), help-lines: true)

line((0,0), (2,2), name: "a")
for i in (0%, 20%, 50%, 80%, 100%, 125%) { // Relative distance
  content(("a.start", i, "a.end"),
  box(fill: white, inset: 1pt, [#i]))
}

line((1,0), (3,2), name: "b")
for i in (0, 0.5, 1, 2) { // Absolute distance
  content(("b.start", i, "b.end"),
  box(fill: white, inset: 1pt, text(red, [#i])))
}
```

---

```typ
grid((0,0), (3,3), help-lines: true)
line((1,0), (3,2))
line((1,0), ((1, 0), 1, 10deg, (3,2)))
fill(red)
stroke(none)
circle(((1, 0), 50%, 10deg, (3, 2)), radius: 2pt)
```

---

```typ
grid((0,0), (4,4), help-lines: true)

fill(black)
stroke(none)
let n = 16
for i in range(0, n+1) {
  circle(((2,2), i / 8, i * 22.5deg, (3,2)), radius: 2pt)
}
```

You can even chain them together!

```typ
grid((0,0), (3, 2), help-lines: true)
line((0,0), (3,2))
stroke(red)
line(((0,0), 0.3, (3,2)), (3,0))
fill(red)
stroke(none)
circle(
  ( // a
    (((0, 0), .3, (3, 2))),
    0.7,
    (3,0)
  ),
  radius: 2pt
)
```

---

```typ
grid((0,0), (3, 2), help-lines: true)
line((1,0), (3,2))
for (l, c) in ((0cm, "0cm"), (1cm, "1cm"), (15mm, "15mm")) {
  content(((1,0), l, (3,2)), box(fill: white, $ #c $))
}
```

Interpolation coordinates can be used to get the _normal_ on a tangent:

```typ
let (a, b) = ((0,0), (3,2))
line(a, b)
// Get normal for tangent from a to () with distance .5, at a
circle(a, radius: .1, fill: black)
line((a, .7, b), (a: (), b: a, number: .5, angle: 90deg), stroke: red)
```

### Projection

To project a point `pt` onto a line from `a` to `b`, you can use the
`(project: pt, onto: (a, b))` or short `(pt, "_|_", a, b)` coordinate.

```typc exapmle
set-style(fill: black, radius: 0.1)

circle(name: "A", (0, 0))
circle(name: "B", (3, 1))
circle(name: "P", (1.9, -1.6))

line("A", "B")
line("P", (project: "P", onto: ("A", "B")))
```

### Function

An array where the first element is a function and the rest are coordinates will cause the function to be called with the resolved coordinates. The resolved coordinates will be given as a `vector` that represents an xyz point in space.

The example below shows how to use this system to create an offset from an anchor, however this could easily be replaced with a [relative coordinate](#relative) with the `to` argument set.

```typ
circle((0, 0), name: "c")
fill(red)
circle((v => cetz.vector.add(v, (0, -1)), "c.west"), radius: 0.3)
```

---

## Anchors

You can refer to a position relative to an element by using its anchors. Anchors come in three different variations but can all be used in two ways.

The first is by using the `anchor` argument on an element. When given, the element will be translated such that the given anchor will be where the given position is. This is supported by all elements that have the `anchor` argument.

```typ
// Draw a circle and place its "west" anchor at the origin.
circle((0,0), anchor: "west")

// Draw a smaller red circle at the origin.
fill(red)
stroke(none)
circle((0,0), radius: 0.3)
```

The second is by using [anchor coordinates](/basics/coordinate-systems#anchor). You must first give the element a name by passing a string to its `name` argument, you can then use its anchors to place other elements. Note that this is only available for elements that have a `name` argument.

```typ
// Name the circle
circle((0,0), name: "circle")

// Draw a smaller red circle at "circle"'s east anchor
fill(red)
stroke(none)
circle("circle.east", radius: 0.3)
```

### Named

Named anchors are normally unique to the type of element, such as a bezier curve's control points. Other border and path anchors specify their own named anchors that are available to all elements that support border or path anchors.

Elements that have an `anchor` argument also have a "default" named anchor. You can use it by just giving the element's name without an anchor.

### Border

A border anchor refers to a point on the element's border where a ray is cast from the element's center at a given angle and hits the border.

They are given as angles where `0deg` is towards the right and `90deg` is up.

Border anchors also specify named compass directions such as "north", "north-east", etc. Border anchors also specify a "center" named anchor which is where the ray cast originates from.

```typ
circle((0, 0), name: "circle", radius: 1)

set-style(content: (frame: "rect", stroke: none, fill: white, padding: .1))
content((name: "circle", anchor: 0deg), [0deg], anchor: "west")
content((name: "circle", anchor: 160deg), [160deg], anchor: "south-east")
content("circle.north", [North], anchor: "south")
content("circle.south-east", [South East], anchor: "north-west")
content("circle.south-west", [South West], anchor: "north-east")
```

### Path

A path anchor refers to a point along the path of an element. They can be given as either a `number` for an absolute distance along the path, or a `ratio` for a relative distance along the path.

Path anchors also specify three anchors "start", "mid" and "end".

```typ
line((0,0), (10, 1), name: "line")

set-style(content: (frame: "rect", stroke: none, fill: white, padding: .1))
content("line.start", [0%, 0, "start"], anchor: "east")
content("line.mid", [50%, "mid"])
content("line.end", [100%, "end"], anchor: "west")

content((name: "line", anchor: 75%), [75%])
content((name: "line", anchor: 50pt), [50pt])
```

---

## Marks

Marks are arrow tips that can be added to the end of path based elements that support the `mark` style key, or can be directly drawn by using the `mark` draw function. Marks are specified by giving their names (or shorthand) as strings and have several options to customise them. You can give an array of names to have multiple marks, and dictionaries can be used in the array for per mark styling.

```typ render
#set page(margin: 0cm)
#align(center, table(
  columns: 3,
  [*Name*], [*Shorthand*], [*Shape*],
  ..(for (name, item) in cetz.mark-shapes.marks {
    let name-to-mnemonic = (:)
    for (name, item) in cetz.mark-shapes.mnemonics {
      let list = name-to-mnemonic.at(item.at(0), default: ())
      list += (raw(name) + if item.at(1).at("reverse", default: false) { " (reversed)" },)
      name-to-mnemonic.insert(item.at(0), list)
    }
    (
      raw(name),
      name-to-mnemonic.at(name, default: ([],)).join([, ]),
      cetz.canvas(cetz.draw.line((), (1, 0), mark: (end: name)))
    )
  })
))
```

```typ
let c = ((rel: (0, -1)), (rel: (2, 0), update: false)) // Coordinates to draw the line, it is not necessary to understand this for this example.

// No marks
line((), (rel: (1, 0), update: false))

// Draws a triangle mark at both ends of the line.
set-style(mark: (symbol: ">"))
line(..c)

// Overrides the end mark to be a diamond but the start is still a triangle.
set-style(mark: (end: "<>"))
line(..c)

// Draws two triangle marks at both ends but the first mark of end is still a diamond.
set-style(mark: (symbol: (">", ">")))
line(..c)

// Sets the stroke of first mark in the sequence to red but the end mark overrides it to be blue.
set-style(mark: (symbol: ((symbol: ">", stroke: red), ">"), end: (stroke: blue)))
line(..c)
```

---

- `symbol` (none,str,array,dictionary) = `none`: This option sets the mark to draw when using the `mark` draw function, or applies styling to both mark ends of path based elements. The mark's name or shorthand can be given. Multiple marks can be drawn by passing an array of names or shorthands. When `none`, no marks will be drawn. A style{" "} `dictionary` can be given instead of a `str` to override styling for that particular mark, just make sure to still give the mark name using the `symbol` key otherwise nothing will be drawn!

- `start` (none,str,array,dictionary) = `none`: This option sets the mark to draw at the start of a path based element. It will override all options of the `symbol` key and will not affect marks drawn using the `mark` draw function.

- `end` (none,str,array,dictionary) = `none`: Like `start` but for the mark at the end of a path.

- `length` (number) = `0.2cm`: The size of the mark in the direction it is pointing.

- `width` (number) = `0.15cm`: The size of the mark along the normal of its direction.

- `inset` (number) = `0.05cm`: It specifies a distance by which something inside the arrow tip is set inwards; for the stealth arrow tip it is the distance by which the back angle is moved inwards.

- `scale` (float) = `1`: A factor that is applied to the mark's length, width and inset.

- `sep` (number) = `0.1cm`: The distance between multiple marks along their path.

- `position-samples` (int) = `30`: Only applicable when marks are used on curves such as bezier and hobby. The maximum number of samples to use for calculating curve positions. A higher number gives better results but may slow down compilation

- `pos` (number,ratio,none) = `none`: Overrides the mark's position along a path. A number will move it an absolute distance, while a ratio will be a distance relative to the length of the path. Note that this may be removed in the future in preference of a different method.

- `offset` (number,ratio,none) = `none`: Like `pos` but it advances the position of the mark instead of overriding it.

- `anchor` (str) = `tip`: Anchor to position the mark at. Can be one of `base`, `center` or `tip`.

- `slant` (ratio) = `0%`: How much to slant the mark relative to the axis of the arrow. 0% means no slant 100% slants at 45 degrees.

- `harpoon` (bool) = `false`: When true only the top half of the mark is drawn.

- `flip` (bool) = `false`: When true the mark is flipped along its axis.

- `reverse` (bool) = `false`: Reverses the direction of the mark.

- `xy-up` (vector) = `(0, 0, 1)`: The direction which is "up" for use when drawing 2D marks.

- `z-up` (vector) = `(0, 1, 0)`: The direction which is "up" for use when drawing 3D marks.

- `shorten-to` (int,auto,none) = `auto`: Which mark to shorten the path to when multiple marks are given. `auto` will shorten to the last mark, `none` will shorten to the first mark (effectively disabling path shortening). An integer can be given to select the mark's index.

- `transform-shape` (bool) = `true`: When `false` marks will not be stretched/affected by the current transformation, marks will be placed after the path is transformed.

---

## Libraries

CeTZ provides more specialised and focused functions in order to draw plots, charts, angles etc. They have been separated from the `draw` module into separate libraries for the sake of organisation and clarity.

---

## Tree

The tree library allows the drawing of diagrams with simple tree layout algorithms.

### Nodes

A tree node is an array consisting of the node's value at index 0 followed by its child nodes. For the default `draw-node` function, the value (the first item) of a node must be of type `content`.

Example of a list of nodes:

```typ
cetz.tree.tree(
  (
    [A],
    (
      [B],
      (
        [C],
        ([D],)
      )
    )
  ),
  direction: "right"
)
```

Example of a tree of nodes:

```typ
cetz.tree.tree(
  (
    [A],
    (
      [B],
      [C]
    ),
    (
      [D],
      [E]
    )
  ),
  direction: "right"
)
```

### Drawing and Styling Tree Nodes

The `tree()` function takes an optional `draw-node:` and `draw-edge:` callback function that can be used to customice node and edge drawing.

The `draw-node` function must take the current node and its parents node anchor as arguments and return one or more elements.

For drawing edges between nodes, the `draw-edge` function must take two node anchors and the target node as arguments and return one or more elements.

```typ
import cetz.tree
let data = ([\*], ([A], [A.A], [A.B]), ([B], [B.A]))
tree.tree(
  data,
  direction: "right",
  draw-node: (node) => {
    circle((), radius: .35, fill: blue, stroke: none)
    content((), text(white, [#node.content]))
  },
  draw-edge: (parent, child) => {
    let (a, b) = (parent.group-name, child.group-name)
    line((a, .4, b), (b, .4, a))
  }
)
```

---

## A Picture for Karl's New Students

This tutorial is intended for new users of CeTZ. It does not give an exhaustive account of all the features of CeTZ, just of those you are likely to use right away. This tutorial also acts as a parallel to Ti*k*Z's tutorial [A Picture for Karl's Students](https://tikz.dev/tutorial).

Karl is a math and chemistry high-school teacher. He used to create the graphics in his worksheets and exams using the Ti*k*Z package with $\LaTeX$. While the results were acceptable, Karl, for his own reasons, has started using Typst instead. He looks through the provided packages in [Typst: Universe](https://typst.app/universe/) and finds CeTZ, which is supposed to stand for "CeTZ, ein Typst Zeichenpaket" and appears appropriate.

### Problem Statement

Karl wants to put a graphic on the next worksheet for his students. He is currently teaching his students about sine and cosine. He already has the graphic drawn with Ti*k*Z and would like to keep it as close to it as possible:

```
Either the example gets rendered using a block or we pre-render it I'm not sure yet.
```

### Setting up the Environment

In CeTZ, to draw a picture, two imports and a function call is all you need. Karl sets up his file as follows:

```typ
#set page(width: auto, height: auto)
#import "@preview/cetz:0.5.2"

We are working on
#cetz.canvas({
  import cetz.draw: *
  line((-1.5, 0), (1.5, 0))
  line((0, -1.5), (0, 1.5))
})
```

When compiled via the Typst web app or the Typst command line interface, the resulting output will contain something that looks like this:

```typ
We are working on
#cetz.canvas({
  import cetz.draw: *
  line((-1.5, 0), (1.5, 0))
  line((0, -1.5), (0, 1.5))
})
```

Admittedly, not quite the whole picture, yet, but we do have the axes established. Well, not quite, but we have the lines that make up the axes drawn. Karl suddenly has a sinking feeling that the picture is still some way off.

Let's have a more detailed look at the code. First, the package `cetz` is imported. The `canvas` function in the `cetz` module is then called and a pair of curly braces are placed as the function's first (and only) positional argument. The braces create a scope or body, in which more functions can be called, but first must be imported from the `draw` module.

Inside the body there are two `line` functions. They are draw functions that draw straight lines between given positions. The first `line` function is given the parameters `(-1.5, 0), (1.5, 0)`, which refer to a point at position $(-1.5, 0)$ and $(1.5, 0)$. Here, the positions are specified within a special coordinate system in which, initially, one unit is 1cm.

Karl is quite pleased to note that the environment automatically reserves enough space to encompass the picture.

### Line Construction

The basic building block of all pictures in CeTZ are draw functions. A draw function is a function that can be called inside the canvas body in order to create the graphic, such as `line`, `bezier`, `rect` and many more (not all draw functions _actually_ draw something, like `set-style`, but still effect the outcome of the picture).

In order to draw a path of straight lines, the `line` draw function can be used. You specify the coordinates of the start position by passing an array with two numbers (a `coordinate` type) to the first parameter of `line`. The second coordinate must be given as the second parameter of the function otherwise it will panic. Subsequent coordinates can be passed to the function to draw additional lines between the previous and next coordinates.

```typ
line((-1.5, 0), (1.5, 0), (0, -1.5), (0, 1.5))
```

Note that the `canvas` function and import statements have been omitted from the code as they are boiler plate and don't always need to be shown. They are very much still required in order to produce the picture, so just remember they are there okay.

### Curve Construction

The next think Karl wants to do is to draw the circle. For this, straight lines obviously will not do. Instead, we need some way to draw curves. For this, CeTZ provides several other draw functions, the most useful here would be the `bezier` function. As the name suggests, it can draw a bezier curve when a start and end coordinate is given, as well as one or two control points.

Here is an example (the control points have been added for clarity):

```typ {8}
// start and end
circle((0, 0), radius: 2pt, fill: gray)
circle((2, 0), radius: 2pt, fill: gray)
// control points
circle((1, 1), radius: 2pt, fill: gray)
circle((2, 1), radius: 2pt, fill: gray)

bezier((0, 0), (2, 0), (1, 1), (2, 1))
```

So, Karl can now add the first half circle to the picture:

```typ
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))

bezier((-1, 0), (0, 1), (-1, 0.555), (-0.555, 1))
bezier((0, 1), (1, 0), (0.555, 1), (1, 0.555))
```

Karl is happy with the result, but finds specifying circles in this way to be extremely awkward. Fortunately, there is a much simpler way.

### Circle Construction

In order to draw a circle, the `circle` draw function can be used:

```typ
circle((0, 0), radius: 10pt)
```

You can also draw an ellipse with this draw function by passing an array of two numbers to the `radius` argument:

```typ
circle((0, 0), radius: (20pt, 10pt))
```

To draw an ellipse whose axes are not horizontal and vertical, but point in an arbitrary direction you can use transformations, which are explained later.

So, returning to Karl's problem, he can write `circle((0, 0))` to draw the circle as, by default, the `radius` argument is `1`:

```typ
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))

circle((0, 0))
```

At this point, Karl is a bit alarmed that the circle is so small when he wants the final picture to be much bigger. He is pleased to learn that CeTZ has transformation draw functions and scaling everything by a factor of three is very easy. But let us leave the size as it is for the moment to save some space.

### Rectangle Construction

The next things we would like to have is the grid in the background. There are several ways to produce it. For example, one might draw lots of rectangles. To do so, the `rect` draw function can be used. Two coordinates should be passed as arguments, they specify the corners of the rectangle:

```typ
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))

rect((0, 0), (0.5, 0.5))
rect((-0.5, -0.5), (-1, -1))
```

While this may be nice in other situations, this is not really leading anywhere with Karl's problem: First, we would need an awful lot of these rectangles and then there is the border that is not "closed".

So, Karl is about to resort to simply drawing four vertical and four horizontal lines using the nice `line` draw function, when he learns that there is a `grid` draw function.

### Grid Construction

The `grid` draw function adds a grid to the picture. It will add lines making up a grid that fills the rectangle specified by two coordinates passed to it.

For Karl, the following code could be used:

```typ
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))

grid((-1.5, -1.5), (1.5, 1.5), step: 0.5)
```

Having another look at his desired picture, karl notices that it would be nice for the grid to be more subdued. To subdue the grid, Karl adds more named arguments to the `grid` draw function. First, he uses the color `gray` for the grid lines. Second, he reduces the line width to `0.2pt` (Ti*k*Z's `very thin`). Finally, he swaps the ordering of the commands so that the grid is drawn first and everything else on top.

```typ
grid((-1.5, -1.5), (1.5, 1.5), step: 0.5, stroke: gray + 0.2pt)
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))
```

### Adding a Touch of Style

Karl notices that the thickness of the circle and axes paths are much greater than the grid's thickness. He learns that CeTZ's default stroke thickness is actually `1pt` and not Ti*k*Z's `0.4pt`. Karl decides that he would like to use the thinner lines to keep this new picture as close to the original as possible.

We can use the `set-style` draw function to apply styling to all subsequent draw functions, similar to how Typst's `set` and `show` rules work. To set the stroke's thickness he uses the named argument `stroke: 0.4pt`:

```typ
set-style(stroke: 0.4pt)
grid((-1.5, -1.5), (1.5, 1.5), step: 0.5, stroke: gray + 0.2pt)
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))
```

Karl can also move the grid's styling into the same `set-style` function by passing it as a dictionary to the `grid` named argument:

```typc
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
grid((-1.5, -1.5), (1.5, 1.5))
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))
```

### Arc Construction

Our next obstacle is to draw the arc for the angle. For this, the `arc` draw function can be used, which draws part of a circle or ellipse. This function requires arguments to specify the arc. An example would be `arc((0, 0), start: 10deg, stop: 80deg, radius: 10pt)`, which creates an arc starting at $(0, 0)$ at an angle of $10°$ to $80°$ with a radius of `10pt`. Karl obviously needs an arc from $0°$ to $30°$. The radius should be something relatively small, perhaps around one third of the circle's radius.

```typ
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
grid((-1.5, -1.5), (1.5, 1.5))
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))
arc((3mm, 0), start: 0deg, stop: 30deg, radius: 3mm)
```

Karl thinks this is really a bit small and he cannot continue unless he learns how to do scaling. For this, he can use the `scale` draw function at the start of the canvas body

```typ
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
scale(3)
grid((-1.5, -1.5), (1.5, 1.5))
line((-1.5, 0), (1.5, 0))
line((0, -1.5), (0, 1.5))
circle((0, 0))
arc((3mm, 0), start: 0deg, stop: 30deg, radius: 3mm)
```

As for circles, you can specify the radius as an array of two numbers to get an elliptical arc.

```typ
arc((0, 0), start: 0deg, stop: 315deg, radius: (1.75, 1))
```

### Not Really Path Clipping

In order to save space in this manual, it would be nice to clip Karl's graphics a bit so we can focus on the "interesting" parts. Unfortunately clipping is not currently possible in CeTZ. So instead we can replace the circle with an arc and modify the grid.

```typ
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
scale(3)
grid((-0.5, -0.5), (1, 1))
line((-0.5, 0), (1, 0))
line((0, -0.5), (0, 1))
arc((0, 1), start: 90deg, delta: -120deg)
arc((3mm, 0), start: 0deg, stop: 30deg, radius: 3mm)
```

### Filling and Drawing

Returning to the picture, Karl now wants the angle to be "filled" with a very light green. For this he uses the `fill` styling parameter. Here is what Karl does:

```typ {18-19}
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
scale(3)
grid((-0.5, -0.5), (1, 1))
line((-0.5, 0), (1, 0))
line((0, -0.5), (0, 1))
arc((0, 1), start: 90deg, delta: -120deg)
arc(
  (3mm, 0),
  start: 0deg,
  stop: 30deg,
  radius: 3mm,
  mode: "PIE",
  fill: color.mix((green, 20%), white),
)
```

The color `color.mix((green, 20%), white)` means 20% green and 80% white mixed together. In fact `fill` can take any value of type `color`, you can even do shading!

By default arcs are in "OPEN" mode where only the curve is drawn and only the chord of the arc will be filled. By using `mode: "PIE"` the arc will be closed around its origin leaving you with a shape akin to a slice of pie, or in this case an angle which can be properly filled.

### Specifying Coordinates

Karl now wants to add the sine and cosine lines. He knows already that he can use the `stroke:` styling parameter to set the lines' colors. So, what is the best way to specify the coordinates?

There are different ways of specifying coordinates. The easiest way is to say something like `(10pt, 2cm)`. This means 10pt in $x$-direction and 2cm in $y$-directions. Alternatively, you can also leave out the units as in `(1, 2)`, which means "one times the unit length in the $x$-direction and twice the unit length in the $y$-direction". The unit length defaults to 1cm in both directions.

In order to specify points in polar coordinates, use an `array` of the form `(30deg, 1cm)`, which means 1cm in direction 30 degree. This is obviously quite useful to "get to the point $(\cos 30\degree, \sin 30 \degree)$ on the circle".

You can wrap a coordinate in a `dictionary` with the key `rel` as in `(rel: (0cm, 1cm))`. Such coordinates are interpreted differently: They mean "1cm upwards from the previous specified position, making this the new specified position". You can include the key and value `update: false` in the coordinate `(rel: (2cm, 0cm), update: false)` which means "2cm to the right of the previous specified position and do not change the previous position". For example, we an draw the sine line as follows:

```typ {21}
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
scale(3)
grid((-0.5, -0.5), (1, 1))
line((-0.5, 0), (1, 0))
line((0, -0.5), (0, 1))
arc((0, 1), start: 90deg, delta: -120deg)
arc(
  (3mm, 0),
  start: 0deg,
  stop: 30deg,
  radius: 3mm,
  mode: "PIE",
  fill: color.mix((green, 20%), white),
)
line((30deg, 1cm), (rel: (0, -0.5)), stroke: red + 1.2pt)
```

Karl used the fact $\sin 30 \degree = 1/2$. However, he very much doubts that his students know this, so it would be nice to have a way of specifying "the point straight down from `(30deg, 1cm)` that lies on the $x$-axis". This is, indeed, possible using a special coordinate: Karl can write `((30deg, 1cm), "|-", (0, 0))`. In general, the meaning of `(p, "|-", q)` is "the intersection of a vertical line through $p$ and a horizontal line through $q$".

Next, let us draw the cosine line. One way would be to use `line(((30deg, 1cm), "|-", (0, 0)), (0, 0))`. Another way is the following: we "continue" from where the sine ends:

```typ {22}
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
scale(3)
grid((-0.5, -0.5), (1, 1))
line((-0.5, 0), (1, 0))
line((0, -0.5), (0, 1))
arc((0, 1), start: 90deg, delta: -120deg)
arc(
  (3mm, 0),
  start: 0deg,
  stop: 30deg,
  radius: 3mm,
  mode: "PIE",
  fill: color.mix((green, 20%), white),
)
line((30deg, 1cm), (rel: (0, -0.5)), stroke: red + 1.2pt)
line((), (0, 0), stroke: blue + 1.2pt)
```

Note that an empty array `()` is given as the line's starting coordinate. This value means "the previous specified coordinate", which in this case is the end of the cosine line.

### Intersecting Paths

Karl is left with the line for $\tan \alpha$, which seems difficult to specify using transformations and polar coordinates. The first - and easiest - thing he can do is so simply use the coordinate `(1, calc.tan(30deg))`.

Karl can, however, also use a more elaborate, but also more "geometric" way of computing the length of the orange line: He can specify intersections of paths as coordinates. The line for $\tan \alpha$ starts at $(1, 0)$ and goes upward to a point that is at the intersection of a line going "up" and a line going from the origin through `(30deg, 1cm)`. Such computations are made available by the `intersections` function.

What Karl must do is to create two "invisible" paths that intersect at the position of interest. Creating lines that are not otherwise seen can be done by either setting their stroke to `none` or by wrapping them in the `hide` function. Then, Karl can add the `name` parameter to the lines for later reference. Once the lines have been constructed, Karl can use the `intersections` function to get the coordinate for later reference.

```typc
hide({
  line((1, 0), (1, 1), name: "upward line")
  line((0, 0), (30deg, 1.5cm), name: "sloped line") // a bit longer, so that there is an intersection
})

intersections("x", "upward line", "sloped line")
line((1, 0), "x.0", stroke: orange + 1.2pt)
```

### Adding Marks

Karl now wants to add the little arrow tips at the end of the axes. He has noticed that in many plots, even in scientific journals, these arrow tips seem to be missing, presumably because the generating programs cannot produce them. Karl thinks arrow tips belong at the end of axes. His son agrees. His students do not care about arrow tips.

It turns out that adding arrow tips is pretty easy: Karl adds the `mark` styling parameter with the value `(end: ">")` to the line functions for the axes:

```typ {10-11}
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  )
)
scale(3)
grid((-0.5, -0.5), (1.5, 1.5))
line((-0.5, 0), (1.5, 0), mark: (end: ">"))
line((0, -0.5), (0, 1.5), mark: (end: ">"))
arc((0, 0), start: 120deg, stop: -30deg, anchor: "origin")
arc(
  (3mm, 0),
  start: 0deg,
  stop: 30deg,
  radius: 3mm,
  mode: "PIE",
  fill: color.mix((green, 20%), white),
)
line((30deg, 1cm), (rel: (0, -0.5)), stroke: red + 1.2pt)
line((), (0, 0), stroke: blue + 1.2pt)

hide({
  line((1, 0), (1, 1), name: "upward line")
  line((0, 0), (30deg, 1.5cm), name: "sloped line")
})
intersections("x", "upward line", "sloped line")
line((1, 0), "x.0", stroke: orange + 1.2pt)
```

If Karl had used the value `(start: ">")` instead of `(end: ">")`, arrow tips would have been put at the beginning of the path. The value `(start: ">", end: ">")` or `(symbol: ">")` puts the marks at both ends of the path.

Some elements do not support marks. As a rule of thumb, you can add marks only to elements that do not have a closed path.

Karl notices that the marks are unnaturally large, this is because the shape of marks are transformed by default. So the marks are three times as big. This can be resolved by setting the `transform-shape: false` styling parameter. He also wants the mark to be filled and to have a different shape. As done earlier, the `fill` styling parameter can be used to fill marks and a different shape can be obtained by referring to the table of currently [supported marks](../basics/marks).

### Repeating Things: For-Loops

Karl's next aim is to add little ticks on the axes at positions $-1$, $-1/2$, $1/2$, and $1$. For this, it would be nice to use some kind of "loop", especially since he wishes to do the same thing at each of these positions. Thankfully Typst [has built in loops](https://typst.app/docs/reference/scripting/#loops).

Karl can then use the following code:

```typc {26-31} example
set-style(
  stroke: 0.4pt,
  grid: (
    stroke: gray + 0.2pt,
    step: 0.5
  ),
  mark: (
    transform-shape: false,
    fill: black
  )
)
scale(3)
grid((-1, -1), (1.5, 1.5))
line((-1, 0), (1.5, 0), mark: (end: "stealth"))
line((0, -1), (0, 1.5), mark: (end: "stealth"))
circle((0, 0))
arc(
  (3mm, 0),
  start: 0deg,
  stop: 30deg,
  radius: 3mm,
  mode: "PIE",
  fill: color.mix((green, 20%), white),
)

for x in (-1, -0.5, 1) {
  line((x, -1pt), (x, 1pt))
}
for y in (-1, -0.5, 0.5, 1) {
  line((-1pt, y), (1pt, y))
}
```

### Adding Text

Karl is, by now, quite satisfied with the picture. However, the most important parts, namely the labels, are still missing!

CeTZ has the `content` draw function which allows you to place any content onto the canvas at a specified position.

---

## Custom Types

### `context`

A `dictionary` that holds the internal state of the canvas such as the element dictionary, the current transformation matrix, group and canvas unit length.
The following fields are considered stable:
- length (length): Length of one canvas unit as typst length
- transform (matrix): Current 4x4 transformation matrix
- background (none,color,gradient,tiling): The canvas' background
- debug (bool): True if the canvas' debug flag is set
- shared-state (dictionary): State that is not scoped by `group` or `scope` elements and can be used to share canvas-global state

### `element`

A function that, when called with a `context`, returns some data that effects the canvas. Can also be an `array` of this type.

---

## Advanced: Transformations

The default transformation matrix of the canvas is set to:
$mat(1, 0,-0.5, 0;
     0,-1, 0.5, 0;
     0, 0, 0,   0;
     0, 0, 0,   1)$

---

# Part 2: API Reference (Draw Functions)

These are the functions imported via `import cetz.draw: *` inside a canvas body. Signatures and examples are extracted from the source docstrings.

## Shapes

### `circle`

**Signature:** `circle(..points-style, name: none, anchor: none)`

Draws a circle or ellipse.

```typ
// Draw a circle with center (0, 0)
circle((0, 0))
```

```typ
// Draw an ellipse
circle((2, 0), radius: (1, 0.5))
```

```typ
let (a, b) = ((2, 1), (1, 1))

// Draw a circle with its center at (2, 1), going
// through point (1, 1)
circle(a, b)

// Show both points
set-style(content: (frame: "circle", padding: 1pt, fill: white))
content(a, [A]); content(b, [B])
```

- ..points-style (coordinate, style): The position to place the circle on.
  If given two coordinates, the distance between them is used as radius.
  If given a single coordinate, the radius can be set via the `radius` (style)
  argument.
- name (none,str):
- anchor (none, str):

**Styling**

*Root*: `circle`

- radius (number, array) = 1: A number that defines the size of the circle's radius. Can also be set to a tuple of two numbers to define the radii of an ellipse, the first number is the `x` radius and the second is the `y` radius.

**Anchors**

  Supports border and path anchors. The `"center"` anchor is the default.

### `circle-through`

**Signature:** `circle-through(a, b, c, name: none, anchor: none, ..style)`

Draws a circle through three coordinates.

```typ
let (a, b, c) = ((0, 0), (2, -0.5), (1, 1))

// Draw a circle through 3 points
circle-through(a, b, c, name: "c")

// Show the points
set-style(content: (frame: "circle", padding: 1pt, fill: white))
content(a, [A]); content(b, [B]); content(c, [C])
```

- a (coordinate): Coordinate a.
- b (coordinate): Coordinate b.
- c (coordinate): Coordinate c.
- name (none,str):
- anchor (none,str):
- ..style (style):

**Styling**

*Root*: `circle`

`circle-through` has the same styling as `circle` except for
`radius` as the circle's radius is calculated by the
given coordinates.

**Anchors**

Supports the same anchors as `circle` as well as:
- a: Coordinate a
- b: Coordinate b
- c: Coordinate c

### `arc`

**Signature:** `arc(position, start: auto, stop: auto, delta: auto, name: none, anchor: none, ..style,)`

Draws a circular segment.

```typ
arc((0,0), start: 45deg, stop: 135deg)
arc((0,-0.5), start: 45deg, delta: 90deg, mode: "CLOSE")
arc((0,-1), stop: 135deg, delta: 90deg, mode: "PIE")
```

Note that two of the three angle arguments (`start`, `stop` and `delta`) must be set.
The current position `()` gets updated to the arc's end coordinate (anchor `arc-end`).

- position (coordinate): Position to place the arc at.
- start (auto,angle): The angle at which the arc should start. Remember that `0deg` points directly towards the right and `90deg` points up.
- stop (auto,angle): The angle at which the arc should stop.
- delta (auto,angle): The change in angle away start or stop.
- name (none,str):
- anchor (none, str):
- ..style (style):

**Styling**

*Root*: `arc`\
- radius (number, array) = 1: The radius of the arc. An elliptical arc can be created by passing a tuple of numbers where the first element is the x radius and the second element is the y radius.
- mode (str) = "OPEN": The options are: `"OPEN"` no additional lines are drawn so just the arc is shown; `"CLOSE"` a line is drawn from the start to the end of the arc creating a circular segment; `"PIE"` lines are drawn from the start and end of the arc to the origin creating a circular sector.
- update-position (bool) = true: Update the current canvas position to the arc's end point (anchor `"arc-end"`). This overrides the default of `true`, that allows chaining of (arc) elements.

**Anchors**

Supports border and path anchors.
- arc-start: The position at which the arc's curve starts, this is the default.
- arc-end: The position of the arc's curve end.
- arc-center: The midpoint of the arc's curve.
- center: The center of the arc, this position changes depending on if the arc is closed or not.
- chord-center: Center of chord of the arc drawn between the start and end point.
- origin: The origin of the arc's circle.

### `arc-through`

**Signature:** `arc-through(a, b, c, name: none, ..style, ) = get-ctx(ctx => { let (ctx, a, b, c) = coordinate.resolve(ctx, a, b, c) (a, b, c) = (a, b, c).map(pt => pt.map(calc.round.with(digits: matrix.precision))) assert(a.at(2) == b.at(2) and b.at(2) == c.at(2), message: "The z coordinate of all points must be equal, but is: " + repr((a, b, c).map(v => v.at(2)))) // Calculate the circle center from three points or fails if all // three points are on one straight line. let center = util.calculate-circle-center-3pt(a, b, c) let radius = vector.dist(center, a) // Find the start and inner angle between a-center-c let start = vector.angle2(center, a) let delta = vector.angle(a, center, c) // Returns a negative number if pt is left of the line a-b, // if pt is right to a-b, a positive number is returned, // otherwise zero. let side-on-line(a, b, pt) = { let (x1, y1, ..) = a let (x2, y2, ..) = b let (x, y, ..)`

Draws an arc that passes through three points a, b and c.

Note that all three points must not lie on a straight line, otherwise
the function fails.

```typ
let (a, b, c) = ((0, 1), (2, 2), (2, 0))

// Draw an arc through 3 points
arc-through(a, b, c)

// Show the points
set-style(content: (frame: "circle", padding: 1pt, fill: white))
content(a, [A]); content(b, [B]); content(c, [C])
```

- a (coordinate): Start position of the arc
- b (coordinate): Position the arc passes through
- c (coordinate): End position of the arc
- name (none, str):
- ..style (style):

**Styling**

*Root*: `arc` \
Uses the same styling as `arc`.

**Anchors**

For anchors see `arc`.

### `mark`

**Signature:** `mark(from, to, ..style)`

Draws a single mark pointing towards a target coordinate.

```typ
// Show a grid
grid((-1, -1), (1, 1), stroke: gray)

// Draw a mark with its tip at (0, 0) pointing to (1, 0)
mark((0, 0), (1, 0), symbol: ")>", scale: 4)
```

```typ
// Show a grid
grid((-1, -1), (1, 1), stroke: gray)

// Draw a mark with its center at (0, 0) pointing to (1, 1)
mark((0, 0), (1, 1), symbol: ">>", anchor: "center", scale: 5)
```

Note: To place a mark centered at the first coordinate (`from`) use
the marks `anchor: "center"` style.

- from (coordinate): The position to place the mark.
- to (coordinate,angle): The position or angle the mark should point towards.
- ..style (str,style): If the third positional argument is of type string, it is treated as mark name (e.g. `">"`) and overrules style keys such as `mark.symbol` or `mark.end`

**Styling**

*Root*: `mark`

You can directly use the styling from mark styling.

### `line`

**Signature:** `line(..pts-style, close: false, name: none)`

Draws a line, more than two points can be given to create a line-strip.

```typ
// Draw a line between two points
line((0, 0), (1.5, 1))
```

```typ
// Draw a line between more than two points
line((0, 0), (1, 0.5), (2, -0.5), (3, 0))
```

```typ
// Draw a polygon using `close: true`
line((0, 0), (0, 1), (1, 2), (2, 1), (2,0), close: true)
```

If the first or last coordinates are given as the name of an element,
that has a `"default"` anchor, the intersection of that element's border
and a line from the first or last two coordinates given is used as coordinate.
This is useful to span a line between the borders of two elements. Note, that passing
strings bypasses custom resolvers when trying to find elements!

```typ
circle((1,2), radius: .5, name: "a")
rect((2,1), (rel: (1,1)), name: "b")
line("a", "b")
```
- ..pts-style (coordinate,style): Positional two or more coordinates to draw lines between. Accepts style key-value pairs.
- close (bool): If true, the line-strip gets closed to form a polygon
- name (none,str):

**Styling**

*Root:* `line`

Supports mark styling.

**Anchors**

  Supports path anchors.
- centroid: The centroid anchor is calculated for _closed non self-intersecting_ polygons if all vertices share the same z value.

### `polygon`

**Signature:** `polygon(origin, sides, angle: 0deg, name: none, anchor: none, ..style)`

Draws a regular polygon.

```typ
set-style(polygon: (radius: 0.65))

polygon((0, 0), 3, angle: 90deg)
polygon((1.5,0), 5)
polygon((3, 0), 7)
```

- origin (coordinate): Coordinate to draw the polygon at
- sides (int): Number of sides of the polygon (>= 3)
- angle (angle) = 0deg: Angle angle to rotate the polygon arround its origin
- name (none, str):

**Styling**

*Root*: `polygon`
- radius (number) = 1: Radius of the polygon

### `n-star`

**Signature:** `n-star(origin, sides, angle: 0deg, name: none, anchor: none, ..style)`

Draws a n-pointed star.

```typ
set-style(n-star: (radius: 0.65))

n-star((0, 0), 5)

// An 8-pointed star, rotated
n-star((1.5, 0), 8, angle: 11.25deg)

// A 6-pointed star showing its inner hexagon
n-star((3, 0), 6, show-inner: true)
```

- origin (coordinate): Coordinate to draw the star's center at.
- sides (int): Number of points of the star (>= 3).
- angle (angle) = 0deg: Angle to rotate the star around its origin.
- name (none, str): An optional name to identify the shape.

**Styling**

Root: nstar

- radius (number): The radius of the star's outer points.
- inner-radius (number,ratio): The radius (if of type ratio, relative to the outer radius) of the star's inner points of the star's inner points.
- show-inner (bool) = false: If true, also draws the inner polygon connecting the star's inner points.
- fill (color, gradient): The fill color for the star.
- stroke (color, thickness, ...): The stroke for the star and the inner polygon.

### `grid`

**Signature:** `grid(from, to, name: none, ..style)`

Draws a grid between two coordinates

```typ
// Draw a grid
grid((0,0), (2,2))

// Draw a smaller blue grid
grid((1,1), (2,2), stroke: blue, step: .25)
```

- from (coordinate): The top left of the grid
- to (coordinate): The bottom right of the grid
- name (none,str):
- ..style (style):

**Styling**

*Root*: `grid`
- step (number, array, dictionary) = 1: Distance between grid lines. A distance of $1$ means to draw a grid line every $1$ length units in x- and y-direction. If given a dictionary with `x` and `y` keys or a tuple, the step is set per axis.
- shift (number, array, dictionary) = 0: Offset of the grid lines. Supports an array of the form `(x, y)` or a dictionary of the form `(x: <number>, y: <number>)`.
- help-lines (bool) = false: If true, force the stroke style to `gray + 0.2pt`

**Anchors**

  Supports border anchors.

### `content`

**Signature:** `content(..args-style, angle: 0deg, anchor: none, name: none,)`

Positions Typst content in the canvas. Note that the content itself is not transformed only its position is.

```typ
content((0,0), [Hello World!])
```
To put text on a line you can let the function calculate the angle between its position and a second coordinate by passing it to `angle`:

```typ
line((0, 0), (3, 1), name: "line")
content(
  ("line.start", 50%, "line.end"),
  angle: "line.end",
  padding: .1,
  anchor: "south",
  [Text on a line]
)
```

```typ
// Place content in a rect between two coordinates
content(
  (0, 0),
  (2, 2),
  box(
    par(justify: false)[This is a long text.],
    stroke: 1pt,
    width: 100%,
    height: 100%,
    inset: 1em
  )
)
```

- ..args-style (coordinate, content, style): When one coordinate is given as a positional argument, the content will be placed at that position. When two coordinates are given as positional arguments, the content will be placed inside a rectangle between the two positions. All named arguments are styling and any additional positional arguments will panic.
- angle (angle,coordinate): Rotates the content by the given angle. A coordinate can be given to rotate the content by the angle between it and the first coordinate given in `args`. This effectively points the right hand side of the content towards the coordinate. This currently exists because Typst's rotate function does not change the width and height of content.
- anchor (none, str):
- name (none, str):

**Styling**

*Root*: `content`
- padding (number, dictionary) = 0: Sets the spacing around content. Can be a single number to set padding on all sides or a dictionary to specify each side specifically. The dictionary follows Typst's `pad` function: https://typst.app/docs/reference/layout/pad/
- frame (str, none) = none: Sets the frame style. Can be `none`, `"rect"` or `"circle"` and inherits the `stroke` and `fill` style.
- auto-scale (bool): If `true`, apply current canvas scaling to the content. Defaults to `false`.
- wrap (function, none) = none: A function to apply the content body to. Must return content. Example: `text.with(red)` to wrap every content element in a `text(red, <body>)` element.

**Anchors**

Supports border anchors, the default anchor is set to *center*.
- mid: Content center, from baseline to top bounds
- mid-east: Content center extended to the east
- mid-west: Content center extended to the west
- base: Horizontally centered baseline of the content
- base-east: Baseline height extended to the east
- base-west: Baseline height extended to the west
- text: Position at the content start on the baseline of the content

### `rect`

**Signature:** `rect(a, b, name: none, anchor: none, ..style)`

Draws a rectangle between two coordinates.
```typ
// Draw a rect from A(0, 0) to B(1, 1)
rect((0, 0), (1, 1))

// Show the points
set-style(content: (frame: "circle", padding: 1pt, fill: white))
content((0, 0), [A]); content((1, 1), [B])
```

```typ
rect((0,0), (rel: (1,1)), radius: 0)
rect((2,0), (rel: (1,1)), radius: 25%)
rect((4,0), (rel: (1,1)), radius: (north: 50%))
rect((6,0), (rel: (1,1)), radius: (north-east: 50%))
rect((8,0), (rel: (1,1)), radius: (south-west: 0, rest: 50%))
rect((10,0), (rel: (1,1)), radius: (rest: (20%, 50%)))
```

**Styling**

*Root*: `rect`

- a (coordinate): Coordinate of the bottom left corner of the rectangle.
- b (coordinate): Coordinate of the top right corner of the rectangle. You can draw a rectangle with a specified width and height by using relative coordinates for this parameter `(rel: (width, height))`.
- name (none,str):
- anchor (none, str):
- ..style (style):
- radius (number,ratio,dictionary) = 0: The rectangle's corner radius. If set to a single number, that radius is applied to all four corners of the rectangle. If passed a dictionary you can set the radii per corner. The following keys support either a type:number, type:ratio or an array of type:number or type:ratio for specifying a different x- and y-radius: `north`, `east`, `south`, `west`, `north-west`, `north-east`, `south-west` and `south-east`. To set a default value for remaining corners, the `rest` key can be used.
  Ratio values are relative to the rectangle's width and height.

**Anchors**

  Supports border and path anchors. It's default is the `"center"` anchor.

### `bezier`

**Signature:** `bezier(start, end, ..ctrl-style, name: none)`

Draws a quadratic or cubic bezier curve

```typ
let (a, b, c) = ((0, 0), (2, 0), (1, 1))
bezier(a, b, c)

set-style(content: (frame: "circle", padding: 1pt, fill: white))
content(a, [A]); content(b, [B]); content(c, [C])
```

```typ
let (a, b, c, d) = ((0, 0), (2, 0), (.5, -1), (1.5, 1))
bezier(a, b, c, d)

set-style(content: (frame: "circle", padding: 1pt, fill: white))
content(a, [A]); content(b, [B]); content(c, [C]); content(d, [D])
```

- start (coordinate): Start position
- end (coordinate): End position (last coordinate)
- name (none,str):
- ..ctrl-style (coordinate,style): The first two positional arguments are taken as cubic bezier control points, where the first is the start control point and the second is the end control point. One control point can be given for a quadratic bezier curve instead. Named arguments are for styling.

**Styling**

*Root* `bezier`

Supports marks.

**Anchors**

Supports path anchors.
- ctrl-n: nth control point where n is an integer starting at 0

### `bezier-through`

**Signature:** `bezier-through(start, pass-through, end, name: none, ..style)`

Draws a cubic bezier curve through a set of three points.
See `bezier` for style and anchor details.

```typ
let (a, b, c) = ((0, 0), (1, 1), (2, -1))
bezier-through(a, b, c, name: "curve")

// Show the computed control points: 1 and 2
set-style(content: (frame: "circle", padding: 1pt, fill: white))
content(a, [A]); content(b, [B]); content(c, [C])
content("curve.ctrl-1", [2]); content("curve.ctrl-0", [1])
```

- start (coordinate): The position to start the curve.
- pass-through (coordinate): The position to pass the curve through.
- end (coordinate): The position to end the curve.
- name (none,str):
- ..style (style):

### `catmull`

**Signature:** `catmull(..pts-style, close: false, name: none)`

Draws a Catmull-Rom curve through a set of points.

```typ
catmull((0,0), (1,1), (2,-1), (3,0), tension: .4, stroke: blue)
catmull((0,0), (1,1), (2,-1), (3,0), tension: .5, stroke: red)
```

- ..pts-style (coordinate,style): Positional arguments should be coordinates that the curve should pass through. Named arguments are for styling.
- close (bool): Closes the curve with a straight line between the start and end of the curve.
- name (none,str):

**Styling**

*Root*: `catmull`

Supports marks.

- tension (float) = 0.5: How tight the curve should fit to the points. The higher the tension the less curvy the curve.

**Anchors**

Supports path anchors.
- pt-n: The nth given position (0 indexed so "pt-0" is equal to "start")

### `hobby`

**Signature:** `hobby(..pts-style, ta: auto, tb: auto, close: false, name: none)`

Draws a Hobby curve through a set of points.

```typ
hobby((0, 0), (1, 1), (2, -1), (3, 0), omega: 0, stroke: blue)
hobby((0, 0), (1, 1), (2, -1), (3, 0), omega: 1, stroke: red)
```

- ..pts-style (coordinate,style): Positional arguments are the coordinates to use to draw the curve with, a minimum of two is required. Named arguments are for styling.
- tb (auto,array): Incoming tension at `pts.at(n+1)` from `pts.at(n)` to `pts.at(n+1)`. The number given must be one less than the number of points.
- ta (auto, array): Outgoing tension at `pts.at(n)` from `pts.at(n)` to `pts.at(n+1)`. The number given must be one less than the number of points.
- close (bool): Closes the curve with a proper smooth curve between the start and end of the curve.
- name (none,str):

**Styling**

*Root* `hobby`

Supports marks.
- omega (array) = (1, 1): A tuple of floats that describe how curly the curve should be at each endpoint. When the curl is close to zero, the spline approaches a straight line near the endpoints. When the curl is close to one, it approaches a circular arc.

**Anchors**

Supports path anchors.
- pt-n: The nth given position (0 indexed, so "pt-0" is equal to "start")

### `compound-path`

**Signature:** `compound-path(body, name: none, ..style)`

Create a new path with each element used as sub-paths.
This can be used to create paths with holes.

Unlike `merge-path`, this function groups the shapes as sub-paths
instead of concatenating them into a single continuous path.

```typ
compound-path({
  rect((-1, -1), (1, 1))
  circle((0, 0), radius: .5)
}, fill: blue, fill-rule: "even-odd")
```

**Anchors**

- *centroid*: Centroid of the _closed and non self-intersecting_ shape. Only exists if `close` is true.
  Supports path anchors and shapes where all vertices share the same z-value.

- body (elements): Elements with paths to be merged together.
- name (none,str):
- ..style (style):

### `merge-path`

**Signature:** `merge-path(body, join: true, ignore-marks: true, ignore-hidden: true, close: false, name: none, ..style)`

Merges two or more paths by concatenating their elements. Anchors and visual styling, such as `stroke` and `fill`, are not preserved. When an element's path does not start at the same position the previous element's path ended, a straight line is drawn between them so that the final path is continuous. You must then pay attention to the direction in which element paths are drawn.

```typ
merge-path(fill: white, {
  line((0, 0), (1, 0))
  bezier((), (0, 0), (1,1), (0,1))
})
```

Elements hidden via [hide](../grouping/hide) are ignored.

**Anchors**

- centroid: Centroid of the _closed and non self-intersecting_ shape. Only exists if `close` is true.
  Supports path anchors and shapes where all vertices share the same z-value.

- body (elements): Elements with paths to be merged together.
- join (bool): Connect all sub-paths with a straight line
- close (bool): Close the path with a straight line from the start of the path to its end.
- ignore-marks (bool): If true, remove marks from input elements
- ignore-hidden (bool): If true, ignore all hidden elements
- name (none,str):
- ..style (style):

### `rect-around`

**Signature:** `rect-around(..pts-style, ignore-marks: false, ignore-hidden: false, ignore-floating: false, ignore-shapes: false)`

Draws an axis aligned bounding box around all given coordinates and/or elements.
Everything else (styling, anchors) is similar to `rect`.

Bounds of elements are calculated by computing the bounding box of their paths,
or as a fallback, using all anchors of the element.

```typ
circle((1, 1), radius: 0.1, fill: blue, name: "c1")
circle((0, 1), radius: 0.1, fill: red, name: "c2")
rect((0, 2), (1, 2.5), name: "r1")
rect-around("c1", "c2", "r1", stroke: yellow, padding: 0.1)
```
- ..pts-style (coordinates,style): Positional two or more coordinates/elements to calculate bounding box of. Accepts style key-value pairs.
- ignore-marks (bool): If true, ignore mark shapes when calculating a shape's bounding box
- ignore-hidden (bool):
- ignore-floating (bool):
- ignore-shapes (bool): Use only anchors for bounds calculation

**Styling**

The padding attribute can be used to control spacing.
Other attributes are forwarded to the rect shape.

**Anchors**

The same as for the rect shape.

### `svg-path`

**Signature:** `svg-path(name: none, anchor: none, ..commands-style)`

Create a new path from a SVG-like list of commands.

The following commands are supported (uppercase command names use absolute coordinates, lowercase use relative coordinates)
- `("l", coordinate)` line to `coordinate`
- `("h", number)` Horizontal line
- `("v", number)` Vertical line
- `("m", coordinate)` Move to `coordinate`
- `("c", ctrl-coordinate-a, ctrl-coordinate-b, coordinate)` Cubic bezier curve to `coordinate` with two control points a and b
- `("q", ctrl-coordinate, coordinate)` Quadratic bezier curve
- `("z",)` Close the current path
- `("anchor", "<anchor-name>", [coordinate=(0, 0)])` named anchor.
  If the anchor coordinate is unset, the default `(0, 0, 0)` is used.
  The anchor named "default" serves as origin for the `anchor:` argument.

```typ
svg-path(("h", 2),
         ("anchor", "here"),
         ("c", (0, 1), (0, 0), (-1, 0)),
         ("v", -0.5),
         ("h", -1),
         ("z",), name: "svg")
circle("svg.here", fill: white, radius: 0.1cm)
```

- name (none, string):
- anchor (none, coordinate):
- ..commands-style (any): Path commands and style keys

---

## Grouping

### `hide`

**Signature:** `hide(body, bounds: false)`

Hides an element.

Hidden elements are not drawn to the canvas, are ignored when calculating bounding boxes and discarded by [`merge-path`](../shapes/merge-path). All other behaviours remain the same as a non-hidden element.

```typ
set-style(radius: .5)
intersections("i", {
  circle((0,0), name: "a")
  circle((1,2), name: "b")
  // Use a hidden line to find the border intersections
  hide(line("a.center", "b.center"))
})
line("i.0", "i.1")
```

- body (element): One or more elements to hide
- bounds (bool): If true, respect the bounding box of the hidden elements for resizing the canvas

### `floating`

**Signature:** `floating(body)`

Places an element without affecting bounding boxes.

Floating elements are drawn to the canvas but are ignored when calculating bounding boxes. All other behaviours remain the same.

```typ
group(name: "g", {
  content((1,0), [Normal])
  content((0,1), [Normal])
  floating(content((.5,1.5), [Floating]))
})
set-style(stroke: red)
rect("g.north-west", "g.south-east")
```

- body (element): One or more elements to place

### `scope`

**Signature:** `scope(body) = (ctx => { let drawables = () let group-ctx = ctx group-ctx.groups.push(()) (ctx: group-ctx, drawables, bounds: _)`

This element acts as a scope, all state changes such as transformations and styling only affect the elements in the scope.
Elements after the scope are not affected by the changes inside the scope.
In contrast to `group`, the `scope` element does not create a named element itself and "leaks" body elements and anchors to the outside.

- body (elements, function): Elements to group together. At least one is required. A function that accepts `ctx` and returns elements is also accepted.

### `intersections`

**Signature:** `intersections(name, ..elements, samples: 10, sort: none, ignore-marks: true)`

Calculates the intersections between multiple paths and creates one anchor per intersection point.

All resulting anchors will be named numerically, starting at `0`. i.e., a call `intersections("a", ...)` will generate the anchors `"a.0"`, `"a.1"`, `"a.2"` to `"a.n"`, depending of the number of intersections.

```typ
intersections("i", {
  circle((0, 0))
  bezier((0,0), (3,0), (1,-1), (2,1))
  line((0,-1), (0,1))
  rect((1.5,-1),(2.5,1))
})
for-each-anchor("i", (name) => {
  circle("i." + name, radius: .1, fill: blue)
})
```

You can also use named elements:

```typ
circle((0,0), name: "a")
rect((0,0), (1,1), name: "b")
intersections("i", "a", "b")
for-each-anchor("i", (name) => {
  circle("i." + name, radius: .1, fill: blue)
})
```

You can calculate intersections with hidden elements by using [`hide`](./hide).

- name (str): Name to prepend to the generated anchors. (Not to be confused with other `name` arguments that allow the use of anchor coordinates.)
- ..elements (elements,str): Elements and/or element names to calculate intersections with. Elements referred to by name are (unlike elements passed) not drawn by the intersections function!
- samples (int): Number of samples to use for non-linear path segments. A higher sample count can give more precise results but worse performance.
- sort (none,function): A function of the form `(context, array<vector>) -> array<vector>`
  that gets called with the list of intersection points.
- ignore-marks (bool): If true, ignore mark shapes.

  CeTZ provides the following sorting functions:
    - sorting.points-by-distace(points, reference: (0, 0, 0))
    - sorting.points-by-angle(points, reference: (0, 0, 0))

### `group`

**Signature:** `group(body, name: none, anchor: none, ..style)`

Groups one or more elements together. This element acts as a scope, all state changes such as transformations and styling only affect the elements in the group. Elements after the group are not affected by the changes inside the group.

```typ
// Create group
group({
  stroke(5pt)
  scale(.5); rotate(45deg)
  rect((-1,-1),(1,1))
})
rect((-1,-1),(1,1))
```

- body (elements, function): Elements to group together. At least one is required. A function that accepts `ctx` and returns elements is also accepted.
- anchor (none, str): Anchor to position the group and it's children relative to. For translation the difference between the groups `"default"` anchor and the passed anchor is used.
- name (none, str):
- ..style (style):

**Styling**

*Root:* `group`

- padding (none, number, array, dictionary) = none: How much padding to add around the group's bounding box. `none` applies no padding. A number applies padding to all sides equally. A dictionary applies padding following Typst's `pad` function: https://typst.app/docs/reference/layout/pad/. An array follows CSS like padding: `(y, x)`, `(top, x, bottom)` or `(top, right, bottom, left)`.

**Anchors**

Supports border and path anchors of the axis aligned bounding box of all the child elements of the group.

You can add custom named anchors to the group by using the [anchor](./anchor) element while in the scope of said group, see [anchor](./anchor) for more details.

The default anchor is `"center"` but this can be overridden by using [anchor](./anchor) to place a new anchor called `"default"`.

When using named elements within a group, you can access the element's anchors outside of the group by using the implicit anchor coordinate. e.g. `"a.b.north"`
```typ
group(name: "a", {
  circle((), name: "b")
})
circle("a.b.south", radius: 0.2)
circle((name: "a", anchor: "b.north"), radius: 0.2)
```

### `anchor`

**Signature:** `anchor(name, position)`

Creates a new anchor for the current group. The new anchor will be accessible from inside the group by using just the anchor's name as a coordinate.

```typ
// Inside a group
group(name: "g", {
  circle((0,0))
  anchor("x", (.4, .1))
  circle("x", radius: .2)
})
circle("g.x", radius: .1)
```

```typ
// At the root scope
anchor("x", (1, 1))
// ...
circle("x", radius: .1)
```

- name (str): The name of the anchor
- position (coordinate): The position of the anchor

### `copy-anchors`

**Signature:** `copy-anchors(element, filter: auto)`

Copies multiple anchors from one element into the current group. Panics when used outside of a group. Copied anchors will be accessible in the same way anchors created by the `anchor` element are.

- element (str): The name of the element to copy anchors from.
- filter (auto,array): When set to `auto` all anchors will be copied to the group. An array of anchor names can instead be given so only the anchors that are in the element and the list will be copied over.

### `set-ctx`

**Signature:** `set-ctx(callback)`

An advanced element that allows you to modify the current canvas type:context.
Note: The transformation matrix (`transform`) is rounded after calling the `callback` function and therefore might be not exactly the matrix specified. This is due to rounding errors and should not cause any problems.

```typ
// Setting custom shared state
set-ctx(ctx => {
  ctx.shared-state.my-state = (
    key: 123
  )
  return ctx
})

// ...

// Access the context object
get-ctx(ctx => content((), [#repr(ctx.shared-state)]))
```

You can store shared context data under a key in the `ctx.shared-state`
dictionary. Note: the `ctx.shared-state` dictionary is not scoped by
`group` or `scope` elements and can be used for canvas global state.

- callback (function): A function that accepts the type:context dictionary and only returns a new one.

### `get-ctx`

**Signature:** `get-ctx(callback)`

An advanced element that allows you to read the current `context` through a callback and return `element`s based on it.

```typ
// Print the transformation matrix
get-ctx(ctx => {
  content((), [#repr(ctx.transform)])
})
```

- callback (function): A function that accepts the type:context and can return elements.

### `for-each-anchor`

**Signature:** `for-each-anchor(name, callback, exclude: ())`

Iterates through all named anchors of an element and calls a callback for each one.

```typ
// Label nodes anchors
rect((0, 0), (2,2), name: "my-rect")
for-each-anchor("my-rect", exclude: ("start", "mid", "end"), (name) => {
   content((), box(inset: 1pt, fill: white, text(8pt, [#name])), angle: -30deg)
})
```

- name (str): The name of the element with the anchors to loop through.
- callback (function): A function that takes the anchor name and can return elements.
- exclude (array): An array of anchor names to not include in the loop.

### `on-layer`

**Signature:** `on-layer(layer, body)`

Places elements on a specific layer.

A layer determines the position of an element in the draw queue. A lower layer is drawn before a higher layer.

Layers can be used to draw behind or in front of other elements, even if the other elements were created before or after. An example would be drawing a background behind a text, but using the text's calculated bounding box for positioning the background.

```typ
// Draw something behind text
set-style(stroke: none)
content((0, 0), [This is an example.], name: "text")
on-layer(-1, {
  circle("text.north-east", radius: .3, fill: red)
  circle("text.south", radius: .4, fill: green)
  circle("text.north-west", radius: .2, fill: blue)
})
```

- layer (float, int): The layer to place the elements on. Elements placed without `on-layer` are always placed on layer 0.
- body (elements, function): Elements to draw on the layer specified. A function that accepts `ctx` and returns elements is also accepted.

---

## Styling

### `set-style`

**Signature:** `set-style(..style)`

Set current style

- ..style (style): Style key-value pairs

### `fill`

**Signature:** `fill(fill)`

Set current fill style

Shorthand for `set-style(fill: <fill>)`

- fill (paint): Fill style

### `stroke`

**Signature:** `stroke(stroke)`

Set current stroke style

Shorthand for `set-style(stroke: <fill>)`

- stroke (stroke): Stroke style

### `register-mark`

**Signature:** `register-mark(symbol, body, mnemonic: none, tip: none, base: none, center: none, reverse-tip: none, reverse-base: none, reverse-center: none)`

Register a custom mark to the canvas

The mark should contain both anchors called *tip* and *base* that are used to determine the marks orientation. If unset both default to `(0, 0)`.
An anchor named *center* is used as center of the mark, if present. Otherwise the mid between *tip* and *base* is used.

```typ
register-mark(":)", style => {
  circle((0,0), radius: .5, fill: yellow)
  arc((0,0), start: 180deg + 30deg, delta: 180deg - 60deg, anchor: "origin", radius: .3)
  circle((-0.15, 0.15), radius: .1, fill: white)
  circle((-0.10, 0.10), radius: .025, fill: black)
  circle(( 0.15, 0.15), radius: .1, fill: white)
  circle(( 0.20, 0.10), radius: .025, fill: black)

  anchor("tip",  ( 0.5, 0))
  anchor("base", (-0.5, 0))
})

line((0,0), (3,0), mark: (end: ":)"))
```

- symbol (str): Mark name
- mnemonic (none, str): Mark short name
- body (function): Mark drawing callback, receiving the mark style as argument and returning elements. Format `(styles) => elements`.
- tip (none, number, coordinate): Tip coordinate (if passed a number, the y component is 0)
- base (none, number, coordinate): Base coordinate (see tip)
- center (none, number, coordinate): Center coordinate (see tip)
- reverse-tip (none, number, coordinate): Reversed tip coordinate (see tip)
- reverse-base (none, number, coordinate): Reversed base coordinate (see tip)
- reverse-center (none, number, coordinate): Reversed center coordinate (see tip)

---

## Transformations

### `set-transform`

**Signature:** `set-transform(mat)`

Overwrites the transformation matrix.

- mat (none, matrix): The 4x4 transformation matrix to set. If `none` is passed, the transformation matrix is set to the identity matrix (`matrix.ident(4)`).

### `transform`

**Signature:** `transform(mat)`

Applies a $4 times 4$ transformation matrix to the current transformation.

Given the current transformation $C$ and the new transformation $T$,
the function sets the new canvas' transformation $C'$ to $C' = C T$.

- mat (none, matrix): The 4x4 transformation matrix to set. If `none` is passed, the transformation matrix is set to the identity matrix (`matrix.ident(4)`).

### `rotate`

**Signature:** `rotate(..angles, origin: none)`

Rotates the transformation matrix on the z-axis by a given angle or other axes when specified.

```typ
// Rotate on z-axis
rotate(z: 45deg)
rect((-1,-1), (1,1))
// Rotate on y-axis
rotate(y: 80deg)
circle((0,0))
```

- ..angles (angle): A single angle as a positional argument to rotate on the z-axis by.
  Named arguments of `x`, `y` or `z` can be given to rotate on their respective axis.
  You can give named arguments of `yaw`, `pitch` or `roll`, too.
- origin (none,coordinate): Origin to rotate around, or (0, 0, 0) if set to `none`.

### `translate`

**Signature:** `translate(..args, pre: false)`

Translates the transformation matrix by the given vector or dictionary.

```typ
// Outer rect
rect((0, 0), (2, 2))
// Inner rect
translate(x: .5, y: .5)
rect((0, 0), (1, 1))
```

- ..args (vector, float, length): A single vector or any combination of the named arguments `x`, `y` and `z` to translate by.
  A translation matrix with the given offsets gets multiplied with the current transformation depending on the value of `pre`.
- pre (bool): Specify matrix multiplication order
  - false: `World = World * Translate`
  - true:  `World = Translate * World`

### `scale`

**Signature:** `scale(..args, origin: none)`

Scales the transformation matrix by the given factor(s).

```typ
// Scale the y-axis
scale(y: 50%)
circle((0,0))
```

Note that content like text does not scale automatically. See `auto-scale` styling of content for that.

- ..args (float, ratio): A single value to scale the transformation matrix by or per axis
  scaling factors. Accepts a single float or ratio value or any combination of the named arguments
  `x`, `y` and `z` to set per axis scaling factors. A ratio of 100% is the same as the value $1$.
- origin (none,coordinate): Origin to rotate around, or (0, 0, 0) if set to `none`.

### `set-origin`

**Signature:** `set-origin(origin)`

Sets the given position as the new origin `(0, 0, 0)`

```typ
// Draw some rect
rect((0,0), (2,2), name: "r")

// Move (0, 0) to the top edge of “r”
set-origin("r.north")
circle((0, 0), radius: .1, fill: white)
```

- origin (coordinate): Coordinate to set as new origin `(0,0,0)`

### `move-to`

**Signature:** `move-to(pt)`

Sets the previous coordinate. 

The previous coordinate can be used via `()` (empty coordinate).
It is also used as base for relative coordinates if not specified
otherwise.

```typ
circle((), radius: .25)
move-to((1,0))
circle((), radius: .15)
```

- pt (coordinate): The coordinate to move to.

### `set-viewport`

**Signature:** `set-viewport(from, to, bounds: (1, 1, 1))`

Span viewport between two coordinates and set-up scaling and translation

```typ
rect((0,0), (2,2))
set-viewport((0,0), (2,2), bounds: (10, 10))
circle((5,5))
```

- from (coordinate): Bottom left corner coordinate
- to (coordinate): Top right corner coordinate
- bounds (vector): Viewport bounds vector that describes the inner width,
  height and depth of the viewport

---

## Projections

### `ortho`

**Signature:** `ortho(x: 35.264deg, y: 45deg, z: 0deg, sorted: true, cull-face: none, reset-transform: false, flatten: false, body)`

Set-up an orthographic projection environment.

This is a transformation matrix that rotates elements around the x, the y and the z axis by the parameters given.

By default an isometric projection (x ≈ 35.264°, y = 45°) is set.

```typ
ortho({
  on-xz({
    rect((-1,-1), (1,1))
  })
})
```

- x (angle): X-axis rotation angle
- y (angle): Y-axis rotation angle
- z (angle): Z-axis rotation angle
- sorted (bool): Sort drawables by maximum distance (front to back)
- cull-face (none,str): Enable back-face culling if set to `"cw"` for clockwise
  or `"ccw"` for counter-clockwise. Polygons of the specified order will not get drawn.
- reset-transform (bool): Ignore the current transformation matrix
- flatten (bool): Set all z-components to 0.
- body (element): Elements to draw

### `on-xy`

**Signature:** `on-xy(z: 0, body)`

Draw elements on the xy-plane with optional z offset.

All vertices of all elements will be changed in the following way: $mat(x, y, z_"argument")$, where $z_"argument"$ is the z-value given as argument.

```typ
ortho({
  on-xy({
    rect((-1, -1), (1, 1))
  })
})
```

- z (number): Z offset for all coordinates
- body (element): Elements to draw

### `on-xz`

**Signature:** `on-xz(y: 0, body)`

Draw elements on the xz-plane with optional y offset.

All vertices of all elements will be changed in the following way: $mat(x, y_"argument", y)$, where $y_"argument"$ is the y-value given as argument.

```typ
ortho({
  on-xz({
    rect((-1, -1), (1, 1))
  })
})
```

- y (number): Y offset for all coordinates
- body (element): Elements to draw

### `on-zy`

**Signature:** `on-zy(x: 0, body)`

Draw elements on the zy-plane with optional x offset.

All vertices of all elements will be changed in the following way:
$mat(x_"argument", y, x)$, where $x_"argument"$ is the x-value given
as argument.

```typ
ortho({
  on-zy({
    rect((-1, -1), (1, 1))
  })
})
```

- x (number): X offset for all coordinates
- body (element): Elements to draw

### `perspective`

**Signature:** `perspective(x: 35.264deg, y: 45deg, z: 0deg, distance: auto, sorted: true, cull-face: none, reset-transform: false, body, ) = scope(ctx => { let view-rotation-matrix = ortho-matrix(x, y, z) let (distance, near)`

Set-up a perspective projection environment.

Coordinates are transformed by a view matrix and then projected with
perspective division:
$x' = (d_"ref" * x) / w$ and $y' = (d_"ref" * y) / w$,
where $w = max(-z, "near")$ in view space.

By default this uses the same isometric camera angles as `ortho`, but with
perspective foreshortening.

```typ
perspective({
  on-xz({
    rect((-1,-1), (1,1))
  })
})
```

- x (angle): X-axis rotation angle
- y (angle): Y-axis rotation angle
- z (angle): Z-axis rotation angle
- distance (number,auto): Distance from camera to scene origin. `auto`
  derives a stable value from scene depth.
- sorted (bool): Sort drawables by depth (back to front)
- cull-face (none,str): Enable back-face culling if set to `"cw"` for clockwise
  or `"ccw"` for counter-clockwise. Polygons of the specified order will not get drawn.
- reset-transform (bool): Ignore the current transformation matrix
- body (element): Elements to draw

---

## Boolean Path Operations

### `boolean`

**Signature:** `boolean(a, b, op: "difference", fill-rule-a: auto, fill-rule-b: auto, eps: auto, ignore-marks: true, ignore-hidden: true, name: none, ..style,)`

Performs a boolean operation on the paths produced by two CeTZ bodies.
The supported operations are `"union"`, `"intersection"`, `"difference"`,
and `"xor"`.

```typ
boolean(
  { rect((-1, -1), (1, 0)) },
  { circle((0, 0), radius: 0.8) },
  op: "difference",
  fill: blue,
)
```

Each operand can either be one or more type:elements or the name of an already-defined element (a string).

```typ
rect((-1, -1), (1, 0), name: "r")
circle((0, 0), radius: 0.8, name: "c")
boolean("r", "c", op: "difference", fill: blue)
```

All input subpaths must be closed and lie in a single z-plane. The output
is a single path drawable in the z-plane of the first input.

Each operand has its own fill-rule, which decides how its self-overlapping
or nested subpaths are interpreted as a filled region *before* the
boolean operation runs. By default (`auto`) the fill-rule is inferred
from the operand: if every path drawable produced by the body agrees on
one fill-rule (e.g. the body is a single `compound-path(..., fill-rule:
"even-odd")`), that value is used; otherwise it falls back to
`boolean`'s own resolved style.

- a (elements, str): First operand. Either an element body or the name
  of an existing element.
- b (elements, str): Second operand. Either an element body or the name
  of an elementxisting element.
- op (string): One of `"union"`, `"intersection"`, `"difference"`, `"xor"`.
- fill-rule-a (auto, string): `"non-zero"` or `"even-odd"`, applied to `a`. If `auto`, inferred from `a`'s drawables
- fill-rule-b (auto, string): `"non-zero"` or `"even-odd"`, applied to `b`. If `auto`, inferred from `b`'s drawables
- eps (auto, float): Numerical accuracy. `auto` uses an automatically determined value.
- ignore-marks (bool): Drop marks from the inputs (default: `true`).
- ignore-hidden (bool): Drop hidden elements from the inputs (default: `true`).
- name (none, string):
- ..style (style):

---

## Utility

### `assert-version`

**Signature:** `assert-version(min, max: none, hint: "")`

Assert that the cetz version of the canvas matches the given version (range).

- min (version): Minimum version (current >= min)
- max (none, version): First unsupported version (current < max)
- hint (string): Name of the function/module this assert is called from

### `register-coordinate-resolver`

**Signature:** `register-coordinate-resolver(resolver)`

Push a custom coordinate resolve function to the list of coordinate
resolvers. This resolver is scoped to the current context scope!

A coordinate resolver must be a function of the format `(context, coordinate) => coordinate`. And must _always_ return a valid coordinate or panic, in case of an error.

If multiple resolvers are registered, coordinates get passed through all
resolvers in reverse registering order. All coordinates get passed to cetz'
default coordinate resolvers.

```typ
register-coordinate-resolver((ctx, c) => {
  if type(c) == dictionary and "log" in c {
    c = c.log.map(n => calc.log(n, base: 10))
  }
  return c
})

circle((log: (10, 1e-6)), radius: .25)
circle((log: (100, 1e-6)), radius: .25)
circle((log: (1000, 1e-6)), radius: .25)
```

- resolver (function): The resolver function, taking a context and a single coordinate and returning a single coordinate

---

# Part 3: API Reference (Libraries)

Libraries provide specialised functions (angles, decorations, palettes, trees). Access them via the library module, e.g. `cetz.angle.angle(...)` or by importing the relevant module.

## Angle

### `angle`

**Signature:** `angle(origin, a, b, direction: "ccw", label: none, name: none, ..style ) = draw.group(name: name, ctx => { let style = styles.resolve(ctx.style, merge: style.named(), base: default-style, root: "angle") let radius = resolve-number(ctx, style.radius) let label-radius = resolve-number(ctx, style.label-radius) let (ctx, origin) = coordinate.resolve(ctx, origin) let (ctx, a, b) = coordinate.resolve(ctx, a, b, update: false) assert(float-eq(origin.at(2), a.at(2)) and float-eq(a.at(2), b.at(2)), message: "Angle z coordinates of all three points must be equal") assert(direction in ("cw", "ccw", "near", "far"), message: "Invalid angle direction " + repr(direction)) let (start, delta) = { let s = vector.angle2(origin, a) if s < 0deg { s += 360deg } let e = vector.angle2(origin, b) if e < 0deg { e += 360deg } if e < s { e += 360deg } let d = e - s if direction == "ccw" or (direction == "near" and d < 180deg) or (direction == "far" and d >= 180deg) { (s, (e - s)) } else { (s, -(360deg - (e - s))) } } let mid = start + delta / 2 // Radius can be relative to the min-distance between origin-a and origin-b if type(radius) == ratio { radius = radius * calc.min(vector.dist(origin, a), vector.dist(origin, b)) / 100% } // Label radius can be relative to radius if type(label-radius) == ratio { label-radius = label-radius * radius / 100% } let label-pt = vector.add(origin, (calc.cos(mid) * label-radius, calc.sin(mid) * label-radius, 0)) let start-pt = vector.add(origin, (calc.cos(start) * radius, calc.sin(start) * radius, 0)) let end-pt = vector.add(origin, (calc.cos(start + delta) * radius, calc.sin(start + delta) * radius, 0)) draw.anchor("origin", origin) draw.anchor("label", label-pt) draw.anchor("start", start-pt) draw.anchor("end", end-pt) draw.anchor("a", a) draw.anchor("b", b) draw.anchor("center", ("a", 50%, "b")) if delta != 0deg { if style.fill != none { draw.arc(origin, start: start, delta: delta, anchor: "origin", name: "arc", ..style, radius: radius, mode: "PIE", mark: none, stroke: none) } if style.stroke != none { draw.arc(origin, start: start, delta: delta, anchor: "origin", name: "arc", ..style, radius: radius, fill: none) } } let label = if type(label)`

Draw an angle counter-clock-wise between `a` and `b` through origin `origin`

```typ
line((0, 0), (60deg, 2), name: "a")
line((0, 0), (330deg, 2), name: "b")

// Draw an angle between the two lines
cetz.angle.angle("a.start", "a.end", "b.end", label: $alpha$,
  mark: (end: ">"), radius: 1.5)
cetz.angle.angle("a.start", "b.end", "a.end", label: $beta$,
  radius: 50%, direction: "ccw")
```

- origin (coordinate): Angle origin
- a (coordinate): Coordinate of side `a`, containing an angle between `origin` and `b`.
- b (coordinate): Coordinate of side `b`, containing an angle between `origin` and `a`.
- direction (string): Direction of the angle. Accepts "ccw" (counter-clockwise), "cw" (clockwise), "near" (inner angle), "far" (outer angle), the first one being the default.
- label (none,content,function): Draw a label at the angles "label" anchor. If label is a function, it gets the angle value passed as argument. The function must be of the format `angle => content`.
- name (none,str): Element name, used for querying anchors.
- ..style (style): Style key-value pairs.

**Styling**

*Root:* `angle` \

- radius (number) = 0.5: The radius of the angles arc. If of type `ratio`, it is relative to the smaller distance of either origin to a or origin to b.
- label-radius (number, ratio) = 50%: The radius of the angles label origin. If of type `ratio`, it is relative to `radius`.

**Anchors**

- a: Point a
- b: Point b
- origin: Origin
- label: Label center
- start: Arc start
- end: Arc end

### `right-angle`

**Signature:** `right-angle(origin, a, b, label: "•", name: none, ..style ) = draw.group(name: name, ctx => { let style = styles.resolve(ctx.style, merge: style.named(), base: default-style, root: "angle") let (ctx, origin) = coordinate.resolve(ctx, origin) let (ctx, a, b) = coordinate.resolve(ctx, a, b, update: false) let vo = origin; let va = a; let vb = b // Radius can be relative to the min-distance between origin-a and origin-b if type(style.radius) == ratio { style.radius = style.radius * calc.min(vector.dist(vo, va), vector.dist(vo, vb)) / 100% } let (r, _) = resolve-radius(style.radius).map(resolve-number.with(ctx)) let va = vector.add(vo, vector.scale(vector.norm(vector.sub(va, vo)), r)) let vb = vector.add(vo, vector.scale(vector.norm(vector.sub(vb, vo)), r)) let angle-b = vector.angle2(vo, vb) let vm = vector.add(va, (calc.cos(angle-b) * r, calc.sin(angle-b) * r, 0)) // Label radius can be relative to the distance between origin and the // angle corner if type(style.label-radius) == ratio { style.label-radius = style.label-radius * vector.dist(vm, vo) / 100% } let (ra, _)`

Draw a right angle between `a` and `b` through origin `origin`

```typ
line((0,0), (1,2), name: "a")
line((0,0), (2,-1), name: "b")

// Draw an angle between the two lines
cetz.angle.right-angle(
  "a.start",
  "a.end",
  "b.end",
  radius: 1.5
)
```

- origin (coordinate): Angle origin
- a (coordinate): Coordinate of side `a`, containing an angle between `origin` and `b`.
- b (coordinate): Coordinate of side `b`, containing an angle between `origin` and `a`.
- label (none,content): Draw a label at the angles "label" anchor.
- name (none,str): Element name, used for querying anchors.
- ..style (style): Style key-value pairs.

**Styling**

Styling is the same as the `angle` function.

**Anchors**

Anchors are the same as the `angle` function

---

## Decorations: Braces

### `brace`

**Signature:** `brace(start, end, ..style, name: none)`

Draw a curly brace between two points.

```typ
cetz.decorations.brace((0,1),(2,1))
cetz.decorations.brace((0,0),(2,0), outer-inset: 0)
```

- start (coordinate): Start point
- end (coordinate): End point
- name (string, none): Element name used for querying anchors
- ..style (style): Style key-value pairs

**Styling**

*Root:* `brace`
- amplitude (number) = 0.25cm: Sets the height of the brace, from its baseline to its middle tip.
- thickness (number,ratio) = 0.015cm: Thickness of tapered braces (if ratio, relative to half the amplitude).
- pointiness (ratio) = 50%: Thickness of the mid-spice
- taper (bool) = true: Draw a tapered brace
- outer-inset (number,ratio): Inset of the outer curve points
- outer-curvyness (ratio): Curvyness of the outer curves
- inner-outset (number,ratio): Inset of the inner tip curve points
- inner-curvyness (ratio): Curvyness of the inner tip curves
- outer-thickness (number) = 0: Thickness of the outer tips
- content-offset (number) = 0.3: Offset of the `"content"` anchor from the spike of the brace.
- flip (bool) = false: Mirror the brace along the line between start and end.

Use the `fill` style for tapered braces and set `stroke` to none.

**Anchors**

- start: Where the brace starts, same as the `start` parameter.
- end: Where the brace end, same as the `end` parameter.
- spike: Point of the spike, halfway between `start` and `end` and shifted by `amplitude` towards the pointing direction.
- content: Point to place content/text at, in front of the spike.
- center: Center of the enclosing rectangle.

### `flat-brace`

**Signature:** `flat-brace(start, end, flip: false, debug: false, name: none, ..style,)`

Draw a flat curly brace between two points.

```typ
cetz.decorations.flat-brace((0,1),(2,1))

cetz.decorations.flat-brace((0,0),(2,0),
  curves: .2,
  aspect: 25%)
cetz.decorations.flat-brace((0,-1),(2,-1),
  outer-curves: 0,
  aspect: 75%)
```

This mimics the braces from TikZ's [`decorations.pathreplacing` library](https://github.com/pgf-tikz/pgf/blob/6e5fd71581ab04351a89553a259b57988bc28140/tex/generic/pgf/libraries/decorations/pgflibrarydecorations.pathreplacing.code.tex#L136-L185).
In contrast to the `brace` function, these braces use straight line segments, resulting in better looks for long braces with a small amplitude.

- start (coordinate): Start point
- end (coordinate): End point
- flip (bool): Flip the brace around
- name (str, none): Element name for querying anchors
- debug (bool):
- ..style (style): Style key-value pairs

**Styling**

*Root:* `flat-brace`
- amplitude (number) = 0.3: Determines how much the brace rises above the base line.
- aspect (ratio) = 50% Determines the fraction of the total length where the spike will be placed.
- curves (number, auto, array) = auto: Curviness factor of the brace, a factor of 0 means no curves.
- outer-curves (number, auto, array) = auto: Curviness factor of the outer curves of the brace. A factor of 0 means no curves.

**Anchors**

- start: Where the brace starts, same as the `start` parameter.
- end: Where the brace end, same as the `end` parameter.
- spike: Point of the spike's top.
- content: Point to place content/text at, in front of the spike.
- center:  Center of the enclosing rectangle.

---

## Decorations: Path (coil, wave, zigzag)

Number of segments

Length of a single segments

Amplitude of a segment in the direction of the segments normal.
The following types are supported:
  - float
  - function ratio -> float (the segment ratio is given as argument)
  - array of floats (the rounded down segment number is used as index modulo the array length)

Decoration start

Decoration stop

Decoration alignment on the target path

Draw remaining space as line ("LINE") or none

Up-vector for 3D lines

Up-vector for 2D lines

Midpoint factor
  0%: Sawtooth (up-down)
 50%: Triangle
100%: Sawtooth (down-up)

Wave (catmull-rom) tension

Coil "overshoot" factor

Midpoint factor

### `zigzag`

**Signature:** `zigzag(target, name: none, close: auto, ..style) = draw.get-ctx(ctx => { let style = styles.resolve(ctx.style, merge: style.named(), base: zigzag-default-style, root: "zigzag") let (segments, close) = get-segments(ctx, target) let style = resolve-style(ctx, segments, style) let num-segments = style.segments // Return points for a zigzag line // // m1 ▲ // / \ │ Up // ..a....\....b.. ' // \ / // m2 // |--| // q-dir (quarter length between a and b) // // For the first/last segment, a/b get added. For all // other segments we only have to add m1 and m2 to the // list of points for the line-strip. let fn(i, a, b, norm)`

Draw a zig-zag or saw-tooth wave along a path.

The number of tooths can be controlled via the `segments` or `segment-length` style key, and the width via `amplitude`.

```typ
line((0,0), (2,1), stroke: gray)
cetz.decorations.zigzag(line((0,0), (2,1)), amplitude: .25, start: 10%, stop: 90%)
```

- target (drawable): Target path
- close (auto,bool): Close the path
- name (none,string): Element name
- ..style (style): Style

**Styling**

*Root*: `zigzag`
- factor (ratio) = 100%: Triangle mid between its start and end. Setting this to 0% leads to a falling sawtooth shape, while 100% results in a raising sawtooth.

### `coil`

**Signature:** `coil(target, close: auto, name: none, ..style) = draw.get-ctx(ctx => { let style = styles.resolve(ctx.style, merge: style.named(), base: coil-default-style, root: "coil") let (segments, close) = get-segments(ctx, target) let style = resolve-style(ctx, segments, style) let num-segments = calc.max(style.segments, 1) let length = path-util.length(segments) let phase-length = length / num-segments let overshoot = calc.max(0, (style.factor - 100%) / 100% * phase-length) // Offset both control points so the curve approximates // an elliptic arc let ellipsize-cubic(s, e, c1, c2) = { let m = vector.scale(vector.add(c1, c2), .5) let d = vector.sub(e, s) c1 = vector.sub(m, vector.scale(d, .5)) c2 = vector.add(m, vector.scale(d, .5)) return (s, e, c1, c2) } // Return a list of drawables to form a coil-like loop // // ____ ┐ // / \ │ Upper curve // | | ┘ // ..a...b..|.. ┐ Lower curve // \_/ ┘ // // └──┘ // Overshoot // let fn(i, a, b, norm) = { let ab = vector.sub(b, a) let amplitude = resolve-amplitude(ctx, style.amplitude, i, num-segments) let up = vector.scale(norm, amplitude / 2) let dist = vector.dist(a, b) let d = vector.norm(ab) let overshoot-at(i)`

Draw a stretched coil/loop spring along a path

The number of windings can be controlled via the `segments` or `segment-length` style key, and the width via `amplitude`.

```typ
line((0,0), (2,1), stroke: gray)
cetz.decorations.coil(line((0,0), (2,1)), amplitude: .25, start: 10%, stop: 90%)
```
- target (drawable): Target path
- close (auto,bool): Close the path
- name (none,string): Element name
- ..style (style): Style

**Styling**

*Root*: `coil`
- factor (ratio) = 150%: Factor of how much the coil overextends its length to form a curl.

### `wave`

**Signature:** `wave(target, close: auto, name: none, ..style) = draw.get-ctx(ctx => { let style = styles.resolve(ctx.style, merge: style.named(), base: wave-default-style, root: "wave") let (segments, close) = get-segments(ctx, target) let style = resolve-style(ctx, segments, style) let num-segments = style.segments // Return a list of points for the catmull-rom curve // // ╭ ma ╮ ▲ // │ │ │ Up // ..a....m....b.. ' // │ │ // ╰ mb ╯ // let fn(i, a, b, norm)`

Draw a wave along a path using a catmull-rom curve

The number of phases can be controlled via the `segments` or `segment-length` style key, and the width via `amplitude`.

```typ
line((0,0), (2,1), stroke: gray)
cetz.decorations.wave(line((0,0), (2,1)), amplitude: .25, start: 10%, stop: 90%)
```

- target (drawable): Target path
- close (auto,bool): Close the path
- name (none,string): Element name
- ..style (style): Style

**Styling**

*Root*: `wave`

- tension (float) = 0.5 Catmull-Rom curve tension, see [Catmull](/api/draw-functions/shapes/catmull)

### `square`

**Signature:** `square(target, close: auto, name: none, ..style) = draw.get-ctx(ctx => { let style = styles.resolve(ctx.style, merge: style.named(), base: square-default-style, root: "square") let (segments, close) = get-segments(ctx, target) let style = resolve-style(ctx, segments, style) let num-segments = style.segments let factor = calc.max(0, calc.min(style.factor / 100%, 1)) // Return a list of points for the line-strip // // +----+ ▲ // | | │ Up // ..a....m....b.. ' // | | // +----+ // let fn(i, a, b, norm)`

Draw a square-wave along a path using a line-strip

The number of phases can be controlled via the `segments` or `segment-length` style key, and the width via `amplitude`.

```typ
line((0,0), (2,1), stroke: gray)
cetz.decorations.square(line((0,0), (2,1)), amplitude: .25, start: 10%, stop: 90%)
```

- target (drawable): Target path
- close (auto,bool): Close the path
- name (none,string): Element name
- ..style (style): Style

**Styling**

*Root*: `squre`

- factor (ratio) = 50% Square-Wave midpoint

---

## Palette

### `new`

**Signature:** `new(base: base-style, colors: (), dash: ())`

Create a new palette based on a base style

```typ
let p = cetz.palette.new(colors: (red, blue, green))
for i in range(0, p("len")) {
  set-style(..p(i))
  circle((0,0), radius: .5)
  set-origin((1.1, 0))
}
```

The functions returned by this function have the following named arguments:
- fill (bool) = true: If true, the returned fill color is one of the colors from the `colors` list, otherwise the base styles fill is used.
- stroke (bool) = false: If true, the returned stroke color is one of the colors from the `colors` list, otherwise the base styles stroke color is used.

You can use a palette for stroking via: `red.with(stroke: true)`.

- base (style): Style dictionary to use as base style for the styles generated per color
- colors (none, array): List of colors the returned palette should return styles with.
- dash (none, array): List of stroke dash patterns the returned palette should return styles with.
-> function

---

## Tree

### `default-draw-edge`

**Signature:** `default-draw-edge(parent, child)`

Default edge draw callback

- parent (node): Parent tree node. The field `group-name` (str) provides the elements name.
- child (node): Child tree node. The field `group-name` (str) provides the elements name.

### `default-draw-node`

**Signature:** `default-draw-node(node)`

Default node draw callback

- node (node): The node to draw

### `tree`

**Signature:** `tree(root, draw-node: auto, draw-edge: auto, direction: "down", grow: 1, spread: 1, name: none, node-layer: 1, edge-layer: 0, measure-content: true, anchor: none, group-name-prefix: "g",)`

Lays out and renders tree nodes.

For each node, the `tree` function creates an anchor of the format `"[<child-index>-]<child-index>"` (the root is `"0"`, its first child `"0-0"`, second `"0-1"` and so on) that can be used to query a nodes position on the canvas.

```typ
import cetz.tree
set-style(content: (padding: .1))
tree.tree(([Root], ([A], [A.A], [A.B]), ([B], [B.A])))
```

The `node` object passed to callbacks contains the following keys:
  - `name` (str): Name of the node's anchor
  - `group-name` (str): Name of the node's group element
  - `depth` (int): Depth of the node
  - `n` (int): Sibling index of the node
  - `content` (any): Content of the node

- root (array): A nested array of content that describes the structure the tree should take. Example: `([root], [child 1], ([child 2], [grandchild 1]))`
- draw-node (auto,function): The function to call to draw a node. The function will be passed the node to draw (a dictionary with a `content` key) and is expected to return elements (`(node) => elements`). The node must be drawn at the `(0,0)` coordinate. If `auto` is given, just the node's value will be drawn as content.
- draw-edge (none,auto,function): The function to call draw an edge between two nodes. The function will be passed the name of the starting node, the name of the ending node, the start node, the end node, and is expected to return elements (`(parent-node, child-node) => elements`). If `auto` is given, a straight line will be drawn between nodes.
- direction (str): A string describing the direction the tree should grow in ("up", "down", "left", "right")
- grow (float): Depth grow factor
- spread (float): Sibling spread factor
- name (none,str): The tree element's name
- node-layer (int): Layer to draw nodes on
- edge-layer (int): Layer to draw edges on
- anchor (none, string): Name of the anchor to align the tree to. Use the root node anchor (`"0"`) to align the tree to the root nodes position.
- group-name-prefix (string): Prefix of node group names

---

# Notes on Internal API

CeTZ also ships an "internal" API (vector, matrix, bezier, hobby, coordinate,
drawable, intersection, path-util, aabb, etc.) used to implement the package and
write custom draw functions. It is rarely needed for translating ordinary
TikZ diagrams and is omitted here for brevity. If a custom element or low-level
computation is required, consult the upstream documentation at
https://cetz-package.github.io/docs/api/internal/.
