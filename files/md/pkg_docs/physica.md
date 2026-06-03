# physica package: a LaTeX-to-Typst conversion reference

This file teaches an agent to convert LaTeX math into Typst math that uses the `physica` package (version 0.9.8). The agent reads raw text, not rendered Markdown, so this file uses no tables and no escaped characters: every pipe `|`, backslash, and brace appears literally as it should be read.

Each reference entry has the same three lines:

- `latex:` one or more LaTeX forms a user might send. Several different LaTeX strings often map to the same physica output; they are all listed so the agent recognizes any of them.
- `physica:` the Typst + physica code to emit. This is the answer.
- `renders:` a short description of the visual result, given only where the layout is not obvious from the LaTeX.

Important: the strings on the `latex:` lines describe the *input* to recognize. Never emit them as output. The output is always the `physica:` line, wrapped in math mode.

---

## Translation contract (read this first)

These rules apply to the whole conversion, not to any single symbol.

1. Wrap every result in math mode. Use `$...$` with no surrounding spaces for inline math, and `$ ... $` with surrounding spaces for display (block) math. The auto-sizing of bra-kets, large derivatives, and tall delimiters only works in display math, so prefer `$ ... $` for anything with fractions or brackets inside delimiters.

2. Greek letters and most named symbols are the LaTeX name without the backslash: `\alpha` becomes `alpha`, `\Gamma` becomes `Gamma`, `\phi` becomes `phi`, `\varphi` becomes `phi.alt`, `\infty` becomes `oo`, `\partial` becomes `partial`, `\nabla` becomes `nabla`.

3. Subscripts and superscripts keep the same `_` and `^`, but multi-token scripts must be parenthesized in Typst: `x_i` stays `x_i`, but `x^{2k}` becomes `x^(2k)` and `T_{ij}` becomes `T_(i j)`.

4. Fractions: `\frac{a}{b}` becomes `frac(a, b)`, or `a/b` for simple cases.

5. Plain function names and operators drop the backslash: `\sin \cos \tan \log \exp \ln \det` become `sin cos tan log exp ln det`. `\int` becomes `integral`, `\sum` becomes `sum`, `\prod` becomes `product`, `\cdot` becomes `dot`, `\times` becomes `times`, `\pm` becomes `plus.minus`.

6. When a `physica` function matches the construct, prefer it over hand-built equivalents. Producing the physica form is the entire purpose of the conversion.

7. Pass-through rule: if a LaTeX construct has no physica function and no special Typst form, convert it to the nearest plain Typst math and leave it. Do not invent physica function names that are not in this file.

8. Disambiguation that matters (details in the entries below):
   - `\vec{a}` becomes `va(a)` (arrow, not bold). `\mathbf{a}` or `\boldsymbol{a}` becomes `vb(a)` (bold). `\hat{\mathbf{a}}` becomes `vu(a)` (bold with hat). A plain non-bold `\hat{a}` stays `hat(a)`, the Typst built-in, not `vu`.
   - A transpose `^T` or `^\top` needs the show rule enabled (see "transpose" below). If you cannot rely on the show rule, emit the explicit glyph `TT`: `A^\top` becomes `A^TT`.
   - A conjugate transpose `^\dagger` becomes `^dagger`, or `^+` if the dagger show rule is enabled.

---

## Worked end-to-end examples

These show whole expressions converted, so the agent sees how the pieces combine.

1. Partial derivative
   - latex: `\frac{\partial f}{\partial x}`
   - physica: `$ pdv(f, x) $`

2. Mixed second-order partial derivative
   - latex: `\frac{\partial^2 f}{\partial x \, \partial y}`
   - physica: `$ pdv(f, x, y) $`
   - renders: total order 2 is computed automatically from two order-1 variables.

3. Maxwell-Ampere law
   - latex: `\nabla \times \mathbf{B} = \mu_0 \mathbf{J}`
   - physica: `$ curl vb(B) = mu_0 vb(J) $`

4. Expectation value of a Hamiltonian
   - latex: `\langle \psi | \hat{H} | \psi \rangle`
   - physica: `$ expval(hat(H), psi) $`
   - renders: angle-bracket form with psi on both sides. Equivalent long form: `braket(psi, hat(H), psi)`.

