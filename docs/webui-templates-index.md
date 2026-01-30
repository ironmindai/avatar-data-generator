# Web UI Templates Index - Avatar Data Generator

> *Maintained by: frontend-brand-guardian agent*
> *Last Updated: 2026-01-30*

## Overview

This document provides a comprehensive index of all web UI templates in the Avatar Data Generator application. All templates follow the branding guidelines specified in `docs/brandbook.md` and utilize the centralized CSS system defined in `/static/css/main.css`.

## Template Architecture

### Technology Stack
- **Template Engine**: Jinja2 (Flask)
- **CSS Framework**: Custom CSS with CSS Variables (Brandbook-compliant)
- **Icon System**: Feather Icons (via CDN)
- **JavaScript Libraries**:
  - Select2 (searchable dropdowns)
  - jQuery (required for Select2)

### Template Types
1. **Standalone Pages**: No navigation (e.g., login)
2. **Dashboard Layout Pages**: Include header + sidebar navigation (e.g., dashboard, generate)

## Templates

### 1. Login Page

**File**: `/templates/login.html`

**Route**: `GET/POST /login`

**Authentication**: Public (redirects if already authenticated)

**Purpose**: User authentication entry point

**Layout Type**: Standalone (no navigation)

**Key Features**:
- Email/password authentication form
- "Remember me" checkbox for persistent sessions
- CSRF protection
- Forgot password link (placeholder)
- Sign up link (placeholder)
- Alert system for error/success messages
- Dark mode optimized (logo-white.jpeg)

**Template Variables**:
- `error` (optional): Error message string for failed login attempts
- `success` (optional): Success message string
- `csrf_token()`: CSRF token function

**Stylesheets**:
- `/static/css/main.css` - Global brandbook styles
- `/static/css/login.css` - Login-specific styles

**JavaScript**:
- `/static/js/login.js` - Form validation and interactivity

**Accessibility**:
- ARIA labels on all form inputs
- Role attributes for alerts
- Autocomplete attributes for email/password
- Semantic HTML structure

**Form Fields**:
1. `email` - Email address (required, type="email")
2. `password` - Password (required, type="password")
3. `remember` - Remember me checkbox (optional)
4. `csrf_token` - Hidden CSRF token (required)

**Links**:
- `/forgot-password` - Password reset (not yet implemented)
- `/signup` - User registration (not yet implemented)

---

### 2. Dashboard Page

**File**: `/templates/dashboard.html`

**Route**: `GET /dashboard`

**Authentication**: Protected (requires login)

**Purpose**: Main application dashboard and landing page for authenticated users

**Layout Type**: Dashboard Layout (header + sidebar)

**Key Features**:
- Header navigation with logo and user info
- Collapsible sidebar navigation
- User avatar with initial badge
- Logout functionality
- Under construction placeholder content
- Alert system for messages
- Feather Icons integration
- Navigation to all major app sections

**Template Variables**:
- `user_name`: String - Username (derived from email, e.g., "admin" from "admin@example.com")
- `message` (optional): Info/success message string
- `total_avatars` (planned): Total avatars generated
- `active_datasets` (planned): Number of active datasets
- `processing_jobs` (planned): Number of jobs in progress

**Stylesheets**:
- `/static/css/main.css` - Global brandbook styles

**JavaScript**:
- Feather Icons (CDN): `https://unpkg.com/feather-icons`
- `/static/js/dashboard.js` - Dashboard-specific functionality

**Navigation Links**:
1. `/dashboard` - Dashboard (active)
2. `/generate` - Generate Avatars
3. `/datasets` - Datasets
4. `/history` - History
5. `/settings` - Settings

**Header Actions**:
- User name display
- User avatar badge (shows first letter of username)
- Logout button with icon

**Current Status**:
- Displays "Under Construction" placeholder
- All navigation links are active (routes exist but some redirect back)

