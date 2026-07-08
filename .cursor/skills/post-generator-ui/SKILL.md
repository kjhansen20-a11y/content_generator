---
name: post-generator-ui
description: >-
  Streamlit design system for Post Generator — B2B SaaS content marketing dashboard.
  Use when styling dashboard pages, layout components, or applying UI polish.
---

# Post Generator UI

## Product context
B2B SaaS tool for AI-assisted social media content: company/brand profiles, knowledge base, post generation, content calendar, mock publishing.

## Design system (Minimal / Soft UI)

| Token | Value | Usage |
|-------|-------|--------|
| Primary | `#2563EB` | CTAs, active states |
| Background | `#F8FAFC` | Page background |
| Surface | `#FFFFFF` | Cards, sidebar |
| Border | `#E2E8F0` | Dividers, card edges |
| Text | `#0F172A` | Headings, body |
| Text muted | `#64748B` | Captions, hints |
| Font | Inter | Via Google Fonts in `layout.py` |

## Streamlit implementation
- Theme: `dashboard/.streamlit/config.toml`
- Tokens: `dashboard/components/design.py`
- Layout helpers: `dashboard/components/layout.py` (`page_header`, `stat_cards`, `section_card`, `status_badge`, `workflow_steps`)
- Feed previews: `dashboard/components/platform_preview.py`

## Rules
- Use `page_header()` instead of `st.header()` on all pages
- Hide dev settings (API URL) in sidebar expander
- Status colors from `STATUS_COLORS` in design.py
- Avoid emoji-as-icons; use text labels and badges
- Keep forms in cards with clear primary actions
- Anti-patterns: neon gradients, generic “AI purple”, cluttered sidebars

## Page patterns
- **Marketing Plan:** AI builder (keywords → generate) | Overview viz | Pillars | Schedule
- **Home:** stat cards + workflow + recent activity
- **Forms:** two-column where platform/type apply; primary button right-aligned
- **Calendar/Queue:** feed preview above actions; status badges
