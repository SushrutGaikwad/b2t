# Theorion (Typst) Reference for LLMs

This document explains how to write theorem-style environments in **Typst** using the
**theorion** package (version `0.6.x`) with the **fancy** cosmos. It is written as a
text-only reference: there is no visual rendering here, so every environment is
described in words, and every code block shows exactly what to emit.

Whenever you generate Typst code that uses theorion, follow the conventions in this
document. The required imports are fixed (see "Required Preamble"). Do not switch
cosmos and do not change the import lines.

---

## 1. What theorion is

theorion provides ready-made, automatically numbered environments for mathematical and
technical writing: `theorem`, `definition`, `lemma`, `corollary`, `proof`, and many
more, plus a set of colored callout boxes (`tip-block`, `warning-block`, etc.).

Key facts to keep in mind:

- All numbered environments share one counter by default, so numbering runs
  `1.1, 1.2, 1.3, ...` across the whole family within a heading section.
- Every environment can be cross-referenced with a Typst label and the `@` reference
  syntax.
- A "cosmos" is a visual theme. This reference uses `cosmos.fancy`. Other cosmos exist
  (`simple`, `rainbow`, `clouds`) but are out of scope here.
- The package is multilingual; the supplement word (for example "Theorem") follows the
  document language set by `#set text(lang: ...)`.

---

## 2. Required Preamble

Always start a theorion document with these lines, in this order:

```typst
#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion
```

- Line 1 imports the package. Use the version your project pins; `0.6.0` is assumed
  throughout this reference.
- Line 2 selects the fancy cosmos. This is mandatory for this reference. Do not replace
  it with `cosmos.simple`, `cosmos.rainbow`, or `cosmos.clouds`.
- Line 3 (`#show: show-theorion`) activates the show rules so the environments render.
  Without it, the environments will not display correctly.

A typical full header also sets heading numbering and language, because theorion
numbering is derived from headings:

```typst
#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion

#set heading(numbering: "1.1")
#set text(lang: "en")
#set par(first-line-indent: 1em, justify: true)
```

If `#set heading(numbering: ...)` is omitted, theorem numbers will not include a section
prefix.

---

## 3. The Core Calling Convention (read this carefully)

In theorion `0.6.x`, the **title is passed as the first content block**, and the
**body is the second content block**. This is the single most important syntax rule.

There are two valid forms for every numbered environment:

### Form A: body only (no title)

```typst
#theorem[
  There are infinitely many prime numbers.
]
```

Renders as a numbered theorem with the supplement and number only (for example
"Theorem 1.1"), followed by the body.

### Form B: title plus body (two content blocks)

```typst
#theorem[Euclid's Theorem][
  There are infinitely many prime numbers.
]
```

The first `[...]` is the **title**, the second `[...]` is the **body**. This renders
as something like "Theorem 1.1 (Euclid's Theorem)" followed by the body.

> Do **not** write `#theorem[Euclid's Theorem]` and expect the sentence to be the body.
> A single bracket is always treated as the body, never as the title. To give a title,
> you must supply two brackets.

### Equivalent named-argument form

The title can also be given as a named argument, which is useful when you also pass
`number` or `supplement`:

```typst
#theorem(title: "Euclid's Theorem")[
  There are infinitely many prime numbers.
]
```

Both `#theorem[Euclid's Theorem][...]` and `#theorem(title: "Euclid's Theorem")[...]`
produce the same result. Prefer the two-bracket form for plain titles; use the named
form when combining with other named arguments.

---

## 4. Numbered Theorem-like Environments

All of the following are numbered, share the common theorem counter, appear in the
theorem outline, and accept the Form A / Form B calling convention from Section 3.