**Accessibility**:
- `role="navigation"` on sidebar
- `aria-label="Main Navigation"` on sidebar
- `aria-current="page"` on active navigation item
- `aria-label="User Avatar"` on avatar badge
- `aria-label="Logout"` on logout button

---

### 3. Generate Avatars Page

**File**: `/templates/generate.html`

**Route**: `GET/POST /generate`

**Authentication**: Protected (requires login)

**Purpose**: Avatar generation form with persona description, language selection, and batch configuration

**Layout Type**: Dashboard Layout (header + sidebar)

**Key Features**:
- Comprehensive avatar generation form
- Searchable language dropdown (Select2) with 100+ languages
- Number input with synchronized slider
- Radio buttons for images per persona selection
- Real-time form validation
- Loading state with spinner animation
- Information cards explaining features
- CSRF protection
- Alert system for error/success messages

**Template Variables**:
- `user_name`: String - Username for header display
- `error` (optional): Error message string
- `success` (optional): Success message string
- `csrf_token()`: CSRF token function

**Stylesheets**:
- `/static/css/main.css` - Global brandbook styles
- `/static/css/generate.css` - Generate page-specific styles
- Select2 CSS (CDN): `https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css`

**JavaScript**:
- Feather Icons (CDN): `https://unpkg.com/feather-icons`
- jQuery (CDN): `https://code.jquery.com/jquery-3.6.0.min.js`
- Select2 (CDN): `https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js`
- `/static/js/generate.js` - Form interactivity and submission handling

**Form Fields**:

1. **Persona Description** (`persona_description`)
   - Type: Textarea (5 rows)
   - Required: Yes
   - Placeholder: "Students from Japan, living and studying in America, fair split between male and female and most of them interested in tech"
   - Purpose: Describe demographic, interests, and characteristics
   - ARIA: `aria-describedby="persona-description-help"`

2. **Bio Language** (`bio_language`)
   - Type: Select (searchable via Select2)
   - Required: Yes
   - Options: 100+ languages organized in optgroups:
     - Most Common (11 languages)
     - European Languages (24 languages)
     - Asian Languages (30 languages)
     - Middle Eastern & African Languages (15 languages)
     - Americas Languages (4 languages)
     - Other Languages (16 languages)
   - Default: None (placeholder: "Select a language")
   - Features: Type-to-search, native language names with translations

3. **Number to Generate** (`number_to_generate`)
   - Type: Number + Range slider (synchronized)
   - Required: Yes
   - Min: 10
   - Max: 300
   - Step: 5
   - Default: 50
   - Features: Dual input (number field + slider)
   - ARIA: `aria-describedby="number-help"`

4. **Images per Persona** (`images_per_persona`)
   - Type: Radio buttons
   - Required: Yes
   - Options: 4 images (default) or 8 images
   - Custom styled radio buttons with visual feedback

5. **CSRF Token** (`csrf_token`)
   - Type: Hidden
   - Required: Yes
   - Auto-generated by Flask-WTF

**Form Actions**:
- **Submit Button**: "Generate Avatars" (primary button with zap icon)
- **Reset Button**: "Reset Form" (secondary button with rotate icon)

**Loading State**:
- Hidden by default (`#loadingState`)
- Shows spinner animation when form is submitted
- Displays "Generating Avatars..." message
- Prevents navigation during generation
- Controlled via JavaScript

**Information Cards** (3-column grid):

1. **AI-Powered**
   - Icon: Zap (primary color)
   - Message: Advanced AI models generate realistic avatars

2. **Privacy First**
   - Icon: Shield (success color)
   - Message: All avatars are synthetic, not real individuals

3. **Export Ready**
   - Icon: Download Cloud (accent purple)
   - Message: Download datasets in multiple formats

**Navigation Links**:
1. `/dashboard` - Dashboard
2. `/generate` - Generate Avatars (active)
3. `/datasets` - Datasets
4. `/history` - History
5. `/settings` - Settings

