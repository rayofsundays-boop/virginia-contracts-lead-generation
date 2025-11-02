/**
 * Lead Click Tracker
 * Tracks free user clicks and shows subscription popup after 3 clicks
 */

class LeadClickTracker {
    constructor() {
        this.FREE_LIMIT = 3;
        this.clicksUsed = 0;
        this.remaining = 3;
        this.isUnlimited = false;
        this.init();
    }

    async init() {
        // Check current lead access status on page load
        await this.checkLeadAccess();
        
        // Show status banner if user is free
        this.updateStatusBanner();
        
        // Set up event listeners for lead cards
        this.setupLeadClickListeners();
    }

    async checkLeadAccess() {
        try {
            const response = await fetch('/api/check-lead-access');
            const data = await response.json();
            
            if (data.success) {
                this.clicksUsed = data.clicks_used || 0;
                this.remaining = data.remaining || 0;
                this.isUnlimited = data.is_unlimited || false;
                this.requiresLogin = data.requires_login || false;
                
                return data;
            }
        } catch (error) {
            console.error('Error checking lead access:', error);
        }
        return null;
    }

    updateStatusBanner() {
        // Don't show banner for paid/admin users
        if (this.isUnlimited) {
            return;
        }

        // Check if banner already exists
        let banner = document.getElementById('lead-access-banner');
        
        if (!banner) {
            // Create banner
            banner = document.createElement('div');
            banner.id = 'lead-access-banner';
            banner.style.cssText = `
                position: fixed;
                top: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 9999;
                font-size: 14px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 12px;
                animation: slideDown 0.3s ease-out;
            `;
            document.body.appendChild(banner);
        }

        // Update banner content based on remaining clicks
        if (this.remaining === 0) {
            banner.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm1 15H9v-2h2v2zm0-4H9V5h2v6z" fill="currentColor"/>
                </svg>
                <span>🔒 Free views used! <strong>Subscribe for unlimited access</strong></span>
                <a href="/pricing" style="background: white; color: #667eea; padding: 6px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: all 0.2s;">
                    Upgrade Now
                </a>
            `;
            banner.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        } else {
            const emoji = this.remaining === 1 ? '⚠️' : '👁️';
            banner.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="10" cy="10" r="10" fill="rgba(255,255,255,0.2)"/>
                    <text x="10" y="14" text-anchor="middle" font-size="12" fill="white" font-weight="bold">${this.remaining}</text>
                </svg>
                <span>${emoji} <strong>${this.remaining}</strong> free lead view${this.remaining !== 1 ? 's' : ''} remaining</span>
                <a href="/pricing" style="background: rgba(255,255,255,0.2); color: white; padding: 6px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: all 0.2s; border: 1px solid rgba(255,255,255,0.3);">
                    Unlock All
                </a>
            `;
        }
    }

