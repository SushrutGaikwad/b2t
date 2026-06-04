# Writing Math Equations in Typst

A reference for how mathematical formulas work in Typst. Sourced from the official Typst documentation (Math reference and the Math Mode section of the Syntax reference).

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

## 3. Implied multiplication

Letters separated by a space are treated as implied multiplication.

```typst
$x y$        // x times y
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

## 15. Quick syntax summary

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
| Implied multiplication        | `$x y$`               |
| Symbol shorthand              | `$->$`, `$!=$`        |
| Text/string in math           | `$a "is natural"$`    |
| Math function call            | `$floor(x)$`          |
| Code expression in math       | `$#rect(width: 1cm)$` |
| Character escape              | `$x\^2$`              |
| Comment                       | `$/* comment */$`     |

## 16. Key rules to remember

1. Whitespace just inside the dollar signs decides block vs inline. `$ x $` is a block, `$x$` is inline.
2. A single letter is a variable shown verbatim. Multiple letters together form a name (symbol, function, or variable), not a product. Use quotes for literal multi-letter text, and spaces (`x y`) for multiplication.
3. Use `#` to drop in code values or call ordinary code functions from within math.
4. Math function calls (no hash) keep you in math mode, support named arguments and spreading, and use `;` to separate rows in 2D argument lists.
5. `&` sets alignment points that alternate right/left; `\` breaks lines.
6. All math helpers are in the `math` module, prefixed with `math.` outside equations.
