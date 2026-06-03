# `unify` (Typst package) reference

> A complete, self-contained reference for the Typst package **`unify`** (version **0.8.1**), intended to be fed to an LLM so it can write correct `unify` code. English data only.

`unify` simplifies typesetting of **numbers**, **units**, and **ranges** in Typst. It is the rough equivalent of LaTeX's `siunitx`. It supports physical units, monetary units, and binary (data) units.

- Author: Christopher Hecker
- License: MIT
- Version documented here: 0.8.1
- Repository: https://github.com/ChHecker/unify
- Universe page: https://typst.app/universe/package/unify

---

## 1. Installation and import

```typ
// Import only the most-used functions:
#import "@preview/unify:0.8.1": num, qty, numrange, qtyrange

// Or import everything (also gives `unit`, `add-unit`, `add-prefix`):
#import "@preview/unify:0.8.1": *
```

Exported functions: `num`, `unit`, `qty`, `numrange`, `qtyrange`, `add-unit`, `add-prefix`.

---

## 2. How it works (read this first)

1. Every function returns **math content**. Internally `unify` builds a math string, wraps it in `$...$`, and `eval`s it. You can call the functions inside or outside math mode; the output is always math.
2. Numbers are given as **strings** and parsed (so you control the exact digits, uncertainties, and exponent).
3. Units are given as **strings** in one of two notations (written-out words, or shorthand symbols), and looked up in built-in tables.
4. Because the result is evaluated in **math mode**, you cannot use a plain space `" "` as a thousands separator. Use the string `"space"` instead, or a math spacing command like `"#h(...)"`.
5. Spacing arguments accept Typst math expressions as strings, e.g. `"#h(2mm)"`, `"dot"`, `"space"`, or the default thin space `"#h(0.166667em)"`.

Minimal examples:

```typ
$ num("-1.32865+-0.50273e-6") $
$ qty("1.3+1.2-0.3e3", "erg/cm^2/s", space: "#h(2mm)") $
$ numrange("1,1238e-2", "3,0868e5", thousandsep: "'") $
$ qtyrange("1e3", "2e3", "meter per second squared", per: "/", delimiter: "\"to\"") $
$ qty("55.36", "usd") $
```

---

## 3. Number syntax (used by `num`, `qty`, `numrange`, `qtyrange`)

A number string may contain, in order:

1. A `float` or `integer` value. The decimal separator may be `.` **or** `,` (both are accepted; `unify` auto-detects which one you used).
2. Optionally an uncertainty, in one of these forms (where `{}` is a number):
   - Symmetric: `+-{}` or `±{}` , e.g. `1.5+-0.2` renders as `1.5 ± 0.2`.
   - Asymmetric: `+{}-{}` , e.g. `1.5+0.3-0.2` renders with a superscript `+0.3` and subscript `-0.2`.
3. Optionally exponential notation: `e{}` or `E{}` , e.g. `1.3e-6`.

Behavior notes:
- Parentheses `()` are added automatically around the value when an uncertainty is present.
- Spaces inside the number string are stripped, and a Unicode minus is normalized to ASCII `-`.
- An invalid number string raises an assertion error (`invalid number: ...`).

Spacing/quirk of thousands grouping (from the implementation):
- The thousands separator is only inserted when the **integer part has 6 or more digits** (grouped in threes). For example `12345` is left ungrouped, while `123456` becomes `123 456`.
- The decimal part is grouped only when it has **5 or more digits**.

---

## 4. Unit syntax (used by `unit`, `qty`, `qtyrange`)

A unit string can be written in **two notations**. `unify` first tries to parse the whole string as written-out words; if any token is not recognized as a keyword/prefix/unit, it re-parses the **entire string** using the shorthand (symbolic) notation.

### 4.1 Written-out notation (space-separated words)

Tokens are separated by spaces. Each unit can have up to four parts:

