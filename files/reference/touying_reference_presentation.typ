#import "@preview/touying:0.7.3": *
#import themes.university: *

#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion

#show: university-theme.with(
  align: horizon,
  aspect-ratio: "16-9",
  config-common(frozen-counters: (theorem-counter,), slide-level: 2),
  config-info(
    title: [Main Title of the Presentation],
    subtitle: [Subtitle of the Presentation],
    author: [Author's Name],
    date: datetime(year: 2026, month: 5, day: 10),  // put "datetime.today()" for today's date
    institution: [Institute's Name],
  ),
)

// Comment out the following for heading numbering (like Beamer section numbers)
// #import "@preview/numbly:0.1.0": numbly
// #set heading(numbering: numbly("{1}.", default: "1.1"))

// Fonts (using New Computer Modern to avoid the Fira font warning)
#set text(
  // font: "New Computer Modern",  // comment out for default font
  weight: "light",
  size: 20pt,
  lang: "en",
  region: "US"
)

#title-slide()

= Outline <touying:hidden>

== Outline <touying:hidden>

#components.adaptive-columns(outline(title: none, indent: 1em))

= Example Section 1

== Example Subsection 1

This is an example paragraph. This is #emph[emphasis]. This is #strong[strong]. This is an example paragraph. This is an example paragraph. This is an example paragraph. This is an example paragraph.
#list(
  [Example bullet item 1.],
  [Example bullet item 2.],
)
This is an example paragraph. This is an example paragraph. This is an example paragraph. This is an example paragraph. This is an example paragraph. This is an example paragraph.
#enum(
  [Example enumerated item 1.],
  [Example enumerated item 2.],
)
Citing articles: @hawking1975particle, @einstein1935can.

== Frame with Paragraphs

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui

== Hyperlinks, URLs, and Inline Code

Visit the #link("https://www.example.com")[example website] for more information.\
Raw URL: #link("https://www.example.com/some/long/path").\
Inline code: `print("hello world")`.\
Inline code: `x = [i**2 for i in range(10)]`.\
Strikethrough text: #strike[this idea was discarded].

== Footnotes

Footnotes are nice. See this#footnote[This is a footnote.]. This is another sentence with another footnote#footnote[Footnotes are useful for citations or asides.]. This#footnote[@einstein1935can] is footnote citation.

== Quotation and Pull Quote

#quote(attribution: [Steve Jobs], block: true)[
  The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle.
]

= Special Environments

== Special Environments I

#remark-block[
  This is an example of a remark.
]

#caution-block[
  This is an example of a caution.
]

#example(title: "Example Name")[
  This is an example of an example.
]

#theorem(title: "Theorem Name")[
  This is an example of a theorem. Following is an equation.
  $ a^2 + b^2 = c^2. $
]

== Special Environments II

#lemma(title: "Lemma Name")[
  This is an example of a lemma.
]

#corollary(title: "Corollary Name")[
  This is an example of a corollary.
]

#definition(title: "Definition Name")[
  This is an example of a definition.
]

#proof(title: "Proof Name")[
  This is an example of a proof.
]

= Math

== Equation and Alignment

Inline math equation: $a^2 + b^2 = c^2$.
#[
  #set math.equation(numbering: "(1)")
  $ a^2 + b^2 = c^2. $ <eq:pythagorean_theorem>
]
Cross reference to @eq:pythagorean_theorem.
$ a^2 + b^2 &= c^2 \
  a^2 &= c^2 - b^2 \
  a &= sqrt(c^2 - b^2) $

== More Ways of Typing Equations

For multiple unaligned equations:
$ x^2 + y^2 = r^2 \
  e^(i pi) + 1 = 0 \
  zeta(s) = sum_(n=1)^infinity 1/n^s $

For a single long equation that needs to break:
$ f(x_1, x_2, dots, x_12) = a_1 x_1 + a_2 x_2 + a_3 x_3 + a_4 x_4 + a_5 x_5 + a_6 x_6 + a_7 x_7 + a_8 x_8 \
+ a_9 x_9 + a_10 x_10 + a_11 x_11 + a_12 x_12 + b $

Piecewise functions:
#[
  #set math.equation(numbering: "(1)")
  $ abs(x) = cases(
      x & "if " x >= 0,
      -x & "if " x < 0,
    ) $ <eq:cases>
]
Cross reference to @eq:cases.

== Sets, Limits, Sums, and Products

#import "@preview/physica:0.9.8": *

