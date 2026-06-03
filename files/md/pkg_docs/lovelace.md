# Lovelace

This is a package for writing pseudocode in Typst. It is named after the computer science pioneer Ada Lovelace and inspired by the pseudo package for LaTeX.

Pseudocode is not a programming language, it doesn't have strict syntax, so you should be able to write it however you need to in your specific situation. Lovelace lets you do exactly that.

On the following pages, we will explore all of Lovelace's features together.

## Getting Started

Import the package using

```typ
#import "@preview/lovelace:0.3.1": *
```

The simplest usage is via `#pseudocode-list` which transforms a nested list into pseudocode:

```typ
#pseudocode-list[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

As you can see, every list item becomes one line of code and nested lists become indented blocks. There are no special commands for common keywords and control structures, you just use whatever you like.

Maybe in your domain very uncommon structures make more sense? No problem!

```typ
#pseudocode-list[
  + *in parallel for each* $i = 1, ..., n$ *do*
    + fetch chunk of data $i$
    + *with probability* $exp(-epsilon_i slash k T)$ *do*
      + perform update
    + *end*
  + *end*
]
```

## Lower level interface

If you feel uncomfortable with abusing Typst's lists like we did on the previous page, you can also use the `#pseudocode` function directly:

```typ
#pseudocode(
  [do something],
  [do something else],
  [*while* still something to do],
  indent(
    [do even more],
    [*if* not done yet *then*],
    indent(
      [wait a bit],
      [resume working],
    ),
    [*else*],
    indent(
      [go home],
    ),
    [*end*],
  ),
  [*end*],
)
```

This is equivalent to the first example. Note that each line is given as one content argument and you indent a block by using the `indent` function.

This approach has the advantage that you do not rely on significant whitespace and code formatters can automatically correctly indent your Typst code.

## Line numbers

Lovelace puts a number in front of each line by default. If you want no numbers at all, you can set the `line-numbering` option to `none`. The initial example then looks like this:

```typ
#pseudocode-list(line-numbering: none)[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

(You can also pass this keyword argument to `#pseudocode`.)

If you do want line numbers in general but need to turn them off for specific lines, you can use `-` items instead of `+` items in `#pseudocode-list`:

```typ
#pseudocode-list[
  + normal line with a number
  - this line has no number
  + this one has a number again
]
```

It's easy to remember: `-` items usually produce unnumbered lists and `+` items produce numbered lists!

When using the `#pseudocode` function, you can achieve the same using `no-number`:

```typ
#pseudocode(
  [normal line with a number],
  no-number[this line has no number],
  [this one has a number again],
)
```

### Line number customization

Other than `none`, you can assign anything in ["1", "a", "A", "i", "I", "α", "Α", "一", "壹", "あ", "い", "ア", "イ", "א", "가", "ㄱ", "*", "١", "۱", "१", "১", "ক", "①", and "⓵"] to `line-numbering`. The "*" character means that symbols should be used to count, in the order of "*", "†", "‡", "§", "¶", "‖". If there are more than six items, the number is represented using repeated symbols.

So maybe you happen to think about the Roman Empire a lot and want to reflect that in your pseudocode?

```typ
#set text(font: "Cinzel")

#pseudocode-list(line-numbering: "I:")[
  + explore European tribes
  + *while* not all tribes conquered
    + *for each* tribe *in* unconquered tribes
      + try to conquer tribe
    + *end*
  + *end*
]
```

#### Alignment

By default, line numbers are placed with the alignment `horizon + right`, which can look weird when a single step in the algorithm spans multiple typesetting lines. You can modify the line numbering alignment using the `line-number-alignment` option:

```typ
#pseudocode-list(line-number-alignment: top + right)[
  + Single line
  + Multiple \ lines
]
```

### Referencing lines

You can reference an inividual line of a pseudocode by giving it a label. Inside `#pseudocode-list`, you can use `line-label`:

```typ
#pseudocode-list[
  + #line-label(<start>) do something
  + #line-label(<important>) do something important
  + go back to @start
]

The relevance of the step in @important cannot be overstated.
```

When using `#pseudocode`, you can use `with-line-label`:

```typ
#pseudocode(
  with-line-label(<start>)[do something],
  with-line-label(<important>)[do something important],
  [go back to @start],
)

The relevance of the step in @important cannot be overstated.
```

This has the same effect as the previous example.

The number shown in the reference uses the numbering scheme defined in the `line-numbering` option (see previous section).

#### Supplement

By default, `"Line"` is used as the supplement for referencing lines. You can change that using the `line-number-supplement` option to `pseudocode` or `pseudocode-list`.

```typ
#pseudocode-list(line-number-supplement: "Step")[
  + Stir vegetables on low heat.
  + *while* not tasty enough
    + #line-label(<soy-sauce>) Add soy sauce.
    + Taste again.
  + *end*
  + Serve hot.
]

@soy-sauce is the secret to a great meal.
```

## Indentation guides

By default, Lovelace puts a thin gray (`gray + 1pt`) line to the left of each indented block, which guides the reader in understanding the indentations, just like a code editor would. You can customise this using the `stroke` option which takes any value that is a valid Typst stroke. You can especially set it to `none` to have no indentation guides.