| Part    | Meaning                                         | Example                                                       |
| ------- | ----------------------------------------------- | ------------------------------------------------------------- |
| `per`   | Inverts the unit that follows it                | `meter per second`                                            |
| prefix  | A written-out SI prefix, placed before the unit | `centi` in `centimeter` (write `centi meter` or `centimeter`) |
| unit    | The written-out unit name                       | `gram`, `meter`, `second`                                     |
| postfix | A power applied after the unit (respects `per`) | `squared`, `cubed`                                            |

Examples:
```typ
$ unit("meter per second squared") $   // m s^(-2)  (with default per: "symbol")
$ unit("kilo gram") $                  // kg
$ unit("centimeter") $                 // cm
```

Notes:
- Written-out input is lowercased before lookup, so case does not matter for words.
- A prefix and unit may be written together (`centimeter`) or separated (`centi meter`); both work as long as the combined token resolves.
- For micro, the written-out word is `micro`.

### 4.2 Shorthand (symbolic) notation

Tokens are separated by spaces; `/` introduces an inverse unit; `^` introduces an exponent. Each unit has up to four parts:

| Part         | Meaning                                       | Example       |
| ------------ | --------------------------------------------- | ------------- |
| `/`          | Inverts the unit that follows it              | `m/s`         |
| prefix       | A short SI prefix, placed before the unit     | `k` in `kg`   |
| unit         | The short unit symbol                         | `g`, `m`, `s` |
| `^` exponent | A power applied after the unit (respects `/`) | `m^2`, `s^-1` |

Examples:
```typ
$ unit("kg") $          // kg
$ unit("m/s^2") $       // m s^(-2)  (default per)
$ unit("erg/cm^2/s") $  // erg cm^(-2) s^(-1)
```

Notes:
- Use `u` for the micro prefix (e.g. `um` = micrometer).
- Unicode superscripts (such as `m²`) are accepted and converted to `^2` automatically.
- Shorthand resolution checks whether the token is a **full unit symbol first**; only if that fails does it try **prefix + unit**. So `cd` is read as the unit candela, not centi+day.

### 4.3 The `per` option (how inverses are rendered)

The `per` argument controls how units after `per` / `/` are displayed. Valid values:

| Value(s)                                           | Result                                               |
| -------------------------------------------------- | ---------------------------------------------------- |
| `"symbol"` (default)                               | Negative exponents, e.g. `m s^(-1)`                  |
| `"fraction"` or `"/"`                              | A built-up fraction, e.g. numerator over denominator |
| `"fraction-short"`, `"short-fraction"`, or `"\\/"` | An inline slashed fraction, e.g. `m\/s`              |

(When writing the inline-fraction value in Typst source, escape the backslash: `per: "\\/"`.)

### 4.4 Raw units

If you set `rawunit: true` (available in `qty` and `qtyrange`), the unit string is **not** looked up; it is passed through and `eval`ed as math directly. Because it goes through `eval`, escape inner quotes as `\"` when needed.

```typ
$ qty("3.5", "upright(\"widgets\")", rawunit: true) $
```

---

## 5. Function reference

All spacing defaults shown are the literal default argument values. The thin space `#h(0.166667em)` is roughly a math thin space.

### 5.1 `num(value, multiplier: "dot", thousandsep: "#h(0.166667em)")`

Formats a single number.

| Argument      | Default            | Description                                                                          |
| ------------- | ------------------ | ------------------------------------------------------------------------------------ |
| `value`       | (required)         | String with the number (see Section 3). Non-strings are converted to string.         |
| `multiplier`  | `"dot"`            | Math symbol placed between the mantissa and `10^exp`. Use `"times"` for a cross.     |
| `thousandsep` | `"#h(0.166667em)"` | Separator between thousands. Use `"space"` for a normal space; do **not** use `" "`. |

```typ
$ num("1.5") $
$ num("1.5+-0.3") $
$ num("1.5+0.3-0.2") $
$ num("6.022e23") $
$ num("123456", thousandsep: "'") $   // 123'456
$ num("3e8", multiplier: "times") $
```

