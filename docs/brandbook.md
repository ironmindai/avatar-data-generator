# Galacticos AI Avatar Data Generator - Brand Guidelines

> *Maintained by: frontend-brand-guardian agent*

## Project Overview

**Project Name:** Avatar Data Generator by Galacticos AI
**Brand Identity:** Premium Developer Tools / Technical Product
**Design Philosophy:** Sophisticated, precise, and technical - inspired by VS Code, GitHub Dark Mode, Railway, and professional development tools
**Visual Style:** Charcoal backgrounds, neon electric accents, sharp corners, monospace technical elements
**Primary Use Case:** Enterprise-grade avatar data generation platform
**Target Audience:** Developers, AI practitioners, and technical professionals

---

## Color System

### Background Palette (Charcoal & Dark Grays)
- **Charcoal Primary:** `#1a1a1a` - Main background (deep charcoal)
- **Charcoal Secondary:** `#0f0f0f` - Darker variation for depth
- **Charcoal Elevated:** `#242424` - Elevated surfaces (cards, modals)
- **Charcoal Hover:** `#2a2a2a` - Interactive element hover states
- **Charcoal Border:** `#333333` - Subtle borders and dividers

### Accent Colors (Neon Electric)
- **Neon Cyan:** `#00d9ff` - Primary accent (buttons, links, highlights)
- **Neon Blue:** `#0088ff` - Secondary accent, interactive states
- **Neon Cyan Dark:** `#00a8cc` - Hover states for cyan elements
- **Neon Blue Dark:** `#0066cc` - Hover states for blue elements

### Text Colors (High Contrast)
- **Text Primary:** `#ffffff` - Primary text (pure white for maximum contrast)
- **Text Secondary:** `#cccccc` - Secondary text, descriptions
- **Text Tertiary:** `#999999` - Tertiary text, captions
- **Text Muted:** `#666666` - Disabled text, very subtle content
- **Text Placeholder:** `#555555` - Input placeholders

### Semantic Colors
- **Success:** `#00ff88` - Success states, confirmations (neon green)
- **Success Dark:** `#00cc6a` - Success hover states
- **Warning:** `#ffaa00` - Warning states (electric amber)
- **Warning Dark:** `#cc8800` - Warning hover
- **Error:** `#ff4466` - Error states, destructive actions (neon red)
- **Error Dark:** `#cc3355` - Error hover states
- **Info:** `#00d9ff` - Informational elements (neon cyan)

### Terminal/Code Colors (Monospace Context)
- **Code Background:** `#0f0f0f` - Code block backgrounds
- **Code Text:** `#00ff88` - Code text (terminal green)
- **Code Comment:** `#666666` - Comments
- **Code Keyword:** `#00d9ff` - Keywords (cyan)
- **Code String:** `#ffaa00` - Strings (amber)

### CSS Variable Names (IMPORTANT - Use These Exact Names)

**Background Variables:**
- `var(--color-bg-primary)` → `#1a1a1a` (Charcoal Primary)
- `var(--color-bg-secondary)` → `#0f0f0f` (Charcoal Secondary)
- `var(--color-bg-elevated)` → `#242424` (Charcoal Elevated)
- `var(--color-bg-hover)` → `#2a2a2a` (Charcoal Hover)
- `var(--color-border)` → `#333333` (Charcoal Border)

**Accent Variables:**
- `var(--color-accent-cyan)` → `#00d9ff` (Neon Cyan)
- `var(--color-accent-blue)` → `#0088ff` (Neon Blue)
- `var(--color-accent-cyan-dark)` → `#00a8cc` (Neon Cyan Dark)
- `var(--color-accent-blue-dark)` → `#0066cc` (Neon Blue Dark)

**Text Variables:**
- `var(--color-text-primary)` → `#ffffff` (Text Primary)
- `var(--color-text-secondary)` → `#cccccc` (Text Secondary)
- `var(--color-text-tertiary)` → `#999999` (Text Tertiary)
- `var(--color-text-muted)` → `#666666` (Text Muted)
- `var(--color-text-placeholder)` → `#555555` (Text Placeholder)

**Semantic Variables:**
- `var(--color-success)` → `#00ff88` (Success)
- `var(--color-warning)` → `#ffaa00` (Warning)
- `var(--color-error)` → `#ff4466` (Error)
- `var(--color-info)` → `#00d9ff` (Info)