// Custom math operators (equivalent to \DeclareMathOperator in LaTeX)
#let argmin = math.op($arg thin min$, limits: true)
#let argmax = math.op($arg thin max$, limits: true)

Set-builder notation:
$ A = { x in RR mid(|) x^2 < 4 }, quad abs(A) = "cardinality of " A $

Norms and absolute values:
$ norm(vb(x))_2 = sqrt(sum_(i=1)^n x_i^2), quad abs(x - y) <= abs(x) + abs(y) $

Limits, sums, and products:
$ lim_(n -> infinity) (1 + 1/n)^n = e, quad
  sum_(k=0)^infinity 1/k! = e, quad
  product_(k=1)^n k = n! $

Custom operators:
$ hat(theta) = argmin_(theta in Theta) cal(L)(theta), quad
  hat(y) = argmax_(y in cal(Y)) P(y mid(|) x) $

== Vectors and Matrices

#import "@preview/physica:0.9.8": *

$ vb(alpha) = mat(delim: "[", alpha_1; alpha_2; alpha_3), quad
  vb(alpha)^top = mat(delim: "[", alpha_1, alpha_2, alpha_3) $

$ vb(A) = mat(delim: "[", a_11, a_12; a_21, a_22), quad
  vb(A)^top = mat(delim: "[", a_11, a_21; a_12, a_22) $

$ vb(Sigma) = mat(delim: "[",
    sigma_11, sigma_12, dots, sigma_(1 d);
    sigma_21, sigma_22, dots, sigma_(2 d);
    dots.v, dots.v, dots.down, dots.v;
    sigma_(n 1), sigma_(n 2), dots, sigma_(n d)
  ), quad
  vb(Sigma)^top = mat(delim: "[",
    sigma_11, sigma_21, dots, sigma_(n 1);
    sigma_12, sigma_22, dots, sigma_(n 2);
    dots.v, dots.v, dots.down, dots.v;
    sigma_(1 d), sigma_(2 d), dots, sigma_(n d)
  ) $

== Derivatives and Integrals

#import "@preview/physica:0.9.8": *

$ f(x) = x^2 + 2x ==> dv(f(x), x) = 2x + 2 ==> dv(f(x), x, 2) = 2 ==> dv(f(x), x, 3) = 0 $

$ dv(, x) sin(x) = cos(x) $

$ op("sigmoid")(x) = 1/(1 + e^(-x)) ==> dv(, x) op("sigmoid")(x) = (1/(1 + e^(-x))) (e^(-x)/(1 + e^(-x))) $

$ integral sin(x) dd(x) = -cos(x) + C $

$ f(vb(x)) = vb(x)^top vb(A) vb(x) + vb(b)^top vb(x) ==> nabla_vb(x) f(vb(x)) = vb(A)^top vb(x) + vb(A) vb(x) + vb(b)
  ==> nabla_vb(x)^2 f(vb(x)) = vb(A)^top + vb(A) $

$ f(x, y) = x^2 + y^2 + 3 ==> pdv(f(x\, y), x) = 2x ==> pdv(f(x\, y), x, 2) = 2 ==> pdv(f(x\, y), x, 3) = 0 $

$ f(x, y) = x^2 + x y + 3 ==> pdv(f(x\, y), x) = 2x + y ==> pdv(f(x\, y), x, y) = 1 $

== Probability and Statistics

#import "@preview/physica:0.9.8": *

$X$ is a discrete random variable. If discrete, PMF is denoted by $p_X (x)$. If continuous, PDF is denoted by $f_X (x)$. CDF is always denoted by $F_X (x)$.

PMF of Binomial Distribution:
$ p_X (x; n, p) = binom(n, x) p^x (1-p)^(n-x), quad x in {0, 1, dots, n} $

$ EE[X] = n p, quad "Var"[X] = n p (1-p) $

PDF of Normal random variable $X$, i.e., $X tilde cal(N)(mu, sigma^2)$:
$ phi(x\; mu, sigma^2) = 1/(sigma sqrt(2 pi)) exp(-((x-mu)^2)/(2 sigma^2)), quad x in RR $

$ EE[X] = mu, quad "Var"[X] = sigma^2 $

CDF of a Normal random variable $X$, i.e., $X tilde cal(N)(mu, sigma^2)$:
$ Phi(x) = 1/(sigma sqrt(2 pi)) integral_(-infinity)^x exp(-((t-mu)^2)/(2 sigma^2)) dd(t), quad x in RR $

== Chemical Equations

#import "@preview/whalogen:0.3.0": ce