### 5.2 `unit(unit, space: "#h(0.166667em)", per: "symbol")`

Formats a unit by itself (no number).

| Argument | Default            | Description                               |
| -------- | ------------------ | ----------------------------------------- |
| `unit`   | (required)         | String with the unit (see Section 4).     |
| `space`  | `"#h(0.166667em)"` | Space inserted between consecutive units. |
| `per`    | `"symbol"`         | How inverses render (see Section 4.3).    |

```typ
$ unit("kg") $
$ unit("meter per second squared") $
$ unit("J/(mol K)") $
$ unit("m/s", per: "fraction") $
```

### 5.3 `qty(value, unit, rawunit: false, space: "#h(0.166667em)", num-unit-space: "#h(0.166667em)", multiplier: "dot", thousandsep: "#h(0.166667em)", per: "symbol")`

Formats a quantity: a number followed by a unit.

| Argument         | Default            | Description                                                             |
| ---------------- | ------------------ | ----------------------------------------------------------------------- |
| `value`          | (required)         | Number string (see Section 3).                                          |
| `unit`           | (required)         | Unit string (see Section 4).                                            |
| `rawunit`        | `false`            | If `true`, pass the unit through to `eval` unchanged (see Section 4.4). |
| `space`          | `"#h(0.166667em)"` | Space between consecutive units.                                        |
| `num-unit-space` | `"#h(0.166667em)"` | Space between the number and the unit.                                  |
| `multiplier`     | `"dot"`            | Symbol between mantissa and exponent.                                   |
| `thousandsep`    | `"#h(0.166667em)"` | Thousands separator (use `"space"`, not `" "`).                         |
| `per`            | `"symbol"`         | How inverses render.                                                    |

```typ
$ qty("9.81", "m/s^2") $
$ qty("1.3+1.2-0.3e3", "erg/cm^2/s", space: "#h(2mm)") $
$ qty("55.36", "usd") $
$ qty("100", "kilometer per hour", per: "/") $
$ qty("3.5", "GiB") $
```

### 5.4 `numrange(lower, upper, multiplier: "dot", delimiter: "-", space: "#h(0.16667em)", thousandsep: "#h(0.166667em)")`

Formats a numeric range. If both numbers share the same exponent, that exponent is **factored out** and the range is wrapped in parentheses.

| Argument      | Default            | Description                                     |
| ------------- | ------------------ | ----------------------------------------------- |
| `lower`       | (required)         | First number string.                            |
| `upper`       | (required)         | Second number string.                           |
| `multiplier`  | `"dot"`            | Symbol between mantissa and exponent.           |
| `delimiter`   | `"-"`              | Symbol placed between the two numbers.          |
| `space`       | `"#h(0.16667em)"`  | Space between the numbers and the delimiter.    |
| `thousandsep` | `"#h(0.166667em)"` | Thousands separator (use `"space"`, not `" "`). |

```typ
$ numrange("10", "20") $
$ numrange("1e3", "5e3") $                       // shared exponent gets factored
$ numrange("1,1238e-2", "3,0868e5", thousandsep: "'") $
$ numrange("5", "10", delimiter: "\"to\"") $
```

To use a word like "to" as the delimiter, pass it as a quoted math string: `delimiter: "\"to\""`.

### 5.5 `qtyrange(lower, upper, unit, rawunit: false, multiplier: "dot", delimiter: "-", space: "", unitspace: "#h(0.16667em)", range-unit-space: "#h(0.166667em)", thousandsep: "#h(0.166667em)", per: "symbol")`

Formats a range with a unit (a combination of `numrange` and `unit`). The range is always wrapped in parentheses.