**⚠️ DO NOT use non-existent variables like:**
- ❌ `var(--color-charcoal-*)` - These don't exist!
- ✅ Use `var(--color-bg-*)` instead

---

## Typography System

### Font Families
- **Primary Font:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif`
- **Monospace Font:** `'JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', 'Monaco', 'Courier New', monospace`

### Font Usage Guidelines
- **Monospace Elements:** Code snippets, technical labels, data fields, technical metrics
- **Sans-serif Elements:** Body text, descriptions, headings (except technical headings)
- **Technical Headings:** Use monospace for highly technical page titles or section headers

### Font Sizes (Precise Scale)
- **Hero:** `3rem` (48px) - Hero headings
- **H1:** `2rem` (32px) - Page titles
- **H2:** `1.5rem` (24px) - Section headings
- **H3:** `1.25rem` (20px) - Subsection headings
- **H4:** `1rem` (16px) - Card titles
- **Body:** `0.875rem` (14px) - Default body text
- **Small:** `0.75rem` (12px) - Small text, captions
- **Tiny:** `0.6875rem` (11px) - Tiny text, labels

### Font Weights
- **Light:** `300` - Light emphasis (rare use)
- **Regular:** `400` - Body text
- **Medium:** `500` - Emphasized text, labels
- **Semibold:** `600` - Headings, buttons
- **Bold:** `700` - Strong emphasis

### Line Heights
- **Tight:** `1.2` - Headings
- **Normal:** `1.5` - Body text
- **Relaxed:** `1.6` - Long-form content

---

## Spacing System

Uses a tight, precise 4px base unit system:

- **0:** `0` (0px)
- **1:** `0.25rem` (4px)
- **2:** `0.5rem` (8px)
- **3:** `0.75rem` (12px)
- **4:** `1rem` (16px)
- **5:** `1.25rem` (20px)
- **6:** `1.5rem` (24px)
- **8:** `2rem` (32px)
- **10:** `2.5rem` (40px)
- **12:** `3rem` (48px)

### Container Widths
- **Max Width:** `1280px` - Maximum content width
- **Narrow Width:** `480px` - Login, narrow forms
- **Medium Width:** `800px` - Medium content
- **Wide Width:** `1440px` - Dashboard wide content

---

## Corner Radius Standards

**CRITICAL: NO ROUNDED CORNERS**
- **All Elements:** `border-radius: 0` - Sharp, precise corners throughout
- **Buttons:** `0` - Sharp rectangular buttons
- **Inputs:** `0` - Sharp input fields
- **Cards:** `0` - Sharp card edges
- **Modals:** `0` - Sharp modal windows
- **Badges:** `0` - Sharp badge rectangles

**Philosophy:** Sharp corners convey precision, technical expertise, and professional tooling. This is a core brand differentiator.

---

## Component Patterns

### Buttons (Developer Tools Style)

#### Primary Button (Neon Glow)
- **Background:** `#00d9ff` (neon cyan)
- **Text:** `#0f0f0f` (dark for contrast)
- **Padding:** `0.75rem 1.5rem` (12px 24px)
- **Border:** `none`
- **Border Radius:** `0` - SHARP CORNERS
- **Font Size:** `0.875rem` (14px)
- **Font Weight:** `600` (semibold)
- **Font Family:** `var(--font-primary)` (sans-serif)
- **Text Transform:** `uppercase`
- **Letter Spacing:** `0.05em` (wider for impact)
- **Box Shadow (default):** `0 0 20px rgba(0, 217, 255, 0.3)` (neon glow)
- **Box Shadow (hover):** `0 0 30px rgba(0, 217, 255, 0.6), 0 0 60px rgba(0, 217, 255, 0.3)` (enhanced glow)
- **Hover:** Background `#00a8cc`, enhanced glow
- **Active:** Background `#008fb3`, glow reduced
- **Focus:** Glow `0 0 0 3px rgba(0, 217, 255, 0.4)`
- **Transition:** `all 0.2s ease-out`

#### Secondary Button (Outlined with Glow)
- **Background:** `transparent`
- **Border:** `1px solid #00d9ff`
- **Text:** `#00d9ff`
- **Padding:** `0.75rem 1.5rem`
- **Border Radius:** `0` - SHARP CORNERS
- **Font Size:** `0.875rem`
- **Font Weight:** `600`
- **Text Transform:** `uppercase`
- **Letter Spacing:** `0.05em`
- **Box Shadow (default):** `0 0 15px rgba(0, 217, 255, 0.2)` (subtle glow)
- **Hover:** Border color `#00d9ff`, background `rgba(0, 217, 255, 0.1)`, glow `0 0 25px rgba(0, 217, 255, 0.4)`
- **Transition:** `all 0.2s ease-out`