This is the formula for water: #ce("H2O")

This is a chemical reaction: #ce("HCl + H2O -> H3O+ + Cl-")

Whalogen aligns properly in math mode:
$
#ce("CO2 + C &-> 2CO")\
#ce("CH4 + 2O2 &-> CO2 + 2H2O")
$

Charges apply correctly: #ce("H+ + [AgCl2]-")

Nuclides and isotopes: #ce("@Th,227,90@^+")

Different reaction arrows: #ce("A <=> B ->[H2O] C")

Oxidation number support: #ce("|Mn,+II|")

= Figures

== Example Figure

#figure(
  image("graphics/example_image.png", width: 50%),
  caption: [Example Figure],
) <fig:example_figure_a>

Cross reference to @fig:example_figure_a.

== Subfigures

#import "@preview/subpar:0.2.2"

#subpar.grid(
  figure(image("graphics/example_image.png", width: 100%), caption: [Subcaption A]), <fig:sub_a>,
  figure(image("graphics/example_image.png", width: 100%), caption: [Subcaption B]), <fig:sub_b>,
  figure(image("graphics/example_image.png", width: 100%), caption: [Subcaption C]), <fig:sub_c>,
  columns: (1fr, 1fr, 1fr),
  caption: [A figure with three subfigures.],
  label: <fig:subfigures_example>,
)

Cross reference to @fig:sub_a, @fig:sub_b, @fig:sub_c.

== Flowchart Diagram

#import "@preview/fletcher:0.5.8" as fletcher: node, edge
#let fletcher-diagram = touying-reducer.with(reduce: fletcher.diagram, cover: fletcher.hide)

#figure(
  fletcher-diagram(
    node-stroke: 0.5pt,
    node-corner-radius: 4pt,
    spacing: (3em, 3em),
    node((0, 0), [Input], name: <input>),
    node((1, 0), [Process], name: <process>),
    node((2, 0), [Output], name: <output>),
    node((1, 1), [Feedback], name: <feedback>),
    edge(<input>, <process>, "-|>"),
    edge(<process>, <output>, "-|>"),
    edge(<output>, <feedback>, "-|>", corner: right),
    edge(<feedback>, <input>, "-|>", corner: right),
  ),
  caption: [A simple flowchart.],
) <fig:flowchart>

== Flowchart Diagrams

#import "@preview/subpar:0.2.2"

#import "@preview/fletcher:0.5.8" as fletcher: node, edge
#let fletcher-diagram = touying-reducer.with(reduce: fletcher.diagram, cover: fletcher.hide)

#subpar.grid(
  figure(
    fletcher.diagram(
      node-stroke: 0.5pt,
      node-corner-radius: 4pt,
      spacing: (3em, 3em),
      node((0, 0), [Input], name: <input>),
      node((1, 0), [Process], name: <process>),
      node((2, 0), [Output], name: <output>),
      node((1, 1), [Feedback], name: <feedback>),
      edge(<input>, <process>, "-|>"),
      edge(<process>, <output>, "-|>"),
      edge(<output>, <feedback>, "-|>", corner: right),
      edge(<feedback>, <input>, "-|>", corner: right),
    ),
    caption: [A feedback loop.],
  ), <fig:flowchart-a>,
  figure(
    fletcher.diagram(
      node-stroke: 0.5pt,
      node-corner-radius: 4pt,
      spacing: (3em, 3em),
      node((0, 0), [Start], name: <start>),
      node((1, 0), [Check], name: <check>),
      node((2, 0), [Done], name: <done>),
      node((1, 1), [Retry], name: <retry>),
      edge(<start>, <check>, "-|>"),
      edge(<check>, <done>, "-|>", label: [ok]),
      edge(<check>, <retry>, "-|>", label: [fail], bend: 25deg),
      edge(<retry>, <check>, "-|>", bend: 25deg),
    ),
    caption: [A retry path.],
  ), <fig:flowchart-b>,
  columns: (1fr, 1fr),
  caption: [Two simple flowcharts.],
  label: <fig:flowcharts>,
)

== Fletcher Diagram

#import "@preview/fletcher:0.5.8" as fletcher: node, edge
#let fletcher-diagram = touying-reducer.with(reduce: fletcher.diagram, cover: fletcher.hide)

#figure(
  fletcher-diagram($
    G edge(f, ->) edge("d", pi, ->>) & im(f) \
    G slash ker(f) edge("ur", tilde(f), "hook-->")
  $),
  caption: [A Fletcher diagram.],
) <fig:fletcher-diagram>