| Argument           | Default            | Description                                                             |
| ------------------ | ------------------ | ----------------------------------------------------------------------- |
| `lower`            | (required)         | First number string.                                                    |
| `upper`            | (required)         | Second number string.                                                   |
| `unit`             | (required)         | Unit string.                                                            |
| `rawunit`          | `false`            | If `true`, pass the unit through unchanged.                             |
| `multiplier`       | `"dot"`            | Symbol between mantissa and exponent.                                   |
| `delimiter`        | `"-"`              | Symbol between the two numbers.                                         |
| `space`            | `""`               | Space between the numbers and the delimiter.                            |
| `unitspace`        | `"#h(0.16667em)"`  | Space between consecutive units (same role as `space` in `unit`/`qty`). |
| `range-unit-space` | `"#h(0.166667em)"` | Space between the range (or exponent) and the units.                    |
| `thousandsep`      | `"#h(0.166667em)"` | Thousands separator (use `"space"`, not `" "`).                         |
| `per`              | `"symbol"`         | How inverses render.                                                    |

```typ
$ qtyrange("10", "20", "kg") $
$ qtyrange("1e3", "2e3", "meter per second squared", per: "/", delimiter: "\"to\"") $
$ qtyrange("100", "200", "km/h", range-unit-space: "#h(3mm)") $
```

### 5.6 `add-prefix(prefix, shorthand, symbol)`

Registers a new prefix **at runtime** (added to the current language database for the rest of the document).

| Argument    | Description                                                                               |
| ----------- | ----------------------------------------------------------------------------------------- |
| `prefix`    | Full written-out name (e.g. `"pre"`).                                                     |
| `shorthand` | Short symbol (e.g. `"P"`).                                                                |
| `symbol`    | Typst math expression string inserted as the rendered symbol (e.g. `"upright(\"pre\")"`). |

```typ
#add-prefix("pre", "P", "upright(\"pre\")")
```

### 5.7 `add-unit(unit, shorthand, symbol, space: true)`

Registers a new unit **at runtime**.

| Argument    | Default    | Description                                                                     |
| ----------- | ---------- | ------------------------------------------------------------------------------- |
| `unit`      | (required) | Full written-out name (e.g. `"unit"`).                                          |
| `shorthand` | (required) | Short symbol (e.g. `"U"`).                                                      |
| `symbol`    | (required) | Typst math expression string for the rendered symbol (e.g. `"bold(\"unit\")"`). |
| `space`     | `true`     | Whether a space is inserted before this unit.                                   |

```typ
#add-prefix("pre", "P", "upright(\"pre\")")
#add-unit("unit", "U", "bold(\"unit\")")
$ unit("PU") $   // renders the custom prefix + custom unit
```

To add units or prefixes **permanently**, edit the CSV files in the package's library directory (`prefixes-en.csv`, `units-en.csv`, `postfixes.csv`); see Section 7.

---

## 6. Built-in data tables (English)

The "Typst symbol" column is the exact math expression `unify` inserts. The "Space before" column (units only) says whether a space is placed before the unit; this is `false` for angle units so that, for example, `90 deg` renders as `90°` with no gap.

### 6.1 SI (decimal) prefixes

| Prefix (written-out) | Shorthand | Typst symbol  |
| -------------------- | --------- | ------------- |
| quecto               | q         | upright("q")  |
| ronto                | r         | upright("r")  |
| yocto                | y         | upright("y")  |
| zepto                | z         | upright("z")  |
| atto                 | a         | upright("a")  |
| femto                | f         | upright("f")  |
| pico                 | p         | upright("p")  |
| nano                 | n         | upright("n")  |
| micro                | u         | upright("µ")  |
| milli                | m         | upright("m")  |
| centi                | c         | upright("c")  |
| deci                 | d         | upright("d")  |
| deca                 | da        | upright("da") |
| hecto                | h         | upright("h")  |
| kilo                 | k         | upright("k")  |
| mega                 | M         | upright("M")  |
| giga                 | G         | upright("G")  |
| tera                 | T         | upright("T")  |
| peta                 | P         | upright("P")  |
| exa                  | E         | upright("E")  |
| zeta                 | Z         | upright("Z")  |
| yotta                | Y         | upright("Y")  |
| ronna                | R         | upright("R")  |
| quetta               | Q         | upright("Q")  |

