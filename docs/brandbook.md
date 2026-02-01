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
- **Padding:** `16px 32px` (vertical 16px, horizontal 32px on desktop)
  - Tablet (≤1024px): `12px 24px`
  - Mobile (≤640px): `12px 16px`
- **Box Shadow:** `0 2px 10px rgba(0, 0, 0, 0.5)`
- **Position:** `sticky; top: 0; z-index: 50;`
- **Layout:** Full-width with `justify-content: space-between` for left/right alignment
- **Note:** Removed fixed height to allow content-based height with proper vertical padding

#### Header Brand (Logo & Title)
- **Layout:** Flexbox, left-aligned, `16px` gap between logo and title
- **Logo Size:** `64px` height (desktop), `48px` (mobile)
- **Title Text:** "Avatar Data & Image Generator"
- **Title Font Size:** `1.25rem` (20px - H3 size on desktop), `0.875rem` (14px on mobile)
- **Title Font Weight:** `600` (semibold)
- **Title Color:** `#ffffff` (primary text)
- **Title Margin:** `0` (no margin, controlled by flex gap)
- **Title Behavior:** `white-space: nowrap` (prevents wrapping)

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

### Page Container Pattern (CRITICAL - Use Consistently)

All page-level content MUST be wrapped in a `.content-wrapper` container to maintain consistent width across the application.

**CSS Class: `.content-wrapper`**
```css
.content-wrapper {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--spacing-6); /* 24px horizontal padding */
}
```

**Usage in Templates:**
```html
{% block content %}
<div class="content-wrapper">
    <!-- All page content goes here -->
    <div class="page-header">...</div>
    <div class="page-body">...</div>
</div>
{% endblock %}
```

**Responsive Padding:**
- Desktop (>768px): `0 var(--spacing-6)` (24px)
- Tablet/Mobile (≤768px): `0 var(--spacing-4)` (16px)

**Why This Matters:**
- Prevents content from stretching excessively on wide screens
- Maintains comfortable reading width and visual hierarchy
- Ensures consistent layout across all pages (generate, settings, history, etc.)
- Centers content horizontally on the page

**Pages Using This Pattern:**
- `/generate` - Generate Avatars page
- `/settings` - Settings page
- `/history` - Generation History page
- All future authenticated pages MUST follow this pattern

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

### 2026-01-30 - Generate Form Submission Fix

**Issue Fixed:**
- Duplicate form validation listeners causing potential validation bypass
- First listener validated but didn't show loading state
- Second listener showed loading state but didn't properly prevent invalid submission

**Solution:**
- Consolidated validation into single submission handler
- Form now properly validates before showing loading overlay
- Invalid forms are prevented from submitting with clear error messages
- Loading overlay only displays for valid form submissions

**Form Submission Flow:**
1. User clicks "Generate Avatars"
2. Client-side validation runs (persona description, language, number, images per persona)
3. If validation fails: Alert shown, submission prevented, no loading overlay
4. If validation succeeds: Loading overlay displays, form inputs disabled, form submits naturally
5. Backend receives POST request to `/generate` with form data (not JSON)
6. Backend validates server-side and redirects to dashboard with flash message

**Files Modified:**
- `/static/js/generate.js` - Consolidated validation logic into submission handler

---

### 2026-01-31 - Crop White Borders Setting Added

**New Setting Created:**
- Added "Crop White Borders" toggle as the first setting in Face Generation Settings section
- Boolean checkbox that controls automatic white border removal from generated images
- Setting stored in Config table with key `crop_white_borders`
- Default value: False (disabled)
- Integrated with existing face settings form and state management
- Saves via AJAX to `/settings/save` endpoint
- Migration created: `70c50b9233b6_add_crop_white_borders_config.py`

**Components Updated:**
- Settings template: Added checkbox before "Randomize Face" option
- Settings JavaScript: Integrated into face settings state tracking
- Backend: Added to expected_boolean_keys and template rendering
- Checkbox follows brandbook styling (sharp corners, neon cyan glow on checked)

**Files Modified:**
- `/templates/settings.html` - Added crop_white_borders checkbox
- `/static/js/settings.js` - Added state management for new checkbox
- `/app.py` - Added to settings loading and saving logic
- `/migrations/versions/70c50b9233b6_add_crop_white_borders_config.py` - Database migration