== Fletcher Diagrams

#import "@preview/subpar:0.2.2"

#import "@preview/fletcher:0.5.8" as fletcher: node, edge
#let fletcher-diagram = touying-reducer.with(reduce: fletcher.diagram, cover: fletcher.hide)

#subpar.grid(
  figure(
    fletcher.diagram($
      G edge(f, ->) edge("d", pi, ->>) & im(f) \
      G slash ker(f) edge("ur", tilde(f), "hook-->")
    $),
    caption: [The first isomorphism theorem.],
  ), <fig:fletcher-a>,
  figure(
    fletcher.diagram($
      A edge(f, ->) edge("d", g, ->) & B edge("d", h, ->) \
      C edge(k, ->) & D
    $),
    caption: [A commutative square.],
  ), <fig:fletcher-b>,
  columns: (1fr, 1fr),
  caption: [Two Fletcher diagrams.],
  label: <fig:fletcher-diagrams>,
)

== Plot

#import "@preview/lilaq:0.6.0" as lq

#figure(
  lq.diagram(
    width: 10cm,
    height: 7cm,
    xlabel: $x$,
    ylabel: $f(x)$,
    xlim: (-3, 3),
    legend: (position: top + left),
    xaxis: (tick-distance: 1),
    yaxis: (tick-distance: 10),
    lq.plot(
      lq.linspace(-3, 3, num: 100),
      x => calc.pow(x, 2),
      mark: none,
      stroke: blue + 1.5pt,
      label: $x^2$,
    ),
    lq.plot(
      lq.linspace(-3, 3, num: 100),
      x => calc.pow(x, 3),
      mark: none,
      stroke: (paint: red, thickness: 1.5pt, dash: "dashed"),
      label: $x^3$,
    ),
  ),
  caption: [An example plot.],
) <fig:plot_example>

== Plots

#import "@preview/subpar:0.2.2"

#import "@preview/lilaq:0.6.0" as lq

#subpar.grid(
  figure(
    lq.diagram(
      width: 7cm,
      height: 5cm,
      xlabel: $x$,
      ylabel: $f(x)$,
      xlim: (-3, 3),
      legend: (position: top + left),
      xaxis: (tick-distance: 1),
      yaxis: (tick-distance: 10),
      lq.plot(
        lq.linspace(-3, 3, num: 100),
        x => calc.pow(x, 2),
        mark: none,
        stroke: blue + 1.5pt,
        label: $x^2$,
      ),
      lq.plot(
        lq.linspace(-3, 3, num: 100),
        x => calc.pow(x, 3),
        mark: none,
        stroke: (paint: red, thickness: 1.5pt, dash: "dashed"),
        label: $x^3$,
      ),
    ),
    caption: [Powers of $x$.],
  ), <fig:plot-a>,
  figure(
    lq.diagram(
      width: 7cm,
      height: 5cm,
      xlabel: $x$,
      ylabel: $f(x)$,
      xlim: (-calc.pi, calc.pi),
      legend: (position: top + left),
      yaxis: (tick-distance: 0.5),
      lq.plot(
        lq.linspace(-calc.pi, calc.pi, num: 100),
        x => calc.sin(x),
        mark: none,
        stroke: green + 1.5pt,
        label: $sin x$,
      ),
      lq.plot(
        lq.linspace(-calc.pi, calc.pi, num: 100),
        x => calc.cos(x),
        mark: none,
        stroke: (paint: purple, thickness: 1.5pt, dash: "dashed"),
        label: $cos x$,
      ),
    ),
    caption: [Sine and cosine.],
  ), <fig:plot-b>,
  columns: (1fr, 1fr),
  caption: [Two example plots.],
  label: <fig:plots>,
)

= Tables

== Example Table

#figure(
  table(
    columns: 3,
    align: center,
    stroke: none,
    table.hline(stroke: 1pt),
    table.header(
      [Column 1], [Column 2], [Column 3],
    ),
    table.hline(stroke: 0.5pt),
    [Row 1, Col 1], [Row 1, Col 2], [Row 1, Col 3],
    [Row 2, Col 1], [Row 2, Col 2], [Row 2, Col 3],
    [Row 3, Col 1], [Row 3, Col 2], [Row 3, Col 3],
    table.hline(stroke: 1pt),
  ),
  caption: [Example table summarizing its key takeaway in one line.],
) <tab:example_table>

Cross reference to @tab:example_table.

== Multi-row and Multi-column Cells