#### Ghost Button
- **Background:** `transparent`
- **Text:** `#cccccc`
- **Padding:** `0.75rem 1.5rem`
- **Border Radius:** `0` - SHARP CORNERS
- **Hover:** Background `#242424`, text `#ffffff`
- **Transition:** `all 0.2s ease-out`

#### Danger Button (Neon Red)
- **Background:** `#ff4466`
- **Text:** `#0f0f0f`
- **Box Shadow:** `0 0 20px rgba(255, 68, 102, 0.3)`
- **Hover:** Background `#cc3355`, glow `0 0 30px rgba(255, 68, 102, 0.6)`

### Input Fields (Sharp, Technical)

- **Background:** `#0f0f0f` (darker charcoal)
- **Border:** `1px solid #333333`
- **Border Radius:** `0` - SHARP CORNERS
- **Padding:** `0.75rem 1rem` (12px 16px)
- **Font Size:** `0.875rem` (14px)
- **Font Family:** `var(--font-primary)`
- **Text Color:** `#ffffff`
- **Placeholder:** `#666666`
- **Focus:** Border color `#00d9ff`, box shadow `0 0 20px rgba(0, 217, 255, 0.3)` (neon glow)
- **Hover:** Border color `#444444`
- **Error State:** Border color `#ff4466`, box shadow `0 0 20px rgba(255, 68, 102, 0.3)`
- **Disabled:** Opacity `0.5`, cursor `not-allowed`
- **Transition:** `all 0.2s ease-out`

### Monospace Input Fields (Code/Data Entry)
- **Font Family:** `var(--font-mono)`
- **Background:** `#0f0f0f`
- **Text Color:** `#00ff88` (terminal green)
- **All other properties:** Same as standard input

### Textarea (Multi-line Input)
- Same styling as input fields
- **Min Height:** `120px`
- **Resize:** Vertical only
- **Line Height:** `1.5`

### Cards (Sharp, Grid-Based)

- **Background:** `#1a1a1a` (charcoal primary)
- **Border:** `1px solid #333333`
- **Border Radius:** `0` - SHARP CORNERS
- **Padding:** `1.5rem` (24px)
- **Box Shadow:** `none` (sharp, flat design)
- **Hover (interactive cards):** Border color `#00d9ff`, box shadow `0 0 20px rgba(0, 217, 255, 0.15)` (subtle glow)
- **Transition:** `all 0.2s ease-out`

### Card Variants

#### Elevated Card
- **Background:** `#242424`
- **Border:** `1px solid #444444`

#### Code Card (Technical Content)
- **Background:** `#0f0f0f`
- **Border:** `1px solid #00d9ff`
- **Font Family:** `var(--font-mono)`

### Navigation (Header & Sidebar)

#### Header
- **Background:** `#1a1a1a`
- **Border Bottom:** `1px solid #333333`
- **Height:** `60px`
- **Padding:** `0 1.5rem`
- **Box Shadow:** `0 2px 10px rgba(0, 0, 0, 0.5)`
- **Position:** `sticky; top: 0; z-index: 50;`

#### Sidebar
- **Background:** `#1a1a1a`
- **Border Right:** `1px solid #333333`
- **Width:** `240px`
- **Padding:** `1.5rem 0.75rem`

#### Nav Link (Sidebar)
- **Padding:** `0.75rem 1rem`
- **Border Radius:** `0` - SHARP CORNERS
- **Font Size:** `0.875rem`
- **Font Weight:** `500`
- **Text Color:** `#999999`
- **Icon Size:** `18px`
- **Gap:** `0.75rem` (between icon and text)
- **Hover:** Background `#242424`, text `#ffffff`
- **Active:** Background `rgba(0, 217, 255, 0.1)`, border-left `3px solid #00d9ff`, text `#00d9ff`, padding-left `calc(1rem - 3px)`
- **Transition:** `all 0.15s ease-out`

### Alert Messages (Technical)

- **Border:** `1px solid`
- **Border Radius:** `0` - SHARP CORNERS
- **Padding:** `0.75rem 1rem`
- **Font Size:** `0.875rem`
- **Font Weight:** `500`
- **Border Left Width:** `3px` (accent indicator)
- **Icon Size:** `18px`
- **Gap:** `0.75rem` between icon and text