---

### 2026-02-01 - Max Concurrent Tasks Setting Added

**New Setting Created:**
- Added "Max Concurrent Tasks" number input in Face Generation Settings section
- Number input allowing users to control how many tasks process simultaneously
- Setting stored in IntConfig table with key `max_concurrent_tasks`
- Default value: 1 (sequential processing)
- Range: 1-5 with step of 1
- Positioned after "Gender Lock" and before form action buttons

**Components Updated:**
- Settings template: Added number input with validation attributes and range info
- Settings CSS: Added `.form-number-input` and `.number-input-wrapper` styles with:
  - Monospace font (H3 size, 20px) for technical prominence
  - Cyan color for value display
  - Centered text alignment
  - Sharp corners, neon cyan glow on focus
  - Hidden browser spinners for cleaner appearance
  - Max-width 150px for compact display
  - Range label showing "Range: 1-5" in small monospace text
- Settings JavaScript:
  - Added `maxConcurrentTasksInput` to elements object
  - Added `validateMaxConcurrentTasks()` function with min/max clamping
  - Integrated into face settings state tracking
  - Added input/blur event listeners for validation and dirty state
  - Included in form submission data
  - Added to reset functionality
- Backend:
  - Added `expected_integer_keys` list with `max_concurrent_tasks`
  - Added integer validation (type check + range 1-5)
  - Saves to IntConfig table via `IntConfig.set_value()`
  - Loads from IntConfig with default value of 1
  - Passes to template rendering

**Implementation Details:**
- Label: "MAX CONCURRENT TASKS" with zap icon (lightning bolt)
- Description: "Maximum number of generation tasks that can run simultaneously (1 = sequential processing)"
- Input type: number with min="1", max="5", step="1"
- Validation: Client-side clamping on input/blur, server-side range validation
- State tracking: Independent from other settings, tracked in faceSettings state
- Save button: Enables when value differs from original database value
- Reset button: Restores original database value

**Files Modified:**
- `/templates/settings.html` - Added max_concurrent_tasks number input (lines 119-144)
- `/static/css/settings.css` - Added number input styles (lines 292-353)
- `/static/js/settings.js` - Added state management, validation, event listeners (lines 50, 93, 138-147, 414-439, 446-453, 486-487, 495, 569)
- `/app.py` - Added IntConfig loading/saving with range validation (lines 604, 614, 651-653, 656, 699-721)
- `/docs/brandbook.md` - Documented implementation

**Design Rationale:**
- Number input provides precise control over concurrency level
- Monospace cyan number display follows technical aesthetic
- Range 1-5 prevents system overload while allowing parallelization
- Consistent with brandbook: Sharp corners, neon accents, validation feedback
- Clear labeling explains sequential (1) vs parallel (2-5) behavior

---

### 2026-02-01 - Randomize Image Styles Setting Added

**New Setting Created:**
- Added "Randomize Image Styles" toggle as the second setting in Face Generation Settings section
- Boolean checkbox that controls random style variations to make images look like different sources
- Setting stored in Config table with key `randomize_image_style`
- Positioned after "Crop White Borders" and before "Randomize Face" options
- Integrated with existing face settings form and state management
- Saves via AJAX to `/settings/save` endpoint
- Default value: False (disabled)

**Components Updated:**
- Settings template: Added checkbox after "Crop White Borders" option
- Settings JavaScript:
  - Added randomizeImageStyleCheckbox to elements object
  - Integrated into face settings state tracking (storeFaceSettingsOriginalValues)
  - Added change event listener for dirty state detection
  - Included in checkFaceSettingsDirtyState function
  - Added to form submission data (handleFaceSettingsSubmit)
  - Added to reset functionality (handleFaceSettingsReset)
- Checkbox follows brandbook styling (sharp corners, neon cyan glow on checked)

**Implementation Details:**
- Label: "RANDOMIZE IMAGE STYLES" (uppercase, semibold, letter-spacing 0.05em)
- Description: "Apply random style variations to make images look like different sources"
- Consistent styling with other Face Generation Settings checkboxes
- State tracked independently from other settings
- Save button enables only when changes are detected
- Reset button restores original database value