**Accessibility**:
- All inputs have `aria-label` attributes
- Help text linked via `aria-describedby`
- Icon-only buttons have `aria-label`
- Form validation messages
- Keyboard navigation supported
- Focus management on form submission

**Current Implementation Status**:
- Frontend: Complete (template + CSS + JS) - Created 2026-01-30
- Backend: Route needs to be implemented or verified
- Form validation: Client-side fully implemented with real-time feedback
- Avatar generation logic: Backend implementation required
- Navigation: Added to sidebar in base.html

---

### 4. Settings Page

**File**: `/templates/settings.html`

**Route**: `GET/POST /settings` and `POST /settings/save`

**Authentication**: Protected (requires login)

**Purpose**: Configure bio prompts for social media platforms and manage application settings

**Layout Type**: Dashboard Layout (header + sidebar)

**Key Features**:
- Bio prompts configuration section with 4 platform-specific textarea fields
- Form state tracking with dirty state detection (only enable save when changes detected)
- AJAX form submission to `/settings/save` endpoint
- Real-time character counter for each textarea
- Save button with loading state (spinner animation)
- Reset to original values functionality with confirmation
- Toast notification system for success/error messages
- Responsive design optimized for mobile/tablet/desktop
- Information card explaining bio prompts purpose
- Sharp corners, charcoal backgrounds, neon glow effects (brandbook compliant)

**Template Variables**:
- `user_name`: String - Username for header display
- `facebook_bio_prompt`: String - Current Facebook bio prompt value
- `instagram_bio_prompt`: String - Current Instagram bio prompt value
- `x_bio_prompt`: String - Current X (Twitter) bio prompt value
- `tiktok_bio_prompt`: String - Current TikTok bio prompt value
- `error` (optional): Error message string
- `success` (optional): Success message string
- `csrf_token()`: CSRF token function

**Stylesheets**:
- `/static/css/main.css` - Global brandbook styles
- `/static/css/settings.css` - Settings page-specific styles

**JavaScript**:
- Feather Icons (CDN): `https://unpkg.com/feather-icons`
- `/static/js/settings.js` - Form state management and AJAX submission

**Form Fields**:

1. **Facebook Bio Prompt** (`facebook_bio_prompt`)
   - Type: Textarea (5 rows)
   - Required: Yes
   - Character counter: Real-time
   - Icon: Facebook
   - ARIA: `aria-describedby="facebook-help"`

2. **Instagram Bio Prompt** (`instagram_bio_prompt`)
   - Type: Textarea (5 rows)
   - Required: Yes
   - Character counter: Real-time
   - Icon: Instagram
   - ARIA: `aria-describedby="instagram-help"`

3. **X (Twitter) Bio Prompt** (`x_bio_prompt`)
   - Type: Textarea (5 rows)
   - Required: Yes
   - Character counter: Real-time
   - Icon: Twitter
   - ARIA: `aria-describedby="x-help"`

4. **TikTok Bio Prompt** (`tiktok_bio_prompt`)
   - Type: Textarea (5 rows)
   - Required: Yes
   - Character counter: Real-time
   - Icon: Custom TikTok SVG
   - ARIA: `aria-describedby="tiktok-help"`

5. **CSRF Token** (`csrf_token`)
   - Type: Hidden
   - Required: Yes
   - Auto-generated by Flask-WTF

**Form Actions**:
- **Save Button**: "Save Changes" (primary button, disabled by default)
  - Only enabled when form has changes (dirty state)
  - Shows loading spinner during AJAX submission
  - Icon: Save
- **Reset Button**: "Reset to Original" (secondary button)
  - Restores original values
  - Confirmation dialog before reset
  - Icon: Rotate counter-clockwise

**JavaScript State Management**:
- Stores original values on page load
- Tracks dirty state (compares current vs original values)
- Enables/disables save button based on dirty state
- Adds `.dirty` class to modified textareas
- Updates character counters in real-time
- AJAX submission with fetch API
- Updates original values after successful save
- Resets dirty state after save
- Shows toast notifications for success/error