#### Success Alert
- **Background:** `rgba(0, 255, 136, 0.1)`
- **Border:** `1px solid rgba(0, 255, 136, 0.3)`
- **Border Left Color:** `#00ff88`
- **Text Color:** `#00ff88`

#### Error Alert
- **Background:** `rgba(255, 68, 102, 0.1)`
- **Border:** `1px solid rgba(255, 68, 102, 0.3)`
- **Border Left Color:** `#ff4466`
- **Text Color:** `#ff4466`

#### Warning Alert
- **Background:** `rgba(255, 170, 0, 0.1)`
- **Border:** `1px solid rgba(255, 170, 0, 0.3)`
- **Border Left Color:** `#ffaa00`
- **Text Color:** `#ffaa00`

#### Info Alert
- **Background:** `rgba(0, 217, 255, 0.1)`
- **Border:** `1px solid rgba(0, 217, 255, 0.3)`
- **Border Left Color:** `#00d9ff`
- **Text Color:** `#00d9ff`

### Badges (Sharp Rectangles)

- **Padding:** `0.25rem 0.5rem` (4px 8px)
- **Border Radius:** `0` - SHARP CORNERS
- **Font Size:** `0.6875rem` (11px)
- **Font Weight:** `600`
- **Text Transform:** `uppercase`
- **Letter Spacing:** `0.05em`
- **Display:** Inline-flex
- **Align Items:** Center

#### Badge Variants

**Primary Badge**
- Background: `#00d9ff`
- Text: `#0f0f0f`

**Success Badge**
- Background: `#00ff88`
- Text: `#0f0f0f`

**Error Badge**
- Background: `#ff4466`
- Text: `#ffffff`

**Warning Badge**
- Background: `#ffaa00`
- Text: `#0f0f0f`

### Loading States (Technical)

#### Spinner
- **Size:** `32px`
- **Border Width:** `3px`
- **Border Color:** `#333333` (base)
- **Border Top Color:** `#00d9ff` (animated)
- **Border Radius:** `50%` (exception for circular spinner)
- **Animation:** Rotate 0.8s linear infinite

#### Loading Overlay
- **Background:** `rgba(15, 15, 15, 0.9)`
- **Position:** Absolute, full coverage
- **Display:** Flex, centered
- **Z-index:** `50`

---

## Glow Effects (Neon Aesthetic)

### Button Glow (Primary CTA)
- **Default:** `box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);`
- **Hover:** `box-shadow: 0 0 30px rgba(0, 217, 255, 0.6), 0 0 60px rgba(0, 217, 255, 0.3);`
- **Active:** `box-shadow: 0 0 15px rgba(0, 217, 255, 0.4);`

### Input Focus Glow
- **Focus:** `box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);`

### Card Hover Glow (Interactive)
- **Hover:** `box-shadow: 0 0 20px rgba(0, 217, 255, 0.15);`

### Error Glow
- **Error State:** `box-shadow: 0 0 20px rgba(255, 68, 102, 0.3);`

### Success Glow
- **Success State:** `box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);`

**Philosophy:** Glow effects create the neon, electric aesthetic. Use subtle glows (opacity 0.2-0.3) for default states, enhanced glows (0.5-0.6) for hover/active states.

---

## Layout Standards

### Responsive Breakpoints
- **Mobile:** `< 640px`
- **Tablet:** `640px - 1024px`
- **Desktop:** `> 1024px`
- **Wide Desktop:** `> 1440px`

### Grid System (Precise Alignment)
- **Desktop:** 12-column grid with 24px gutters
- **Tablet:** 8-column grid with 16px gutters
- **Mobile:** 4-column grid with 12px gutters

**Grid Philosophy:** Use CSS Grid for layout precision. Grid-based design ensures perfect alignment and technical appearance.

---

## Accessibility Standards

- **Minimum Contrast Ratio:** 7:1 for normal text (WCAG AAA) - ensured by white text on charcoal
- **Focus Indicators:** Visible neon glow: `box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.4);`
- **Keyboard Navigation:** All interactive elements must be keyboard accessible
- **ARIA Labels:** Use appropriate ARIA labels for screen readers
- **Alt Text:** All images must have descriptive alt text

---

## Animation Guidelines