The example from the beginning becomes:

```typ
#pseudocode-list(stroke: none)[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

### Ending blocks with hooks

Some people prefer using the indentation guide to signal the end of a block instead of writing something like "end" by having a small "hook" at the end. To achieve that in Lovelace, you can make use of the `hooks` option and specify how far a line should extend to the right from the indentation guide:

```typ
#pseudocode-list(hooks: .5em)[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
]
```

## Spacing

You can control how far indented lines are shifted right by the `indentation` option. To change the space between lines, use the `line-gap` option.

```typ
#pseudocode-list(indentation: 3em, line-gap: 1.5em)[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

## Decoration

So far, our pseudo code was a bit naked, in a way. If you like, you can also add a title and/or a frame around your algorithm.

### Title

Using the `title` option, you can give your pseudocode a title (surprise!). For example, to achieve CLRS style, you can do something like

```typ
#pseudocode-list(stroke: none, title: smallcaps[Fancy-Algorithm])[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

### Booktabs

If you like wrapping your algorithm in elegant horizontal lines, you can do so by setting the `booktabs` option to `true`.

```typ
#pseudocode-list(booktabs: true)[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

Together with the `title` option, you can produce

```typ
#pseudocode-list(booktabs: true, title: [My cool title])[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

#### Stroke

By default, the outer booktab strokes are `text.fill + 2pt`. You can change that with the option `booktabs-stroke` to any valid Typst stroke. The inner line will always have the same stroke as the outer ones, just with half the thickness.

#### Inset

By setting the `title-inset` option, you can specify the space around the title:

```typ
#pseudocode-list(booktabs: true, title: [My cool title], title-inset: 2em)[
  + do something
  + do something else
  + *while* still something to do
    + do even more
    + *if* not done yet *then*
      + wait a bit
      + resume working
    + *else*
      + go home
    + *end*
  + *end*
]
```

## Algorithm as `figure`

To make algorithms referencable and being able to float in the document, you can use Typst's `#figure` function with a custom `kind`.

```typ
#figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [My cool algorithm],

  pseudocode-list[
    + do something
    + do something else
    + *while* still something to do
      + do even more
      + *if* not done yet *then*
        + wait a bit
        + resume working
      + *else*
        + go home
      + *end*
    + *end*
  ]
)
```

### Numbered title

If you want to have the algorithm counter inside the title instead (see previous section), there is the option `numbered-title`:

```typ
#figure(
  kind: "algorithm",
  supplement: [Algorithm],

  pseudocode-list(booktabs: true, numbered-title: [My cool algorithm])[
    + do something
    + do something else
    + *while* still something to do
      + do even more
      + *if* not done yet *then*
        + wait a bit
        + resume working
      + *else*
        + go home
      + *end*
    + *end*
  ]
) <cool>

See @cool for details on how to do something cool.
```

Note that the `numbered-title` option only makes sense when nesting your pseudocode inside a figure with `kind: "algorithm"`, otherwise it produces undefined results.

## Customization overview

Both `#pseudocode` and `#pseudocode-list` accept the following configuration arguments:

| option                   | type                  | default           |
| ------------------------ | --------------------- | ----------------- |
| `line-numbering`         | `none` or a numbering | `"1"`             |
| `line-number-supplement` | content or string     | `"Line"`          |
| `line-number-alignment`  | alignment             | `horizon + right` |
| `stroke`                 | stroke                | `1pt + gray`      |
| `hooks`                  | length                | `0pt`             |
| `indentation`            | length                | `1em`             |
| `line-gap`               | length                | `.8em`            |
| `booktabs`               | bool                  | `false`           |
| `booktabs-stroke`        | stroke                | `2pt + text.fill` |
| `title`                  | content or `none`     | `none`            |
| `title-inset`            | length                | `0.8em`           |
| `numbered-title`         | content or `none`     | `none`            |

Until Typst supports user defined types, we can use the following trick when wanting to set own default values for these options. Say, you always want your algorithms to have colons after the line numbers, no indentation guides and, if present, blue booktabs. In this case, you would put the following at the top of your document:

```typ
#let my-lovelace-defaults = (
  line-numbering: "1:",
  stroke: none,
  booktabs-stroke: 2pt + blue,
)

#let pseudocode = pseudocode.with(..my-lovelace-defaults)
#let pseudocode-list = pseudocode-list.with(..my-lovelace-defaults)
```

## Exported functions

Lovelace exports the following functions:

- `pseudocode`: Typeset pseudocode with each line as an individual content argument.
- `pseudocode-list`: Takes a standard Typst list and transforms it into a pseudocode.
- `indent`: Inside the argument list of `pseudocode`, use `indent` to specify an indented block.
- `no-number`: Wrap an argument to `pseudocode` in this function to have the corresponding line be unnumbered.
- `with-line-label`: Use this function in the `pseudocode` arguments to add a label to a specific line.
- `line-label`: When using `pseudocode-list`, you do not use `with-line-label` but insert a call to `line-label` somewhere in a line to add a label.