(Note: the written-out name for the `Z` prefix in the data file is `zeta`, not the SI spelling "zetta".)

### 6.2 Binary (IEC) prefixes

| Prefix (written-out) | Shorthand | Typst symbol  |
| -------------------- | --------- | ------------- |
| kibi                 | Ki        | upright("Ki") |
| mebi                 | Mi        | upright("Mi") |
| gibi                 | Gi        | upright("Gi") |
| tebi                 | Ti        | upright("Ti") |
| pebi                 | Pi        | upright("Pi") |
| exbi                 | Ei        | upright("Ei") |
| zebi                 | Zi        | upright("Zi") |
| yobi                 | Yi        | upright("Yi") |

### 6.3 Postfixes (written-out exponents)

Used only in the **written-out** unit notation; they map to the exponent shown.

| Postfix | Exponent |
| ------- | -------- |
| squared | 2        |
| cubed   | 3        |
| fourth  | 4        |
| fifth   | 5        |
| sixth   | 6        |
| seventh | 7        |
| eighth  | 8        |
| ninth   | 9        |
| tenth   | 10       |

### 6.4 Physical and other units

Grouped by domain for readability. "Renders as" is the displayed glyph.

**Length**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| meter              | m         | upright("m")  | m          | true         |
| metre              | m         | upright("m")  | m          | true         |
| lightyear          | ly        | upright("ly") | ly         | true         |
| parsec             | pc        | upright("pc") | pc         | true         |
| astronomicalunit   | au        | upright("au") | au         | true         |
| angstrom           | A         | upright("Å")  | Å          | true         |

**Area and volume**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| hectare            | ha        | upright("ha") | ha         | true         |
| barn               | b         | upright("b")  | b          | true         |
| litre              | l         | upright("l")  | l          | true         |
| liter              | L         | upright("L")  | L          | true         |

**Time**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| second             | s         | upright("s")   | s          | true         |
| minute             | min       | upright("min") | min        | true         |
| hour               | h         | upright("h")   | h          | true         |
| day                | d         | upright("d")   | d          | true         |
| year               | a         | upright("a")   | a          | true         |
| year               | yr        | upright("yr")  | yr         | true         |

**Frequency and speed**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| hertz              | Hz        | upright("Hz") | Hz         | true         |
| speedoflight       | c         | c             | c          | true         |

**Mass**

| Unit (written-out) | Shorthand | Typst symbol | Renders as | Space before |
| ------------------ | --------- | ------------ | ---------- | ------------ |
| gram               | g         | upright("g") | g          | true         |
| ton                | t         | upright("t") | t          | true         |
| tonne              | t         | upright("t") | t          | true         |
| atomicmassunit     | u         | upright("u") | u          | true         |

**Force**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| newton             | N         | upright("N")   | N          | true         |
| dyne               | dyn       | upright("dyn") | dyn        | true         |

**Pressure**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| pascal             | Pa        | upright("Pa")  | Pa         | true         |
| atmosphere         | atm       | upright("atm") | atm        | true         |
| bar                | bar       | upright("bar") | bar        | true         |

**Energy**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| joule              | J         | upright("J")   | J          | true         |
| erg                | erg       | upright("erg") | erg        | true         |
| electronvolt       | eV        | upright("eV")  | eV         | true         |
| calorie            | cal       | upright("cal") | cal        | true         |

**Power**

| Unit (written-out) | Shorthand | Typst symbol | Renders as | Space before |
| ------------------ | --------- | ------------ | ---------- | ------------ |
| watt               | W         | upright("W") | W          | true         |

**Electrical**