### Transitions (Precise, Snappy)
- **Fast:** `0.15s` - Instant feedback (hovers, focus)
- **Base:** `0.2s` - Default transitions
- **Slow:** `0.3s` - Deliberate animations (modals)
- **Easing:** `ease-out` (snappy, technical feel)

### Hover Effects (Subtle Glows)
- **Buttons:** Enhanced glow effect
- **Cards:** Border color change + subtle glow
- **Links:** Color change to neon cyan
- **Icons:** Glow effect on hover

### Focus States (Accessibility)
- **Glow:** `box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.4);`
- **Transition:** `0.2s ease-out`

---

## Logo Usage

### Primary Logo
- **File:** `logo-white.jpeg`
- **Usage:** All contexts (white logo on dark backgrounds)
- **Minimum Size:** 120px width

### Logo Placement
- **Login Page:** Centered, 160px width
- **Dashboard Header:** Left-aligned, 120px width

---

## Code Style Conventions

### CSS Organization
1. Use CSS custom properties for all colors, spacing, and typography
2. Define variables in `:root` selector
3. Use utility classes for common patterns
4. Group related styles together
5. NO rounded corners anywhere - always `border-radius: 0`

### HTML Structure
- Use semantic HTML5 elements (`<header>`, `<nav>`, `<main>`, `<section>`)
- Proper heading hierarchy (h1 → h2 → h3)
- Include ARIA labels for accessibility
- Use form elements with proper labels

### File Organization
- `static/css/` - Stylesheets
- `static/js/` - JavaScript files
- `static/images/` - Image assets
- `templates/` - HTML templates

---

## Template Structure (Jinja2 Inheritance)

All templates use Jinja2 template inheritance with `templates/base.html` as the base template.

### Base Template (`base.html`)
Provides:
- Common HTML structure
- Header navigation (conditional via `show_header`)
- Sidebar navigation (conditional via `show_sidebar`)
- Alert message section

**Available Blocks:**
- `{% block title %}` - Page title
- `{% block extra_css %}` - Page-specific stylesheets
- `{% block content %}` - Main content (for pages with sidebar)
- `{% block standalone_content %}` - Standalone content (for pages without sidebar)
- `{% block extra_js %}` - Page-specific JavaScript

---

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile Safari: iOS 13+
- Chrome Android: Last 2 versions

---

## Design Principles

1. **Technical Precision:** Sharp corners, precise alignment, grid-based layout
2. **High Contrast:** White text on charcoal backgrounds for maximum readability
3. **Neon Accents:** Electric cyan/blue for interactive elements with subtle glows
4. **Monospace Context:** Use monospace fonts for technical elements
5. **Sophisticated Simplicity:** Clean, minimal, professional - like premium dev tools
6. **Dark First:** Design exclusively for dark mode (charcoal aesthetic)

---

## Recent Updates

### 2026-01-30 - Settings Page Implementation

**New Template Created:**
- Settings page for bio prompts configuration
- Four textarea fields for platform-specific bio prompts (Facebook, Instagram, X/Twitter, TikTok)
- Form state tracking with dirty state detection
- AJAX submission to `/settings/save` endpoint
- Save button only enabled when changes are detected
- Loading state with spinner during save
- Success/error toast notifications
- Reset to original values functionality
- Character counters for all textarea fields
- Responsive design for mobile/tablet/desktop

**Components Added:**

**Toast Notification System**
- Fixed position: Bottom-right corner (2rem from edges)
- Background: `#242424` (charcoal elevated)
- Border-left: 3px solid (success/error color)
- Success glow: `0 0 30px rgba(0, 255, 136, 0.3)`
- Error glow: `0 0 30px rgba(255, 68, 102, 0.3)`
- Slide-in animation (0.3s ease-out)
- Auto-hide after 4 seconds
- Sharp corners, responsive design

**Character Counter**
- Font: Monospace (`var(--font-mono)`)
- Size: 11px
- Color: `#666666` (muted text)
- Position: Below textarea, right-aligned
- Updates in real-time on input

**Files Created:**
- `/templates/settings.html` - Settings page template
- `/static/css/settings.css` - Settings page styles
- `/static/js/settings.js` - Form state management and AJAX

**Navigation:**
- Settings link already present in sidebar (base.html)

---

### 2026-01-30 - Generate Page Layout Optimization

**Layout Improvements:**
- Added max-width constraint (1280px) to prevent content from stretching on wide screens
- Implemented horizontal form row layout for compact controls
- Bio Language, Number to Generate, and Images per Persona now display in one horizontal row
- Professional field widths: Selects limited to 400px max-width
- Responsive grid layout with `auto-fit` for adaptive column arrangement
- Improved spacing and visual hierarchy
- Better mobile responsiveness with single-column layout on smaller screens