| Function      | Typical supplement word | Use for                   |
| ------------- | ----------------------- | ------------------------- |
| `theorem`     | Theorem                 | main results              |
| `lemma`       | Lemma                   | helper results            |
| `corollary`   | Corollary               | direct consequences       |
| `proposition` | Proposition             | minor results             |
| `definition`  | Definition              | definitions               |
| `axiom`       | Axiom                   | axioms                    |
| `postulate`   | Postulate               | postulates                |
| `conjecture`  | Conjecture              | unproven statements       |
| `assumption`  | Assumption              | stated assumptions        |
| `property`    | Property                | properties                |
| `remark`      | Remark                  | remarks                   |
| `note`        | Note                    | notes                     |
| `example`     | Example                 | worked examples           |
| `exercise`    | Exercise                | exercises                 |
| `problem`     | Problem                 | problems to solve         |
| `proof`       | Proof                   | proofs (see Section 6)    |
| `solution`    | Solution                | solutions (see Section 6) |
| `conclusion`  | Conclusion              | concluding statements     |

Examples:

```typst
#definition[
  A natural number is called a #highlight[_prime number_] if it is greater than 1
  and cannot be written as the product of two smaller natural numbers.
] <def:prime>

#conjecture[Twin Prime Conjecture][
  There are infinitely many primes $p$ such that $p+2$ is also prime.
]

#corollary[
  There is no largest prime number.
] <cor:infinite-prime>

#proposition[
  Every field is a ring, but not every ring is a field.
] <prop:ring-field>
```

Note the `<label>` placed immediately after the closing bracket. Labels are optional
but required if you want to cross-reference the environment later (Section 7).

---

## 5. Unnumbered Environments: the `-box` variants

Every numbered environment has a matching `-box` function (for example `theorem-box`,
`definition-box`, `lemma-box`). The `-box` form is used to suppress numbering.

In `0.6.x`, an important behavior change applies: a `-box` environment **is still shown
in the outline and still displays the supplement prefix** unless you opt out. To create
a fully unnumbered, non-outlined box, pass `outlined: false`.

```typst
#theorem-box(outlined: false)[Theorem without numbering][
  This theorem is not numbered and does not appear in the theorem outline.
]
```

The same Form A / Form B convention applies to `-box` variants:

```typst
#definition-box(outlined: false)[
  An unnumbered definition with no title.
]
```

Use the `-box` variants when you want the styling of an environment without consuming
a number (for example, restating a known theorem, or an informal aside).

---

## 6. Proof, Solution, and the QED Symbol

`proof` and `solution` work like other environments and accept an optional title as the
first content block. They typically end with a QED marker.

```typst
#theorem[Euclid's Theorem][
  There are infinitely many prime numbers.
] <thm:euclid>

#proof[Proof of @thm:euclid][
  By contradiction: suppose $p_1, p_2, dots, p_n$ enumerates all primes.
  Let $P = p_1 p_2 dots p_n$. Then $P + 1$ is divisible by some prime $p_j$,
  which also divides $P$, so $p_j$ divides 1, a contradiction.
]
```

Here the first bracket `[Proof of @thm:euclid]` is the proof's title, and the second
bracket is the proof body.

`solution` accepts a `qed` argument to control the end-of-proof symbol. Use
`qed: auto` to show the default symbol:

```typst
#problem[
  Prove that for any integer $n > 1$, there exists a run of $n$ consecutive composite
  numbers.
]

#solution(qed: auto)[
  Consider $n! + 2, n! + 3, dots, n! + n$. For each $2 <= k <= n$, the term $n! + k$
  is divisible by $k$, so all of these are composite.
]
```

To change the QED symbol globally, set it in the preamble:

```typst
#set-qed-symbol[#math.qed]
```

To hide answers entirely (for example, when generating a worksheet without solutions),
use:

```typst
#set-result("noanswer")
```

---

## 7. Cross-References

Attach a label to an environment by placing `<label>` right after its closing bracket.
Reference it elsewhere with `@label`.

```typst
#theorem[Pythagorean Theorem][
  In a right triangle, $x^2 + y^2 = z^2$.
] <thm:pythagoras>

This result, @thm:pythagoras, bridges geometry and algebra.
```

A plain `@thm:pythagoras` renders as the supplement plus number (for example
"Theorem 1.4"). theorion also supports two special reference forms via a trailing
supplement bracket:

- `@thm:pythagoras[-]` renders the reference **without** the title.
- `@thm:pythagoras[!!]` renders the reference **with** both the title and the number.

```typst
A reference without the title: @thm:euclid[-];
a reference with title and number: @thm:euclid[!!].
```