    setupLeadClickListeners() {
        // Find all lead detail buttons/links
        const leadButtons = document.querySelectorAll('[data-lead-id], .lead-card-action, .view-details-btn, .contact-info-btn');
        
        leadButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                // Don't track if unlimited
                if (this.isUnlimited) {
                    return;
                }

                // Check if user needs to login
                if (this.requiresLogin) {
                    e.preventDefault();
                    this.showLoginModal();
                    return;
                }

                // Check if limit reached
                if (this.remaining <= 0) {
                    e.preventDefault();
                    this.showSubscriptionModal();
                    return;
                }

                // Track the click
                const leadId = button.getAttribute('data-lead-id') || 'unknown';
                const leadType = button.getAttribute('data-lead-type') || this.detectLeadType();
                
                const tracked = await this.trackClick(leadType, leadId);
                
                if (tracked && tracked.limit_reached) {
                    e.preventDefault();
                    this.showSubscriptionModal();
                } else if (tracked && tracked.success) {
                    // Update remaining count
                    this.remaining = tracked.remaining;
                    this.clicksUsed = this.FREE_LIMIT - this.remaining;
                    this.updateStatusBanner();
                }
            });
        });
    }

    async trackClick(leadType, leadId) {
        try {
            const response = await fetch('/api/track-lead-click', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    lead_type: leadType,
                    lead_id: leadId
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error tracking lead click:', error);
            return null;
        }
    }

    detectLeadType() {
        // Detect lead type from URL
        const path = window.location.pathname;
        if (path.includes('commercial')) return 'commercial';
        if (path.includes('college')) return 'college';
        if (path.includes('k12')) return 'k12';
        if (path.includes('government')) return 'government';
        if (path.includes('contracts')) return 'contracts';
        return 'other';
    }

    showLoginModal() {
        const modal = this.createModal(
            'Sign In Required',
            'Please sign in to view lead details and contact information.',
            [
                {
                    text: 'Sign In',
                    primary: true,
                    action: () => window.location.href = '/auth'
                },
                {
                    text: 'Cancel',
                    primary: false,
                    action: () => this.closeModal()
                }
            ]
        );
        document.body.appendChild(modal);
    }

    showSubscriptionModal() {
        const modal = this.createModal(
            '🔒 Upgrade to View More Leads',
            `You've used all ${this.FREE_LIMIT} free lead views. Subscribe now to unlock unlimited access to thousands of cleaning contract opportunities!`,
            [
                {
                    text: 'View Pricing',
                    primary: true,
                    action: () => window.location.href = '/pricing'
                },
                {
                    text: 'Maybe Later',
                    primary: false,
                    action: () => this.closeModal()
                }
            ],
            true // Show benefits
        );
        document.body.appendChild(modal);
    }

    createModal(title, message, buttons, showBenefits = false) {
        const modal = document.createElement('div');
        modal.id = 'lead-tracker-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.2s ease-out;
        `;

        const benefitsHTML = showBenefits ? `
            <div style="margin: 20px 0; padding: 16px; background: #f8f9ff; border-radius: 8px; text-align: left;">
                <h4 style="margin: 0 0 12px 0; color: #667eea; font-size: 16px;">✨ Premium Benefits:</h4>
                <ul style="margin: 0; padding-left: 24px; color: #555; line-height: 1.8;">
                    <li><strong>Unlimited</strong> lead views</li>
                    <li><strong>Full contact information</strong> for all opportunities</li>
                    <li><strong>Advanced search</strong> and filtering</li>
                    <li><strong>Save leads</strong> for later</li>
                    <li><strong>Email alerts</strong> for new opportunities</li>
                </ul>
            </div>
        ` : '';

        modal.innerHTML = `
            <div style="background: white; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3); animation: slideUp 0.3s ease-out;">
                <h2 style="margin: 0 0 16px 0; color: #333; font-size: 24px;">${title}</h2>
                <p style="margin: 0 0 24px 0; color: #666; line-height: 1.6; font-size: 16px;">${message}</p>
                ${benefitsHTML}
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    ${buttons.map(btn => `
                        <button class="modal-btn ${btn.primary ? 'primary' : 'secondary'}" style="
                            padding: 12px 24px;
                            border: none;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.2s;
                            ${btn.primary ? 
                                'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;' : 
                                'background: #e0e0e0; color: #666;'
                            }
                        ">${btn.text}</button>
                    `).join('')}
                </div>
            </div>
        `;

        // Add click handlers
        const modalButtons = modal.querySelectorAll('.modal-btn');
        buttons.forEach((btn, index) => {
            modalButtons[index].addEventListener('click', btn.action);
        });

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });

        return modal;
    }

    closeModal() {
        const modal = document.getElementById('lead-tracker-modal');
        if (modal) {
            modal.style.animation = 'fadeOut 0.2s ease-out';
            setTimeout(() => modal.remove(), 200);
        }
    }
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    @keyframes slideDown {
        from { transform: translate(-50%, -20px); opacity: 0; }
        to { transform: translate(-50%, 0); opacity: 1; }
    }
    .modal-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
`;
document.head.appendChild(style);

// Initialize tracker when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.leadTracker = new LeadClickTracker();
    });
} else {
    window.leadTracker = new LeadClickTracker();
}
