---
name: blog-articles
description: Conventions for writing and editing blog articles in the portal. Use this skill when creating new blog posts, editing article text, adding interactive components, or refining prose in the blog section. Also trigger when the user mentions "blog", "article", "write a post", "edit the article", or refers to any specific article by name.
---

# Blog Article Conventions

The portal's blog articles are long-form interactive essays that combine mathematical rigor with visual demonstrations. Each article teaches a concept from mathematics, computer science, or game theory using the portal's games as concrete examples.

---

## File Structure

- Articles live in: `portal/src/views/blog/<ArticleName>.jsx`
- Blog index: `portal/src/views/Blog.jsx`
- Blog post wrapper: `portal/src/views/BlogPost.jsx` (adds "All Articles" button, layout)
- Sitemap entries: `portal/public/sitemap.xml`

### Adding a new article

1. Create the JSX component in `portal/src/views/blog/`
2. Add it to the `POSTS` array in `Blog.jsx` with slug, title, subtitle, date, category, games
3. Add the route in `BlogPost.jsx`
4. Add the URL to `sitemap.xml`

---

## Typography and Components

### Fonts
- Headings: `'Playfair Display', Georgia, serif`
- Body text: `'Newsreader', Georgia, serif` (set at article level)
- Code/labels: `'Source Code Pro', monospace`

### Standard components

| Component | Usage |
|---|---|
| `<Section num="N" title="...">` | Numbered article section |
| `<M>text</M>` | Inline math (renders in italic serif) |
| `<MathBlock>` | Display math / definition block (centered, bordered) |
| `<Callout>` | Key insight or summary (light background) |
| `<Callout accent>` | Theorem or proof conclusion (accent-colored border) |
| `<figcaption>` | Figure caption (Newsreader italic, 0.82rem, inkSoft color) |

### Section headings within sections
```jsx
const h3s = { fontFamily: "'Source Code Pro',monospace", fontSize: "0.88rem", ... };
<h3 style={h3s}>Subsection title</h3>
```

---

## Writing Style for Articles

Follow the full writing-style guide in `skills/writing-style/writing-style.md`. Key rules for articles:

### Hard rules
- **No em dashes (—)**. Use commas, periods, or parentheses. Search for \u2014 before committing.
- **No double hyphens (--)** in user-visible text. These are em dash substitutes and must also be replaced.
- **No filler transitions**: "Additionally," "Furthermore," "Moreover," "It's worth noting"
- **No performative enthusiasm**: "exciting," "fascinating," "remarkable"

### Prose tightening patterns (from editing sessions)
- "the deepest duality" → "a fundamental duality"
- "fundamentally, provably harder" → "provably harder"
- "Want to explore X more deeply? Play X on this site, or work through the Y tutorial to build your skills step by step." → "Want to try X yourself? Play X on this site, or try the Y tutorial."
- "This is the crux." → "Here's the point."
- "LABEL — description" → "LABEL: description" (in figure labels)
- "Figure N — Caption text" → "Figure N. Caption text" (periods, not em dashes)
- "A dash sets off the aside — like this" → "A comma sets off the aside, like this"
- Cut "single most powerful" → "best". Cut "the real difference isn't X, it's Y" → just state Y.

### Article subtitle conventions (in Blog.jsx POSTS array)
- No em dashes or double hyphens in subtitles
- Use commas: "How X relates to Y, and why Z matters"

---

## Interactive Components

Each article embeds interactive React components that demonstrate the concepts. Conventions:

1. **Self-contained**: Each interactive component is defined in the same article file. No shared component imports between articles.
2. **Color palette**: Define a `C` object at the top of each article with all colors. Use semantic names (`accent`, `inkSoft`, `faint`, `poly`, `exp`).
3. **Stepper pattern**: For multi-stage demonstrations, use `useState` with a `step` index and a `stages` array. Render a "Step" / "Reset" button.
4. **Responsive**: Use `clamp()` for font sizes, `flexWrap` for side-by-side layouts, `maxWidth` on SVGs.
5. **Figure pattern**: Wrap in `<figure>`, add `<figcaption>` below. Keep captions under 2 sentences.

### Board illustrations
- Use the game's actual colors (not arbitrary ones). Example: Hex uses red/blue, not purple/green.
- For abstract illustrations (not game boards), use a warm neutral palette: `boardBg: "#e8e0d4"`, `boardLine: "#d4ccbe"`, etc.
- SVGs should always have a `viewBox` attribute and use `width: "100%"` with a `maxWidth` for responsiveness.

---

## Bottom CTA

Every article ends with a CTA box linking to the relevant game(s):

```jsx
<div style={{ marginTop: "3rem", padding: "1.5rem", background: "rgba(26,20,40,0.04)",
  borderRadius: 8, border: `1px solid ${C.faint}` }}>
  <p style={{ margin: 0, fontSize: "0.95rem", lineHeight: 1.7 }}>
    Want to try X yourself? <a href="/game/ID">Play X</a> on this site,
    or try the <a href="/game/ID/learn">tutorial</a>.
  </p>
</div>
```

Keep it short. One sentence. No "more deeply" or "build your skills step by step."

---

## Game ID Reference

When linking to games from articles, use the correct portal game IDs:

| Game | Game ID (URL) | Internal ID |
|---|---|---|
| Chess | `/game/knights` | knights |
| Othello | `/game/flips` | flips |
| Hex | `/game/hexes` | hexes |
| TwixT | `/game/bridges` | bridges |
| Pente | `/game/pairs` | pairs |
| Go | `/game/stones` | stones |
| Abalone | `/game/marbles` | marbles |
| Quoridor | `/game/walls` | walls |
| Hive | `/game/bugs` | bugs |
| YINSH | `/game/circles` | circles |
| Tak | `/game/stacks` | stacks |
| Santorini | `/game/towers` | towers |

**Common mistake**: Pente's game ID is `pairs`, not `stones`. `stones` is Go.

---

## Deployment

The portal deploys to Vercel. The build command in `vercel.json` includes `CI=false` because Vercel sets `CI=true`, which makes Create React App treat warnings as errors. CSS order conflicts and missing source maps are warnings, not bugs.
