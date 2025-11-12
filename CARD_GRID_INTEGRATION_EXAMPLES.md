# Quick Integration Examples
## Apply Card Grid System to Existing Pages

## Example 1: Services Page
**Before (Bootstrap Cards):**
```html
<div class="row">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Service 1</h5>
                <p class="card-text">Description</p>
                <a href="#" class="btn btn-primary">Learn More</a>
            </div>
        </div>
    </div>
</div>
```

**After (Uniform Grid):**
```html
<div class="card-grid">
    <div class="uniform-card">
        <div class="uniform-card-body">
            <h3 class="uniform-card-title">Service 1</h3>
            <p class="uniform-card-description">Description</p>
        </div>
        <div class="uniform-card-footer">
            <a href="#" class="uniform-card-btn">Learn More</a>
        </div>
    </div>
</div>
```

## Example 2: Quick Wins Page
Replace the current commercial lead cards:

```html
<div class="card-grid">
    {% for lead in commercial_leads %}
    <div class="uniform-card">
        <div class="uniform-card-body">
            {% if lead.urgency == 'emergency' %}
            <div class="uniform-card-badge">🚨 Emergency</div>
            {% endif %}
            
            <h3 class="uniform-card-title">{{ lead.business_name }}</h3>
            <p class="uniform-card-description">
                <strong>Location:</strong> {{ lead.city }}, VA<br>
                <strong>Type:</strong> {{ lead.business_type }}<br>
                <strong>Budget:</strong> {{ lead.budget_range }}<br>
                {{ lead.description }}
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="{{ url_for('lead_detail', id=lead.id) }}" 
               class="uniform-card-btn">
                View Lead
            </a>
        </div>
    </div>
    {% endfor %}
</div>
```

## Example 3: Federal Contracts Page
```html
<div class="card-grid">
    {% for contract in federal_contracts %}
    <div class="uniform-card">
        <div class="uniform-card-body">
            <div class="uniform-card-badge">
                {{ contract.agency_short }}
            </div>
            
            <h3 class="uniform-card-title">{{ contract.title }}</h3>
            
            <p class="uniform-card-description">
                <strong>Agency:</strong> {{ contract.agency }}<br>
                <strong>Value:</strong> ${{ "{:,.0f}".format(contract.value) }}<br>
                <strong>Deadline:</strong> {{ contract.deadline }}<br>
                <strong>Location:</strong> {{ contract.location }}
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="{{ contract.sam_gov_url }}" 
               target="_blank" 
               class="uniform-card-btn">
                View on SAM.gov
            </a>
        </div>
    </div>
    {% endfor %}
</div>
```

## Example 4: Supply Contracts Page
```html
<div class="card-grid">
    {% for supply in supply_contracts %}
    <div class="uniform-card">
        <div class="uniform-card-body">
            {% if supply.is_quick_win %}
            <div class="uniform-card-badge">⚡ Quick Win</div>
            {% endif %}
            
            <h3 class="uniform-card-title">{{ supply.title }}</h3>
            
            <p class="uniform-card-description">
                <strong>Buyer:</strong> {{ supply.agency }}<br>
                <strong>Category:</strong> {{ supply.product_category }}<br>
                <strong>Value:</strong> ${{ "{:,.0f}".format(supply.estimated_value) }}<br>
                {{ supply.description }}
            </p>
        </div>
        <div class="uniform-card-footer">
            {% if current_user.is_authenticated %}
            <a href="mailto:{{ supply.contact_email }}" 
               class="uniform-card-btn">
                Contact Buyer
            </a>
            {% else %}
            <a href="{{ url_for('login') }}" 
               class="uniform-card-btn uniform-card-btn-secondary">
                Login to View Contact
            </a>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
```

## Example 5: Dashboard Overview Cards
```html
<div class="card-grid">
    <!-- Saved Leads Card -->
    <div class="uniform-card">
        <div class="uniform-card-body">
            <h3 class="uniform-card-title">
                📋 Saved Leads
            </h3>
            <p class="uniform-card-description">
                You have {{ saved_leads_count }} saved opportunities.
                Track your progress and never miss a deadline.
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="{{ url_for('saved_leads') }}" 
               class="uniform-card-btn">
                View Saved Leads
            </a>
        </div>
    </div>
    
    <!-- Quick Wins Card -->
    <div class="uniform-card">
        <div class="uniform-card-body">
            <div class="uniform-card-badge">🔥 Hot</div>
            <h3 class="uniform-card-title">
                Quick Wins Available
            </h3>
            <p class="uniform-card-description">
                {{ emergency_count }} emergency requests need immediate attention.
                Fast response = higher conversion rate.
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="{{ url_for('quick_wins') }}" 
               class="uniform-card-btn">
                View Quick Wins
            </a>
        </div>
    </div>
    
    <!-- Credits Card -->
    <div class="uniform-card">
        <div class="uniform-card-body">
            <h3 class="uniform-card-title">
                💳 Credit Balance
            </h3>
            <p class="uniform-card-description">
                Current balance: {{ credits_balance }} credits.
                Each credit unlocks full contact information for one lead.
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="{{ url_for('purchase_credits') }}" 
               class="uniform-card-btn uniform-card-btn-secondary">
                Buy More Credits
            </a>
        </div>
    </div>
</div>
```

## Example 6: Construction Cleanup Leads
```html
<div class="card-grid">
    {% for project in construction_leads %}
    <div class="uniform-card">
        <div class="uniform-card-body">
            <div class="uniform-card-badge">
                {{ project.data_source }}
            </div>
            
            <h3 class="uniform-card-title">{{ project.project_name }}</h3>
            
            <p class="uniform-card-description">
                <strong>Builder:</strong> {{ project.builder }}<br>
                <strong>Location:</strong> {{ project.city }}, {{ project.state }}<br>
                <strong>Type:</strong> {{ project.project_type }}<br>
                <strong>Value:</strong> ${{ "{:,.0f}".format(project.estimated_cleanup_value) }}<br>
                <strong>Completion:</strong> {{ project.completion_date }}
            </p>
        </div>
        <div class="uniform-card-footer">
            <a href="tel:{{ project.contact_phone }}" 
               class="uniform-card-btn">
                Call {{ project.contact_name }}
            </a>
        </div>
    </div>
    {% endfor %}
</div>
```

## Conversion Tips

1. **Replace `row`/`col-*` with `card-grid`**
   - Single container, no column wrappers needed

2. **Replace `card` with `uniform-card`**
   - Maintains height consistency automatically

3. **Split content into body and footer**
   - Body: Title, description, metadata
   - Footer: Button only

4. **Use badges for status indicators**
   - Emergency, Featured, Hot, New, etc.

5. **Conditional buttons based on auth**
   - Show different CTAs for logged in/out users

## Pages to Update
- [ ] `/quick-wins` - Commercial leads grid
- [ ] `/federal-contracts` - Government contracts
- [ ] `/supply-contracts` - Supply opportunities  
- [ ] `/construction-cleanup-leads` - Construction projects
- [ ] `/customer-leads` - All leads dashboard
- [ ] `/dashboard` - User overview cards
- [ ] `/pricing-guide` - Pricing tier cards
- [ ] `/services` - Service offerings (if exists)
- [ ] `/resources` - Resource cards (if exists)

## Testing After Integration
1. Visit each updated page
2. Resize browser window (test responsive breakpoints)
3. Verify buttons align at bottom
4. Test hover effects work
5. Check on mobile device
6. Ensure links/buttons are clickable