A common label convention is `<kind:short-name>`, for example `<thm:euclid>`,
`<def:ring>`, `<cor:infinite-prime>`, `<lem:proportion>`. This is a convention, not a
requirement; any valid Typst label works.

---

## 8. Callout / Admonition Blocks

The fancy cosmos provides colored callout boxes for notes and warnings. These are
**not numbered** and do not share the theorem counter. Each takes a single body block
(no title block).

| Function          | Intended meaning          |
| ----------------- | ------------------------- |
| `tip-block`       | a helpful tip             |
| `note-block`      | a general note            |
| `important-block` | something important       |
| `warning-block`   | a warning                 |
| `caution-block`   | a caution                 |
| `remark-block`    | a remark aside            |
| `quote-block`     | a quotation               |
| `emph-block`      | an emphasized summary box |

Examples:

```typst
#tip-block[
  Differentiability implies continuity, but not the reverse. For instance, $f(x) = |x|$
  is continuous but not differentiable at $x = 0$.
]

#warning-block[
  Both conditions matter here:
  - the function must be continuous
  - the domain must be a closed interval
]

#important-block[
  This theorem is one of the most fundamental results in plane geometry.
]

#note-block[
  Mathematical proofs should be both rigorous and clear.
]

#caution-block[
  With infinite series, always verify convergence before discussing other properties.
]

#quote-block[
  Mathematics is the queen of the sciences, and number theory is the queen of
  mathematics. (Gauss)
]

#emph-block[
  Chapter summary:
  - introduced basic number theory concepts
  - proved several important theorems
]
```

Use these blocks for prose asides and emphasis. Use the numbered environments from
Section 4 for formal mathematical statements.

---

## 9. Numbering Control

theorion derives numbers from the document heading counter. Adjust behavior with these
setter calls, normally placed in the preamble:

```typst
#set-inherited-levels(1)        // how many heading levels prefix the number
#set-zero-fill(true)            // pad numbers, e.g. 01 instead of 1
#set-leading-zero(true)         // include a leading zero
#set-theorion-numbering("1.1")  // the numbering pattern string
```

- `set-inherited-levels(n)` controls how many heading levels appear in the theorem
  number. With `1`, a theorem under heading "2" might be "Theorem 2.1"; with `2`, under
  "2.3" it might be "Theorem 2.3.1".
- `set-theorion-numbering("1.1")` sets the format string, matching Typst's heading
  numbering syntax (for example `"1.1"`, `"A.1"`, `"1.1.1"`).

### Manually setting a number or supplement

You can override the automatic number or the supplement word per environment:

```typst
#theorem(title: "Euclid's Theorem", number: "233", supplement: [Theorion])[
  There are infinitely many prime numbers.
]
```

### Continuing the counter from a specific value

Pass an array to `number` to set the counter explicitly and continue from there:

```typst
#theorem(number: (2, 3))[
  This theorem is numbered 2.3. The next auto-numbered theorem will be 2.4.
]
```

### Custom full title

Override the entire auto-generated "Prefix Number (Title)" label with `full-title`:

```typst
#theorem(full-title: [Fundamental Theorem])[
  There is a fundamental result.
]
```

---

## 10. Theorem Outline (Table of Theorems)

To produce a list of all theorem-kind figures (a "table of theorems"), target the
theorem figure kind in an outline:

```typst
#outline(title: none, target: figure.where(kind: "theorem"))
```

This collects every numbered environment that is outlined. Environments created with a
`-box` variant and `outlined: false` are excluded.

---

## 11. Appendix Numbering

To switch to appendix-style numbering (for example "A.1") partway through a document,
reset the heading counter, change the heading numbering, and tell theorion to match:

```typst
#counter(heading).update(0)
#set heading(numbering: "A.1")
#set-theorion-numbering("A.1")

= Appendix

== Advanced Analysis

#theorem[Maximum Value Theorem][
  A continuous function on a closed interval attains both a maximum and a minimum.
] <thm:max-value>
```

---

## 12. Restating Theorems

theorion can reprint previously stated theorems elsewhere (for example, gathering all
theorems at the end of a chapter). Use `theorion-restate`.