5. Time-dependent Schrodinger equation
   - latex: `i\hbar \frac{\partial}{\partial t}\psi = -\frac{\hbar^2}{2m}\nabla^2\psi`
   - physica: `$ i hbar pdv(, t) psi = -frac(hbar^2, 2m) laplacian psi $`
   - renders: note the empty first argument in `pdv(, t)` gives the bare operator with no function in the numerator.

6. Transpose identity (requires the show rule)
   - latex: `(AB)^T = B^T A^T`
   - physica:

     ```typst
     #show: super-T-as-transpose
     $ (A B)^T = B^T A^T $
     ```

   - renders: each `^T` becomes a proper transpose marker. Without the show rule, write `(A B)^TT = B^TT A^TT`.

7. Three vector decorations at once
   - latex: `\vec{r}, \ \mathbf{a}, \ \hat{n}`
   - physica: `$ va(r), vb(a), vu(n) $`
   - renders: r with an arrow (not bold), bold a, bold n with a hat.

8. Determinant of a 2x2 matrix
   - latex: `\begin{vmatrix} 1 & x \\ 1 & y \end{vmatrix}`
   - physica: `$ mdet(1, x; 1, y) $`
   - renders: rows separated by `;`, entries by `,`, wrapped in vertical determinant bars.

---

## Reference: braces and delimited notations

### absolute value (Typst built-in)

- latex: `|x|`, `\left| x \right|`, `\lvert x \rvert`
- physica: `abs(x)`
- renders: x between single vertical bars.

### norm (Typst built-in)

- latex: `\|x\|`, `\lVert x \rVert`, `\left\| x \right\|`
- physica: `norm(x)`
- renders: x between double vertical bars.

### big-O

- latex: `O(x^2)`, `\mathcal{O}(x^2)`, `\mathrm{O}(x^2)`
- physica: `Order(x^2)`
- renders: capital O followed by (x^2).

### small-o

- latex: `o(1)`, `\mathrm{o}(1)`
- physica: `order(1)`
- renders: lowercase o followed by (1).

### set-builder

- latex: `\{ a_i \mid \forall i \}`, `\left\{ a_i : \forall i \right\}`
- physica: `Set(a_i; forall i)`
- renders: braces around "a_i | forall i"; the `;` becomes the dividing bar. Use capital `Set`; lowercase `set` is a Typst keyword. With no condition, `Set(a_n)` gives just { a_n }.

### evaluation bar

- latex: `\left. f(x) \right|_{0}^{\infty}`
- physica: `eval(f(x))_0^oo`
- renders: f(x) followed by a tall vertical bar carrying the lower bound 0 and upper bound infinity. The bounds are attached outside as ordinary `_` and `^`. Long name: `evaluated(...)`.

### expectation value (plain)

- latex: `\langle u \rangle`
- physica: `expval(u)`
- renders: u inside angle brackets. See also the Dirac section, where `expval` takes two arguments.

---

## Reference: vectors and vector calculus

### column vector (Typst built-in)

- latex: `\begin{pmatrix} 1 \\ 2 \end{pmatrix}`, `\binom{1}{2}` (when meant as a column vector)
- physica: `vec(1, 2)`

### row vector

- latex: `\begin{pmatrix} \alpha & b \end{pmatrix}`, `(\alpha \ \ b)`
- physica: `vecrow(alpha, b)`
- renders: alpha and b side by side in parentheses. Change the bracket with `delim:`, e.g. `vecrow(alpha, b, delim:"[")`.

### transpose glyph

- latex: `v^T`, `v^\top`, `v^\intercal`, `A^{\mathsf{T}}`
- physica: `v^TT`, `A^TT`
- renders: a transpose marker in the superscript. If the `super-T-as-transpose` show rule is enabled you may instead write `v^T` directly and it becomes a transpose. Use `TT` when you cannot rely on the show rule.

### bold vector

- latex: `\mathbf{a}`, `\boldsymbol{a}`, `\vb{a}`, `\mathbf{\mu}_1`
- physica: `vb(a)`, `vb(mu_1)`
- renders: upright bold symbol. Long name: `vectorbold(...)`.

### unit vector

- latex: `\hat{\mathbf{a}}`, `\vu{a}`, `\uvec{a}`, `\hat{\boldsymbol{a}}`
- physica: `vu(a)`
- renders: bold symbol with a hat. Long name: `vectorunit(...)`. A plain `\hat{a}` that is not bold should become `hat(a)` instead.