**AJAX Response Format** (expected from backend):
```json
{
  "success": true,
  "message": "Settings saved successfully"
}
```

**Toast Notification System**:
- Fixed position: Bottom-right (2rem from edges)
- Success state: Green left border, success icon, success glow
- Error state: Red left border, error icon, error glow
- Slide-in animation (0.3s)
- Auto-hide after 4 seconds
- Manually dismissible via animation
- Responsive on mobile (full-width at bottom)

**Character Counter Features**:
- Font: Monospace (technical aesthetic)
- Updates on every input event
- Format: "N character(s)"
- Position: Below textarea, right-aligned
- Color: Muted text (#666666)

**Information Card**:
- Explains purpose of bio prompts
- Lists platform-specific guidelines:
  - Facebook: Longer, detailed personal stories
  - Instagram: Concise, emoji-friendly, hashtag-aware
  - X (Twitter): Brief, witty, 160-character limit
  - TikTok: Fun, trendy, creative with emojis
- Icon: Info
- Left border accent: Neon cyan

**Navigation Links**:
1. `/dashboard` - Dashboard
2. `/generate` - Generate Avatars
3. `/datasets` - Datasets
4. `/history` - History
5. `/settings` - Settings (active)

**Accessibility**:
- All textareas have `aria-label` attributes
- Help text linked via `aria-describedby`
- Icon-only elements have `aria-label`
- Form validation messages
- Keyboard navigation supported
- Focus management
- Toast notifications with `role="alert"` and `aria-live="polite"`

**Current Implementation Status**:
- Frontend: Complete (template + CSS + JS) - Created 2026-01-30
- Backend: Routes need to be implemented (`GET /settings` and `POST /settings/save`)
- State management: Fully implemented with dirty state tracking
- AJAX submission: Implemented, expects JSON response
- Navigation: Settings link already in sidebar (base.html)

---

## Common Template Components

### Header Navigation

**Used in**: Dashboard, Generate (all protected pages)

**Structure**:
```html
<header class="header">
  <div class="header-content">
    <div class="header-brand">
      <img src="/static/images/logo-white.jpeg" alt="Galacticos AI">
    </div>
    <div class="header-user">
      <div class="user-name">{{ user_name }}</div>
      <div class="user-avatar">{{ user_name[0].upper() }}</div>
      <a href="/logout" class="btn btn-ghost">
        <i data-feather="log-out"></i>
      </a>
    </div>
  </div>
</header>
```

**Features**:
- Fixed positioning at top
- Brand logo (white version for dark backgrounds)
- User name display
- Circular avatar badge with user initial
- Logout button with icon
- Responsive layout

---

### Sidebar Navigation

**Used in**: Dashboard, Generate (all protected pages)

**Structure**:
```html
<aside class="sidebar" role="navigation" aria-label="Main Navigation">
  <nav>
    <ul class="sidebar-nav">
      <li class="sidebar-nav-item">
        <a href="/dashboard" class="sidebar-nav-link [active]">
          <i data-feather="home" class="sidebar-nav-icon"></i>
          Dashboard
        </a>
      </li>
      <!-- Additional nav items -->
    </ul>
  </nav>
</aside>
```

**Navigation Items** (consistent across all pages):
1. Dashboard - `/dashboard` - Icon: home
2. Generate Avatars - `/generate` - Icon: image
3. Datasets - `/datasets` - Icon: database
4. History - `/history` - Icon: clock
5. Settings - `/settings` - Icon: settings

**Active State**:
- Add `active` class to current page link
- Add `aria-current="page"` for accessibility
- Visual highlight via CSS (primary color border)

**Responsive Behavior**:
- Full sidebar on desktop
- Collapsible on tablet/mobile (implementation pending)

---

### Alert System

**Used in**: All templates

**Types**:
1. `alert-error` - Red - Error messages
2. `alert-success` - Green - Success messages
3. `alert-info` - Blue - Informational messages
4. `alert-warning` - Yellow - Warning messages (not yet used)

**Structure**:
```html
{% if error %}
<div class="alert alert-error" role="alert">
  <i data-feather="alert-circle"></i>
  {{ error }}
</div>
{% endif %}
```

**Backend Integration**:
- Use Flask's `flash(message, category)` function
- Categories: 'error', 'success', 'info', 'warning'
- Templates check for variables: `error`, `success`, `message`

---

## Template Standards

### Brandbook Compliance

All templates MUST follow guidelines in `/docs/brandbook.md`:

**Color Palette**:
- Primary: `#6B46C1` (Purple)
- Primary Dark: `#5A3BA6`
- Success: `#10B981` (Green)
- Error: `#EF4444` (Red)
- Background: `#0F172A` (Dark Blue)
- Surface: `#1E293B`
- Text Primary: `#F8FAFC`
- Text Secondary: `#94A3B8`

**Typography**:
- Font Family: Inter, system-ui, sans-serif
- Headings: 600-700 weight
- Body: 400 weight
- Line Height: 1.6 for body, 1.2 for headings

**Spacing**:
- Base unit: 4px
- Scale: xs(4px), sm(8px), md(16px), lg(24px), xl(32px), 2xl(48px), 3xl(64px)

**Components**:
- Cards: `background: var(--color-surface)`, `border-radius: var(--radius-lg)`
- Buttons: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`
- Forms: `.form-group`, `.form-label`, `.form-input`, `.form-select`

### CSS Variables

All styling uses CSS custom properties defined in `/static/css/main.css`:

```css
/* Colors */
--color-primary
--color-primary-dark
--color-success
--color-error
--color-background
--color-surface
--color-text-primary
--color-text-secondary

/* Typography */
--font-family-base
--font-size-body
--font-size-h1, h2, h3, etc.

/* Spacing */
--spacing-xs, sm, md, lg, xl, 2xl, 3xl

/* Other */
--radius-sm, md, lg
--shadow-sm, md, lg
--transition-base
```

### CSRF Protection

All forms MUST include CSRF token:
```html
<form method="POST">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
  <!-- form fields -->
</form>
```

### Icon System

Use Feather Icons for all UI icons:
1. Include CDN: `<script src="https://unpkg.com/feather-icons"></script>`
2. Use icon: `<i data-feather="icon-name"></i>`
3. Initialize: `<script>feather.replace();</script>`

### Accessibility Requirements

All templates must include:
- Semantic HTML5 elements
- ARIA labels on interactive elements
- ARIA roles where appropriate
- `aria-current="page"` on active navigation
- `aria-describedby` for form help text
- Focus management for modals/dynamic content
- Keyboard navigation support
- Alt text on all images

---

## File Structure

```
templates/
├── login.html           # Standalone login page
├── dashboard.html       # Main dashboard (protected)
├── generate.html        # Avatar generation form (protected)
└── settings.html        # Settings page (protected)

static/
├── css/
│   ├── main.css         # Global brandbook styles (all pages)
│   ├── login.css        # Login page styles
│   ├── generate.css     # Generate page styles
│   └── settings.css     # Settings page styles
├── js/
│   ├── login.js         # Login form logic
│   ├── dashboard.js     # Dashboard interactions
│   ├── generate.js      # Generate form logic
│   └── settings.js      # Settings form state management
└── images/
    └── logo-white.jpeg  # Logo (white version for dark backgrounds)
```

---

## Future Templates (Planned)

### 4. Datasets Page
**Route**: `/datasets`
**Purpose**: View, manage, and download generated avatar datasets
**Status**: Route exists but redirects to dashboard

**Planned Features**:
- Dataset list with thumbnails
- Search and filter functionality
- Download options (ZIP, JSON, CSV)
- Dataset details modal
- Delete confirmation

---

### 5. History Page
**Route**: `/history`
**Purpose**: View past generation jobs and their status
**Status**: Route exists but redirects to dashboard

**Planned Features**:
- Generation history table
- Status indicators (pending, processing, completed, failed)
- Date/time stamps
- Re-run capability
- Filter by date range

---

### 6. Forgot Password Page
**Route**: `/forgot-password`
**Purpose**: Password reset request
**Status**: Route redirects to login with message

**Planned Features**:
- Email input for reset link
- Email verification
- Password reset token handling

---

### 7. Signup Page
**Route**: `/signup`
**Purpose**: New user registration
**Status**: Route redirects to login (registration disabled)

**Planned Features**:
- User registration form
- Email verification
- Terms of service acceptance
- Admin approval workflow (if enabled)

---

## Template Maintenance Guidelines

### Adding New Templates

1. **Create template file** in `/templates/`
2. **Choose layout type**:
   - Standalone: Copy structure from `login.html`
   - Dashboard layout: Copy structure from `dashboard.html`
3. **Create route** in `app.py`
4. **Add CSS file** in `/static/css/` if needed
5. **Add JavaScript file** in `/static/js/` if needed
6. **Update navigation** in sidebar (if dashboard layout)
7. **Update this documentation** with template details
8. **Update backend-routes.md** with route information

### Modifying Existing Templates

1. **Check brandbook compliance** before making changes
2. **Maintain consistent navigation** across all dashboard pages
3. **Update CSS variables** instead of hardcoding values
4. **Test accessibility** after changes
5. **Update documentation** if structure/variables change
6. **Keep CSRF protection** on all forms

### Template Testing Checklist

- [ ] Loads without errors
- [ ] CSRF token present on forms
- [ ] Icons render correctly (Feather Icons initialized)
- [ ] Responsive on mobile/tablet/desktop
- [ ] Navigation links work
- [ ] Active state shows correctly
- [ ] Alert messages display properly
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Follows brandbook colors/typography
- [ ] JavaScript functionality works
- [ ] Form validation functional

---

## Backend Integration

### Route Handlers

Each template requires a corresponding route in `/app.py`:

```python
@app.route('/page-name', methods=['GET', 'POST'])
@login_required  # If protected
def page_name():
    # GET handler
    if request.method == 'GET':
        return render_template('page-name.html',
                             user_name=get_user_name(),
                             # other variables
                             )

    # POST handler
    if request.method == 'POST':
        # Process form data
        # Validate input
        # Return response/redirect
        pass
```

### Template Variables Convention

**Standard variables for dashboard layout pages**:
- `user_name`: String - Username for header display (required)
- `error`: String - Error message (optional)
- `success`: String - Success message (optional)
- `message`: String - Info message (optional)

**Page-specific variables**:
- Document in template section above
- Pass explicitly from route handler
- Use Jinja2 defaults: `{{ var or 'default' }}`

---

## Resources

### External Dependencies

**CDN Resources**:
- Feather Icons: `https://unpkg.com/feather-icons`
- jQuery: `https://code.jquery.com/jquery-3.6.0.min.js`
- Select2: `https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js`
- Select2 CSS: `https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css`

**Local Assets**:
- Logo: `/static/images/logo-white.jpeg`
- Main CSS: `/static/css/main.css`

### Documentation Links

- Brandbook: `/docs/brandbook.md`
- Backend Routes: `/docs/backend-routes.md`
- System/DevOps: `/docs/system-devops-admin.md`

### Flask/Jinja2 Resources

- Template variables: `{{ variable }}`
- Conditionals: `{% if condition %} ... {% endif %}`
- Loops: `{% for item in items %} ... {% endfor %}`
- CSRF token: `{{ csrf_token() }}`
- URL generation: `{{ url_for('route_name') }}`
- Flash messages: Rendered via template variables

---

## Contact

For changes to templates, CSS, or this documentation, contact the **frontend-brand-guardian** agent.

For backend routes and API changes, contact the **backend-coder** agent.

---

**Last Review**: 2026-01-30
**Next Review**: As needed when new templates are added
