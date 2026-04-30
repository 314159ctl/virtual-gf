---
name: frontend-design
description: Create high-quality, production-grade frontend interfaces with strong design taste. Avoid generic "AI slop" aesthetic. Use when building UI components, pages, or full applications.
---

# Frontend Design Guidelines

## Core Principles

Before writing any frontend code, pause and determine a clear **aesthetic direction**. Never default to the generic AI aesthetic (Inter font, purple gradients, glassmorphism cards, blue buttons). The design must feel intentional.

### 1. Pick an Aesthetic

Choose ONE direction and commit fully:

**Editorial / Minimalist** — Black on white, strong typography hierarchy, generous whitespace, thin borders, no shadows. Like a well-designed magazine or Linear/Notion.

**Brutalist / Raw** — Bold typography, high contrast, visible grid lines, monospace accents, raw structural elements. Swiss typography meets CRT terminal.

**Warm / Organic** — Rounded corners, warm color palette (terracotta, cream, sage), subtle textures, friendly typography, soft shadows.

**Luxury / Refined** — Dark neutrals, gold/bronze accents, serif headings, refined spacing, subtle animations, premium feel.

**Fun / Playful** — Bright colors, rounded everything, bouncy animations, bold typography, emoji accents, gradient accents.

**Neo-Brutalist** — Hard shadows, bold borders, primary colors, no gradients, raw but intentional.

### 2. Typography

- NEVER default to Inter for everything
- Use 1-2 fonts max: one for headings, one for body
- Good heading fonts: Playfair Display, Cormorant Garamond, DM Serif Display, Syne, Space Grotesk
- Good body fonts: Inter (only paired with a distinctive heading font), Source Sans 3, IBM Plex Sans, Geist, Lora
- For Chinese: Noto Sans SC, LXGW WenKai, ZCOOL QingKe HuangYou
- Establish clear type scale: h1 ~2.5rem, h2 ~1.8rem, h3 ~1.3rem, body 1rem, small 0.875rem
- Line-height: headings 1.2, body 1.6

### 3. Color

- Use 3-5 colors max (not counting neutrals)
- Define CSS custom properties: --color-primary, --color-bg, --color-surface, --color-text, --color-text-muted, --color-border, --color-accent
- Avoid pure black (#000) — use near-black (#0a0a0a, #111)
- Avoid pure white backgrounds — use off-white (#fafaf9, #fdfbf7)
- Gradients: subtle, max 2 stops, used sparingly as accents

### 4. Spacing & Layout

- Use consistent spacing scale: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px
- Max content width for readable text: 680px
- Generous padding on cards and sections
- Grid gaps should match surrounding padding

### 5. Icons & Imagery

- Use SVG icons from a consistent set (Lucide, Heroicons, Phosphor)
- Icons: 20px-24px, stroke-width 1.5-2
- Never use emoji as UI icons — use proper SVG icon components
- Avatar placeholders: use gradients, not generic silhouettes
- Images should have rounded corners and consistent aspect ratios

### 6. Shadows & Depth

- Minimal shadows. Max 3 levels:
  - Subtle: `0 1px 2px rgba(0,0,0,0.04)`
  - Medium: `0 4px 12px rgba(0,0,0,0.06)`
  - Elevated: `0 12px 32px rgba(0,0,0,0.08)`
- Use elevation sparingly — not everything needs a card with shadow

### 7. Motion

- Respect `prefers-reduced-motion`
- Transitions: 150-300ms, ease-out or custom cubic-bezier
- Page transitions: subtle fade or slide, under 300ms
- Hover states: color shift, subtle scale(1.02), or underline reveal
- Loading states: skeleton screens > spinners for content
- Stagger children animations for lists

### 8. Interactive States

- All interactive elements need: default, hover, focus-visible, active, disabled states
- Focus rings: 2-3px outline, offset by 2px, brand color
- Use `:focus-visible`, not `:focus`
- Touch targets: minimum 44x44px on mobile
- Cursor: `pointer` on clickable elements only

### 9. Responsive Design

- Mobile-first media queries
- Breakpoints: 480px (small phone), 768px (tablet), 1024px (small desktop), 1280px (desktop)
- Test at 320px minimum width
- Sidebar: off-screen drawer on mobile, persistent on desktop

### 10. Anti-Patterns — NEVER use

- Purple-to-blue gradients as default
- Glassmorphism (frosted glass) without purpose
- Inter font as the only font
- Giant emoji as hero elements
- Neon/glow effects on everything
- Cookie-cutter card layouts with identical rounded corners
- Placeholder lorem ipsum in production code
- "Coming soon" empty states

## Output Requirements

- Write complete, production-ready code
- No placeholder comments like "// more items here"
- No skipped sections with "..." or "etc."
- Every state must be implemented (loading, empty, error, success)
- Use the user's chosen tech stack (Vue 3, React, Svelte, HTML/CSS, etc.)
- All CSS must be scoped or use a defined naming convention