### arrow vector

- latex: `\vec{a}`, `\va{a}`, `\overrightarrow{a}`
- physica: `va(a)`
- renders: symbol with an over-arrow, not bold (per ISO 80000-2:2019). Long name: `vectorarrow(...)`.

### gradient

- latex: `\nabla f`, `\grad f`, `\operatorname{grad} f`
- physica: `grad f`
- renders: nabla followed by f.

### divergence

- latex: `\nabla \cdot \mathbf{E}`, `\div \mathbf{E}`, `\operatorname{div} \mathbf{E}`
- physica: `div vb(E)`
- renders: nabla dot E.

### curl

- latex: `\nabla \times \mathbf{B}`, `\curl \mathbf{B}`, `\operatorname{curl} \mathbf{B}`
- physica: `curl vb(B)`
- renders: nabla cross B.

### Laplacian

- latex: `\nabla^2 u`, `\Delta u` (when meaning the Laplacian), `\laplacian u`
- physica: `laplacian u`
- renders: nabla squared, then u. This is the Laplacian; do not confuse it with the Typst built-in `laplace`, which is the script-L transform symbol.

### dot product

- latex: `a \cdot b`, `\vb{a} \cdot \vb{b}`
- physica: `a dprod b`
- renders: a, a centered dot, b. Long name: `dotproduct`.

### cross product

- latex: `a \times b`
- physica: `a cprod b`
- renders: a, a cross, b. Long name: `crossproduct`.

### inner product

- latex: `\langle u, v \rangle`, `\langle u | v \rangle` (when meaning an inner product rather than a bra-ket)
- physica: `iprod(u, v)`
- renders: u and v separated by a comma inside angle brackets. Long name: `innerproduct`.

---

## Reference: matrices

All matrix builders below accept `delim:` to change the outer bracket (for example `delim:"["` for square brackets, `delim:"|"` for vertical bars; default is round parentheses). The fillable builders also accept `fill:` to set the off-structure cell content, commonly `fill:0`, `fill:dot`, or `fill:*`.

### general matrix (Typst built-in)

- latex: `\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}`, `\begin{bmatrix} ... \end{bmatrix}`
- physica: `mat(1, 2; 3, 4)`
- renders: rows separated by `;`, entries by `,`. Use `mat(..., delim:"[")` for the bracket form.

### determinant

- latex: `\begin{vmatrix} 1 & x \\ 1 & y \end{vmatrix}`, `\det\begin{pmatrix} 1 & x \\ 1 & y \end{pmatrix}`
- physica: `mdet(1, x; 1, y)`
- renders: same content as `mat`, wrapped in vertical determinant bars. Long name: `matrixdet`.

### diagonal matrix

- latex: `\operatorname{diag}(1, 2)`, `\begin{pmatrix} 1 & 0 \\ 0 & 2 \end{pmatrix}`
- physica: `dmat(1, 2)`
- renders: the given entries on the main diagonal, zeros (or `fill:`) elsewhere. Example with options: `dmat(1, a, xi, delim:"[", fill:0)`. Long name: `diagonalmatrix`.

### anti-diagonal matrix

- latex: `\begin{pmatrix} 0 & 1 \\ 2 & 0 \end{pmatrix}` (entries on the anti-diagonal)
- physica: `admat(1, 2)`
- renders: the given entries on the anti-diagonal, from top-right to bottom-left. Example: `admat(1, a, xi, delim:"[", fill:dot)`. Long name: `antidiagonalmatrix`.

### identity matrix

- latex: `I_2`, `\mathbb{1}_2`, `\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}`
- physica: `imat(2)`
- renders: the 2x2 identity. Example: `imat(3, delim:"[", fill:*)`. Long name: `identitymatrix`.

### zero matrix

- latex: `\mathbf{0}_2`, `O_2`, a matrix of all zeros
- physica: `zmat(2)`
- renders: the 2x2 zero matrix. Example: `zmat(3, delim:"[")`. Long name: `zeromatrix`.

### Jacobian matrix

