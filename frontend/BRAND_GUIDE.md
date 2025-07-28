# ISP Framework Brand & Color Guide

## Brand Colors

The ISP Framework uses a consistent green color palette that reflects growth, connectivity, and reliability - core values of internet service providers.

### Primary Green Palette

```css
/* Brand Colors */
--brand-50: #f0fdf4   /* Lightest green - backgrounds, subtle highlights */
--brand-100: #dcfce7  /* Very light green - hover states, light backgrounds */
--brand-200: #bbf7d0  /* Light green - borders, disabled states */
--brand-300: #86efac  /* Medium light green - secondary actions */
--brand-400: #4ade80  /* Medium green - interactive elements */
--brand-500: #22c55e  /* Primary green - main brand color */
--brand-600: #16a34a  /* Dark green - primary hover states */
--brand-700: #15803d  /* Darker green - active states, emphasis */
--brand-800: #166534  /* Very dark green - text on light backgrounds */
--brand-900: #14532d  /* Darkest green - high contrast text */
--brand-950: #052e16  /* Ultra dark green - maximum contrast */
```

### Semantic Color Usage

#### Primary Colors
- **Primary**: `brand-600` (#16a34a) - Main buttons, links, active states
- **Primary Hover**: `brand-700` (#15803d) - Hover states for primary elements
- **Primary Foreground**: White or `brand-50` - Text on primary backgrounds

#### Success States
- **Success Background**: `brand-50` (#f0fdf4) - Success message backgrounds
- **Success Border**: `brand-200` (#bbf7d0) - Success message borders
- **Success Text**: `brand-800` (#166534) - Success message text
- **Success Icon**: `brand-600` (#16a34a) - Success icons and indicators

#### Interactive Elements
- **Links**: `brand-600` (#16a34a) - Default link color
- **Link Hover**: `brand-700` (#15803d) - Link hover state
- **Focus Ring**: `brand-600` (#16a34a) - Focus indicators
- **Selection**: `brand-100` (#dcfce7) - Text selection background

#### Status Indicators
- **Online/Active**: `brand-500` (#22c55e) - Online status, active services
- **Connected**: `brand-400` (#4ade80) - Connection status indicators
- **Available**: `brand-300` (#86efac) - Available resources, capacity

### Component-Specific Usage

#### Navigation
- **Active Navigation**: `brand-600` background with white text
- **Navigation Hover**: `brand-50` background with `brand-800` text
- **Navigation Icons**: `brand-600` for active, `gray-600` for inactive

#### Buttons
- **Primary Button**: `brand-600` background, white text
- **Primary Button Hover**: `brand-700` background
- **Secondary Button**: `brand-100` background, `brand-800` text
- **Ghost Button**: Transparent background, `brand-600` text

#### Forms
- **Input Focus**: `brand-600` border and ring
- **Input Valid**: `brand-200` border, `brand-50` background
- **Label**: `brand-800` text for emphasis
- **Help Text**: `brand-600` for positive guidance

#### Cards & Containers
- **Card Border**: `brand-100` for subtle definition
- **Card Hover**: `brand-50` background
- **Section Dividers**: `brand-200` borders
- **Highlight Backgrounds**: `brand-50` for important content

#### Data Visualization
- **Primary Data**: `brand-600` - Main metrics, primary data series
- **Secondary Data**: `brand-400` - Secondary metrics
- **Positive Trends**: `brand-500` - Growth, positive changes
- **Neutral Data**: `brand-300` - Baseline, neutral states

### Accessibility Guidelines

#### Contrast Ratios
- **Text on White**: Use `brand-800` or darker for AA compliance
- **Text on Brand**: Use white or `brand-50` for maximum contrast
- **Interactive Elements**: Ensure 3:1 contrast ratio minimum
- **Focus Indicators**: Use `brand-600` with sufficient thickness

#### Color Blindness Considerations
- Never rely solely on color to convey information
- Use icons, text labels, or patterns alongside color
- Test with color blindness simulators
- Provide alternative indicators for status

### Dark Mode Adaptations

```css
/* Dark Mode Brand Colors */
.dark {
  --primary: 142.1 70.6% 45.3%;     /* Slightly lighter green for dark backgrounds */
  --primary-foreground: 144.9 80.4% 10%; /* Very dark green for contrast */
  --ring: 142.4 71.8% 29.2%;        /* Darker green for focus rings */
}
```

#### Dark Mode Usage
- **Primary Elements**: Use `brand-400` instead of `brand-600`
- **Text**: Use `brand-200` for secondary text, `brand-100` for primary
- **Backgrounds**: Use `brand-900` or `brand-950` for colored backgrounds
- **Borders**: Use `brand-800` for subtle borders

### Implementation Examples

#### CSS Classes
```css
/* Primary button */
.btn-primary {
  @apply bg-brand-600 text-white hover:bg-brand-700 focus:ring-brand-600;
}

/* Success alert */
.alert-success {
  @apply bg-brand-50 border-brand-200 text-brand-800;
}

/* Navigation active state */
.nav-active {
  @apply bg-brand-600 text-white;
}

/* Status indicator */
.status-online {
  @apply text-brand-600 bg-brand-50 border-brand-200;
}
```

#### Component Props
```typescript
// Button variants
<Button variant="primary" className="bg-brand-600 hover:bg-brand-700">
<Button variant="secondary" className="bg-brand-100 text-brand-800">
<Button variant="ghost" className="text-brand-600 hover:bg-brand-50">

// Status badges
<Badge className="bg-brand-50 text-brand-800 border-brand-200">
<Badge variant="success" className="bg-brand-600 text-white">
```

### Brand Consistency Checklist

- [ ] All primary actions use `brand-600` or `brand-700`
- [ ] Success states use green palette consistently
- [ ] Interactive elements have proper hover/focus states
- [ ] Contrast ratios meet WCAG AA standards
- [ ] Dark mode variants are properly implemented
- [ ] Status indicators use semantic green colors
- [ ] Navigation reflects brand hierarchy
- [ ] Forms use green for positive states
- [ ] Data visualizations use brand colors appropriately
- [ ] No conflicting color schemes in components

### Tools & Resources

#### Color Palette Generators
- [Coolors.co](https://coolors.co) - For generating complementary palettes
- [Adobe Color](https://color.adobe.com) - For advanced color harmony
- [Accessible Colors](https://accessible-colors.com) - For contrast checking

#### Testing Tools
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/)
- [Stark](https://www.getstark.co/) - Design accessibility plugin

This brand guide ensures consistent, accessible, and professional use of the ISP Framework's green color palette across all components and interfaces.
