/**
 * CUMULATIVE LAYOUT SHIFT (CLS) PREVENTION - SKELETON LOADERS
 * Displays placeholder content during loading to prevent page jumping
 */

// ===== RFP/CONTRACT CARD SKELETON LOADER =====
function showSkeletonCards(containerId, count = 3) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Set minimum height to prevent collapse
    container.style.minHeight = '400px';
    
    const skeletonHtml = `
        <div class="skeleton-cards-container">
            ${Array.from({length: count}, (_, i) => `
                <div class="card mb-3 skeleton-card" style="min-height: 280px;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div style="flex: 1;">
                                <div class="skeleton-loader" style="width: 120px; height: 24px; margin-bottom: 8px;"></div>
                                <div class="skeleton-loader" style="width: 90px; height: 24px;"></div>
                            </div>
                            <div class="skeleton-loader" style="width: 80px; height: 32px;"></div>
                        </div>
                        
                        <div class="skeleton-loader mb-3" style="width: 100%; height: 24px;"></div>
                        <div class="skeleton-loader mb-3" style="width: 85%; height: 24px;"></div>
                        
                        <div class="row g-2 mb-3">
                            <div class="col-md-6">
                                <div class="skeleton-loader" style="width: 100%; height: 18px;"></div>
                            </div>
                            <div class="col-md-6">
                                <div class="skeleton-loader" style="width: 100%; height: 18px;"></div>
                            </div>
                            <div class="col-md-6">
                                <div class="skeleton-loader" style="width: 100%; height: 18px;"></div>
                            </div>
                            <div class="col-md-6">
                                <div class="skeleton-loader" style="width: 100%; height: 18px;"></div>
                            </div>
                        </div>
                        
                        <div class="skeleton-loader" style="width: 100%; height: 38px;"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = skeletonHtml;
}

// ===== STATE CARD SKELETON LOADER =====
function showStateCardSkeleton(cardElement) {
    if (!cardElement) return;
    
    // Set minimum height to prevent collapse
    cardElement.style.minHeight = '300px';
    
    const skeletonHtml = `
        <div class="card-body skeleton-state-card">
            <div class="text-center mb-3">
                <div class="skeleton-loader mx-auto" style="width: 60px; height: 60px; border-radius: 50%;"></div>
            </div>
            
            <div class="skeleton-loader mx-auto mb-3" style="width: 180px; height: 28px;"></div>
            
            <div class="mb-3">
                <div class="skeleton-loader mb-2" style="width: 100%; height: 16px;"></div>
                <div class="skeleton-loader mb-2" style="width: 90%; height: 16px;"></div>
                <div class="skeleton-loader" style="width: 70%; height: 16px;"></div>
            </div>
            
            <div class="skeleton-loader mx-auto mb-3" style="width: 150px; height: 38px;"></div>
            
            <div class="skeleton-loader mx-auto" style="width: 120px; height: 32px;"></div>
        </div>
    `;
    
    cardElement.innerHTML = skeletonHtml;
}

// ===== MODAL SKELETON LOADER =====
function showModalSkeleton(modalBodyElement) {
    if (!modalBodyElement) return;
    
    // Set minimum height to prevent modal size jump
    modalBodyElement.style.minHeight = '400px';
    
    const skeletonHtml = `
        <div class="modal-skeleton">
            <div class="skeleton-loader mb-3" style="width: 70%; height: 32px;"></div>
            <div class="skeleton-loader mb-4" style="width: 100%; height: 20px;"></div>
            
            <div class="row g-3 mb-4">
                <div class="col-md-6">
                    <div class="skeleton-loader" style="width: 100%; height: 80px;"></div>
                </div>
                <div class="col-md-6">
                    <div class="skeleton-loader" style="width: 100%; height: 80px;"></div>
                </div>
            </div>
            
            <div class="skeleton-loader mb-2" style="width: 100%; height: 18px;"></div>
            <div class="skeleton-loader mb-2" style="width: 100%; height: 18px;"></div>
            <div class="skeleton-loader mb-2" style="width: 95%; height: 18px;"></div>
            <div class="skeleton-loader mb-4" style="width: 80%; height: 18px;"></div>
            
            <div class="skeleton-loader" style="width: 140px; height: 42px;"></div>
        </div>
    `;
    
    modalBodyElement.innerHTML = skeletonHtml;
}

// ===== TABLE SKELETON LOADER =====
function showTableSkeleton(tableBodyElement, rows = 5) {
    if (!tableBodyElement) return;
    
    const skeletonRows = Array.from({length: rows}, (_, i) => `
        <tr>
            <td><div class="skeleton-loader" style="width: 90%; height: 16px;"></div></td>
            <td><div class="skeleton-loader" style="width: 80%; height: 16px;"></div></td>
            <td><div class="skeleton-loader" style="width: 70%; height: 16px;"></div></td>
            <td><div class="skeleton-loader" style="width: 60%; height: 16px;"></div></td>
            <td><div class="skeleton-loader" style="width: 80px; height: 32px;"></div></td>
        </tr>
    `).join('');
    
    tableBodyElement.innerHTML = skeletonRows;
}