**Files Modified:**
- `/templates/settings.html` - Added randomize_image_style checkbox between crop_white_borders and randomize_face_base
- `/static/js/settings.js` - Added complete state management, event listeners, submission, and reset handling
- `/docs/brandbook.md` - Documented new setting implementation

**Backend Integration Required:**
- Backend must handle `randomize_image_style` boolean field in `/settings/save` endpoint
- Backend must pass `randomize_image_style` value to template when rendering settings page
- Database migration required to add `randomize_image_style` to Config table (if not already present)

---

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

### 2026-01-30 - History Page Implementation

**New Page Created:**
- Generation history page for viewing all avatar generation tasks
- Table layout for desktop (responsive, full data visibility)
- Card layout for mobile/tablet (stacked, touch-friendly)
- Empty state for when no tasks exist
- Error modal for viewing detailed error logs

**Components Added:**

**History Table (Desktop)**
- Full-width responsive table with horizontal scroll
- Column headers: Task ID, Status, Persona Description, Language, Count, Images, Created, Completed, Actions
- Row hover effect: Background changes to elevated color
- Monospace font for technical data (Task ID, language, dates)
- Status badges with color-coded glows
- Copy button for Task ID with success animation
- View error button for failed tasks

**Task Cards (Mobile/Tablet)**
- Stacked card layout below 1024px breakpoint
- Card header with Task ID and status badge
- Card body with all task details in vertical layout
- Responsive grid for compact details (language, count, images)
- View error button for failed tasks

