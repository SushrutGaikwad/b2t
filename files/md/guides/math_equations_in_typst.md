# Writing Math Equations in Typst

A reference for how mathematical formulas work in Typst. Sourced from the official Typst documentation (the Math reference, the Math Mode section of the Syntax reference, and the Symbols reference covering shorthands and the `sym` module).

## 1. Entering math mode

Math is written by wrapping an equation in dollar signs (`$...$`). This works inside both markup mode and code mode.

There are two display forms:

- **Inline math**: no surrounding spaces inside the dollar signs. The formula flows within the text.
  - Example: `$x^2$` renders inline.
- **Block math**: the content starts and ends with at least one space. The formula is typeset as its own centered block.
  - Example: `$ x^2 $` renders as a block.

So the only difference between inline and block is whether there is whitespace just inside the dollar signs.

```typst
$-x$ is the opposite of $x$.   // inline

$ x^2 + y^2 = z^2 $            // block (note the spaces)
```

## 2. Variables: single vs multiple letters

This is one of the most important rules in Typst math, and it differs from LaTeX.

- A **single letter** is always displayed as is (as a variable).
- **Multiple consecutive letters** are interpreted as a named variable, function, or symbol, not as a product of individual letters.

To display multiple letters verbatim as text, put them in quotes. To insert the value of a code-level single-letter variable, use the hash (`#`) syntax.

```typst
$ A = pi r^2 $
$ "area" = pi dot "radius"^2 $
$ cal(A) := { x in RR | x "is natural" } $
#let x = 5
$ #x < 17 $
```

Here `pi`, `dot`, and `RR` are recognized symbol names (because they are multiple letters), `"area"` and `"is natural"` are literal text, and `#x` pulls in the code variable whose value is 5.

## 3. Implied multiplication (CRITICAL for LaTeX conversion)

**This is the single most important difference to get right when converting LaTeX to Typst.** In LaTeX, adjacent letters like `$xy$` are automatically a product of two variables. In Typst, adjacent letters with **no space** are read as one multi-letter name, not a product (see section 2). To express "x times y" in Typst you **must separate the letters with a space**.

So the rule for the conversion agent is: whenever LaTeX has two or more single-letter variables written next to each other, insert a space between each pair in the Typst output.

| LaTeX   | Wrong Typst | Correct Typst | Why                                                        |
| ------- | ----------- | ------------- | ---------------------------------------------------------- |
| `$xy$`  | `$xy$`      | `$x y$`       | `xy` (no space) is treated as a single unknown name `xy`.  |
| `$abc$` | `$abc$`     | `$a b c$`     | `abc` would be one name; spaces make it `a` times `b` times `c`. |
| `$2x$`  | —           | `$2 x$` or `$2x$` | A number then a letter is fine either way, but a space is safe and clear. |
| `$xy^2$`| `$xy^2$`    | `$x y^2$`     | Keep the product spaced even with attachments.             |

Remember that the space *inside* the dollar signs is what separates the two display modes (section 1). The multiplication space goes **between the letters**, so both forms still work:

```typst
$x y$          // INLINE: "x times y" (no outer spaces, internal space between letters)
$ x y $        // BLOCK:  "x times y" (outer spaces for block, internal space between letters)
```

In other words, converting LaTeX `$xy$`:

- inline becomes `$x y$`
- block becomes `$ x y $`

The internal space between `x` and `y` is mandatory in both; only the outer spaces differ.

```typst
$x y$        // x times y (inline)
$ a b c $    // a times b times c (block)
$ F = m a $  // F = m times a, not a variable named "ma"
```

## 4. Symbols and shorthands

