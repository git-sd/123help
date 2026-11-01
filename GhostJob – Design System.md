# GhostJob – Design System

*Verify Before You Apply.*

Version 1.0 · Palette: Orange, White and Black · Stack: React, Tailwind CSS, React Flow

## 1. Design Principles

1. **Clarity over cleverness.** A stressed student must understand the risk level within three seconds.
2. **Evidence first.** Every warning is shown next to the proof that caused it.
3. **Calm, not alarmist.** Strong colour is reserved for what matters; wording stays neutral and advisory.
4. **Bold and high contrast.** Black and white carry the layout; orange is the single accent that guides the eye to actions.
5. **Accessible by default.** WCAG 2.1 AA contrast, keyboard navigation, and never relying on colour alone.
6. **Mobile first.** Most students will check listings from a phone.

## 2. Brand

- **Name:** GhostJob
- **Tagline:** Verify Before You Apply .
- **Voice:** Direct, friendly, protective. Short sentences. Plain language. Avoid accusing companies; say "warning signs detected" rather than "this is a scam" .
- **Logo concept:** A black ghost silhouette with a small orange magnifying glass or checkmark. Provide black-on-white, white-on-black and orange-on-black versions.

## 3. Colour System

### 3.1 Core Palette

| Token | Hex | Usage |
| --- | --- | --- |
| `--gj-orange-500` | #FF6B00 | Primary accent, buttons, highlights, active states |
| `--gj-orange-600` | #E65F00 | Button hover |
| `--gj-orange-700` | #C2410C | Orange text and links on white (passes AA) |
| `--gj-orange-100` | #FFEDD5 | Soft backgrounds, selected rows, callouts |
| `--gj-orange-50` | #FFF7ED | Page tints, subtle panels |
| `--gj-black` | #0A0A0A | Primary text, dark surfaces, headings |
| `--gj-gray-800` | #262626 | Dark cards, dark-mode surfaces |
| `--gj-gray-600` | #525252 | Secondary text |
| `--gj-gray-300` | #D4D4D4 | Borders, dividers |
| `--gj-gray-100` | #F5F5F5 | Light panels, table stripes |
| `--gj-white` | #FFFFFF | Page background, text on black |

### 3.2 Contrast Rules (critical for "fix color contrast")

Pure orange is bright, so white text on orange fails contrast. Follow these rules:

| Combination | Approx. ratio | Allowed? |
| --- | --- | --- |
| Black (#0A0A0A) on orange (#FF6B00) | about 7:1 | Yes, use for button labels |
| White on orange (#FF6B00) | about 2.9:1 | **No** for text |
| Orange (#FF6B00) on black | about 7:1 | Yes, for accents and large or small text |
| Orange (#FF6B00) on white | about 2.9:1 | **No** for text; icons and large decorative use only |
| Dark orange (#C2410C) on white | about 5.2:1 | Yes, for text and links |
| Black on white | about 19:1 | Yes |
| Gray-600 (#525252) on white | about 7.8:1 | Yes |

Always verify final values with a contrast checker and Lighthouse before launch.

### 3.3 Semantic Status Colours

The evidence system needs four distinct states. Keep the brand palette dominant, and use these only for status indicators. **Every status also has an icon and a text label**, so meaning never depends on colour alone.

| Status | Colour | Icon | Label | Used for |
| --- | --- | --- | --- | --- |
| Verified | Green #15803D on #DCFCE7 | Check circle | Verified | Evidence confirmed by reliable sources |
| Warning | Red #B91C1C on #FEE2E2 | Triangle alert | Warning | Suspicious indicator detected |
| Unverified | Orange #C2410C on #FFEDD5 | Question mark in circle | Unverified | Claim could not be confirmed |
| Unknown | Gray #404040 on #F5F5F5 | Dashed circle | Unknown | Not enough information |

### 3.4 Risk Level Colours

| Risk | Treatment |
| --- | --- |
| Low | Green accent, white card, label "Low Risk" with check icon |
| Medium | Orange background #FFEDD5 with dark orange text, label "Medium Risk" with alert icon |
| High | Black card with orange and white text and a red warning icon, label "High Risk"; the strongest visual weight on the page |

### 3.5 Tailwind Configuration

```js
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gj: {
          orange: { 50:'#FFF7ED', 100:'#FFEDD5', 500:'#FF6B00', 600:'#E65F00', 700:'#C2410C' },
          black: '#0A0A0A',
          gray: { 100:'#F5F5F5', 300:'#D4D4D4', 600:'#525252', 800:'#262626' },
        },
        status: {
          verified:'#15803D', warning:'#B91C1C', unverified:'#C2410C', unknown:'#404040',
        },
      },
      fontFamily: {
        display: ['Space Grotesk','Inter','system-ui','sans-serif'],
        sans: ['Inter','system-ui','sans-serif'],
        mono: ['JetBrains Mono','ui-monospace','monospace'],
      },
      borderRadius: { gj: '12px' },
    },
  },
};
```

## 4. Typography

| Role | Font | Notes |
| --- | --- | --- |
| Headings | Space Grotesk (fallback Inter) | Bold, tight letter spacing; gives a confident, tech feel |
| Body and UI | Inter | Highly legible at small sizes |
| Evidence quotes and URLs | JetBrains Mono | Distinguishes verbatim text from analysis |

Self-host or preload fonts, use `font-display: swap`, and limit to two weights per family for speed.

### Type Scale

| Style | Size / Line height | Weight | Usage |
| --- | --- | --- | --- |
| Display | 48 / 52 (desktop), 34 / 38 (mobile) | 700 | Landing hero |
| H1 | 36 / 40 | 700 | Page titles |
| H2 | 28 / 34 | 600 | Section titles |
| H3 | 20 / 28 | 600 | Card titles |
| Body | 16 / 24 | 400 | Default text (never below 16px on mobile inputs) |
| Small | 14 / 20 | 400 | Captions, metadata |
| Mono | 14 / 20 | 400 | Quoted evidence |

## 5. Spacing, Layout and Shape

- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 64, 96 px (Tailwind default steps).
- **Grid:** 12 columns desktop, 8 tablet, 4 mobile. Max content width 1200px; report pages 880px for readability.
- **Breakpoints:** sm 640, md 768, lg 1024, xl 1280.
- **Radius:** 12px for cards, 8px for inputs and buttons, 999px for badges.
- **Borders:** 1px gray-300 on light; 2px black for emphasis; focus ring 3px orange with 2px offset.
- **Elevation:** Prefer borders to heavy shadows. Use one soft shadow level for floating elements (menus, banners): `0 8px 24px rgba(0,0,0,0.12)`.

## 6. Iconography and Imagery

- Icon set: Lucide (outline, 1.75px stroke), sizes 16, 20, 24.
- Illustrations: flat black line art with a single orange highlight.
- Every informative image has descriptive alt text; decorative images use empty alt.
- Use compressed WebP or AVIF, responsive `srcset`, and lazy loading below the fold.
- Social preview image: 1200 x 630 px, black background, white headline "Verify Before You Apply.", orange ghost logo.
- Favicon: ghost mark, provided as SVG, 32x32 PNG, 180x180 Apple touch icon.

## 7. Components

### 7.1 Buttons

| Variant | Style | Use |
| --- | --- | --- |
| Primary | Orange #FF6B00 background, black bold label, 8px radius, hover #E65F00 | The one main action per screen ("Check a job now") |
| Secondary | White background, 2px black border, black label, hover black fill with white label | Supporting actions |
| Ghost | No border, dark orange #C2410C label with underline on hover | Tertiary actions |
| Danger | Black background, white label, red icon | Delete account or investigation |
| Disabled | Gray-100 background, gray-600 label | Always with a tooltip or helper text explaining why |

Minimum tap target 44 x 44 px. Show a spinner and keep the label while loading.

### 7.2 Form Fields

- Visible label above the input (no placeholder-only labels).
- 1px gray-300 border, 2px orange focus ring, 16px text.
- Inline validation on blur with a clear message, an error icon, and `aria-describedby`.
- Job URL input has a paste button and an example hint.
- Job description textarea shows a character counter and limit.
- Spam protection (honeypot and CAPTCHA challenge) is invisible until needed.

### 7.3 Navigation

- **Top bar:** Black background, white logo, links in white, active link underlined in orange, primary orange "New Investigation" button.
- **Mobile:** Hamburger menu opening a full-screen black sheet; bottom tab bar on dashboard (Home, New, History, Account).
- **Footer:** Black, with Privacy Policy, Terms, Contact and tagline.

### 7.4 Cards

- White card, 1px gray-300 border, 12px radius, 24px padding.
- **Report card:** company, role, risk badge, date, and a one-line verdict.
- **Stat card:** large number in Space Grotesk, label beneath, orange top border.
- **Warning card:** red-tinted background with the exact triggering text in a mono quote block.

### 7.5 Badges and Chips

Risk badge and status badge: pill shape, icon + label, always visible text. Examples: "High Risk", "Verified", "Fee Requested".

### 7.6 Tables and Lists

Zebra stripes with gray-100, sticky header, horizontal scroll container on mobile, or collapse to stacked cards below 640px.

### 7.7 Alerts and Banners

| Type | Style |
| --- | --- |
| Fee warning (flagship) | Full-width black banner, orange left border 6px, white text: "This listing asks for a payment. Verify independently before paying anything." |
| Info | Orange-50 background, dark orange text |
| Error | Red tint with icon and retry button |
| Success | Green tint with check icon |

### 7.8 Cookie Consent Banner

- Fixed to the bottom, black background, white text, 16px, max width 720px on desktop, full width on mobile.
- Buttons: "Accept all" (primary orange), "Reject non-essential" (secondary), and "Manage preferences".
- Links to the Privacy Policy. Analytics loads only after consent.
- Keyboard focus is trapped to the banner until a choice is made; choice is remembered.

### 7.9 Modals, Toasts and Tooltips

Modals are focus-trapped with a visible close button and `Esc` support. Toasts appear bottom right (top on mobile), auto-dismiss after 5 seconds, and use `aria-live="polite"`.

## 8. Key Screens

### 8.1 Landing Page

1. **Hero:** Black background, large white headline "Verify Before You Apply.", subtext, and one orange button "Check a job now". Inline URL field optional.
2. **Problem strip:** Three short cards (fake recruiters, fee demands, unverifiable listings).
3. **How it works:** Four steps with numbers in orange.
4. **Features:** Fee detection, company verification, recruiter verification, evidence graph, risk report.
5. **Sample report preview:** Static example with a High Risk card.
6. **Trust and disclaimer:** Advisory not a guarantee, privacy-first statement.
7. **Final CTA:** Repeat the same single call to action.

### 8.2 Authentication

Centered card on a white page with a black side panel on desktop. Email and password fields, show-password toggle, password strength meter, Google button (secondary style), links to Terms and Privacy.

### 8.3 Dashboard

- Top row: greeting and primary "New Investigation" button.
- Stats row: Total investigations, High risk found, Fee requests detected, Last investigation.
- Recent reports: list of report cards.
- Empty state: ghost illustration and a prompt to run the first check.

### 8.4 New Investigation

Two tabs: **Job URL** and **Paste Description**. Optional section "Add recruiter details" (name, email, phone). Primary button "Start investigation".

### 8.5 Investigation Progress

Vertical stepper with states (waiting, running, done, failed): Reading the listing, Checking the company, Checking the recruiter, Looking for payment demands, Analysing findings, Building report. Orange animated indicator on the active step; respects `prefers-reduced-motion`. Estimated time and a cancel option.

### 8.6 Investigation Report

Order of content:

1. Risk summary card (level, one-sentence reason, date, advisory note).
2. Fee alert banner if applicable.
3. Detected warning signs.
4. Verified information.
5. Unverified claims.
6. Source links (open in new tab with `rel="noopener noreferrer"`).
7. Recommended next steps (checklist).
8. Button to open the Evidence Graph, plus feedback thumbs and delete.

### 8.7 Scam Evidence Graph

Built with React Flow. Dark canvas option with a toggle for light.

| Node type | Shape | Border / fill |
| --- | --- | --- |
| Claim | Rounded rectangle | White fill, black 2px border |
| Company info | Rectangle with building icon | Gray-100 fill |
| Recruiter info | Rectangle with person icon | Gray-100 fill |
| Suspicious activity | Hexagon-style badge | Red tint, red border, alert icon |
| Evidence | Document-style card | White fill, mono excerpt, link icon |
| Verification result | Pill | Status colour plus icon and label |

Edges: black 1.5px lines with labels such as "supports", "contradicts", "not found". Contradicting edges are dashed orange. A legend, minimap, zoom controls and a **List view** toggle (accessible, mobile-friendly alternative) are always available. Clicking a node opens a side panel (bottom sheet on mobile) with the evidence and source link.

### 8.8 Investigation History

Searchable table with filters (risk level, date). Row shows company, role, risk badge, date, and actions (open, re-run, delete). Pagination or infinite scroll.

### 8.9 Utility Pages

- **Privacy Policy and Terms:** Single-column readable layout, 720px width, table of contents.
- **Custom 404:** Black page, large orange "404", ghost illustration, text "This page vanished like a fake job offer.", and buttons to Home and New Investigation.
- **500 / maintenance:** Same style with a retry button.

## 9. Motion

- Durations: 150 ms for micro-interactions, 250 ms for panels, 400 ms for page transitions.
- Easing: ease-out.
- Use motion to show progress and state change only. Disable non-essential animation when `prefers-reduced-motion` is set.

## 10. Accessibility Standards

- Meet WCAG 2.1 AA: contrast, focus visibility, text resize to 200%, and no horizontal scrolling at 320px width.
- Fully keyboard operable, including the evidence graph (list view fallback) and the cookie banner.
- Semantic HTML landmarks, one H1 per page, ARIA only where native elements are insufficient.
- Status always conveyed by icon, label and colour.
- Form errors announced to screen readers.
- Test with a screen reader (NVDA or VoiceOver) and axe or Lighthouse.

## 11. Dark Mode

The default is light (white) pages with black navigation and footer. Optional dark mode inverts surfaces to black and gray-800, keeps orange #FF6B00 as the accent, switches text to white, and retains all contrast rules.

## 12. Content and Microcopy Guidelines

| Situation | Example text |
| --- | --- |
| Primary CTA | Check a job now |
| Fee detected | This listing asks for money. Legitimate employers rarely charge applicants. Verify before paying. |
| Medium risk | We found some gaps. Verify these items before you apply. |
| Low risk | No major warning signs found. Still verify details independently. |
| Disclaimer | This is an advisory assessment based on public information, not a guarantee. |
| Error | Something went wrong while investigating. Your listing is saved. Try again. |

## 13. SEO and Sharing Assets

| Asset | Specification |
| --- | --- |
| Title | "GhostJob – Check if a Job or Internship is Fake" (under 60 characters) |
| Meta description | "Paste a job link. GhostJob investigates the company and recruiter and flags fee demands. Verify before you apply." (under 160 characters) |
| Open Graph and Twitter | Title, description and 1200 x 630 image on every public page |
| Favicon set | SVG, 32px, 180px touch icon, web manifest |
| Sitemap and robots.txt | Include public pages only; disallow dashboard, admin and API paths |
| Structured data | Organization and WebSite JSON-LD on the landing page |

## 14. Performance Budget for UI

- Largest Contentful Paint under 2.5 seconds, CLS under 0.1, INP under 200 ms.
- Initial JS under 200 KB gzipped on the landing page; lazy load React Flow only on the graph route.
- Images compressed and sized to display size; fonts preloaded.

## 15. Design QA Checklist (Last 20 Things, UI Items)

| Item | Design requirement |
| --- | --- |
| Favicon | Present in all sizes |
| Social preview image | 1200 x 630, tested in a share debugger |
| Alt text | Every informative image |
| Compressed images | WebP or AVIF, under 150 KB each where possible |
| Colour contrast | Pass all rules in section 3.2 |
| Mobile friendly | Tested at 320, 375, 768 and 1280 widths |
| Custom 404 | Implemented per section 8.9 |
| Form validation | Inline, accessible messages |
| Cookie banner | Per section 7.8 |
| One clear call to action | "Check a job now" is the only primary action on the landing page |