#figure(
  table(
    columns: 4,
    align: center,
    stroke: none,
    table.hline(stroke: 1pt),
    table.header(
      table.cell(rowspan: 2)[Group],
      table.cell(colspan: 2)[Measurements],
      table.cell(rowspan: 2)[Total],
      table.hline(start: 1, end: 3, stroke: 0.5pt),
      [Trial 1], [Trial 2],
    ),
    table.hline(stroke: 0.5pt),
    [A], [12], [14], [26],
    [B], [9], [11], [20],
    [C], [15], [13], [28],
    table.hline(stroke: 1pt),
  ),
  caption: [Trial measurements and totals for groups A, B, and C.],
) <tab:multirow_example>

== Table with Units

#import "@preview/unify:0.8.1": qty, unit

#figure(
  table(
    columns: 3,
    align: (left, right, right),
    stroke: none,
    table.hline(stroke: 1pt),
    table.header(
      [Material],
      [Density (#unit("g/cm^3"))],
      [Resistivity (#unit("O m"))],
    ),
    table.hline(stroke: 0.5pt),
    [Copper],   [8.96],  [1.68],
    [Aluminum], [2.70],  [2.65],
    [Iron],     [7.87],  [9.71],
    [Silver],   [10.49], [1.59],
    table.hline(stroke: 1pt),
  ),
  caption: [Density and electrical resistivity of four metals.],
) <tab:units_example>

== Table with Colored Rows

#figure(
  table(
    columns: 3,
    align: center,
    stroke: none,
    fill: (col, row) => if row == 0 {
      blue.lighten(80%)
    } else if row == 2 or row == 4 {
      gray.lighten(85%)
    },
    table.hline(stroke: 1pt),
    table.header(
      [Header 1], [Header 2], [Header 3],
    ),
    table.hline(stroke: 0.5pt),
    [Row 1, Col 1], [Row 1, Col 2], [Row 1, Col 3],
    [Row 2, Col 1], [Row 2, Col 2], [Row 2, Col 3],
    [Row 3, Col 1], [Row 3, Col 2], [Row 3, Col 3],
    [Row 4, Col 1], [Row 4, Col 2], [Row 4, Col 3],
    table.hline(stroke: 1pt),
  ),
  caption: [Table with colored rows.],
) <tab:colored_table>

= Algorithms

== Binary Search

#import "@preview/lovelace:0.3.1": *

#text(size: 13pt)[
#figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [Binary Search],
  pseudocode-list(booktabs: true, numbered-title: [Binary Search])[
    + *Input:* Sorted array $a$, target value $x$
    + *Output:* Index of $x$ in $a$, or $-1$ if not found
    + $italic("lo") <- 0$
    + $italic("hi") <- |a| - 1$
    + *while* $italic("lo") <= italic("hi")$ *do*
      + $italic("mid") <- floor((italic("lo") + italic("hi")) slash 2)$
      + *if* $a[italic("mid")] = x$ *then*
        + *return* $italic("mid")$
      + *else if* $a[italic("mid")] < x$ *then*
        + $italic("lo") <- italic("mid") + 1$
      + *else*
        + $italic("hi") <- italic("mid") - 1$
      + *end*
    + *end*
    + *return* $-1$
  ]
) <alg:binary-search>
]

= Code Snippets

== Python Code

```python
def binary_search(a, x):
    lo = 0
    hi = len(a) - 1

    while lo <= hi:
        mid = (lo + hi) // 2

        if a[mid] == x:
            return mid
        elif a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1

    return -1
```

= Columns

== Two Columns

#slide(composer: (1fr, 1fr))[
  This is dummy text. This is dummy text. This is dummy text. This is dummy text. This is dummy text.
  #list(
    [Bullet 1],
    [Bullet 2],
    [Bullet 3],
  )
][
  This is dummy text. This is dummy text. This is dummy text. This is dummy text. This is dummy text.
  #enum(
    [Enumerated 1],
    [Enumerated 2],
    [Enumerated 3],
  )
]

== Two Columns (Blocks)

#let titled-block(title, body) = block(
  stroke: 0.5pt + gray,
  radius: 4pt,
  inset: 8pt,
  width: 100%,
)[
  #text(weight: "bold")[#title]
  #body
]

#slide(composer: (1fr, 1fr))[
  #titled-block("Left Column Name")[
    #list(
    [Bullet 1],
    [Bullet 2],
    [Bullet 3],
    )
  ]
][
  #titled-block("Right Column Name")[
    #enum(
    [Enumerated 1],
    [Enumerated 2],
    [Enumerated 3],
    )
  ]
]