Math mode exposes a large library of named [symbols](https://typst.app/docs/reference/symbols/sym/) such as `pi`, `dot`, `RR` (the real numbers), `infinity`, and so on.

- **Variants via modifiers**: many symbols have variants you select by appending dot-separated modifiers to the symbol name. For example, `gt.eq.not` is a variant of the greater-than symbol.
- **Shorthands**: Typst recognizes short sequences that approximate a symbol, such as `=>`, `->`, and `!=`. When a shorthand exists, it is listed in that symbol's documentation.

```typst
$ x < y => x gt.eq.not y $
```

Field-access syntax (dots) is how you reach symbol variants, for example `arrow.r.long`.

## 5. Subscripts, superscripts, and attachments

- **Subscript (bottom attachment)**: `x_1`
- **Superscript (top attachment)**: `x^2`

Group multi-token attachments with parentheses.

```typst
$ x_1, x^2, x_(i+1), e^(2 pi i) $
```

More advanced placement (limits, simultaneous top and bottom, prescripts) is handled by the `attach` function. See section 11.

## 6. Fractions

A forward slash creates a fraction. Parenthesized groups become the numerator and denominator.

```typst
$ 1 + (a+b)/5 $
$ frac(a^2, 2) $     // explicit fraction function
```

## 7. Line breaks

A backslash (`\`) inserts a line break inside an equation, so a single equation can span multiple lines.

```typst
$ sum_(k=0)^n k
    &= 1 + ... + n \
    &= (n(n+1)) / 2 $
```

## 8. Alignment

Within an equation, an ampersand (`&`) marks an *alignment point*. Alignment points create columns that alternate between right-aligned and left-aligned.

- Each `&` toggles the alignment for what follows: the first creates a right/left boundary, the next toggles again, and so on.
- Two ampersands in a row (`&&`) create two alignment points at once, which effectively skips a column. `& &` and `&&` behave identically.

In the example below, `(3x + y) / 7` is right-aligned and `= 9` is left-aligned. The annotation after `&&` ("given") is left-aligned because the double ampersand toggled twice.

```typst
$ (3x + y) / 7 &= 9 && "given" \
  3x + y &= 63 & "multiply by 7" \
  3x &= 63 - y && "subtract y" \
  x &= 21 - y/3 & "divide by 3" $
```

## 9. Text and strings inside math

Wrap words in double quotes to render them as upright text rather than as variables.

```typst
$ a "is natural" $
```

Strings are the one kind of code value you can write directly in math without a hash.

## 10. Function calls in math mode

Math mode supports special "math calls" that do not need a hash prefix. Their argument list behaves a little differently from ordinary code calls:

- Inside the arguments you are still in math mode, so you can write math directly. To pass a code expression, use hash syntax (strings are the exception, since they are valid in math syntax directly).
- They accept positional arguments, named arguments, and argument spreading (`..`).
- They do not support trailing content blocks.
- They offer extra syntax for two-dimensional argument lists: a semicolon (`;`) separates rows, merging the comma-separated arguments before it into an array (a row). This is how matrices and similar structures are written.

```typst
$ frac(a^2, 2) $
$ vec(1, 2, delim: "[") $
$ mat(1, 2; 3, 4) $
$ mat(..#range(1, 5).chunks(2)) $
$ lim_x = op("lim", limits: #true)_x $
```

Escaping inside math calls:

- To write a literal comma or semicolon, escape it with a backslash (`\,` or `\;`).
- A colon is only treated specially when it directly follows an identifier (as a named-argument separator). To show a literal colon in that position, put a space before it.

A function call written with a leading hash (`#`) is a normal code call and is not subject to these math-call rules.

## 11. Math library functions

All math functions live in the `math` module, which is available by default inside equations. Outside equations, access them with the `math.` prefix (for example `math.frac(...)`).

Key functions:

Each function is described below with usage examples. Where a function takes named arguments, they are passed inside the call (for example `delim: "["`).

### 11.1 `accent` - accents over a base

Signature: `accent(base, accent, size: auto)`. The accent argument can be a symbol or a shorthand character. Common accents include `hat`, `tilde`, `macron`/`bar`, `dot`, `dot.double`, `arrow`, `breve`, `caron`, `acute`, `grave`, and `circle`.

```typst
$ accent(a, ->) $          // arrow accent using a shorthand
$ accent(a, hat) $         // a with a hat
$ accent(a, tilde) $       // a with a tilde
$ accent(x, dot) $         // x with a single overdot
$ accent(x, dot.double) $  // x with a double overdot
$ accent(A, hat, size: #150%) $  // widen the accent
```

### 11.2 `attach` - sub/superscripts and limits

In most cases you use the shorthand `_` (bottom) and `^` (top). The `attach` function gives full control, including prescripts (top-left `tl`, bottom-left `bl`) and the post positions (`t`, `b`, `tr`, `br`).

```typst
$ sum_(i=0)^n a_i = 2^(1+i) $          // shorthand sub/superscripts
$ attach(Pi, t: alpha, b: beta,
         tl: 1, bl: 2, tr: 3, br: 4) $ // all six attachment slots
```

Limits vs scripts: Typst chooses automatically, but you can force it. `limits()` places attachments above/below; `scripts()` places them as sub/superscripts.

```typst
$ limits(A)_1^2 != A_1^2 $             // force limit placement on the left A
$ op("lim", limits: #true)_(n -> oo) $ // operator with limit below
```

### 11.3 `binom` - binomial coefficients

Signature: `binom(upper, ..lower)`. Extra lower arguments stack as a multinomial.

```typst
$ binom(n, k) $        // standard binomial
$ binom(n, k_1, k_2, k_3) $  // multinomial-style lower row
```

### 11.4 `cancel` - strike-through

Signature: `cancel(body, length: auto, inverted: false, cross: false, angle: auto, stroke: ...)`.

```typst
$ (a dot cancel(x)) / cancel(x) $     // cancel a common factor
$ cancel(x, cross: #true) $           // cross out (an X)
$ cancel(x, inverted: #true) $        // flip the slash direction
$ cancel(x, angle: #45deg) $          // custom angle
```

### 11.5 `cases` - case distinctions

Signature: `cases(..children, delim: "{", reverse: false, gap: ...)`. Each argument is a line; use `&` inside lines to align them.

```typst
$ f(x) = cases(
  1 "if" x >= 0,
  0 "if" x < 0,
) $
$ cases(reverse: #true, 1, 2) $       // brace on the right
$ cases(delim: "[", x, y) $           // square-bracket delimiter
```

### 11.6 `class` - force a math class

Signature: `class(class, body)`. Overrides spacing/behavior by reclassifying content. Classes include `"normal"`, `"binary"`, `"relation"`, `"unary"`, `"opening"`, `"closing"`, `"large"`, `"punctuation"`, `"fence"`, etc.

```typst
$ x class("binary") y $                // treat the gap as a binary operator
$ #class("punctuation", ":") $
```

### 11.7 `equation` - the equation element

Used mainly for styling (show/set rules), numbering, and accessibility, rather than written by hand inside `$...$`.

```typst
#set math.equation(numbering: "(1)")   // number all block equations
$ E = m c^2 $

#math.equation(block: true, numbering: "(1)", $ x + y $)
```

### 11.8 `frac` - fractions

Signature: `frac(num, denom)`. The slash shorthand `a/b` produces the same result.

```typst
$ frac(a + b, c) $     // explicit
$ (a + b) / c $        // slash shorthand, identical output
```

### 11.9 `lr` - left/right auto-sizing delimiters

`lr` makes delimiters grow to fit their content. Plain delimiters around tall content auto-scale already, but `lr` gives explicit control. Related helpers: `abs()`, `norm()`, `floor()`, `ceil()`, `round()`, and `mid()`.

```typst
$ lr(]sum_(x=1)^n] x, size: #50%) $    // mismatched/partial fences
$ abs((x + y) / 2) $                   // absolute value bars
$ norm(x) $                            // double bars
$ floor(x) $, $ ceil(x) $, $ round(x) $
```

### 11.10 `mat` - matrices

Signature: `mat(..rows, delim: "(", augment: none, gap: ...)`. Use `,` to separate columns and `;` to separate rows.

```typst
$ mat(1, 2; 3, 4) $                    // 2x2, default parentheses
$ mat(1, 2; 3, 4, delim: "[") $        // square brackets
$ mat(1, 0, 0; 0, 1, 0; 0, 0, 1) $     // 3x3 identity
$ mat(1, 2, 3; 4, 5, 6, augment: #2) $ // draw a divider after column 2
$ mat(..#range(1, 5).chunks(2)) $      // build rows from code
```

### 11.11 `op` - text operators

Signature: `op(text, limits: false)`. Defines an upright operator name. Many standard operators (`sin`, `cos`, `log`, `lim`, `max`, `min`, etc.) are already built in as symbols.

```typst
$ op("argmax")_x f(x) $                // custom operator
$ op("lim", limits: #true)_(n -> oo) a_n $  // limits below
$ sin x + cos x + log_2 n $            // built-in operators
```

### 11.12 `primes` - grouped primes

Usually written with the apostrophe shorthand; `primes` is the underlying element.

```typst
$ f'(x) $              // one prime
$ f''(x) $             // two primes
$ f'''(x) $            // three primes
```

### 11.13 `root` - roots

Signature: `root(index, radicand)`. Omit the index (or use the `sqrt` symbol) for a square root.

```typst
$ sqrt(x + y) $        // square root
$ root(3, x) $         // cube root
$ root(n, x + 1) $     // nth root
```

### 11.14 `sizes` - force a size style

Functions `display()`, `inline()`, `script()`, and `sscript()` force the size context used for an expression (mirroring LaTeX's `\displaystyle` etc.). Each takes an optional `cramped` boolean.

```typst
$ sum_i x_i != display(sum_i x_i) $    // force full display size inline
$ script(x + y) $                      // script-size
$ inline(1/2) $                        // inline-size fraction
```

### 11.15 `stretch` - stretch a glyph

Signature: `stretch(body, size: ...)`. Stretches a glyph horizontally or vertically, often combined with attachments to label arrows or braces.

```typst
$ stretch(=)^"def" $                   // an equals sign with text above
$ stretch(->, size: #200%) $           // a longer arrow
$ f : A stretch(->)^"phi" B $          // labeled mapping arrow
```

### 11.16 `styles` - alternate letterforms

Functions `upright()`, `italic()`, and `bold()` switch the style of their content within a formula.

```typst
$ upright(A) != A $    // upright vs default italic
$ bold(F) = m bold(a) $  // bold vectors
$ italic("text") $
```

### 11.17 under/over functions

Place braces, brackets, lines, or labels above or below an expression: `underline`, `overline`, `underbrace`, `overbrace`, `underbracket`, `overbracket`, `underparen`, `overparen`, `undershell`, `overshell`. The brace/bracket variants take an optional annotation as a second argument.

```typst
$ underline(x + y) $                   // line below
$ overline(a + b) $                    // line above (e.g. a mean or conjugate)
$ overbrace(1 + 2 + ... + n, "sum") $  // labeled brace above
$ underbrace(a + b + c, "three terms") $ // labeled brace below
$ overbracket(x + y, "label") $        // square bracket above
```

### 11.18 `variants` - alternate typefaces

Functions `serif()`, `sans()`, `frak()` (fraktur), `mono()`, `bb()` (blackboard bold / double-struck), and `cal()` (calligraphic) change the typeface of letters in a formula.

```typst
$ bb(R) $              // blackboard bold R (real numbers), same as RR
$ cal(A) $             // calligraphic A
$ frak(g) $            // fraktur g
$ sans(x) $, $ mono(x) $, $ serif(x) $
```

### 11.19 `vec` - column vectors

Signature: `vec(..children, delim: "(", align: center, gap: ...)`.

```typst
$ vec(1, 2, 3) $                       // column vector, parentheses
$ vec(1, 2, delim: "[") $              // square-bracket delimiter
$ vec(a_1, a_2, gap: #1em) $           // wider row spacing
```

## 12. Math fonts

Set the math font with a show-set rule. Only OpenType math fonts are suitable for typesetting mathematics.

```typst
#show math.equation: set text(font: "Fira Math")
$ sum_(i in NN) 1 + i $
```

## 13. Comments and escapes inside math

- **Comments** work the same as elsewhere: `//` for a line comment and `/* ... */` for a block comment, including inside equations (`$/* comment */$`).
- **Character escape**: precede a special character with a backslash to render it literally, for example `$x\^2$` to show a literal caret.

## 14. Accessibility

For accessible output, supply a natural-language description of an equation using the `alt` parameter of `math.equation`.

```typst
#math.equation(
  alt: "d S equals delta q divided by T",
  block: true,
  $ dif S = (delta q) / T $,
)
```

## 15. Shorthands reference

Shorthands are short character sequences that Typst automatically interprets as a specific glyph. They can be used interchangeably with the named symbol. Some shorthands differ between markup mode and math mode. You can disable a shorthand by escaping one of its characters with a backslash.

### 15.1 Markup-mode shorthands (outside `$...$`)

| Shorthand | Result | Name        | Meaning              |
| --------- | ------ | ----------- | -------------------- |
| `--`      | –      | `dash.en`   | en dash              |
| `---`     | —      | `dash.em`   | em dash              |
| `...`     | …      | `dots.h`    | horizontal ellipsis  |
| `-?`      | (shy)  | `hyph.soft` | soft hyphen          |
| `-`       | −      | `minus`     | minus sign           |
| `~`       | (nbsp) | `space.nobreak` | non-breaking space |

### 15.2 Math-mode shorthands (inside `$...$`)

| Shorthand | Result | Equivalent symbol         | Common LaTeX     |
| --------- | ------ | ------------------------- | ---------------- |
| `->`      | →      | `arrow.r`                 | `\to`, `\rightarrow` |
| `\|->`    | ↦      | `arrow.r.bar` / `mapsto`  | `\mapsto`        |
| `=>`      | ⇒      | `arrow.r.double`          | `\Rightarrow`    |
| `\|=>`    | ⤇      | `arrow.r.double.bar`      |                  |
| `==>`     | ⟹      | `arrow.r.double.long`     | `\Longrightarrow` |
| `-->`     | ⟶      | `arrow.r.long`            | `\longrightarrow` |
| `~~>`     | ⟿      | `arrow.r.long.squiggly`   |                  |
| `~>`      | ⇝      | `arrow.r.squiggly`        | `\rightsquigarrow` |
| `>->`     | ↣      | `arrow.r.tail`            | `\rightarrowtail` |
| `->>`     | ↠      | `arrow.r.twohead`         | `\twoheadrightarrow` |
| `<-`      | ←      | `arrow.l`                 | `\gets`, `\leftarrow` |
| `<==`     | ⟸      | `arrow.l.double.long`     | `\Longleftarrow` |
| `<--`     | ⟵      | `arrow.l.long`            | `\longleftarrow` |
| `<~~`     | ⬳      | `arrow.l.long.squiggly`   |                  |
| `<~`      | ⇜      | `arrow.l.squiggly`        |                  |
| `<-<`     | ↢      | `arrow.l.tail`            | `\leftarrowtail` |
| `<<-`     | ↞      | `arrow.l.twohead`         | `\twoheadleftarrow` |
| `<=>`     | ⇔      | `arrow.l.r.double`        | `\Leftrightarrow` |
| `<==>`    | ⟺      | `arrow.l.r.double.long`   | `\Longleftrightarrow` |
| `<-->`    | ⟷      | `arrow.l.r.long`          | `\longleftrightarrow` |
| `*`       | ∗      | `ast.op`                  | `\ast`           |
| `\|\|`    | ‖      | `bar.v.double`            | `\Vert`          |
| `[\|`     | ⟦      | `bracket.l.double`        | `\llbracket`     |
| `\|]`     | ⟧      | `bracket.r.double`        | `\rrbracket`     |
| `:=`      | ≔      | `colon.eq`                | `\coloneqq`      |
| `::=`     | ⩴      | `colon.double.eq`         |                  |
| `...`     | …      | `dots.h`                  | `\ldots`, `\dots` |
| `=:`      | ≕      | `eq.colon`                | `\eqqcolon`      |
| `!=`      | ≠      | `eq.not`                  | `\neq`           |
| `>>`      | ≫      | `gt.double`               | `\gg`            |
| `>=`      | ≥      | `gt.eq`                   | `\geq`           |
| `>>>`     | ⋙      | `gt.triple`               | `\ggg`           |
| `<<`      | ≪      | `lt.double`               | `\ll`            |
| `<=`      | ≤      | `lt.eq`                   | `\leq`           |
| `<<<`     | ⋘      | `lt.triple`               | `\lll`           |
| `-`       | −      | `minus`                   | `-`              |
| `~`       | ∼      | `tilde.op`                | `\sim`           |

## 16. Named symbol reference (the `sym` module)

All named symbols below come from Typst's `sym` module. Inside a formula (`$...$`) write the name directly (`pi`, `plus.minus`, `arrow.r`). Outside a formula, prefix it with `sym.` (for example `#sym.arrow.r`) or, for the math-only ones, `math.`.

Key conventions:

- **Variants are selected with dot-separated modifiers** appended to the base name. For example `eq` is `=`, `eq.not` is `≠`, `eq.triple` is `≡`. `arrow.r` is `→`, `arrow.r.double` is `⇒`, `arrow.r.long` is `⟶`. This is the single most important pattern: most LaTeX commands map onto a base name plus modifiers.
- **Direction modifiers** are consistent across families: `.l` (left), `.r` (right), `.t` (top/up), `.b` (bottom/down), `.l.r` (left-right), `.t.b` (up-down), plus diagonals `.tr`, `.br`, `.tl`, `.bl`.
- **Common shape/style modifiers**: `.double`, `.triple`, `.quad`, `.not` (negated/struck), `.eq` (with equals), `.o` or `.circle` (in a circle), `.sq` or `.square` (in a square), `.big` (large operator form), `.filled`, `.stroked`, `.small`, `.tiny`, `.alt` (alternate glyph), `.rev` (reversed).
- Two special math identifiers, `dif` and `Dif`, are not ordinary symbols: they render the upright `d`/`D` of a differential (as in `integral f(x) dif x`) and also affect spacing. Outside math, use `math.dif`.

### 16.1 Greek letters, lowercase

| Typst        | Glyph | LaTeX        | Typst        | Glyph | LaTeX        |
| ------------ | ----- | ------------ | ------------ | ----- | ------------ |
| `alpha`      | α     | `\alpha`     | `nu`         | ν     | `\nu`        |
| `beta`       | β     | `\beta`      | `xi`         | ξ     | `\xi`        |
| `beta.alt`   | ϐ     | `\varbeta`   | `omicron`    | ο     | `\omicron`   |
| `gamma`      | γ     | `\gamma`     | `pi`         | π     | `\pi`        |
| `delta`      | δ     | `\delta`     | `pi.alt`     | ϖ     | `\varpi`     |
| `epsilon`    | ε     | `\epsilon`   | `rho`        | ρ     | `\rho`       |
| `epsilon.alt`| ϵ     | `\varepsilon`| `rho.alt`    | ϱ     | `\varrho`    |
| `zeta`       | ζ     | `\zeta`      | `sigma`      | σ     | `\sigma`     |
| `eta`        | η     | `\eta`       | `sigma.alt`  | ς     | `\varsigma`  |
| `theta`      | θ     | `\theta`     | `tau`        | τ     | `\tau`       |
| `theta.alt`  | ϑ     | `\vartheta`  | `upsilon`    | υ     | `\upsilon`   |
| `iota`       | ι     | `\iota`      | `phi`        | φ     | `\phi`       |
| `kappa`      | κ     | `\kappa`     | `phi.alt`    | ϕ     | `\varphi`    |
| `kappa.alt`  | ϰ     | `\varkappa`  | `chi`        | χ     | `\chi`       |
| `lambda`     | λ     | `\lambda`    | `psi`        | ψ     | `\psi`       |
| `mu`         | μ     | `\mu`        | `omega`      | ω     | `\omega`     |

Also available: `digamma` ϝ, `kai` ϗ.

### 16.2 Greek letters, uppercase

Capitalize the name for the uppercase form: `Alpha` Α, `Beta` Β, `Gamma` Γ, `Delta` Δ, `Epsilon` Ε, `Zeta` Ζ, `Eta` Η, `Theta` Θ, `Iota` Ι, `Kappa` Κ, `Lambda` Λ, `Mu` Μ, `Nu` Ν, `Xi` Ξ, `Omicron` Ο, `Pi` Π, `Rho` Ρ, `Sigma` Σ, `Tau` Τ, `Upsilon` Υ, `Phi` Φ, `Chi` Χ, `Psi` Ψ, `Omega` Ω.

In LaTeX only the visually distinct ones have commands (`\Gamma`, `\Delta`, `\Theta`, `\Lambda`, `\Xi`, `\Pi`, `\Sigma`, `\Upsilon`, `\Phi`, `\Psi`, `\Omega`); the rest are typeset as upright Latin capitals. Variants: `Theta.alt` ϴ, `Omega.inv` ℧ (mho), `Digamma` Ϝ, `Kai` Ϗ, `Sha` Ш.

### 16.3 Blackboard bold / double-struck (number sets)

Repeat a capital letter to get its blackboard-bold form. Each is equivalent to `bb(<letter>)` and to LaTeX `\mathbb{<letter>}`.

| Typst | Glyph | Typst | Glyph | Typst | Glyph |
| ----- | ----- | ----- | ----- | ----- | ----- |
| `NN`  | ℕ     | `ZZ`  | ℤ     | `QQ`  | ℚ     |
| `RR`  | ℝ     | `CC`  | ℂ     | `PP`  | ℙ     |
| `HH`  | ℍ     | `AA`  | 𝔸     | `BB`  | 𝔹     |

The full set `AA` through `ZZ` exists for every letter. Related: `Re` ℜ (`\Re`), `Im` ℑ (`\Im`), `ell` ℓ (`\ell`).

### 16.4 Binary operators

| Typst          | Glyph | LaTeX        | Typst             | Glyph | LaTeX        |
| -------------- | ----- | ------------ | ----------------- | ----- | ------------ |
| `plus`         | +     | `+`          | `and`             | ∧     | `\wedge`     |
| `minus`        | −     | `-`          | `or`              | ∨     | `\vee`       |
| `plus.minus`   | ±     | `\pm`        | `union`           | ∪     | `\cup`       |
| `minus.plus`   | ∓     | `\mp`        | `sect` / `inter`  | ∩     | `\cap`       |
| `times`        | ×     | `\times`     | `union.sq`        | ⊔     | `\sqcup`     |
| `div`          | ÷     | `\div`       | `sect.sq`         | ⊓     | `\sqcap`     |
| `dot.op`       | ⋅     | `\cdot`      | `union.plus`      | ⊎     | `\uplus`     |
| `ast.op`       | ∗     | `\ast`       | `union.dot`       | ⊍     | `\uplus`     |
| `star.op`      | ⋆     | `\star`      | `without`         | ∖     | `\setminus`  |
| `compose`      | ∘     | `\circ`      | `wreath`          | ≀     | `\wr`        |
| `bullet.op`    | ∙     | `\bullet`    | `times.l`         | ⋉     | `\ltimes`    |
| `plus.circle`  | ⊕     | `\oplus`     | `times.r`         | ⋊     | `\rtimes`    |
| `minus.circle` | ⊖     | `\ominus`    | `times.div`       | ⋇     | `\divideontimes` |
| `times.circle` | ⊗     | `\otimes`    | `plus.dot`        | ∔     | `\dotplus`   |
| `div.circle`   | ⨸     |              | `dot.circle`      | ⊙     | `\odot`      |
| `plus.square`  | ⊞     | `\boxplus`   | `minus.square`    | ⊟     | `\boxminus`  |
| `times.square` | ⊠     | `\boxtimes`  | `dot.square`      | ⊡     | `\boxdot`    |
| `slash.o`      | ⊘     | `\oslash`    | `convolve`        | ∗     | `\ast`       |

### 16.5 Large (n-ary) operators

These grow in display style and take limits above/below. Each `.big` form is the large variant of a binary operator.

| Typst            | Glyph | LaTeX       | Typst              | Glyph | LaTeX        |
| ---------------- | ----- | ----------- | ------------------ | ----- | ------------ |
| `sum`            | ∑     | `\sum`      | `union.big`        | ⋃     | `\bigcup`    |
| `product`        | ∏     | `\prod`     | `inter.big` / `sect.big` | ⋂ | `\bigcap`  |
| `product.co`     | ∐     | `\coprod`   | `and.big`          | ⋀     | `\bigwedge`  |
| `integral`       | ∫     | `\int`      | `or.big`           | ⋁     | `\bigvee`    |
| `integral.double`| ∬     | `\iint`     | `union.sq.big`     | ⨆     | `\bigsqcup`  |
| `integral.triple`| ∭     | `\iiint`    | `sect.sq.big`      | ⨅     | `\bigsqcap`  |
| `integral.cont`  | ∮     | `\oint`     | `plus.circle.big`  | ⨁     | `\bigoplus`  |
| `integral.surf`  | ∯     | `\oiint`    | `times.circle.big` | ⨂     | `\bigotimes` |
| `integral.vol`   | ∰     | `\oiiint`   | `dot.circle.big`   | ⨀     | `\bigodot`   |
| `integral.cont.ccw` | ∳  |             | `union.plus.big`   | ⨄     | `\biguplus`  |
| `integral.cont.cw`  | ∲  |             | `union.dot.big`    | ⨃     |              |
| `integral.slash` | ⨏     | `\fint`     | `sum.integral`     | ⨋     |              |

Other integral variants exist: `integral.dash` ⨍, `integral.dash.double` ⨎, `integral.quad` ⨌, `integral.ccw` ⨑, `integral.cw` ∱, `integral.inter` / `integral.sect` ⨙, `integral.union` ⨚, `integral.times` ⨘, `integral.square` ⨖, `integral.arrow.hook` ⨗.

### 16.6 Relations: equality and similarity

| Typst          | Glyph | LaTeX        | Typst            | Glyph | LaTeX          |
| -------------- | ----- | ------------ | ---------------- | ----- | -------------- |
| `eq`           | =     | `=`          | `tilde.op`       | ∼     | `\sim`         |
| `eq.not`       | ≠     | `\neq`       | `tilde.eq`       | ≃     | `\simeq`       |
| `eq.def`       | ≝     | `\triangleq` | `tilde.eq.not`   | ≄     | `\not\simeq`   |
| `eq.delta`     | ≜     | `\triangleq` | `tilde.equiv`    | ≅     | `\cong`        |
| `eq.quest`     | ≟     | `\overset{?}{=}` | `tilde.equiv.not`| ≇  | `\ncong`       |
| `eq.colon`     | ≕     | `\eqqcolon`  | `tilde.not`      | ≁     | `\nsim`        |
| `colon.eq`     | ≔     | `\coloneqq`  | `tilde.rev`      | ∽     | `\backsim`     |
| `eq.triple`    | ≡     | `\equiv`     | `tilde.triple`   | ≋     |                |
| `eq.quad`      | ≣     |              | `approx`         | ≈     | `\approx`      |
| `equiv`        | ≡     | `\equiv`     | `approx.eq`      | ≊     | `\approxeq`    |
| `equiv.not`    | ≢     | `\not\equiv` | `approx.not`     | ≉     | `\not\approx`  |
| `prop`         | ∝     | `\propto`    | `asymp`          | ≍     | `\asymp`       |
| `eq.star`      | ≛     |              | `asymp.not`      | ≭     |                |

### 16.7 Relations: order and comparison

| Typst          | Glyph | LaTeX        | Typst            | Glyph | LaTeX          |
| -------------- | ----- | ------------ | ---------------- | ----- | -------------- |
| `lt`           | <     | `<`          | `gt`             | >     | `>`            |
| `lt.eq`        | ≤     | `\leq`       | `gt.eq`          | ≥     | `\geq`         |
| `lt.eq.slant`  | ⩽     | `\leqslant`  | `gt.eq.slant`    | ⩾     | `\geqslant`    |
| `lt.double`    | ≪     | `\ll`        | `gt.double`      | ≫     | `\gg`          |
| `lt.triple`    | ⋘     | `\lll`       | `gt.triple`      | ⋙     | `\ggg`         |
| `lt.not`       | ≮     | `\nless`     | `gt.not`         | ≯     | `\ngtr`        |
| `lt.eq.not`    | ≰     | `\nleq`      | `gt.eq.not`      | ≱     | `\ngeq`        |
| `lt.tilde`     | ≲     | `\lesssim`   | `gt.tilde`       | ≳     | `\gtrsim`      |
| `lt.dot`       | ⋖     | `\lessdot`   | `gt.dot`         | ⋗     | `\gtrdot`      |
| `lt.neq`       | ⪇     | `\lneq`      | `gt.neq`         | ⪈     | `\gneq`        |
| `lt.gt`        | ≶     | `\lessgtr`   | `gt.lt`          | ≷     | `\gtrless`     |
| `lt.eq.gt`     | ⋚     | `\lesseqgtr` | `gt.eq.lt`       | ⋛     | `\gtreqless`   |
| `prec`         | ≺     | `\prec`      | `succ`           | ≻     | `\succ`        |
| `prec.eq`      | ⪯     | `\preceq`    | `succ.eq`        | ⪰     | `\succeq`      |
| `prec.curly.eq`| ≼     | `\preccurlyeq`| `succ.curly.eq` | ≽     | `\succcurlyeq` |
| `prec.tilde`   | ≾     | `\precsim`   | `succ.tilde`     | ≿     | `\succsim`     |
| `prec.not`     | ⊀     | `\nprec`     | `succ.not`       | ⊁     | `\nsucc`       |

### 16.8 Relations: sets, membership, subset

| Typst          | Glyph | LaTeX        | Typst            | Glyph | LaTeX          |
| -------------- | ----- | ------------ | ---------------- | ----- | -------------- |
| `in`           | ∈     | `\in`        | `subset`         | ⊂     | `\subset`      |
| `in.not`       | ∉     | `\notin`     | `supset`         | ⊃     | `\supset`      |
| `in.rev`       | ∋     | `\ni`        | `subset.eq`      | ⊆     | `\subseteq`    |
| `in.rev.not`   | ∌     | `\not\ni`    | `supset.eq`      | ⊇     | `\supseteq`    |
| `subset.neq`   | ⊊     | `\subsetneq` | `supset.neq`     | ⊋     | `\supsetneq`   |
| `subset.not`   | ⊄     | `\not\subset`| `supset.not`     | ⊅     | `\not\supset`  |
| `subset.eq.not`| ⊈     | `\nsubseteq` | `supset.eq.not`  | ⊉     | `\nsupseteq`   |
| `subset.sq`    | ⊏     | `\sqsubset`  | `supset.sq`      | ⊐     | `\sqsupset`    |
| `subset.eq.sq` | ⊑     | `\sqsubseteq`| `supset.eq.sq`   | ⊒     | `\sqsupseteq`  |
| `subset.double`| ⋐     | `\Subset`    | `supset.double`  | ⋑     | `\Supset`      |

### 16.9 Relations: logic, proof, and other binary relations

| Typst          | Glyph | LaTeX          | Typst          | Glyph | LaTeX        |
| -------------- | ----- | -------------- | -------------- | ----- | ------------ |
| `divides`      | ∣     | `\mid`         | `tack.r`       | ⊢     | `\vdash`     |
| `divides.not`  | ∤     | `\nmid`        | `tack.l`       | ⊣     | `\dashv`     |
| `parallel`     | ∥     | `\parallel`    | `tack.r.double`| ⊨     | `\vDash`, `\models` |
| `parallel.not` | ∦     | `\nparallel`   | `tack.r.not`   | ⊬     | `\nvdash`    |
| `perp`         | ⟂     | `\perp`        | `tack.r.double.not` | ⊭ | `\nvDash`    |
| `models`       | ⊧     | `\models`      | `forces`       | ⊩     | `\Vdash`     |
| `bot`          | ⊥     | `\bot`         | `multimap`     | ⊸     | `\multimap`  |
| `top`          | ⊤     | `\top`         | `smile`        | ⌣     | `\smile`     |
| `tack.t`       | ⊥     | `\bot`         | `frown`        | ⌢     | `\frown`     |
| `tack.b`       | ⊤     | `\top`         | `image`        | ⊷     |              |

### 16.10 Logic and set-theory symbols (non-relational)

| Typst        | Glyph | LaTeX          | Typst        | Glyph | LaTeX          |
| ------------ | ----- | -------------- | ------------ | ----- | -------------- |
| `forall`     | ∀     | `\forall`      | `not`        | ¬     | `\neg`         |
| `exists`     | ∃     | `\exists`      | `complement` | ∁     | `\complement`  |
| `exists.not` | ∄     | `\nexists`     | `therefore`  | ∴     | `\therefore`   |
| `nothing` / `emptyset` | ∅ | `\emptyset`, `\varnothing` | `because` | ∵ | `\because`     |
| `and`        | ∧     | `\land`        | `or`         | ∨     | `\lor`         |
| `qed`        | ∎     | `\blacksquare` | `and.double` | ⩓     | `\Cap`-like    |

### 16.11 Arrows

The base names are `arrow.r` →, `arrow.l` ←, `arrow.t` ↑, `arrow.b` ↓, `arrow.l.r` ↔, `arrow.t.b` ↕, plus diagonals `arrow.tr` ↗, `arrow.br` ↘, `arrow.tl` ↖, `arrow.bl` ↙. Add modifiers to any of these. The table shows the right-pointing forms; the same modifiers work for the other directions.

| Typst                  | Glyph | LaTeX               |
| ---------------------- | ----- | ------------------- |
| `arrow.r`              | →     | `\rightarrow`, `\to`|
| `arrow.l`              | ←     | `\leftarrow`, `\gets` |
| `arrow.t`              | ↑     | `\uparrow`          |
| `arrow.b`              | ↓     | `\downarrow`        |
| `arrow.l.r`            | ↔     | `\leftrightarrow`   |
| `arrow.t.b`            | ↕     | `\updownarrow`      |
| `arrow.r.double`       | ⇒     | `\Rightarrow`       |
| `arrow.l.double`       | ⇐     | `\Leftarrow`        |
| `arrow.l.r.double`     | ⇔     | `\Leftrightarrow`   |
| `arrow.t.double`       | ⇑     | `\Uparrow`          |
| `arrow.b.double`       | ⇓     | `\Downarrow`        |
| `arrow.t.b.double`     | ⇕     | `\Updownarrow`      |
| `arrow.r.long`         | ⟶     | `\longrightarrow`   |
| `arrow.l.long`         | ⟵     | `\longleftarrow`    |
| `arrow.l.r.long`       | ⟷     | `\longleftrightarrow` |
| `arrow.r.double.long`  | ⟹     | `\Longrightarrow`   |
| `arrow.l.double.long`  | ⟸     | `\Longleftarrow`    |
| `arrow.l.r.double.long`| ⟺     | `\Longleftrightarrow` |
| `arrow.r.bar` / `mapsto` | ↦   | `\mapsto`           |
| `mapsto.long`          | ⟼     | `\longmapsto`       |
| `arrow.l.bar`          | ↤     | `\mapsfrom`         |
| `arrow.r.hook`         | ↪     | `\hookrightarrow`   |
| `arrow.l.hook`         | ↩     | `\hookleftarrow`    |
| `arrow.r.tail`         | ↣     | `\rightarrowtail`   |
| `arrow.l.tail`         | ↢     | `\leftarrowtail`    |
| `arrow.r.twohead`      | ↠     | `\twoheadrightarrow`|
| `arrow.l.twohead`      | ↞     | `\twoheadleftarrow` |
| `arrow.r.not`          | ↛     | `\nrightarrow`      |
| `arrow.l.not`          | ↚     | `\nleftarrow`       |
| `arrow.l.r.not`        | ↮     | `\nleftrightarrow`  |
| `arrow.r.squiggly`     | ⇝     | `\rightsquigarrow`  |
| `arrow.r.wave`         | ↝     | `\leadsto`          |
| `arrow.r.long.squiggly`| ⟿     |                     |
| `arrow.r.triple`       | ⇛     | `\Rrightarrow`      |
| `arrow.l.triple`       | ⇚     | `\Lleftarrow`       |
| `arrow.r.dashed`       | ⇢     | `\dashrightarrow`   |
| `arrow.l.dashed`       | ⇠     | `\dashleftarrow`    |
| `arrow.r.loop`         | ↬     | `\looparrowright`   |
| `arrow.l.loop`         | ↫     | `\looparrowleft`    |
| `arrow.cw`             | ↻     | `\circlearrowright` |
| `arrow.ccw`            | ↺     | `\circlearrowleft`  |
| `arrow.cw.half`        | ↷     | `\curvearrowright`  |
| `arrow.ccw.half`       | ↶     | `\curvearrowleft`   |
| `arrow.zigzag`         | ↯     |                     |

Paired arrows: `arrows.rr` ⇉, `arrows.ll` ⇇, `arrows.tt` ⇈, `arrows.bb` ⇊, `arrows.lr` ⇆ (`\leftrightarrows`), `arrows.rl` ⇄ (`\rightleftarrows`), `arrows.tb` ⇅, `arrows.bt` ⇵, `arrows.rrr` ⇶, `arrows.lll` ⬱.

### 16.12 Harpoons

Base `harpoon` with direction + side, e.g. `harpoon.rt` ⇀ (right, barb up) = `\rightharpoonup`, `harpoon.rb` ⇁ = `\rightharpoondown`, `harpoon.lt` ↼ = `\leftharpoonup`, `harpoon.lb` ↽ = `\leftharpoondown`, `harpoon.tl`/`tr`/`bl`/`br` for vertical harpoons. Combined: `harpoons.rtlb` ⇌ = `\rightleftharpoons`, `harpoons.ltrb` ⇋ = `\leftrightharpoons`. Each single harpoon also has `.bar` and `.stop` variants.

### 16.13 Delimiters (brackets, braces, bars, fences)

Auto-sizing of these is handled by the `lr` function (section 11.9) or by plain delimiters around tall content; the names below are the glyphs themselves.

| Typst             | Glyph | LaTeX        | Typst             | Glyph | LaTeX        |
| ----------------- | ----- | ------------ | ----------------- | ----- | ------------ |
| `paren.l`         | (     | `(`          | `paren.r`         | )     | `)`          |
| `bracket.l`       | [     | `[`          | `bracket.r`       | ]     | `]`          |
| `brace.l`         | {     | `\{`         | `brace.r`         | }     | `\}`         |
| `angle.l`         | ⟨     | `\langle`    | `angle.r`         | ⟩     | `\rangle`    |
| `floor.l`         | ⌊     | `\lfloor`    | `floor.r`         | ⌋     | `\rfloor`    |
| `ceil.l`          | ⌈     | `\lceil`     | `ceil.r`          | ⌉     | `\rceil`     |
| `bar.v`           | \|    | `\vert`      | `bar.v.double`    | ‖     | `\Vert`      |
| `bar.v.triple`    | ⦀     |              | `bar.h`           | ―     |              |
| `bracket.l.double`| ⟦     | `\llbracket` | `bracket.r.double`| ⟧     | `\rrbracket` |
| `angle.l.double`  | ⟪     |              | `angle.r.double`  | ⟫     |              |
| `brace.l.double`  | ⦃     |              | `brace.r.double`  | ⦄     |              |
| `paren.l.double`  | ⦅     |              | `paren.r.double`  | ⦆     |              |
| `fence.l`         | ⧘     |              | `fence.r`         | ⧙     |              |

Stretchable over/under delimiters (used by `overbrace`/`underbrace` etc.): `brace.t` ⏞, `brace.b` ⏟, `bracket.t` ⎴, `bracket.b` ⎵, `paren.t` ⏜, `paren.b` ⏝, `shell.t` ⏠, `shell.b` ⏡.

### 16.14 Dots

| Typst       | Glyph | LaTeX      | Meaning                    |
| ----------- | ----- | ---------- | -------------------------- |
| `dots.h`    | …     | `\ldots`   | horizontal (baseline) dots |
| `dots.h.c`  | ⋯     | `\cdots`   | horizontal centered dots   |
| `dots.v`    | ⋮     | `\vdots`   | vertical dots              |
| `dots.down` | ⋱     | `\ddots`   | diagonal down dots         |
| `dots.up`   | ⋰     | `\iddots`  | diagonal up dots           |
| `dot.op`    | ⋅     | `\cdot`    | centered multiplication dot|
| `dot.c`     | ·     | `\cdotp`   | middle dot                 |
| `dot.basic` | .     | `.`        | period                     |

### 16.15 Accents

These are passed as the second argument to `accent(base, ...)` (section 11.1), or many have a shorthand usable directly. The accent renders above (or for some, around) the base.

| Typst          | Result over `a` | LaTeX        |
| -------------- | --------------- | ------------ |
| `hat`          | â               | `\hat`       |
| `tilde` / `tilde.basic` | ã      | `\tilde`     |
| `macron` / `bar` | ā             | `\bar`       |
| `acute`        | á               | `\acute`     |
| `grave`        | à               | `\grave`     |
| `breve`        | ă               | `\breve`     |
| `caron`        | ǎ               | `\check`     |
| `diaer`        | ä               | `\ddot` (math) / `\"` |
| `dot.double`   | ä (double dot)  | `\ddot`      |
| `dot.triple`   | (triple dot)    | `\dddot`     |
| `dot.quad`     | (quadruple dot) | `\ddddot`    |
| `arrow` (`arrow.r`) | a⃗          | `\vec`       |
| `circle`       | å               | `\mathring`  |

(For a single overdot use the base `dot` symbol, i.e. `accent(a, dot)` → ȧ, LaTeX `\dot`.)

### 16.16 Calculus and analysis

| Typst        | Glyph | LaTeX        | Notes                          |
| ------------ | ----- | ------------ | ------------------------------ |
| `diff` / `partial` | ∂ | `\partial`   | partial derivative             |
| `gradient` / `nabla` | ∇ | `\nabla`   | nabla / del                    |
| `laplace`    | ∆     | `\Delta`     | Laplace operator (increment)   |
| `infinity` / `oo` | ∞ | `\infty`     | infinity                       |
| `dif`        | (upright d) | `\mathrm{d}` | differential d, as in `dif x`. Affects spacing. |
| `Dif`        | (upright D) | `\mathrm{D}` | capital differential D         |
| `planck`     | ℏ     | `\hbar`      | reduced Planck constant        |
| `prime`      | ′     | `\prime`, `'`| prime                          |
| `prime.double` | ″   | `''`         | double prime                   |
| `prime.triple` | ‴   | `'''`        | triple prime                   |

### 16.17 Miscellaneous math and text symbols

| Typst        | Glyph | LaTeX          | Typst          | Glyph | LaTeX          |
| ------------ | ----- | -------------- | -------------- | ----- | -------------- |
| `degree`     | °     | `\degree`, `^\circ` | `dagger`  | †     | `\dagger`      |
| `angle`      | ∠     | `\angle`       | `dagger.double`| ‡     | `\ddagger`     |
| `angle.arc`  | ∡     | `\measuredangle` | `section`    | §     | `\S`           |
| `angle.right`| ∟     | `\rightangle`  | `pilcrow`      | ¶     | `\P`           |
| `ratio`      | ∶     | `\ratio`       | `copyright`    | ©     | `\copyright`   |
| `colon`      | :     | `:`            | `trademark`    | ™     | `\texttrademark` |
| `permille`   | ‰     | `\permil`      | `trademark.registered` | ® | `\textregistered` |
| `percent`    | %     | `\%`           | `bullet`       | •     | `\bullet`      |
| `numero`     | №     |                | `checkmark`    | ✓     | `\checkmark`   |
| `refmark`    | ※     |                | `crossmark`    | ✗     |                |
| `maltese`    | ✠     | `\maltese`     | `amp`          | &     | `\&`           |

### 16.18 Geometric shapes

Most shapes follow the pattern `<shape>.<fill>.<size?>` where fill is `stroked` (outline) or `filled`, e.g. `circle.stroked` ○, `circle.filled` ●.

| Typst              | Glyph | LaTeX (approx) | Typst              | Glyph |
| ------------------ | ----- | -------------- | ------------------ | ----- |
| `circle.stroked`   | ○     | `\bigcirc`     | `circle.filled`    | ●     |
| `square.stroked`   | □     | `\square`      | `square.filled`    | ■     |
| `triangle.stroked.t` | △   | `\triangle`    | `triangle.filled.t`| ▲     |
| `triangle.stroked.b` | ▽   | `\triangledown`| `triangle.filled.b`| ▼     |
| `triangle.stroked.r` | ▷   | `\triangleright` | `triangle.filled.r` | ▶  |
| `triangle.stroked.l` | ◁   | `\triangleleft`| `triangle.filled.l`| ◀     |
| `diamond.stroked`  | ◇     | `\diamond`     | `diamond.filled`   | ◆     |
| `lozenge.stroked`  | ◊     | `\lozenge`     | `lozenge.filled`   | ⧫     |
| `star.stroked`     | ☆     | `\star`        | `star.filled`      | ★     |

Each has finer size variants such as `.tiny`, `.small`, `.medium`, `.big`, and dotted/rounded variants. Related families: `rect.*`, `ellipse.*`, `parallelogram.*`, `penta.*`, `hexa.*`.

### 16.19 Currency, punctuation, and other symbols

For completeness (rarely needed in math, but available): currency such as `dollar` $, `cent` ¢, `pound` £, `euro` €, `yen` ¥, `won` ₩, `lira` ₺, `rupee.indian` ₹, `ruble` ₽, `franc` ₣, `bitcoin` ₿. Punctuation and quotes such as `excl` !, `quest` ?, `quest.inv` ¿, `excl.inv` ¡, `quote.l.double` “, `quote.r.double` ”, `quote.l.single` ‘, `quote.r.single` ’, `quote.angle.l.double` «, `quote.angle.r.double` ». Spaces such as `space` ␣, `space.nobreak` (nbsp), `space.en`, `space.quad`, `space.thin`, `space.hair`. Other typographic controls: `wj` (word joiner), `zwj`, `zwnj`, `zws` (zero-width space), `lrm`, `rlm`.

There are also non-mathematical families: card suits (`suit.heart.filled` ♥, `suit.spade.filled` ♠, `suit.club.filled` ♣, `suit.diamond.filled` ♦), musical notes (`note.quarter`, `note.eighth`, `flat` ♭, `natural` ♮, `sharp` ♯), dice (`die.one` ⚀ through `die.six` ⚅), and astronomical/planetary symbols (`sun` ☉, `mercury` ☿, `venus` ♀, `earth`, `mars` ♂, `jupiter` ♃, `saturn` ♄, `uranus`, `neptune`).

### 16.20 Conversion notes for LaTeX to Typst

When converting LaTeX math to Typst, keep these mappings in mind:

- **Space out implied multiplication (most common mistake):** adjacent single-letter variables in LaTeX must be separated by spaces in Typst, because unspaced letters become a single name. `$xy$` becomes `$x y$`, `$abc$` becomes `$a b c$`, `$ma$` (mass times acceleration) becomes `$m a$`. See section 3.
- Drop the backslash and translate the command to its Typst name: `\alpha` becomes `alpha`, `\rightarrow` becomes `arrow.r` (or the shorthand `->`), `\pm` becomes `plus.minus`, `\leq` becomes `lt.eq` (or `<=`).
- LaTeX `var`-prefixed letters map to the `.alt` modifier: `\varepsilon` becomes `epsilon.alt`, `\varphi` becomes `phi.alt`, `\vartheta` becomes `theta.alt`.
- `\mathbb{R}` becomes `RR` (or `bb(R)`); `\mathcal{A}` becomes `cal(A)`; `\mathfrak{g}` becomes `frak(g)`.
- Negation usually maps to the `.not` modifier rather than a `\not` prefix: `\neq` becomes `eq.not`, `\notin` becomes `in.not`, `\nleq` becomes `lt.eq.not`.
- "In a circle" maps to `.circle` or `.o`, and "in a square" to `.square` or `.sq`: `\oplus` becomes `plus.circle`, `\boxtimes` becomes `times.square`.
- Big operators are the bare name (`\sum` becomes `sum`); the `.big` variants are the enlarged versions of binary operators (`\bigoplus` becomes `plus.circle.big`).
- Accents become the `accent()` function: `\hat{x}` becomes `accent(x, hat)`, `\vec{v}` becomes `accent(v, arrow)`, `\bar{x}` becomes `accent(x, macron)`.
- Prefer the shorthand when one exists and is readable (`->`, `=>`, `<=`, `>=`, `!=`, `|->`), but the named form always works and is unambiguous.

## 17. Worked conversion examples (LaTeX to Typst)

These are complete formulas converted end to end, so the agent can see how the pieces compose, not just how individual tokens map. In each pair, the Typst line shows the **content that goes between the dollar signs**. To use it inline write `$...$` (no spaces just inside the dollars); to display it as a block write `$ ... $` (with spaces just inside the dollars). See section 1.

Recurring patterns to notice across all examples:

- Adjacent single-letter variables get a **space** between them (`4ac` becomes `4a c`, `mc` becomes `m c`). This applies inside scripts and groups too (`g^{ik}` becomes `g^(i k)`). See section 3.
- LaTeX **braces** `{...}` for grouping become **parentheses** `(...)` in Typst (`x^{n-k}` becomes `x^(n-k)`).
- LaTeX **environments** (`pmatrix`, `cases`, `align`) become **function calls** or alignment syntax (`mat(...)`, `cases(...)`, `&`/`\`).
- LaTeX **accent macros** (`\hat`, `\vec`, `\bar`) become **accent functions** (`hat(...)`, `arrow(...)`, `macron(...)`).
- The differential `d` in `dx`, `dy` becomes `dif` (`dif x`), which renders upright and adds correct spacing.

### 17.1 Algebra and arithmetic

```
LaTeX:  E = mc^2
Typst:  E = m c^2

LaTeX:  F = ma
Typst:  F = m a

LaTeX:  (a + b)(a - b) = a^2 - b^2
Typst:  (a + b)(a - b) = a^2 - b^2

LaTeX:  ax^2 + bx + c = 0
Typst:  a x^2 + b x + c = 0
```

### 17.2 Powers, roots, fractions, subscripts

```
LaTeX:  x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
Typst:  x = (-b plus.minus sqrt(b^2 - 4a c)) / (2a)

LaTeX:  e^{i\pi} + 1 = 0
Typst:  e^(i pi) + 1 = 0

LaTeX:  \sqrt[3]{x + 1}
Typst:  root(3, x + 1)

LaTeX:  \frac{1}{1 + \frac{1}{x}}
Typst:  1/(1 + 1/x)

LaTeX:  x_{i+1} = x_i - \frac{f(x_i)}{f'(x_i)}
Typst:  x_(i+1) = x_i - f(x_i)/(f'(x_i))

LaTeX:  T^{i}_{j} = g^{ik} T_{kj}
Typst:  T^i_j = g^(i k) T_(k j)
```

### 17.3 Sums, products, integrals, limits

```
LaTeX:  \sum_{n=0}^{\infty} r^n = \frac{1}{1 - r}
Typst:  sum_(n=0)^oo r^n = 1/(1 - r)

LaTeX:  \prod_{i=1}^{n} i = n!
Typst:  product_(i=1)^n i = n!

LaTeX:  \int_0^\infty e^{-x^2} \, dx = \frac{\sqrt{\pi}}{2}
Typst:  integral_0^oo e^(-x^2) dif x = sqrt(pi)/2

LaTeX:  \iint_D f(x, y) \, dA
Typst:  integral.double_D f(x, y) dif A

LaTeX:  \lim_{h \to 0} \frac{f(x + h) - f(x)}{h}
Typst:  lim_(h -> 0) (f(x + h) - f(x))/h

LaTeX:  \sum_{k=1}^{n} k = \frac{n(n + 1)}{2}
Typst:  sum_(k=1)^n k = (n(n + 1))/2
```

### 17.4 Calculus and vectors

```
LaTeX:  f'(x) = \lim_{h \to 0} \frac{f(x + h) - f(x)}{h}
Typst:  f'(x) = lim_(h -> 0) (f(x + h) - f(x))/h

LaTeX:  \frac{dy}{dx} = 2x
Typst:  (dif y)/(dif x) = 2 x

LaTeX:  \nabla f = \frac{\partial f}{\partial x}\hat{x} + \frac{\partial f}{\partial y}\hat{y}
Typst:  nabla f = (partial f)/(partial x) hat(x) + (partial f)/(partial y) hat(y)

LaTeX:  \vec{a} \cdot \vec{b} = |\vec{a}|\,|\vec{b}|\cos\theta
Typst:  arrow(a) dot.op arrow(b) = abs(arrow(a)) abs(arrow(b)) cos theta

LaTeX:  \oint_C \vec{F} \cdot d\vec{r}
Typst:  integral.cont_C arrow(F) dot.op dif arrow(r)
```

### 17.5 Matrices, vectors, and cases

```
LaTeX:  \begin{pmatrix} a & b \\ c & d \end{pmatrix}
Typst:  mat(a, b; c, d)

LaTeX:  \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}
Typst:  mat(1, 0; 0, 1, delim: "[")

LaTeX:  \begin{vmatrix} a & b \\ c & d \end{vmatrix} = ad - bc
Typst:  mat(a, b; c, d, delim: "|") = a d - b c

LaTeX:  \begin{pmatrix} x \\ y \\ z \end{pmatrix}
Typst:  vec(x, y, z)

LaTeX:  |x| = \begin{cases} x & \text{if } x \geq 0 \\ -x & \text{if } x < 0 \end{cases}
Typst:  abs(x) = cases(
          x & "if" x >= 0,
          -x & "if" x < 0,
        )
```

### 17.6 Aligned multi-line equations

The LaTeX `align`/`align*`/`aligned` environments map to `&` (alignment point) and `\` (line break) inside a single block equation. Note `2ab` becomes `2a b`.

```
LaTeX:  \begin{align}
          (a + b)^2 &= a^2 + 2ab + b^2 \\
                    &= a^2 + b^2 + 2ab
        \end{align}

Typst:  $ (a + b)^2 &= a^2 + 2a b + b^2 \
                    &= a^2 + b^2 + 2a b $
```

```
LaTeX:  \begin{align}
          f(x) &= (x + 1)^2 \\
               &= x^2 + 2x + 1
        \end{align}

Typst:  $ f(x) &= (x + 1)^2 \
               &= x^2 + 2x + 1 $
```

### 17.7 Sets, logic, and relations

```
LaTeX:  A = \{ x \in \mathbb{R} \mid x > 0 \}
Typst:  A = { x in RR | x > 0 }

LaTeX:  \mathbb{N} \subseteq \mathbb{Z} \subseteq \mathbb{Q} \subseteq \mathbb{R}
Typst:  NN subset.eq ZZ subset.eq QQ subset.eq RR

LaTeX:  A \cup B = \{ x \mid x \in A \lor x \in B \}
Typst:  A union B = { x | x in A or x in B }

LaTeX:  \forall \varepsilon > 0, \, \exists \delta > 0
Typst:  forall epsilon.alt > 0, exists delta > 0

LaTeX:  p \implies q \quad \text{and} \quad p \iff q
Typst:  p ==> q quad "and" quad p <==> q

LaTeX:  P(A \mid B) = \frac{P(A \cap B)}{P(B)}
Typst:  P(A | B) = P(A inter B)/P(B)
```

### 17.8 Decorations: accents, braces, bars

```
LaTeX:  \hat{\theta} \approx \tilde{\mu}
Typst:  hat(theta) approx tilde(mu)

LaTeX:  \bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i
Typst:  macron(x) = 1/n sum_(i=1)^n x_i

LaTeX:  \overline{A \cup B} = \bar{A} \cap \bar{B}
Typst:  overline(A union B) = overline(A) inter overline(B)

LaTeX:  \underbrace{1 + 2 + \cdots + n}_{n \text{ terms}} = \frac{n(n + 1)}{2}
Typst:  underbrace(1 + 2 + dots.h.c + n, n "terms") = (n(n + 1))/2

LaTeX:  \binom{n}{k} = \frac{n!}{k!(n - k)!}
Typst:  binom(n, k) = n!/(k!(n - k)!)
```

### 17.9 Operators, trig, and custom operators

```
LaTeX:  \sin^2\theta + \cos^2\theta = 1
Typst:  sin^2 theta + cos^2 theta = 1

LaTeX:  \log_2 n + \ln x
Typst:  log_2 n + ln x

LaTeX:  \operatorname*{argmax}_{x \in S} f(x)
Typst:  op("argmax", limits: #true)_(x in S) f(x)

LaTeX:  \gcd(a, b) \quad \deg(p)
Typst:  gcd(a, b) quad op("deg")(p)
```

(`gcd` is built in; `deg` is not, so it uses `op(...)`. Built-in operators include `sin`, `cos`, `tan`, `log`, `ln`, `exp`, `lim`, `max`, `min`, `sup`, `inf`, `det`, `dim`, `gcd`, `mod`, and more; anything missing becomes `op("name")`.)

### 17.10 The multiplication-spacing trap in real formulas

This is the error most likely to slip through, because the LaTeX looks correct and the Typst looks correct, but the meaning silently changes. Always space adjacent variables.

```
LaTeX:  2\pi r            Typst:  2 pi r
LaTeX:  mc^2              Typst:  m c^2
LaTeX:  kT                Typst:  k T          (not kT, which is one name)
LaTeX:  IR                Typst:  I R          (Ohm's law: I times R)
LaTeX:  pV = nRT          Typst:  p V = n R T
LaTeX:  ds^2 = dx^2       Typst:  dif s^2 = dif x^2
LaTeX:  g^{ik}            Typst:  g^(i k)      (space even inside scripts)
LaTeX:  \frac{dy}{dx}     Typst:  (dif y)/(dif x)
```

### 17.11 Spacing keywords (optional fine-tuning)

LaTeX manual math spacing maps to named Typst spaces: `\,` becomes `thin`, `\:` becomes `med`, `\;` becomes `thick`, `\quad` becomes `quad`, and `\qquad` becomes `wide`. These are usually optional, since Typst spaces operators automatically; reach for them only to fine-tune.

```
LaTeX:  \int f(x) \, dx
Typst:  integral f(x) thin dif x

LaTeX:  a \quad b \qquad c
Typst:  a quad b wide c
```

## 18. Quick syntax summary

| Name                          | Example               |
| ----------------------------- | --------------------- |
| Inline math                   | `$x^2$`               |
| Block-level math              | `$ x^2 $`             |
| Bottom attachment (subscript) | `$x_1$`               |
| Top attachment (superscript)  | `$x^2$`               |
| Fraction                      | `$1 + (a+b)/5$`       |
| Line break                    | `$x \ y$`             |
| Alignment point               | `$x &= 2 \ &= 3$`     |
| Variable access (code value)  | `$#x$`, symbol `$pi$` |
| Field access (symbol variant) | `$arrow.r.long$`      |
| Implied multiplication        | `$x y$` (LaTeX `xy` becomes `x y`) |
| Symbol shorthand              | `$->$`, `$!=$`        |
| Text/string in math           | `$a "is natural"$`    |
| Math function call            | `$floor(x)$`          |
| Code expression in math       | `$#rect(width: 1cm)$` |
| Character escape              | `$x\^2$`              |
| Comment                       | `$/* comment */$`     |

## 19. Key rules to remember

1. Whitespace just inside the dollar signs decides block vs inline. `$ x $` is a block, `$x$` is inline.
2. A single letter is a variable shown verbatim. Multiple letters together form a name (symbol, function, or variable), not a product. Use quotes for literal multi-letter text, and spaces for multiplication. **When converting from LaTeX, this means `$xy$` must become `$x y$` (inline) or `$ x y $` (block): adjacent variables need a space between them, or Typst reads them as one name.**
3. Use `#` to drop in code values or call ordinary code functions from within math.
4. Math function calls (no hash) keep you in math mode, support named arguments and spreading, and use `;` to separate rows in 2D argument lists.
5. `&` sets alignment points that alternate right/left; `\` breaks lines.
6. All math helpers are in the `math` module, prefixed with `math.` outside equations.
