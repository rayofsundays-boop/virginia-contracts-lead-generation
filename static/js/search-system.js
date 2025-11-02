/**
 * Global Search System for Subscribers
 * Features:
 * - Real-time search across all leads
 * - Algorithmic suggestions based on user behavior
 * - Search history tracking
 * - Smart pop-ups with personalized recommendations
 */

class SearchSystem {
    constructor() {
        this.searchBox = null;
        this.resultsContainer = null;
        this.suggestionsModal = null;
        this.debounceTimer = null;
        this.isSubscriber = false;
        this.init();
    }

    init() {
        console.log('🔍 Initializing Search System...');
        this.createSearchUI();
        this.checkSubscriptionStatus();
        this.loadSuggestions();
        this.setupEventListeners();
        
        // Show suggestion popup on key pages
        this.showWelcomeSuggestions();
    }

    createSearchUI() {
        // Create search box in header/nav
        const searchHTML = `
            <div class="global-search-container" id="globalSearchContainer">
                <div class="search-box">
                    <input type="text" 
                           id="globalSearchInput" 
                           placeholder="🔍 Search leads, pages, and contracts..." 
                           autocomplete="off"
                           disabled>
                    <button id="searchButton" class="search-btn" disabled>
                        <i class="fas fa-search"></i>
                    </button>
                    <div id="searchStatus" class="search-status"></div>
                </div>
                <div id="searchResults" class="search-results" style="display: none;"></div>
            </div>
        `;

        // Insert into navigation or header
        const nav = document.querySelector('nav') || document.querySelector('header') || document.body;
        const searchContainer = document.createElement('div');
        searchContainer.innerHTML = searchHTML;
        
        // Add to nav if it exists, otherwise to top of body
        if (nav.tagName === 'NAV' || nav.tagName === 'HEADER') {
            nav.appendChild(searchContainer.firstElementChild);
        } else {
            document.body.insertBefore(searchContainer.firstElementChild, document.body.firstChild);
        }

        this.searchBox = document.getElementById('globalSearchInput');
        this.resultsContainer = document.getElementById('searchResults');
        this.searchButton = document.getElementById('searchButton');
    }

    checkSubscriptionStatus() {
        // Check if user is subscriber (will enable search)
        fetch('/api/check-lead-access')
            .then(res => res.json())
            .then(data => {
                this.isSubscriber = data.is_unlimited || false;
                
                if (this.isSubscriber) {
                    this.searchBox.disabled = false;
                    this.searchButton.disabled = false;
                    this.searchBox.placeholder = '🔍 Search leads, pages, and contracts...';
                } else {
                    this.searchBox.placeholder = '🔒 Search available for subscribers only';
                    document.getElementById('searchStatus').innerHTML = 
                        '<small style="color: #f39c12;">⭐ <a href="/pricing">Subscribe</a> to unlock search</small>';
                }
            })
            .catch(err => console.error('Error checking subscription:', err));
    }

