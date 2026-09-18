# Bidi: the model, the characters, and the surfaces markup cannot reach

## Contents
- [Directional strength](#directional-strength)
- [Why neutrals break sentences](#why-neutrals-break-sentences)
- [Every control character](#every-control-character)
- [Isolates versus embeddings](#isolates-versus-embeddings)
- [Markup equivalents](#markup-equivalents)
- [The non-DOM surfaces table](#the-non-dom-surfaces-table)
- [A helper worth writing once](#a-helper-worth-writing-once)
- [Debugging a reordered string](#debugging-a-reordered-string)

## Directional strength

| Strength | Members | Behaviour |
|---|---|---|
| **Strong LTR** | Latin, Cyrillic, Greek, most scripts | Fixed |
| **Strong RTL** | Hebrew, Arabic, Syriac, Thaana | Fixed |
| **Weak** | Digits, and some currency and arithmetic symbols | Context-dependent, own rules |
| **Neutral** | space, `-` `,` `.` `:` `;` `/` `\` `(` `)` `[` `]` `{` `}` `@` `#` `!` `?` `"` `'`, most punctuation and symbols | **Resolve to the base direction** |

## Why neutrals break sentences

A neutral character between two runs of **the same** direction takes that direction. A neutral
between runs of **different** directions **resolves to the paragraph's base direction** — not to
either neighbour.

That is the whole bug. In an RTL paragraph, every neutral sitting at a Hebrew/Latin boundary is
pulled RTL, and anything after it that should have stayed together comes apart.

**Where it bites, in order of frequency:**

| Content | The neutrals |
|---|---|
| Product names with a model number | space, `-` |
| URLs | `:` `/` `.` `?` `=` `&` |
| Email addresses | `@` `.` |
| File paths | `/` `\` `.` |
| Version strings | `.` |
| Phone numbers | `+` `-` space `(` `)` |
| Dimensions (`1920x1080`) | `x` is a letter, but the surrounding neutrals reorder |
| Ranges (`10-20`) | `-` |
| Times (`14:30`) | `:` |
| Any parenthesised aside | `(` `)` |

**The count of interpolation slots is the count of risk points.** A template with one `{name}` has
two boundaries; a template with four slots has eight.

## Every control character

| Char | Code point | Name | Effect |
|---|---|---|---|
| **FSI** | `U+2068` | First Strong Isolate | **Direction from the first strong character inside.** The one to use when you do not know |
| LRI | `U+2066` | Left-to-Right Isolate | Isolates as LTR |
| RLI | `U+2067` | Right-to-Left Isolate | Isolates as RTL |
| **PDI** | `U+2069` | Pop Directional Isolate | Closes any of the three above |
| LRE | `U+202A` | Left-to-Right Embedding | **Legacy. Leaks** |
| RLE | `U+202B` | Right-to-Left Embedding | **Legacy. Leaks** |
| LRO | `U+202D` | Left-to-Right Override | Forces LTR on everything, including letters |
| RLO | `U+202E` | Right-to-Left Override | Forces RTL. **Also the character used in filename-spoofing attacks** |
| PDF | `U+202C` | Pop Directional Formatting | Closes an embedding or override |
| **LRM** | `U+200E` | Left-to-Right Mark | Invisible strong LTR character |
| **RLM** | `U+200F` | Right-to-Left Mark | Invisible strong RTL character |
| ALM | `U+061C` | Arabic Letter Mark | Arabic-specific strong mark |

**LRM and RLM are for nudging a single neutral**, not for wrapping a run. If a trailing period lands
on the wrong side, an LRM before it fixes that one character. Reaching for isolates is better for
anything longer.

**RLO in untrusted input is a security concern**, not just a rendering one: it can make `exe.txt`
display as `txt.exe`. Strip or escape overrides in user-supplied filenames and display names.

## Isolates versus embeddings

```
base: RTL

with RLE...PDF:   the embedding's effect can influence resolution of
                  neutrals AFTER the PDF  ← the leak

with RLI...PDI:   the isolated content is treated as a single neutral
                  object from the outside; nothing leaks
```

**Isolates exist because embeddings leak.** From outside, an isolate's content behaves as one opaque
neutral character — so it cannot reach out and reorder its surroundings, and the surroundings cannot
reach in.

**Always reach for isolates.** The embeddings are legacy and remain in the standard for compatibility.

## Markup equivalents

| Markup | Control characters |
|---|---|
| `<bdi>` | FSI … PDI |
| `<bdi dir="ltr">` | LRI … PDI |
| `<bdo dir="rtl">` | RLO … PDF |
| `unicode-bidi: isolate` | LRI/RLI … PDI |
| `unicode-bidi: embed` | LRE/RLE … PDF (legacy) |
| `unicode-bidi: bidi-override` | LRO/RLO … PDF |
| `unicode-bidi: isolate-override` | Both |
| `unicode-bidi: plaintext` | `isolate` + first-strong self-determination |

**`<bdo>` is an override and you almost never want it.** It forces direction onto letters too, which
reverses Hebrew text character by character. `<bdi>` is the one you want in nearly every case.

**`unicode-bidi: plaintext`** is useful for a container of user-generated content where each block
should determine its own direction — a comment list, a chat log.

## The non-DOM surfaces table

**The single biggest unserved area in the published guidance.** Every bidi guide assumes a DOM;
these have none.

| Surface | Why markup fails | Fix |
|---|---|---|
| `document.title` | Plain text | FSI/PDI |
| `aria-label`, `aria-description` | Attribute value | FSI/PDI |
| `title=` tooltip | Attribute value | FSI/PDI |
| `placeholder` | Attribute value | FSI/PDI |
| `alt` | Attribute value | FSI/PDI |
| Toasts, snackbars, `textContent` | Text node, no children | FSI/PDI |
| **Clipboard** | Plain text | FSI/PDI |
| **CSV export** | No markup layer | FSI/PDI, and beware Excel's handling |
| **PDF export** | Depends on the generator | FSI/PDI; verify — some strip them |
| **Email subject** | Plain text, RFC 2047 encoded | FSI/PDI inside the encoded word |
| Email plain-text part | Plain text | FSI/PDI |
| **Push notification payload** | Plain text, OS-rendered | FSI/PDI |
| SMS | Plain text | FSI/PDI |
| Log lines | Plain text | FSI/PDI, or keep logs LTR-only |
| `console.*` | Plain text | Usually not worth it |
| `<option>` labels | Text node | `<bdi>` is not valid inside `<option>` — use control characters |
| Chart and graph labels (canvas/SVG text) | Rendered text | FSI/PDI |
| `window.prompt` / `alert` | Plain text | FSI/PDI |

**`<option>` is the one people trip on inside HTML**, because it looks like a DOM surface but does
not accept phrasing content. Control characters are the only route.

## A helper worth writing once

```js
const FSI = '⁨';
const PDI = '⁩';
const LRM = '‎';
const RLM = '‏';

/** Isolate a value of unknown direction for a plain-text context. */
export const isolate = (s) => (s == null ? '' : FSI + String(s) + PDI);

/** Force LTR for a value that must always read LTR: paths, URLs, phone numbers, versions. */
export const ltr = (s) => (s == null ? '' : '⁦' + String(s) + PDI);
```

```js
document.title = `${t('editing')} ${isolate(fileName)} — ${t('appName')}`;
btn.setAttribute('aria-label', `${t('download')} ${isolate(fileName)}`);
notify({ body: `${t('sharedWith')} ${isolate(userName)}` });
csvRow.push(isolate(productName));
```

**Apply it at the boundary, not at the source.** Storing control characters in the database means
they leak into search indexes, exports and comparisons. Add them at render time.

**Strip them before comparison, search or length checks:**

```js
const strip = (s) => s.replace(/[⁦-⁩‪-‮‎‏؜]/g, '');
```

## Debugging a reordered string

When something renders wrong and you cannot see why:

1. **Dump the code points.** The problem is usually invisible.
   ```js
   [...str].map(c => c.codePointAt(0).toString(16).padStart(4,'0'))
   ```
2. **Find the boundary.** Locate the neutral between a Hebrew run and a Latin run. That is almost
   always the culprit.
3. **Check whether a `dir` was used where an isolate was needed.** A container `dir` sets the base
   direction — which is what the neutral is resolving *to*. It cannot fix it.
4. **Check for a leaking embedding.** An unclosed LRE/RLE, or one closed with the wrong pop, affects
   everything after it.
5. **Check for a stray override.** RLO in user input reverses display and is often pasted in
   accidentally from another system.
6. **Test the value alone** in an RTL paragraph, isolated and not isolated. If isolating fixes it,
   the value is the problem; if not, the surrounding template is.

**The most common finding is step 3** — someone set `dir="rtl"` on the container, saw the layout flip
correctly, and assumed the string problem was covered by the same change.