- latex: `\frac{\partial(f_1, f_2)}{\partial(x, y)}` written as a matrix of `\frac{\partial f_i}{\partial x_j}`
- physica: `jmat(f_1, f_2; x, y)`
- renders: the matrix of first partials, functions before the `;`, variables after. Add `big:#true` to make the fractions full size instead of cramped, and `delim:` to change the bracket. Long name: `jacobianmatrix`.

### Hessian matrix

- latex: a matrix of `\frac{\partial^2 f}{\partial x_i \partial x_j}`
- physica: `hmat(f; x, y)`
- renders: the matrix of second partials of f. The function may be omitted (leave it blank before the `;`) to show the bare operator: `hmat(; x, y, z; delim:"[")`. Accepts `big:#true` and `delim:`. Long name: `hessianmatrix`.

### matrix from an element builder

- latex: a matrix whose (i, j) entry follows a formula
- physica:

  ```typst
  #let g = (i,j) => $g^(#(i - 1)#(j - 1))$
  $ xmat(2, 2, #g) $
  ```

- renders: a 2x2 matrix whose entry (i, j), 1-indexed, is produced by the Typst function `g`. Long name: `xmatrix`.

### rotation matrices

- latex: `\begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}` and 3D analogues
- physica: `rot2mat(theta)` for 2D; `rot3xmat(theta)`, `rot3ymat(theta)`, `rot3zmat(theta)` for rotations about the x, y, z axes.
- renders: the standard rotation matrices. Accept `delim:`. The angle can be any expression, for example `rot3ymat(45^degree)` or `rot2mat(-a/2, delim:"[")`. Wrap the angle in `display(...)` to force display-size fractions inside cells.

### Gram matrix

- latex: a matrix whose (i, j) entry is `\langle v_i, v_j \rangle`
- physica: `grammat(v_1, v_2, v_3, delim:"[")`
- renders: the Gram matrix of inner products of the listed vectors. Add `norm:#true` to render the diagonal using norm notation. Long name: `grammat`.

---

## Reference: Dirac bra-ket notation

These auto-size to their contents only in display math `$ ... $`. In inline math they stay small.

### bra

- latex: `\langle u |`, `\bra{u}`, `\langle u \vert`
- physica: `bra(u)`
- renders: left angle bracket, u, vertical bar. Works with composite content, for example `bra(vec(1, 2))`.

### ket

- latex: `| u \rangle`, `\ket{u}`, `\vert u \rangle`
- physica: `ket(u)`
- renders: vertical bar, u, right angle bracket.

### braket (overlap)

- latex: `\langle u | v \rangle`, `\braket{u}{v}`, `\langle u \vert v \rangle`
- physica: `braket(u, v)`
- renders: ⟨u|v⟩. One argument `braket(a)` gives ⟨a|a⟩. Three arguments `braket(psi, A/N, phi)` give ⟨psi|A/N|phi⟩.

### ketbra (outer product)

- latex: `| u \rangle \langle v |`, `\ketbra{u}{v}`, `| u \rangle\!\langle v |`
- physica: `ketbra(u, v)`
- renders: |u⟩⟨v|. One argument `ketbra(a)` gives |a⟩⟨a|.

### expectation value (sandwiched)

- latex: `\langle \psi | A | \psi \rangle`, `\expval{A}{\psi}`
- physica: `expval(A, psi)`
- renders: ⟨psi|A|psi⟩. With one argument, `expval(u)` gives ⟨u⟩.

### matrix element

- latex: `\langle n | M | m \rangle`, `\matrixel{n}{M}{m}`, `\mel{n}{M}{m}`
- physica: `mel(n, M, m)`
- renders: ⟨n|M|m⟩. Identical to `braket(n, M, m)`. Long name: `matrixelement`.

---

## Reference: math operators added by physica

These are upright roman operators. Map the matching LaTeX operator to the bare name:

- `\operatorname{diag}` becomes `diag`
- `\operatorname{rank}` becomes `rank`
- `\operatorname{tr}` or `\operatorname{trace}` becomes `trace` (or `Trace` for the capitalized form)
- `\operatorname{Res}` becomes `Res`
- `\operatorname{Re}` or `\Re` becomes `Re`
- `\operatorname{Im}` or `\Im` becomes `Im`
- `\operatorname{sgn}` becomes `sgn`

Use them like `trace(A)`, `rank M`, `sgn(x)`.

---

## Reference: differentials and derivatives

A shared order rule governs `dd`, `dv`, and `pdv`:

- No order given: every variable has order 1, and a variable of order 1 prints as `d x`, not `d^1 x`.
- A single order number applies to every variable: `dd(x, y, 2)` gives both order 2.
- An order array assigns in sequence: `dd(f, x, y, [2,3])` gives x order 2, y order 3. A trailing comma like `[3,]` assigns 3 to the first and 1 to the rest. Shorter arrays leave the remaining variables at order 1.

### differential

- latex: `\mathrm{d}x`, `dx`, `\dd x`, `\,dx`
- physica: `dd(x)`
- renders: an upright d before x, with a thin space in front. Multiple: `dd(x, y)` gives d x d y. Order: `dd(x, 3)` gives d cubed x. Keyword args: `d:` sets the differential symbol (default upright d), `prod:` sets a connector such as `prod:and` for a wedge between components, `compact:#true` removes the thin spaces. Long name: `differential`.

### variation

- latex: `\delta x`, `\delta f`
- physica: `var(f)`
- renders: a delta before the variable. Shorthand for `dd(..., d: delta)`. Long name: `variation`.

### finite difference

- latex: `\Delta x`, `\Delta f`
- physica: `difference(f)`
- renders: a capital Delta before the variable. Shorthand for `dd(..., d: Delta)`.

### ordinary derivative

- latex: `\frac{df}{dx}`, `\frac{\mathrm{d}f}{\mathrm{d}x}`, `\dv{f}{x}`, `\frac{d^2 f}{dx^2}`
- physica: `dv(f, x)`, and `dv(f, x, 2)` for second order
- renders: a vertical fraction d f over d x. The function may be empty for the bare operator: `dv(, x)` gives d over d x. Keyword args: `d:` sets the symbol (for example `d:upright(D)` for a material derivative), `style:` (alias `s:`) controls layout. `style:"horizontal"` gives a flat inline form; `style:"large"` places the d/dx operator in front of a large parenthesized expression with auto-sized parentheses; `style:"skewed"` gives a slanted fraction. Long name: `derivative`.

### partial derivative (including mixed orders)

- latex: `\frac{\partial f}{\partial x}`, `\partial_x f`, `\pdv{f}{x}`, `\frac{\partial^2 f}{\partial x \partial y}`, `\frac{\partial^{n} f}{\partial x^{n}}`
- physica: `pdv(f, x)`; mixed example `pdv(f, x, y)`; with orders `pdv(f, x, y, [2,3])`
- renders: a vertical fraction with partial symbols. The function may be empty: `pdv(, x)` gives the bare operator. The numerator total order is computed automatically when all orders are numeric; supply `total:` to override when orders are symbolic, for example `pdv(, x, y, z, [xi n, n-1], total:(xi+1)n)`. Keyword args: `d:` sets the symbol (use `d:delta` for a functional derivative), `style:` works as in `dv`. To apply the operator to a following expression, put that expression in square brackets after the call: `pdv(, z)[integral_0^z f(x) dd(x, y)]`. Long name: `partialderivative`.

Functional derivative note: `\frac{\delta S}{\delta \phi}` becomes `pdv(S, phi, d:delta)`, and `\frac{\delta^2 W[J]}{\delta J^\mu(x)\, \delta J^\nu(y)}` becomes `pdv(W[J], J^mu (x), J^nu (y), d:delta)`.

---

## Reference: special show rules

A show rule is enabled once with `#show: <rule>` in Typst markup, outside math mode, and then applies to the math that follows. Wrap it in a content block `#[ ... ]` to limit its scope.

### transpose with a plain superscript T

- Purpose: convert a handwritten `^T` into a real transpose marker instead of a literal letter T.
- Enable with: `#show: super-T-as-transpose`
- latex it handles: `A^T`, `(AB)^T`, `\mathbf{v}^T`
- physica: with the rule enabled, emit `A^T` directly and it renders as a transpose.
- The conversion is suppressed (T stays a literal letter) when the base is a `limits(...)` or `scripts(...)` element, an integral, a sum (the operator, not Greek Sigma), a product (not Greek Pi), a vertical bar, or an equation whose last child is one of those. To force a transpose anyway use the glyph `TT` (`A^TT`); to force a literal superscript T use `scripts(T)` (`2^scripts(T)`).

### conjugate transpose with a plain superscript +