== Three Columns

#let titled-block(title, body) = block(
  stroke: 0.5pt + gray,
  radius: 4pt,
  inset: 8pt,
  width: 100%,
)[
  #text(weight: "bold")[#title]
  #body
]

#slide(composer: (1fr, 1fr, 1fr))[
  #titled-block("Column 1 Name")[
    #list(
    [Bullet 1],
    [Bullet 2],
    [Bullet 3],
    )
  ]
][
  #titled-block("Column 2 Name")[
    #list(
    [Bullet 1],
    [Bullet 2],
    [Bullet 3],
    [Bullet 4],
    [Bullet 5],
    )
  ]
][
  #titled-block("Column 3 Name")[
    #list(
    [Bullet 1],
    [Bullet 2],
    [Bullet 3],
    [Bullet 4],
    )
  ]
]

== Image in One Column and Text in the Other Column

#slide(composer: (1fr, 1fr))[
  #align(center)[
    #image("graphics/example_image.png", width: 80%)
  ]
][
  #list(
    [Example bullet item 1.],
    [Example bullet item 2.],
  )

  This is an example paragraph. This is an example paragraph.
]

== Flowchart in One Column and Text in the Other Column

#import "@preview/fletcher:0.5.8" as fletcher: node, edge
#let fletcher-diagram = touying-reducer.with(reduce: fletcher.diagram, cover: fletcher.hide)

#slide(composer: (1fr, 1fr))[
  #align(center)[
    #figure(
      fletcher-diagram(
        node-stroke: 0.5pt,
        node-corner-radius: 4pt,
        spacing: (3em, 3em),
        node((0, 0), [Input], name: <input>),
        node((1, 0), [Process], name: <process>),
        node((2, 0), [Output], name: <output>),
        node((1, 1), [Feedback], name: <feedback>),
        edge(<input>, <process>, "-|>"),
        edge(<process>, <output>, "-|>"),
        edge(<output>, <feedback>, "-|>", corner: right),
        edge(<feedback>, <input>, "-|>", corner: right),
      ),
      caption: [A simple flowchart.],
    ) <fig:flowchart>
  ]
][
  #list(
    [Example bullet item 1.],
    [Example bullet item 2.],
  )

  This is an example paragraph. This is an example paragraph.
]

== Plot in One Column and Text in the Other Column

#import "@preview/lilaq:0.6.0" as lq

#slide(composer: (1fr, 1fr))[
  #align(center)[
    #figure(
      lq.diagram(
        width: 10cm,
        height: 7cm,
        xlabel: $x$,
        ylabel: $f(x)$,
        xlim: (-3, 3),
        legend: (position: top + left),
        xaxis: (tick-distance: 1),
        yaxis: (tick-distance: 10),
        lq.plot(
          lq.linspace(-3, 3, num: 100),
          x => calc.pow(x, 2),
          mark: none,
          stroke: blue + 1.5pt,
          label: $x^2$,
        ),
        lq.plot(
          lq.linspace(-3, 3, num: 100),
          x => calc.pow(x, 3),
          mark: none,
          stroke: (paint: red, thickness: 1.5pt, dash: "dashed"),
          label: $x^3$,
        ),
      ),
      caption: [An example plot.],
    ) <fig:plot_example>
  ]
][
  #list(
    [Example bullet item 1.],
    [Example bullet item 2.],
  )

  This is an example paragraph. This is an example paragraph.
]

#slide(config: (
  page: (header: none, footer: none),
))[
  #set align(center + horizon)
  #text(size: 2.5em)[A Plain Frame]
  #v(0.5em)
  #text(size: 1.2em)[No headline, no footline. Useful for chapter cards or full-bleed images.]
]

== Key Takeaways

#let titled-block(title, body) = block(
  stroke: 0.5pt + gray,
  radius: 4pt,
  inset: 8pt,
  width: 100%,
)[
  #text(weight: "bold")[#title]
  #body
]

#titled-block("Summary")[
  #list(
    [Takeaway 1: a brief, memorable statement of the main point.],
    [Takeaway 2: a follow-up that reinforces the takeaway above.],
    [Takeaway 3: a final point that ties everything together.],
  )
]

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

= Appendix <touying:appendix>

== Backup: Additional Material <touying:appendix>

These slides are typically used for Q&A backup.
#list(
  [Backup point 1.],
  [Backup point 2.],
)
