# Uniform Height Card Grid System
## Complete Implementation Guide

## Overview
A responsive card grid system where all cards maintain equal height and buttons align perfectly at the bottom, regardless of content length. Built with CSS Flexbox for modern browsers.

## Features
✅ **Equal Height Cards** - All cards in a row have the same height  
✅ **Bottom-Aligned Buttons** - Buttons stay at the bottom regardless of content  
✅ **Responsive Grid** - Adapts from 4 columns to 1 column based on screen size  
✅ **Smooth Hover Effects** - Subtle elevation and shadow on hover  
✅ **Mobile Optimized** - Touch-friendly with appropriate spacing  
✅ **Flexible Content** - Works with short or long text, icons, badges  
✅ **Two Button Styles** - Primary (filled) and Secondary (outlined)

## Quick Start

### Basic HTML Structure
```html
<div class="card-grid">
    <div class="uniform-card">
        <div class="uniform-card-body">
            <h3 class="uniform-card-title">Card Title</h3>
            <p class="uniform-card-description">
                Your description text here. Can be any length.
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="#" class="uniform-card-btn">Button Text</a>
        </div>
    </div>
    
    <!-- Add more cards here -->
</div>
```

## CSS Classes Reference

### Container
- **`.card-grid`** - Grid container (required)
  - Auto-responsive columns: 4 → 3 → 2 → 1
  - Gap: 1.5rem (adjusts on mobile)

### Card Structure
- **`.uniform-card`** - Individual card wrapper (required)
  - White background, rounded corners
  - Shadow with hover effect
  - Height: 100% (fills grid cell)

### Card Content
- **`.uniform-card-body`** - Main content area (required)
  - Contains title, description, badges, icons
  - Grows to fill available space (flex: 1)

- **`.uniform-card-title`** - Card heading (required)
  - Font: 1.25rem, bold
  - Min-height ensures consistency

- **`.uniform-card-description`** - Body text (required)
  - Grows to fill space (flex: 1)
  - Pushes footer to bottom

- **`.uniform-card-footer`** - Button container (required)
  - Always positioned at card bottom (margin-top: auto)
  - Contains action button

### Optional Elements
- **`.uniform-card-badge`** - Tag/badge
  - Small pill-shaped label
  - Place at top of card-body

- **`.uniform-card-icon`** - Icon/image
  - 48x48px by default
  - Place before title

- **`.uniform-card-header`** - Optional header section
  - Colored background
  - Place before card-body

### Button Styles
- **`.uniform-card-btn`** - Primary button (default)
  - Blue gradient background
  - Full width of footer
  - Hover: lifts up 2px

- **`.uniform-card-btn-secondary`** - Secondary button
  - Outlined style
  - Add to `.uniform-card-btn`
  - Hover: fills with color

## Advanced Examples

### Card with Badge
```html
<div class="uniform-card">
    <div class="uniform-card-body">
        <div class="uniform-card-badge">Featured</div>
        <h3 class="uniform-card-title">Premium Service</h3>
        <p class="uniform-card-description">
            Get access to exclusive features...
        </p>
    </div>
    <div class="uniform-card-footer">
        <a href="#" class="uniform-card-btn">Learn More</a>
    </div>
</div>
```

### Card with Icon
```html
<div class="uniform-card">
    <div class="uniform-card-body">
        <svg class="uniform-card-icon" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z"/>
        </svg>
        <h3 class="uniform-card-title">Notifications</h3>
        <p class="uniform-card-description">
            Stay updated with real-time alerts...
        </p>
    </div>
    <div class="uniform-card-footer">
        <a href="#" class="uniform-card-btn">Subscribe</a>
    </div>
</div>
```

### Card with Header
```html
<div class="uniform-card">
    <div class="uniform-card-header">
        <small class="text-muted">CATEGORY: SERVICES</small>
    </div>
    <div class="uniform-card-body">
        <h3 class="uniform-card-title">Professional Cleaning</h3>
        <p class="uniform-card-description">
            Commercial and residential options available...
        </p>
    </div>
    <div class="uniform-card-footer">
        <a href="#" class="uniform-card-btn">Get Quote</a>
    </div>
</div>
```