| Unit (written-out) | Shorthand | Typst symbol | Renders as | Space before |
| ------------------ | --------- | ------------ | ---------- | ------------ |
| ampere             | A         | upright("A") | A          | true         |
| volt               | V         | upright("V") | V          | true         |
| ohm                | O         | upright("Ω") | Ω          | true         |
| siemens            | S         | upright("S") | S          | true         |
| coulomb            | C         | upright("C") | C          | true         |
| farad              | F         | upright("F") | F          | true         |

**Magnetic**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| tesla              | T         | upright("T")  | T          | true         |
| gauss              | G         | upright("G")  | G          | true         |
| henry              | H         | upright("H")  | H          | true         |
| weber              | Wb        | upright("Wb") | Wb         | true         |

**Temperature**

| Unit (written-out) | Shorthand | Typst symbol      | Renders as | Space before |
| ------------------ | --------- | ----------------- | ---------- | ------------ |
| kelvin             | K         | upright("K")      | K          | true         |
| celsius            | dC        | upright(degree C) | °C         | true         |
| fahrenheit         | dF        | upright(degree F) | °F         | true         |

**Light**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| candela            | cd        | upright("cd") | cd         | true         |
| lumen              | lm        | upright("lm") | lm         | true         |
| lux                | lx        | upright("lx") | lx         | true         |

**Angle**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| degree             | deg       | degree         | °          | false        |
| radian             | r         | upright("rad") | rad        | true         |
| radian             | rad       | upright("rad") | rad        | true         |
| arcminute          | '         | '              | ′          | false        |
| arcsecond          | \"        | ″              | ″          | false        |
| steradian          | sr        | upright("sr")  | sr         | true         |

(The arcsecond shorthand is a double-quote character; in a shorthand string you write it escaped, e.g. `"5\""`.)

**Amount of substance**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| mole               | mol       | upright("mol") | mol        | true         |
| molar              | M         | upright("M")   | M          | true         |

**Radioactivity and dose**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| becquerel          | Bq        | upright("Bq") | Bq         | true         |
| gray               | Gy        | upright("Gy") | Gy         | true         |
| sievert            | Sv        | upright("Sv") | Sv         | true         |

**Ratios and logarithmic units**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| percent            | %         | percent       | %          | true         |
| decibel            | dB        | upright("dB") | dB         | true         |
| neper              | Np        | upright("Np") | Np         | true         |

**Catalytic activity**

| Unit (written-out) | Shorthand | Typst symbol   | Renders as | Space before |
| ------------------ | --------- | -------------- | ---------- | ------------ |
| katal              | kat       | upright("kat") | kat        | true         |

**Data (binary) units**

| Unit (written-out) | Shorthand | Typst symbol  | Renders as | Space before |
| ------------------ | --------- | ------------- | ---------- | ------------ |
| byte               | B         | upright("B")  | B          | true         |
| bit                | b         | upright("b")  | b          | true         |
| baud               | Bd        | upright("Bd") | Bd         | true         |

### 6.5 Monetary units

These are added to the unit set automatically, so they work in `unit`, `qty`, and `qtyrange`.

| Currency (written-out) | Shorthand | Typst symbol | Renders as     | Space before |
| ---------------------- | --------- | ------------ | -------------- | ------------ |
| bitcoin                | btc       | bitcoin      | ₿              | true         |
| dollar                 | usd       | dollar       | $              | true         |
| euro                   | eur       | euro         | €              | true         |
| franc                  | fr        | franc        | (franc symbol) | true         |
| lira                   | try       | lira         | (lira symbol)  | true         |
| peso                   | peso      | peso         | (peso symbol)  | true         |
| pound                  | gbp       | pound        | £              | true         |
| ruble                  | rub       | ruble        | ₽              | true         |
| rupee                  | inr       | rupee        | ₹              | true         |
| won                    | krw       | won          | ₩              | true         |
| yen                    | jpy       | yen          | ¥              | true         |