    setupEventListeners() {
        // Search input with debounce
        this.searchBox.addEventListener('input', (e) => {
            clearTimeout(this.debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                this.hideResults();
                return;
            }

            this.debounceTimer = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });

        // Search button click
        this.searchButton.addEventListener('click', () => {
            const query = this.searchBox.value.trim();
            if (query.length >= 2) {
                this.performSearch(query);
            }
        });

        // Enter key to search
        this.searchBox.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = this.searchBox.value.trim();
                if (query.length >= 2) {
                    this.performSearch(query);
                }
            }
        });

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.global-search-container')) {
                this.hideResults();
            }
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideResults();
            }
        });
    }

    performSearch(query) {
        if (!this.isSubscriber) {
            this.showSubscriptionPrompt();
            return;
        }

        console.log('🔍 Searching for:', query);
        this.showLoading();

        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.displayResults(data);
                } else if (data.requires_subscription) {
                    this.showSubscriptionPrompt();
                } else {
                    this.showError(data.message);
                }
            })
            .catch(err => {
                console.error('Search error:', err);
                this.showError('Search failed. Please try again.');
            });
    }

    displayResults(data) {
        const { results, total_results, query } = data;
        
        if (total_results === 0) {
            this.resultsContainer.innerHTML = `
                <div class="search-no-results">
                    <p>No results found for "<strong>${this.escapeHtml(query)}</strong>"</p>
                    <p><small>Try different keywords or browse our categories</small></p>
                </div>
            `;
            this.showResults();
            return;
        }

        let html = `<div class="search-results-header">
                        <h4>Found ${total_results} result${total_results !== 1 ? 's' : ''} for "${this.escapeHtml(query)}"</h4>
                    </div>`;

        // Display each category
        const categories = [
            { key: 'pages', title: '📄 Site Pages', icon: '📄' },
            { key: 'local_government', title: '🏛️ Local Government', icon: '🏛️' },
            { key: 'commercial', title: '🏢 Commercial Properties', icon: '🏢' },
            { key: 'k12_schools', title: '🏫 K-12 Schools', icon: '🏫' },
            { key: 'colleges', title: '🎓 Colleges & Universities', icon: '🎓' },
            { key: 'supply_contracts', title: '🌍 Supply Contracts', icon: '🌍' }
        ];

        categories.forEach(cat => {
            const items = results[cat.key];
            if (items && items.length > 0) {
                html += `<div class="search-category">
                            <h5>${cat.icon} ${cat.title} (${items.length})</h5>
                            <div class="search-items">`;
                
                items.forEach(item => {
                    html += `
                        <a href="${item.url}" class="search-result-item" data-category="${cat.key}">
                            <div class="result-title">${this.escapeHtml(item.title)}</div>
                            <div class="result-description">${this.escapeHtml(item.description)}</div>
                            ${item.agency ? `<div class="result-meta">${this.escapeHtml(item.agency)}</div>` : ''}
                            ${item.location ? `<div class="result-meta">📍 ${this.escapeHtml(item.location)}</div>` : ''}
                        </a>
                    `;
                });
                
                html += `</div></div>`;
            }
        });

        this.resultsContainer.innerHTML = html;
        this.showResults();
    }

    showLoading() {
        this.resultsContainer.innerHTML = `
            <div class="search-loading">
                <div class="spinner"></div>
                <p>Searching...</p>
            </div>
        `;
        this.showResults();
    }

    showResults() {
        this.resultsContainer.style.display = 'block';
    }

    hideResults() {
        this.resultsContainer.style.display = 'none';
    }

    showError(message) {
        this.resultsContainer.innerHTML = `
            <div class="search-error">
                <p>❌ ${this.escapeHtml(message)}</p>
            </div>
        `;
        this.showResults();
    }

    showSubscriptionPrompt() {
        this.resultsContainer.innerHTML = `
            <div class="search-subscription-prompt">
                <h4>🔒 Search Feature - Subscribers Only</h4>
                <p>Unlock powerful search across all leads and contracts!</p>
                <a href="/pricing" class="btn-subscribe">Subscribe Now</a>
            </div>
        `;
        this.showResults();
    }

    // Algorithmic Suggestions System
    loadSuggestions() {
        if (!this.isSubscriber) return;

        fetch('/api/search-suggestions')
            .then(res => res.json())
            .then(data => {
                if (data.success && data.suggestions.length > 0) {
                    this.suggestions = data.suggestions;
                    this.personalizedSuggestions = data.personalized;
                }
            })
            .catch(err => console.error('Error loading suggestions:', err));
    }

    showWelcomeSuggestions() {
        // Show suggestions popup 5 seconds after page load (only for subscribers)
        setTimeout(() => {
            if (this.isSubscriber && this.suggestions && this.suggestions.length > 0) {
                this.showSuggestionsModal();
            }
        }, 5000);
    }

    showSuggestionsModal() {
        // Don't show if already dismissed in this session
        if (sessionStorage.getItem('suggestions_dismissed')) return;

        const modal = document.createElement('div');
        modal.className = 'suggestions-modal';
        modal.id = 'suggestionsModal';
        
        const personalizedText = this.personalizedSuggestions 
            ? '🎯 <strong>Personalized</strong> for you' 
            : '🔥 Popular right now';

        let html = `
            <div class="suggestions-modal-content">
                <button class="suggestions-close" onclick="searchSystem.closeSuggestionsModal()">×</button>
                <h3>💡 Suggested Leads for You</h3>
                <p class="suggestions-subtitle">${personalizedText}</p>
                <div class="suggestions-list">
        `;

        this.suggestions.slice(0, 3).forEach(suggestion => {
            html += `
                <a href="${suggestion.url}" class="suggestion-item">
                    <div class="suggestion-icon">${suggestion.icon}</div>
                    <div class="suggestion-content">
                        <h4>${this.escapeHtml(suggestion.title)}</h4>
                        <p>${this.escapeHtml(suggestion.description)}</p>
                    </div>
                </a>
            `;
        });

        html += `
                </div>
                <button class="btn-dismiss" onclick="searchSystem.closeSuggestionsModal()">
                    Maybe Later
                </button>
            </div>
        `;

        modal.innerHTML = html;
        document.body.appendChild(modal);

        // Animate in
        setTimeout(() => modal.classList.add('active'), 100);
    }

    closeSuggestionsModal() {
        const modal = document.getElementById('suggestionsModal');
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => modal.remove(), 300);
        }
        sessionStorage.setItem('suggestions_dismissed', 'true');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize search system when DOM is ready
let searchSystem;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        searchSystem = new SearchSystem();
    });
} else {
    searchSystem = new SearchSystem();
}