// ===== REMOVE SKELETON & FADE IN CONTENT =====
function fadeInContent(element, newContent) {
    if (!element) return;
    
    // Fade out current content
    element.style.opacity = '0';
    element.style.transition = 'opacity 0.3s ease-in-out';
    
    setTimeout(() => {
        // Replace content
        element.innerHTML = newContent;
        
        // Reset min-height if it was set
        element.style.minHeight = 'auto';
        
        // Fade in new content
        setTimeout(() => {
            element.style.opacity = '1';
        }, 50);
    }, 300);
}

// ===== LOADING SPINNER WITHOUT LAYOUT SHIFT =====
function showLoadingSpinner(containerId, message = 'Loading...') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Reserve space to prevent layout shift
    container.style.minHeight = '200px';
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';
    
    const spinnerHtml = `
        <div class="text-center spinner-container">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-secondary">${message}</p>
        </div>
    `;
    
    container.innerHTML = spinnerHtml;
}

// ===== HIDE ELEMENT WITHOUT LAYOUT SHIFT =====
function hideWithoutShift(element) {
    if (!element) return;
    
    element.style.visibility = 'hidden';
    element.style.opacity = '0';
    element.style.pointerEvents = 'none';
    // Keep element in layout flow - don't use display: none
}

// ===== SHOW ELEMENT WITHOUT LAYOUT SHIFT =====
function showWithoutShift(element) {
    if (!element) return;
    
    element.style.visibility = 'visible';
    element.style.opacity = '1';
    element.style.pointerEvents = 'auto';
    element.style.transition = 'opacity 0.3s ease-in-out';
}

// ===== EMPTY STATE PLACEHOLDER (prevents collapse) =====
function showEmptyState(containerId, message, iconClass = 'fa-inbox') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Reserve minimum height
    container.style.minHeight = '250px';
    
    const emptyHtml = `
        <div class="alert alert-no-results d-flex flex-column align-items-center justify-content-center py-5">
            <i class="fas ${iconClass} fa-3x text-secondary mb-3"></i>
            <h5 class="text-secondary mb-2">No Results Found</h5>
            <p class="text-secondary mb-0">${message}</p>
        </div>
    `;
    
    container.innerHTML = emptyHtml;
}

// ===== PROGRESSIVE LOADING FOR LISTS =====
function showProgressiveList(containerId, items, itemRenderer, batchSize = 10) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Reserve full height immediately
    const estimatedItemHeight = 100; // Adjust based on your item height
    container.style.minHeight = `${items.length * estimatedItemHeight}px`;
    
    let currentBatch = 0;
    
    function loadNextBatch() {
        const start = currentBatch * batchSize;
        const end = Math.min(start + batchSize, items.length);
        
        for (let i = start; i < end; i++) {
            const itemHtml = itemRenderer(items[i]);
            container.insertAdjacentHTML('beforeend', itemHtml);
        }
        
        currentBatch++;
        
        if (end < items.length) {
            // Show loading indicator
            container.insertAdjacentHTML('beforeend', `
                <div class="text-center my-3 batch-loader">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Loading more...</span>
                    </div>
                </div>
            `);
            
            // Load next batch after short delay
            setTimeout(() => {
                const loader = container.querySelector('.batch-loader');
                if (loader) loader.remove();
                loadNextBatch();
            }, 100);
        } else {
            // All items loaded - reset min-height
            container.style.minHeight = 'auto';
        }
    }
    
    loadNextBatch();
}

// ===== IMAGE PLACEHOLDER (prevents CLS from image load) =====
function createImagePlaceholder(width, height, bgColor = '#e0e0e0') {
    return `
        <div class="image-placeholder skeleton-loader" 
             style="width: ${width}px; height: ${height}px; background-color: ${bgColor};">
        </div>
    `;
}

// ===== UTILITY: Pre-reserve space for async content =====
function reserveSpace(elementId, minHeight = '400px') {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.minHeight = minHeight;
    }
}

// ===== UTILITY: Smooth content replacement =====
function replaceContentSmoothly(elementId, newContent, fadeTime = 300) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Fade out
    element.style.opacity = '0';
    element.style.transition = `opacity ${fadeTime}ms ease-in-out`;
    
    setTimeout(() => {
        element.innerHTML = newContent;
        // Fade in
        setTimeout(() => {
            element.style.opacity = '1';
        }, 50);
    }, fadeTime);
}

// ===== Export functions for global use =====
window.skeletonLoaders = {
    showSkeletonCards,
    showStateCardSkeleton,
    showModalSkeleton,
    showTableSkeleton,
    fadeInContent,
    showLoadingSpinner,
    hideWithoutShift,
    showWithoutShift,
    showEmptyState,
    showProgressiveList,
    createImagePlaceholder,
    reserveSpace,
    replaceContentSmoothly
};

console.log('✅ CLS Prevention: Skeleton loaders initialized');