**CSS Updates:**
- New `.content-wrapper` class for max-width constraint and centered content
- New `.form-row` class for horizontal grid layout (280px minimum column width)
- Form selects limited to 400px max-width for professional appearance
- Select2 containers inherit width constraints within form rows
- Responsive breakpoints at 1024px (collapse to single column), 768px, and 480px

**Files Modified:**
- `/templates/generate.html` - Restructured layout with content wrapper and form rows
- `/static/css/generate.css` - Added layout constraints and responsive grid

### 2026-01-30 - Generate Page Implementation

**New Components Added:**

**Custom Radio Buttons (Sharp, Technical)**
- Sharp square radio buttons with neon glow on selection
- Background: `#0f0f0f` (darker charcoal)
- Border: `1px solid #333333`
- Checked state: Background `#00d9ff`, glow `0 0 15px rgba(0, 217, 255, 0.5)`
- Inner indicator: 8px square in `#0f0f0f`
- Hover: Border color `#00d9ff`

**Range Slider (Technical Control)**
- Track: 4px height, `#333333` background, sharp edges
- Thumb: 20px square (sharp corners), `#00d9ff` background
- Thumb glow: `0 0 15px rgba(0, 217, 255, 0.5)`
- Hover: Enhanced glow `0 0 25px rgba(0, 217, 255, 0.7)`

**Select2 Integration (Searchable Dropdowns)**
- Custom dark theme matching brandbook
- Sharp corners throughout (no rounded borders)
- Neon cyan accents and glow effects
- Background: `#0f0f0f` for inputs, `#242424` for dropdown
- Focus glow: `0 0 20px rgba(0, 217, 255, 0.3)`
- Dropdown glow: `0 0 30px rgba(0, 217, 255, 0.4)`

**Loading Overlay (Technical Loading State)**
- Full-screen overlay: `rgba(15, 15, 15, 0.95)`
- Circular spinner (exception for circular element): 64px, 4px border
- Spinner colors: `#333333` base, `#00d9ff` animated top
- Loading text: Monospace font, uppercase, pulsing animation
- Z-index: 9999

**Files Created:**
- `/templates/generate.html` - Avatar generation form
- `/static/css/generate.css` - Generate page styles
- `/static/js/generate.js` - Form interactivity
- Updated `/templates/base.html` - Added "Generate Avatars" to navigation

---

### 2026-01-30 - Complete Brand Overhaul: Developer Tools Aesthetic

**Complete redesign to premium developer tools visual style:**

**Core Visual Changes:**
- **Backgrounds:** Charcoal (#1a1a1a primary, #0f0f0f dark, #242424 elevated)
- **Accent Colors:** Neon electric cyan (#00d9ff) and blue (#0088ff)
- **Corner Radius:** Sharp corners throughout (border-radius: 0 everywhere)
- **Text:** Pure white (#ffffff) for maximum contrast
- **Effects:** Neon glow effects on all interactive elements

**Typography:**
- Monospace fonts for technical elements (code, data, technical labels)
- Sans-serif for body text and most headings
- Uppercase button text with wide letter spacing (0.05em)

**Components:**
- Buttons with neon glow effects (subtle default, enhanced on hover)
- Sharp-cornered inputs with focus glow effects
- Sharp-cornered cards with optional hover glow
- Technical alert messages with sharp borders
- Sharp badge rectangles with uppercase text
- Grid-based layouts for precise alignment

**Navigation:**
- Active sidebar items with left border accent (3px solid #00d9ff)
- Header with subtle drop shadow
- Sharp corners on all navigation elements

**Philosophy:**
- Inspired by VS Code, GitHub Dark Mode, Railway, and premium dev tools
- Sophisticated, precise, technical aesthetic
- Clean, minimal, professional appearance
- High contrast for optimal readability
- Neon glows for modern, electric feel

**Files Modified:**
- Complete rewrite of brandbook.md with new design system
- main.css will be updated with sharp corners, charcoal backgrounds, neon accents
- login.html and login.css redesigned with new aesthetic
- dashboard.html and dashboard.css redesigned with new aesthetic
- base.html updated to support new design system

---

*Last Updated: 2026-01-30 (Developer Tools Aesthetic Overhaul)*