**Status Badge System**
- Completed: Green (#00ff88) with success glow
- Failed: Red (#ff4466) with error glow
- Generating (Data/Images): Amber (#ffaa00) with warning glow
- Pending: Cyan (#00d9ff) with info glow
- Sharp corners, uppercase text, letter-spacing 0.05em
- Icons from Feather Icons library

**Error Modal**
- Full-screen modal overlay with backdrop blur
- Modal content: Header, body with error details, footer with close button
- Task ID display with monospace font
- Error message in code block format (pre tag, monospace)
- Left border accent (3px solid red)
- Keyboard support (Escape key closes modal)
- Click backdrop to close
- Sharp corners, neon cyan border glow

**Copy to Clipboard Feature**
- Modern Clipboard API with fallback for older browsers
- Visual feedback: Button turns green with check icon for 2 seconds
- Success animation with glow effect
- Works on both desktop table and mobile cards

**Empty State**
- Large inbox icon (80px)
- Centered message: "No Generation Tasks Yet"
- Description text explaining how to create first task
- Primary CTA button: "Generate Avatars" linking to /generate

**Interactive Features (JavaScript)**
- Copy Task ID to clipboard with visual feedback
- Error modal open/close with smooth transitions
- Feather icons initialization
- Keyboard navigation (Escape to close modal)
- Event delegation for performance
- Commented optional auto-refresh feature (30-second interval)

**Responsive Breakpoints:**
- Desktop (>1024px): Table layout
- Tablet/Mobile (≤1024px): Card layout
- Mobile (≤640px): Single column, reduced spacing

**Files Created:**
- `/templates/history.html` - History page template with Jinja2 logic
- `/static/css/history.css` - History page styles with table/card layouts
- `/static/js/history.js` - Interactive features (copy, modal, icons)

**Navigation:**
- History link already present in sidebar (base.html)

---

### 2026-01-30 - History Page Width Consistency Fix

**Issue Fixed:**
- History page had inconsistent width compared to generate and settings pages
- Content was stretching full-width without the standard max-width constraint

**Solution:**
- Added `.content-wrapper` CSS class to `/static/css/history.css` with standard constraints:
  - `max-width: 1280px`
  - `margin: 0 auto` (centered)
  - `padding: 0 var(--spacing-6)` with responsive adjustments
- Wrapped history.html content in `<div class="content-wrapper">` container
- Documented Page Container Pattern in brandbook Layout Standards section

**Standardized Pattern:**
All authenticated pages (generate, settings, history, dashboard) now use the same `.content-wrapper` pattern for consistent width and centering.

**Files Modified:**
- `/static/css/history.css` - Added `.content-wrapper` class and responsive padding
- `/templates/history.html` - Wrapped content in `.content-wrapper` div
- `/docs/brandbook.md` - Added "Page Container Pattern" documentation

---

### 2026-01-30 - Header Logo & Title Enhancement

**Changes Made:**
- Doubled logo size from 32px to 64px height (desktop)
- Added "Avatar Data & Image Generator" title text next to logo
- Positioned logo and title on left side of header using flexbox
- Added 16px gap between logo and title for professional spacing
- Implemented responsive sizing: 48px logo on mobile, 14px title font size on mobile
- Maintained sharp corners and brandbook color compliance
- Title uses semibold weight (600) with white color for maximum contrast
- Added white-space: nowrap to prevent title wrapping

**Layout Structure:**
```
[LOGO (64px)]  Avatar Data & Image Generator     [user info + logout]
```

**Files Modified:**
- `/templates/base.html` - Added header-title element next to logo
- `/static/css/main.css` - Updated header-brand, header-logo, added header-title styles
- `/docs/brandbook.md` - Documented Header Brand component specifications

**Design Rationale:**
- Larger logo increases brand visibility and presence
- Title text provides immediate context about application purpose
- Left-aligned layout follows standard navigation patterns
- Responsive scaling ensures usability on all device sizes
- Maintains professional developer tools aesthetic with clean typography

---

### 2026-01-30 - Header Layout Alignment Fix

**Issue Identified:**
- Header content was centered on the page instead of left-aligned
- Logo and title appeared in the center of wide screens
- Insufficient vertical padding made header feel cramped
- Fixed height constraint prevented proper padding implementation

**Changes Made:**
- Removed `max-width: 1440px` and `margin: 0 auto` from `.header-content` to prevent centering
- Removed fixed `height: 60px` from `.header` to allow content-based height
- Updated header padding from `0 24px` to vertical and horizontal padding:
  - Desktop: `16px 32px` (proper breathing room)
  - Tablet (≤1024px): `12px 24px`
  - Mobile (≤640px): `12px 16px`
- Reduced mobile header-brand gap from 16px to 12px for tighter spacing on small screens
- Maintained `justify-content: space-between` for proper left/right alignment

**Layout Structure (FIXED):**
```
[32px padding] [LOGO] Avatar Data & Image Generator        [user info + logout] [32px padding]
```

**Files Modified:**
- `/static/css/main.css` - Fixed header layout, removed centering, added proper padding
- `/docs/brandbook.md` - Updated Header component specifications

**Design Rationale:**
- Full-width layout ensures logo starts from left edge with consistent padding
- Vertical padding provides better visual breathing room
- Responsive padding scales appropriately for different screen sizes
- Maintains professional developer tools aesthetic with proper spacing hierarchy

---

### 2026-01-30 - Datasets Viewing Feature Implementation

**New Templates Created:**
- Datasets list page for viewing all generation tasks with progress
- Dataset detail page with real-time updates, pagination, and export functionality
- Responsive design with table layout (desktop) and card layout (mobile/tablet)

**Components Added:**

**Breadcrumb Navigation**
- Display: Flex with chevron separators
- Font size: 12px (small)
- Link color: `#cccccc` (secondary text), hover: `#00d9ff` (cyan)
- Current page: Monospace font, primary text color
- Icon size: 16px for links, 14px for separators
- Gap: 8px between elements

**Progress Bar (Animated)**
- Container: 8px height, charcoal primary background, sharp corners
- Bar: Full height, animated width transition (0.3s ease-out)
- Completed state: Success green with glow `0 0 20px rgba(0, 255, 136, 0.3)`
- Failed state: Error red with glow `0 0 20px rgba(255, 68, 102, 0.3)`
- Generating state: Gradient background (warning to cyan) with pulse animation
- Progress percentage: H4 size, monospace, semibold
- Progress details: Small size, monospace, tertiary text color

**Statistics Panel**
- Grid layout: Auto-fit, minimum 200px columns, 16px gap
- Stat cards: Primary background, border, 24px padding, sharp corners
- Stat label: Small size, uppercase, letter-spacing 0.05em, tertiary color
- Stat value: H2 size, monospace, bold, primary text
- Stat description: Small size, secondary text

**Task Metadata Display**
- Grid layout: Auto-fit, minimum 250px columns, 16px gap
- Background: Secondary charcoal, border, 24px padding
- Label: Small size, uppercase, tertiary color
- Value: Body size, primary text, line-height normal
- Monospace variant for technical data (language, IDs)

**Export Buttons**
- Flex layout with 16px gap, wraps on mobile
- Secondary button style with download/package icons
- Disabled state: 50% opacity, no pointer events
- Loading state: Spinner animation, "Exporting..." text
- Full width on mobile devices

**Pagination Controls**
- Flex layout with 16px gap, wraps on small screens
- Pagination info: Small monospace text showing "X-Y of Z results"
- Page buttons: 36x36px, sharp corners, border, monospace
- Active button: Cyan background with glow `0 0 20px rgba(0, 217, 255, 0.3)`
- Hover: Elevated background, cyan border with glow
- Disabled: 30% opacity, no cursor
- Ellipsis: Monospace, muted text, centered in 36x36px space
- Icon buttons: Chevron left/right, 16px icons

**Result Cards (Persona Display)**
- Grid layout: Auto-fill, minimum 300px columns (desktop), single column (mobile)
- Card: Primary background, border, sharp corners, hover with cyan glow
- Image container: 1:1 aspect ratio, secondary background, zoom on hover (scale 1.05)
- Name: H4 size, semibold, primary text
- Gender badge: Tiny uppercase text, letter-spacing 0.05em
  - Male: Blue border/color `#0088ff`, blue background `rgba(0, 136, 255, 0.1)`
  - Female: Red border/color `#ff4466`, red background `rgba(255, 68, 102, 0.1)`
- Content padding: 16px

**Bio Platform Tabs**
- Flex layout with 4px gap, bottom border
- Tab button: 8px/12px padding, transparent background
- Active tab: Cyan text, 2px bottom border in cyan
- Hover: Primary text, elevated background
- Tab labels: Small uppercase, letter-spacing 0.05em
- Bio content: Small size, secondary text, relaxed line-height

**Gallery Thumbnails**
- Grid: 4 columns (desktop), 3 columns (mobile), 8px gap
- Thumbnail: 1:1 aspect ratio, border, sharp corners, cursor pointer
- Hover: Cyan border with subtle glow `0 0 15px rgba(0, 217, 255, 0.2)`
- Image: Object-fit cover, full container size
- Label: Small uppercase, tertiary color, medium weight

**Image Preview Modal**
- Full-screen overlay: `rgba(15, 15, 15, 0.95)` with backdrop blur (8px)
- Modal content: Centered, max 90vw/90vh
- Close button: Positioned -50px above image, 40x40px, elevated background
- Image: Sharp corners, cyan border, glow `0 0 40px rgba(0, 217, 255, 0.2)`
- Caption: Elevated background, border, 12px/16px padding, small monospace text
- Click backdrop or Escape key to close

**Error Log Section (Collapsible)**
- Container: Secondary background, error border (3px left), sharp corners
- Header: Error red background `rgba(255, 68, 102, 0.1)`, clickable
- Title: H4 size, error color, with alert-triangle icon (20px)
- Collapse button: 32x32px, error border, chevron icon rotates -90deg when collapsed
- Content: Max-height 400px, vertical scroll, 16px padding
- Error message: Monospace, small size, error color, primary background, pre-wrap

**Skeleton Loaders**
- Background: Gradient from secondary to elevated charcoal
- Animation: Shimmer effect (1.5s infinite) moving 200% left to right
- Variants:
  - Badge: 120px x 28px
  - Text: Full width x 20px
  - Stat: Full width x 80px
  - Progress: Full width x 60px
  - Image: 1:1 aspect ratio
- Sharp corners throughout

**Interactive Features (JavaScript)**
- Real-time polling: 3-second interval for task status updates
- Smart DOM updates: Only modify changed elements to prevent flicker
- Copy to clipboard: Modern API with visual feedback (green + check icon for 2s)
- Pagination: Updates URL with `?page=N` parameter, smooth scroll to top
- Bio tabs: Switch between platforms with active state highlighting
- Image preview: Click thumbnails or main image to view full-size in modal
- Export: Download JSON/CSV/ZIP with loading spinner, error handling
- Toast notifications: Slide-in from right, auto-dismiss after 4 seconds
- Stop polling when task completed/failed (prevents unnecessary API calls)

**Responsive Breakpoints:**
- Desktop (>1024px): Table layout, multi-column grids
- Tablet (641px-1024px): Card layout, 2-column grids
- Mobile (≤640px): Single column, stacked cards, reduced spacing

**API Integration:**
- Endpoint: `/datasets/<task_id>/data?page=<page_number>`
- Returns: Task metadata, statistics, results array, pagination info
- Export endpoints: `/datasets/<task_id>/export/{json,csv,zip}`
- Polling stops when task status is 'completed' or 'failed'

**Files Created:**
- `/templates/datasets.html` - Datasets list page with table/card views
- `/templates/dataset_detail.html` - Detail page with real-time updates
- `/static/css/datasets.css` - Complete styling for both pages
- `/static/js/datasets.js` - Interactive features and API integration

**Navigation:**
- Datasets link already present in sidebar (base.html)
- Active state highlights current page

**Empty States:**
- Datasets list: Database icon, "No datasets yet" message, CTA to generate
- Results grid: Inbox icon, "No results generated yet" message
- Error state: Alert icon with error message

**Accessibility:**
- ARIA labels on all interactive elements
- Keyboard navigation: Tab through controls, Escape closes modals
- Alt text on all images with descriptive names
- Focus states with cyan glow
- Proper heading hierarchy (h1 → h2 → h3)
- Time elements with ISO datetime attributes

**Design Philosophy:**
- Consistent with history page patterns (badges, cards, modals)
- Sharp corners and neon glows throughout
- Monospace fonts for technical data (IDs, dates, counts)
- Real-time updates without page refresh
- Progressive disclosure (collapsed error logs, paginated results)
- Smooth transitions and animations (0.2s-0.3s ease-out)

---

### 2026-01-30 - Dashboard Page Implementation

**New Page Created:**
- Complete dashboard page with statistics cards and charts
- Real-time data visualization with automatic refresh
- Overview statistics and 7-day trend charts
- Responsive design for mobile/tablet/desktop

**Components Added:**

**Statistics Cards (Primary and Secondary Rows)**
- Grid layout: Auto-fit, minimum 250px columns, 24px gap
- Card: Primary background, border, 24px padding, sharp corners
- Layout: Flexbox with icon (48px) and content area
- Icon: 32px Feather icons in neon cyan (or success/error colors)
- Hover: Cyan border with subtle glow `0 0 20px rgba(0, 217, 255, 0.15)`
- Stat value: H2 size, monospace font, bold, primary text
- Stat label: Small uppercase, letter-spacing 0.05em, secondary color
- Success variant: Green icon and hover glow
- Error variant: Red icon and hover glow

**Primary Statistics Cards:**
1. Total Tasks (icon: layers)
2. Total Personas (icon: users)
3. Total Images (icon: image)
4. Tasks in Progress (icon: clock)

**Secondary Statistics Cards:**
1. Completed Tasks (icon: check-circle, success green)
2. Failed Tasks (icon: x-circle, error red)
3. Avg Personas/Task (icon: trending-up)
4. Avg Images/Persona (icon: bar-chart-2)

**Chart Cards (3 Charts in Row)**
- Grid layout: Auto-fit, minimum 350px columns, 24px gap
- Card: Primary background, border, 24px padding, sharp corners
- Header: H4 title, semibold, primary text, 16px bottom margin
- Chart body: 250px min-height (200px on mobile)
- Hover: Cyan border with subtle glow

**Chart Types:**
1. Tasks Created (Last 7 Days) - Line chart, neon cyan (#00d9ff)
2. Personas Generated (Last 7 Days) - Line chart, neon green (#00ff88)
3. Images Generated (Last 7 Days) - Line chart, neon purple (#c77dff)

**Chart.js Configuration:**
- Line charts with smooth curves (tension: 0.4)
- Fill area under line with 20% opacity
- Point radius: 4px (6px on hover)
- Points: Colored with dark border (#1a1a1a), white hover border
- Grid lines: Subtle (#333333), no borders
- X-axis labels: Inter font, 11px, tertiary color
- Y-axis labels: Monospace font, 11px, formatted with commas
- Tooltips: Elevated background (#242424), colored border, 12px padding
- Dark theme colors throughout
- Responsive design with maintainAspectRatio: false

**Skeleton Loaders (Loading State)**
- Background: Gradient from secondary to elevated charcoal
- Animation: Shimmer effect (1.5s infinite) moving 200% left to right
- Text skeleton: Inline-block, 60px min-width, transparent text
- Chart skeleton: Full width x 250px height (200px on mobile)
- Sharp corners throughout

**JavaScript Functionality:**
- Fetch data from `/api/dashboard/stats` on page load
- Parse JSON response (overview + last_7_days)
- Animate counter values with ease-out easing (1 second duration)
- Format numbers with commas (e.g., "1,500")
- Format decimals for averages (1 decimal place)
- Initialize Chart.js charts with 7-day data
- Format dates as "MMM DD" (e.g., "Jan 24")
- Auto-refresh every 30 seconds for in-progress tasks
- Update charts without animation on refresh
- Smooth transitions and animations
- Error handling with user-friendly error state
- Cleanup intervals on page unload

**API Integration:**
- Endpoint: `/api/dashboard/stats`
- Returns: Overview statistics and last 7 days data
- Overview fields: total_tasks, total_personas, total_images, completed_tasks, failed_tasks, tasks_in_progress, average_personas_per_task, average_images_per_persona
- Last 7 days: tasks_by_date, personas_by_date, images_by_date (arrays with date/count objects)

**Responsive Breakpoints:**
- Desktop (>1024px): 4 columns for stats, 3 columns for charts
- Tablet (641px-1024px): 2 columns for stats, 2 columns for charts
- Mobile (≤640px): Single column, reduced icon sizes, smaller stat values

**Files Created/Modified:**
- `/templates/dashboard.html` - Dashboard page template (updated from placeholder)
- `/static/css/dashboard.css` - Dashboard styles (complete rewrite)
- `/static/js/dashboard.js` - Dashboard interactivity (complete rewrite)
- Chart.js CDN (v4.4.1) included via script tag

**Navigation:**
- Dashboard link already present in sidebar (base.html)
- Active state highlights dashboard when on page

**Design Philosophy:**
- Consistent with brandbook: Sharp corners, neon accents, dark backgrounds
- Monospace fonts for technical data (statistics values)
- Professional data visualization with Chart.js
- Smooth animations and loading states
- Real-time updates for monitoring in-progress tasks
- High contrast for optimal readability
- Clean, minimal, technical aesthetic

---

### 2026-02-01 - Images per Persona Slider Implementation

**UI Update:**
- Replaced radio button selection (4 or 8 images) with range slider control
- New range: 4 to 20 images with increments of 4 (values: 4, 8, 12, 16, 20)
- Slider follows brandbook styling: Sharp corners, neon cyan glow, monospace number display
- Synchronized slider and number input with real-time validation
- Form validation updated to enforce min/max and step constraints

**Components Updated:**
- Generate template: Replaced radio buttons with slider input group structure
- CSS: Added `.images-slider-group` and `.form-images-number` styles matching number input pattern
- JavaScript: Added `initializeImagesSliderSync()` function with same sync pattern as persona count slider
- Validation: Updated to check range (4-20) and step (4) constraints

**Implementation Details:**
- Number input: Monospace font, H3 size, cyan color, centered text, max-width 150px
- Slider: Sharp square thumb (20px), cyan background with glow, 4px track height
- Range labels: Show min (4) and max (20) below slider
- Real-time sync between number input and slider
- Blur validation rounds to nearest valid increment
- Reset button restores default value of 4

**Files Modified:**
- `/templates/generate.html` - Replaced radio group with slider input group (lines 235-273)
- `/static/css/generate.css` - Added images slider styles (lines 346-365)
- `/static/js/generate.js` - Added slider sync and validation (lines 115-161, 207-216, 288-299)
- `/docs/brandbook.md` - Documented implementation

**Design Rationale:**
- Slider provides more granular control than binary radio buttons
- Consistent UI pattern with existing "Number to Generate" slider
- Maintains brandbook compliance: Sharp corners, neon cyan accents, monospace technical display
- Better scalability for future range adjustments

---

*Last Updated: 2026-02-01 (Images per Persona Slider Implementation)*
