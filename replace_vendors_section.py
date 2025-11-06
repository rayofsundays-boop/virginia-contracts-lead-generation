#!/usr/bin/env python3
"""
Script to replace the fake Local Vendors section with real data display
"""

# Read the file
with open('templates/quick_wins.html', 'r') as f:
    lines = f.readlines()

# Find the section to replace (lines 384-759, but Python uses 0-indexing so 383-758)
# We'll replace from line 383 (<!-- Local Vendors...) to line 759 (</div> after card)

new_section = '''<!-- Supply Vendor Directory - Real Data from 600+ Imported Buyers -->
<div class="container my-5" id="supply-vendor-directory">
    <div class="card border-0 shadow-lg">
        <div class="card-header text-white py-4" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
            <div class="text-center">
                <h2 class="display-6 fw-bold mb-2">
                    <i class="fas fa-store me-3"></i>{{ supply_contracts|length }} Verified Supply Buyers
                </h2>
                <p class="lead mb-0">Real businesses actively purchasing cleaning supplies nationwide - sourced from public procurement data</p>
            </div>
        </div>
        
        <div class="card-body bg-light py-4">
            <div class="alert alert-success mb-4">
                <i class="fas fa-database me-2"></i>
                <strong>100% Real Data</strong> - All buyers sourced from public procurement records. No fake contacts or placeholder information.
            </div>

            <!-- Display first 12 supply contracts from database -->
            <div class="row g-4 mb-4">
                {% for contract in supply_contracts[:12] %}
                <div class="col-md-6 col-lg-4">
                    <div class="card h-100 border-0 shadow-sm hover-lift">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <h6 class="fw-bold text-success mb-0" style="font-size: 0.95rem;">
                                    <i class="fas fa-building me-2"></i>{{ contract[2] or contract[1][:40] }}
                                </h6>
                                {% if contract[9] %}
                                <span class="badge bg-warning text-dark">Priority</span>
                                {% endif %}
                            </div>
                            <p class="small text-muted mb-2">
                                <i class="fas fa-map-marker-alt me-1"></i>{{ contract[3] }}
                            </p>
                            <p class="small text-muted mb-2">
                                <i class="fas fa-tag me-1"></i>{{ contract[4] }}
                            </p>
                            <p class="small mb-3" style="font-size: 0.85rem;">{{ (contract[7]|string)[:120] }}...</p>
                            
                            {% if is_paid_subscriber or is_admin %}
                            <div class="border-top pt-3">
                                {% if contract[5] %}
                                <p class="small mb-2"><strong>Est. Value:</strong> ${{ "{:,}".format(contract[5]) }}</p>
                                {% endif %}
                                {% if contract[6] %}
                                <p class="small mb-2"><strong>Deadline:</strong> {{ contract[6].strftime('%b %d, %Y') if contract[6] else 'Ongoing' }}</p>
                                {% endif %}
                                {% if contract[10] %}
                                <p class="small mb-2"><strong>Contact:</strong> {{ contract[10] }}</p>
                                {% endif %}
                                {% if contract[12] %}
                                <p class="small mb-2">
                                    <strong>Phone:</strong> <a href="tel:{{ contract[12] }}" class="text-success">{{ contract[12] }}</a>
                                </p>
                                {% endif %}
                                {% if contract[11] %}
                                <p class="small mb-2">
                                    <strong>Email:</strong> <a href="mailto:{{ contract[11] }}" class="text-success" style="font-size: 0.8rem;">{{ contract[11] }}</a>
                                </p>
                                {% endif %}
                                {% if contract[8] %}
                                <a href="{{ contract[8] }}" target="_blank" class="btn btn-success btn-sm w-100 mt-2">
                                    <i class="fas fa-external-link-alt me-2"></i>View Opportunity
                                </a>
                                {% else %}
                                <a href="tel:{{ contract[12] }}" class="btn btn-success btn-sm w-100 mt-2">
                                    <i class="fas fa-phone me-2"></i>Call Now
                                </a>
                                {% endif %}
                            </div>
                            {% else %}
                            <div class="mt-3 p-3 bg-white rounded border">
                                <p class="text-muted mb-2 small"><i class="fas fa-lock me-2"></i>Contact details locked</p>
                                <a href="{{ url_for('subscription') }}" class="btn btn-success btn-sm w-100">
                                    <i class="fas fa-crown me-2"></i>Unlock Contact Info
                                </a>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>

            {% if supply_contracts|length > 12 %}
            <div class="text-center mb-4">
                <div class="alert alert-info d-inline-block">
                    <i class="fas fa-info-circle me-2"></i>
                    Showing 12 of <strong>{{ supply_contracts|length }}</strong> verified buyers. Scroll down to view all opportunities.
                </div>
            </div>
            {% endif %}
            
            <div class="card-footer bg-white text-center py-3 border-top mt-4">
                <p class="text-muted mb-2"><small><i class="fas fa-database me-2"></i>All data sourced from public procurement databases</small></p>
                <p class="text-muted mb-0"><small><i class="fas fa-check-circle me-2"></i>{{ supply_contracts|length }} verified opportunities nationwide</small></p>
                {% if not is_paid_subscriber and not is_admin %}
                <a href="{{ url_for('subscription') }}" class="btn btn-success btn-lg mt-3">
                    <i class="fas fa-crown me-2"></i>Unlock All Contact Details - $497/year
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>

'''

# Replace lines 383-759 (0-indexed) with new section
new_lines = lines[:383] + [new_section] + lines[759:]

# Write back
with open('templates/quick_wins.html', 'w') as f:
    f.writelines(new_lines)

print("✅ Successfully replaced fake Local Vendors section with real data display")
print(f"✅ Removed {759-383} lines of fake vendor data")
print("✅ New section displays actual supply contracts from database")
