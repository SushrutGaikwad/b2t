# Whalogen

Whalogen is a Typst package for typesetting chemical formulae and reactions. It is a port of LaTeX's `mhchem`. The main entry point is the `ce` function, which takes a string and returns a content block. All features work in both text mode and math mode.

## Quick Start Guide

```typ
#import "@preview/whalogen:0.3.0": ce

This is the formula for water: #ce("H2O")

This is a chemical reaction: 
#ce("CO2 + C -> 2CO")

It can be placed inside an equation: $#ce("CO2 + C -> 2CO")$

It can be placed on its own line:
$
#ce("CO2 + C -> 2CO")
$
```

## Syntax Reference

Every example below is a string passed to `ce("...")`. This table summarizes the operators; the sections that follow show each one in context.

| Syntax                      | Meaning                                                                     |
| --------------------------- | --------------------------------------------------------------------------- |
| `H2O`                       | A digit directly after an element becomes a subscript automatically         |
| `^`                         | Everything after the caret is superscript, until whitespace or `_`          |
| `_`                         | Explicit subscript                                                          |
| `H+`, `Cl-`                 | Trailing `+` or `-` becomes a charge                                        |
| `^2-`, `^99+`               | A signed superscript becomes a charge with that magnitude                   |
| `^.-`                       | A dot in a superscript renders as a radical dot                             |
| `\|X,Y\|`                   | Places `Y` directly above element `X` (oxidation numbers); no spaces inside |
| `@symbol,A,Z@`              | A nuclide with mass number `A` and atomic number `Z` (either may be empty)  |
| `(NH4)2S`                   | Parentheses, brackets `[]`, and braces `{}` auto-size to their contents     |
| `->`                        | Reaction arrow (right)                                                      |
| `<-`                        | Reaction arrow (left)                                                       |
| `<->`                       | Double-headed arrow (single line, heads on both ends)                       |
| `<-->`                      | Two stacked one-way arrows (top right-to-left, bottom left-to-right)        |
| `<=>`                       | Two stacked half-arrows / harpoons (equilibrium)                            |
| `=`                         | Also renders as a reaction arrow                                            |
| `->[above][below]`          | Text above and (optionally) below an arrow                                  |
| `(aq)`, `(s)`, etc.         | States of aggregation                                                       |
| `$...$`                     | Math mode inside `ce`, used for italic variables                            |
| `&`                         | Alignment point when stacking equations with `\` in math mode               |
| `2 H2O`, `0.5H2O`, `1/2H2O` | Stoichiometric numbers (integer, decimal, or fraction)                      |

## Introduction

This package is designed to facillitate the typesetting of chemical formulas in Typst. It mainly aims to replicate the functionality and operation of LaTeX's `mhchem` package. However, there are naturally some differences in the implementation of some features.

All of the features of this package are designed to function in both text and math mode.

## Chemical Equations

```typ
#ce("CO2 + C -> 2CO")
```

## Chemical Formulae

```typ
#ce("H2O")
```

```typ
#ce("Sb2O3")
```

A digit placed directly after an element is automatically rendered as a subscript, so `H2O` produces H with a subscript 2. To create a subscript in any other position, use an explicit underscore `_`.

## Charges

```typ
#ce("H+")
```

```typ
#ce("CrO4^2-")
```

```typ
#ce("[AgCl2]-")
```

```typ
#ce("Y^99+")
```

In the rendered output, a typed minus sign is shown as a longer dash.

## Oxidation States

```typ
#ce("Fe^II Fe^III_2O4")
```

A caret (^) will imply that subsequent characters should be in the superscript unless interrupted by certain characters (i.e., whitespace and underscore).

## Oxidation Numbers (RedOx Reaction Syntax)

```typ
#ce("|Mn,+II| + |H2,+I||O2,-I| -> |Mn,+IV||O2,-II| + |H2,+I||O,-II|")
```

Wrapping an element X with vertical bars like this: |X,Y| will ensure that Y is placed above X. Make sure to not include any spaces or you may get unintended behavior. Also ensure that anything that should affect the element (for example the 2 in H_2) is placed inside the bars.

## Unpaired Electrons and Radical Dots

```typ
#ce("OCO^.-")
```

```typ
#ce("NO^2.-")
```

## Stoichiometric Numbers

```typ
#ce("2H2O")
```

```typ
#ce("2 H2O")
```

```typ
#ce("0.5H2O")
```

```typ
#ce("1/2H2O")
```

The behavior of the fraction line is inherited from Typst's default behavior and generally obeys the rules for grouping numbers and automatically removing parenthesis.

When whitespace is inserted between the stoichiometric number and a compound with a subscript, the whitespace is automatically trimmed. If there is no subscript, the whitespace is not trimmed. This is a characteristic of Typst.

```typ
#ce("2 CO")
```

## Nuclides, Isotopes

```typ
#ce("@Th,227,90@^+")
```

```typ
#ce("@n,0,-1@^-")
```

```typ
#ce("@Tc,99m,@")
```

The pattern is `@symbol,massNumber,atomicNumber@`. Either of the two numbers may be left empty (note the trailing comma before the closing `@` in the technetium example). To simplify implementation of the parser, this string pattern is introduced to specify nuclides and isotopes. This is different from `mhchem`.

## Parenthesis, Brackets, Braces

```typ
#ce("(NH4)2S")
```

The parenthesis, brackets, and braces will automatically size to match the inner content.

```typ
#ce("[{(X2)3}2]^3+")
```

## Reaction Arrows

```typ
#ce("A -> B")
```

```typ
#ce("A <- B")
```

```typ
#ce("A <-> B")
```

The above rendered arrow is a single line with the left arrow head at its left and right arrow head at its right.

```typ
#ce("A <--> B")
```

The above renders two arrows, an arrow going from B to A at the top, and an arrow going from A to B just below it.

```typ
#ce("A <=> B")
```

The above renders two half arrows, a half arrow going from A to B at the top and a half arrow going from B to A just below it.

These reaction arrows come from the built-in `sym` module.

It is also possible to include text above the arrow. The backend uses the `xarrow` package to resize the arrows and place respective text. With two bracketed groups, the first is placed above the arrow and the second below it.

```typ
#ce("A ->[H2O] B")
```

```typ
#ce("A ->[some text] B")
```

```typ
#ce("A ->[some text above][other text below] B")
```

## States of Aggregation

```typ
#ce("H2(aq)")
```

```typ
#ce("NaOH(aq, #sym.infinity)")
```

In Typst, when parenthesis and similar follow a subscript, it is also included in the subscript. This results in seemingly different behavior for very similar input as seen above. The H_2 has an implied underscore whereas the NaOH does not.

To achieve the opposite behavior as shown above, insert whitespace or underscore respectively.

```typ
#ce("H2 (aq)")
```

```typ
#ce("NaOH_(aq, #sym.infinity)")
```

## Variables

```typ
#ce("H2O <=>[$k_1$][$k_-1$] OH- + H+")
```

```typ
#ce("$x$ NaOH + H2SO4 = Na$_x$ H$_(2 -x)$SO4")
```

Sometimes it is needed to use variables in mathematical notation (i.e., italic). This is possible by using the equation delimiter `$...$` inside `ce()`. Note that in the second example the `=` between the reactants and products is rendered as a reaction arrow, not as a literal equals sign.

## Further Examples

`ce` is a function that takes string input and returns a content block. As such, it can interact with the same rules as other content blocks in math mode. When stacking several equations with a line break `\`, an ampersand `&` inside the string marks the column on which the lines are aligned, exactly as `&` works in ordinary Typst math.

```typ
Example to calculate $K_a$:
$
K_a = (#h(1.3em) [#ce("H+")] overbrace(#ce("[A-]"), "conjugate acid"))/ underbrace(#ce("[HA]"), "acid")
$
Using `ce` in limit text:
$
lim_#ce("[H+]->#sym.infinity") K_a = #sym.infinity
$
Aligning multiple equations:
$
#ce("H2SO4 (aq) &<-> H+ (aq) + HSO4^- (aq)")\
#ce("H+ (aq) + HSO4^- (aq) &<-> H2SO4 (aq)")
$
```

## Appendix

### Under the Hood

This package works by parsing the provided simple text input and converting it into Typst equation input. In general, inserting whitespace will reset the parser's state machine. If there is still some strange behavior, the underlying Typst output can be inspected by setting the debug flag:

```typ
#ce("H2(aq)", debug: true)
```