```typ
$ qty("55.36", "usd") $     // 55.36 $
$ qty("1000", "jpy") $      // 1000 ¥
$ qty("0.5", "btc") $       // 0.5 ₿
```

---

## 7. Adding units and prefixes permanently (CSV files)

The lookup tables are loaded from CSV files in the package library directory. Edit them to add entries permanently.

- `prefixes-en.csv` and `units-en.csv`: English prefixes and units.
- `postfixes.csv`: written-out exponents (shared across languages).
- `money.csv`: monetary units (merged into the unit set).

CSV formats:

**Prefix file** (`name, shorthand, symbol`):
```
milli,m,upright("m")
```

**Postfix file** (`name, exponent`):
```
squared,2
```

**Unit / money file** (`name, shorthand, symbol, space`):
```
meter,m,upright("m"),true
```

Column meanings:
- Column 1: written-out word (must be unique; looked up case-insensitively).
- Column 2: shorthand symbol (should be unique).
- Column 3: the Typst math expression inserted as the rendered symbol.
- Column 4 (units only): whether a space precedes the unit. Accepts `true`/`false` or `1`/`0`.

---

## 8. Notes, quirks, and gotchas

- **Output is math content.** Wrap calls in `$...$` (or call them where math content is expected). Spacing arguments are math expressions given as strings.
- **No plain-space thousands separator.** Use `thousandsep: "space"` or `thousandsep: "#h(...)"`, never `thousandsep: " "`.
- **Decimal separator.** Both `.` and `,` are accepted in number strings and auto-detected.
- **Thousands grouping threshold.** Grouping appears only for integer parts of 6+ digits and decimal parts of 5+ digits.
- **Notation fallback.** If the written-out parse encounters any unrecognized token, the whole string is re-parsed as shorthand. Mixing the two notations in one string is therefore unreliable; pick one.
- **Shorthand collisions.** Some shorthands are shared, and for shorthand (symbolic) input the **last definition wins**. In particular: `A` resolves to ampere (not angstrom), `b` resolves to bit (not barn), `T` resolves to tesla. To get the shadowed unit, use its written-out name (`angstrom`, `barn`) or its distinct value via `add-unit`.
- **Written-out `year`.** The written-out word `year` renders the `yr` symbol. Use the shorthand `a` if you specifically want the `a` glyph.
- **Prefix vs unit shorthands.** A shorthand token is first checked as a full unit; only then as prefix + unit. So `cd` is candela, while `ms` is milli + second.
- **Micro.** Written-out: `micro`. Shorthand: `u`.
- **Raw units** (`rawunit: true`) bypass all lookups and are `eval`ed directly; escape inner quotes as `\"`.
- **Runtime additions** via `add-unit` / `add-prefix` apply from that point in the document onward; CSV edits apply globally.

---

## 9. Language note

`unify` supports multiple languages and selects the table set from `text.lang`. This reference documents the **English** data only (the default and fallback). If `text.lang` is set to a language without its own tables, `unify` falls back to English.

---

## 10. Cheat sheet

```typ
#import "@preview/unify:0.8.1": *

$ num("3.14159") $
$ num("2.5+-0.1") $
$ num("1.2+0.3-0.2") $
$ num("6.022e23") $

$ unit("kg") $
$ unit("m/s^2") $
$ unit("meter per second squared") $
$ unit("J/(mol K)", per: "fraction") $

$ qty("9.81", "m/s^2") $
$ qty("55.36", "usd") $
$ qty("1.3+1.2-0.3e3", "erg/cm^2/s", space: "#h(2mm)") $

$ numrange("10", "20") $
$ numrange("1e3", "5e3") $

$ qtyrange("10", "20", "kg") $
$ qtyrange("1e3", "2e3", "m/s^2", per: "/", delimiter: "\"to\"") $

#add-prefix("pre", "P", "upright(\"pre\")")
#add-unit("unit", "U", "bold(\"unit\")")
$ unit("PU") $
```