### Secondary Button Style
```html
<div class="uniform-card-footer">
    <a href="#" class="uniform-card-btn uniform-card-btn-secondary">
        Contact Us
    </a>
</div>
```

## Integration with Flask Templates

### Using in Jinja2 Template
```html
{% extends "base.html" %}

{% block content %}
<div class="container my-5">
    <h1 class="mb-4">Our Services</h1>
    
    <div class="card-grid">
        {% for service in services %}
        <div class="uniform-card">
            <div class="uniform-card-body">
                {% if service.is_featured %}
                <div class="uniform-card-badge">Featured</div>
                {% endif %}
                
                <h3 class="uniform-card-title">{{ service.name }}</h3>
                <p class="uniform-card-description">
                    {{ service.description }}
                </p>
            </div>
            <div class="uniform-card-footer">
                <a href="{{ url_for('service_detail', id=service.id) }}" 
                   class="uniform-card-btn">
                    View Details
                </a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

## Responsive Breakpoints

| Screen Size | Columns | Gap | Card Padding |
|-------------|---------|-----|--------------|
| Desktop (>1200px) | 4 | 1.5rem | 1.5rem |
| Laptop (768-1200px) | 3 | 1.25rem | 1.5rem |
| Tablet (480-768px) | 1 | 1rem | 1.25rem |
| Mobile (<480px) | 1 | 1rem | 1.25rem |

## Color Customization

The system uses CSS variables from your existing theme:
```css
--primary-color: #0066cc;     /* Button background */
--primary-dark: #004499;      /* Button hover */
```

To customize colors, update these in your `style.css` `:root` section.

## Browser Support
- Chrome 58+
- Firefox 52+
- Safari 11+
- Edge 16+
- iOS Safari 11+
- Android Chrome 62+

## Common Use Cases

### 1. Feature Showcase
```html
<div class="card-grid">
    <div class="uniform-card">
        <div class="uniform-card-body">
            <h3 class="uniform-card-title">Fast Processing</h3>
            <p class="uniform-card-description">Process contracts in minutes</p>
        </div>
        <div class="uniform-card-footer">
            <a href="#" class="uniform-card-btn">Try Now</a>
        </div>
    </div>
</div>
```

### 2. Service Listings
Perfect for displaying cleaning services, contract types, or pricing tiers.

### 3. Resource Cards
Documentation links, guides, or downloadable resources.

### 4. Team Members
Staff profiles with photo, name, role, and contact button.

### 5. Testimonials
Customer reviews with quote and link to case study.

## Troubleshooting

**Issue:** Buttons not aligning at bottom  
**Solution:** Ensure you have all required elements:
- `.card-grid` container
- `.uniform-card-body` with flex: 1
- `.uniform-card-footer` with margin-top: auto

**Issue:** Cards different heights  
**Solution:** Make sure grid display is applied to `.card-grid` and all cards are direct children.

**Issue:** Hover effect not working  
**Solution:** Check that `.uniform-card` class is on the card element, not the grid.

## Testing Checklist
- [ ] Cards have equal height across row
- [ ] Buttons align at same vertical position
- [ ] Hover effects work on cards and buttons
- [ ] Responsive on mobile (1 column)
- [ ] Responsive on tablet (2 columns)
- [ ] Works with varying content lengths
- [ ] Badges and icons display correctly
- [ ] Links are clickable and accessible

## Live Demo
Visit `/card-grid-example` route to see a working demonstration with various content lengths and styles.

## Files Modified
1. **`static/style.css`** - Added card grid CSS classes
2. **`templates/card_grid_example.html`** - Example template
3. **`app.py`** - Added `/card-grid-example` route

## Support
For issues or questions about this card grid system, check:
1. Browser console for CSS errors
2. Ensure Bootstrap 5 is loaded (for container classes)
3. Verify all required CSS classes are present
4. Test on different screen sizes using browser dev tools

---

**Created:** November 12, 2025  
**Version:** 1.0  
**Tested:** Chrome, Firefox, Safari, Mobile browsers