- Purpose: convert a cleaner `^+` into a dagger (Hermitian conjugate).
- Enable with: `#show: super-plus-as-dagger`
- latex it handles: `A^\dagger`, `U^\dagger`
- physica: with the rule enabled, emit `A^+` and it renders as a dagger. Without the rule, emit `A^dagger`.
- The conversion is suppressed when the base is a `limits(...)` or `scripts(...)` element, or an equation whose last child is one of those. Keep a literal superscript plus (for ions or a pseudoinverse) by scoping the rule with `#[ ... ]`, or force it with `scripts(+)`. Force an explicit dagger with the built-in `dagger`.

---

## Reference: miscellaneous

### reduced Planck constant

- latex: `\hbar`
- physica: `hbar`
- renders: h-bar with a true horizontal bar. Prefer this over the Typst built-in `planck`, which shows a slashed h in the default font. Known limitation: `hbar` uses Typst's `strike` internally, so a `show strike` rule affects it; restore the style locally if needed.

### tensors in abstract index notation

- latex: `T^{a}{}_{b}`, `{T^a}_b`, `T\indices{^a_b}`, `\tensor{T}{^a_b}`, `\Gamma^{\nu}{}_{\mu\lambda}`
- physica: `tensor(T, +a, -b)`; `tensor(Gamma, +nu, -mu, -lambda)`
- renders: the symbol with each index in its own horizontal slot. A `+` prefix marks an upper (contravariant) index, a `-` prefix marks a lower (covariant) index; the sign itself is not printed. This keeps upper and lower indices from overlapping, which plain `^` and `_` cannot do. The symbol may be a composite expression, for example `tensor((dd(x^lambda)), -a)`. Long name: `tensor` (no abbreviation).

### isotopes

- latex: `{}^{A}_{Z}\mathrm{X}`, `{}^{127}\mathrm{I}`, `^{211}_{83}\mathrm{Bi}`
- physica: `isotope("Fe", a:56, z:26)`
- renders: the mass number A as a left superscript and the atomic number Z as a left subscript, both before the element symbol. Use a quoted string for multi-letter symbols, for example `"Fe"`; a single letter can be bare, for example `isotope(I, a:127)`. Either `a:` or `z:` may be omitted (default none). Example reaction: `isotope("Bi", a:211, z:83) -> isotope("Tl", a:207, z:81) + isotope("He", a:4, z:2)`.

### nth term of a Taylor series

- latex: `\frac{f^{(n)}(x_0)}{n!}(x - x_0)^n`
- physica: `taylorterm(f, x, x_0, n)`
- renders: the idx-th Taylor term of the function in the given variable about the expansion point. Arguments in order: function, variable, expansion point, term index. If the expansion point or the index is an add/subtract expression, parentheses are added automatically, for example `taylorterm(f, x, 1+a, 2)`. Long name: `taylorterm` (no abbreviation).

### digital timing diagrams

- latex: no LaTeX equivalent; this draws a waveform from a string and is physica-specific.
- physica: `signals("1|0|1|0", step:#0.5em, color:#fuchsia)`
- renders: each character is one glyph. Level glyphs full width: `H` `L` `M` (equivalently `1` `0` `-`) for high, low, mid. Half width: `h` `l` `m`. One-tenth width: `^` `v`. Zero-width edges: `|` `'` `,`. Bus data: `=` empty, `#` shaded. Transitions: `R` rise, `F` fall, `C` charge, `D` drain. Bus markers: `<` `>` `X`. A space is ignored, `&` is a non-drawing separator, and `.` repeats the previous glyph. Keyword args: `step:` glyph width (default `#1em`), `color:` stroke color (default `#black`).

### symbolic addition helper

- latex: not a notation; this is an internal helper.
- physica: `BMEsymadd([a+1, 2(b+1), 1, b+1, 15])`
- renders: a minimal best-effort symbolic sum, used mainly so `pdv` can compute a symbolic total order. It sums numbers and collects simple like terms. For anything it cannot handle, supply `total:` to `pdv` directly instead.

---

## Attribution

Adapted from the `physica` manual (version 0.9.8) by Leedehai. The package source is Copyright 2023 Leedehai; the original manual is licensed CC BY-ND 4.0. Package home: [https://typst.app/universe/package/physica](https://typst.app/universe/package/physica)