```typst
// Restate every outlined environment whose identifier is "theorem"
#theorion-restate(
  filter: it => it.outlined and it.identifier == "theorem",
  render: it => it.render,
)
```

Other patterns:

```typst
// Restate a single labelled theorem (long form)
#theorion-restate(filter: it => it.label == <thm:euclid>)

// Restate a single labelled theorem (short form)
#theorion-restate(filter: <thm:euclid>)

// Restate with a custom render function
#theorion-restate(
  filter: it => it.outlined and it.identifier == "theorem",
  render: it => (prefix: none, title: "", full-title: auto, body) => block[
    #strong[#full-title.]#sym.space#emph(body)
  ],
)
```

---

## 13. Defining a Custom Environment

To create a new environment not in the preset list, use `make-frame`. It returns four
values: a counter, an unnumbered `-box` function, the main function, and a show rule.

```typst
#let (theorem-counter, theorem-box, theorem, show-theorem) = make-frame(
  "theorem",                         // identifier
  "Theorem",                         // supplement: string, dict, or theorion-i18n-map.at("theorem")
  counter: theorem-counter,          // reuse an existing counter; none for a fresh one
  inherited-levels: 2,               // heading levels to inherit when starting a new counter
  inherited-from: heading,           // inherit from heading, or from another counter
  render: (prefix: none, title: "", full-title: auto, body) =>
    [#strong[#full-title.]#sym.space#emph(body)],
)
#show: show-theorem
```

Notes:

- The supplement can be a plain string, a language dictionary such as
  `(en: "Theorem")`, or a built-in entry via `theorion-i18n-map.at("theorem")` for
  automatic translation.
- The `render` callback receives `prefix`, `title`, `full-title`, and `body`, and must
  return content. `full-title` is the assembled label (prefix, number, and title).
- After defining a custom environment you must apply its show rule with
  `#show: show-<name>`.

---

## 14. Other Options

```typst
#set-indent-mode(none)   // controls indentation: auto (default), none, a length, or a dictionary
```

---

## 15. Quick Reference Cheat Sheet

```typst
// Preamble (always)
#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion
#set heading(numbering: "1.1")
#set text(lang: "en")

// Numbered, no title
#theorem[ ...body... ]

// Numbered, with title (first bracket = title, second = body)
#theorem[Title][ ...body... ]

// Numbered, with label for referencing
#theorem[Title][ ...body... ] <thm:key>

// Unnumbered, excluded from outline
#theorem-box(outlined: false)[Title][ ...body... ]

// Proof tied to a labelled theorem
#proof[Proof of @thm:key][ ...body... ]

// Solution with QED symbol
#solution(qed: auto)[ ...body... ]

// References
@thm:key        // supplement + number
@thm:key[-]     // no title
@thm:key[!!]    // title + number

// Manual numbering / supplement
#theorem(title: "T", number: "233", supplement: [Custom])[ ...body... ]
#theorem(number: (2, 3))[ ...body... ]   // continue counter from 2.3
#theorem(full-title: [Custom Full Title])[ ...body... ]

// Callout boxes (unnumbered, body only)
#tip-block[ ... ]    #note-block[ ... ]    #important-block[ ... ]
#warning-block[ ... ]  #caution-block[ ... ]  #remark-block[ ... ]
#quote-block[ ... ]    #emph-block[ ... ]

// Table of theorems
#outline(title: none, target: figure.where(kind: "theorem"))
```

---

## 16. Common Mistakes to Avoid

1. **Forgetting `#show: show-theorion`.** Without it, environments do not render.
2. **Treating one bracket as the title.** `#theorem[Euclid's Theorem]` makes
   "Euclid's Theorem" the *body*, not the title. Use two brackets for a title.
3. **Expecting `-box` to be unnumbered automatically.** In `0.6.x` you must add
   `outlined: false` to exclude it from the outline and suppress numbering behavior.
4. **Swapping the cosmos.** This reference fixes `#import cosmos.fancy: *`. Keep it.
5. **Missing heading numbering.** Without `#set heading(numbering: "1.1")`, theorem
   numbers lack a section prefix.
6. **Putting the label inside the brackets.** The `<label>` goes *after* the closing
   bracket, not inside the body.
