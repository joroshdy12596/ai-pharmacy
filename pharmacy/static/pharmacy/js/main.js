// ============================================================================
// ELESRAA PHARMACY - MAIN JAVASCRIPT
// Modern, Professional, and Responsive UI Enhancements
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    console.log('✓ Elesraa Pharmacy app initialized');
    
    // Initialize all features
    initializeSelect2();
    initializeFadeAnimations();
    initializeTooltips();
    initializeFormValidation();
    initializeTableEnhancements();
    initializeButtonEffects();
    initializeScrollAnimations();
    setupEventDelegation();
}

// ============================================================================
// 1. SELECT2 INITIALIZATION
// ============================================================================
function initializeSelect2() {
    if (typeof $ !== 'undefined' && $.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5',
            placeholder: 'Choose an option...',
            allowClear: true,
            dropdownParent: $('body')
        });

        // Customer search Select2
        if ($('#customer-select').length) {
            $('#customer-select').select2({
                placeholder: 'Search customer by name or phone...',
                allowClear: true,
                ajax: {
                    url: '/pharmacy/customer/search/',
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return { term: params.term };
                    },
                    processResults: function(data) {
                        return {
                            results: data.results.map(function(item) {
                                return {
                                    id: item.id,
                                    text: item.text + ' - Points: ' + item.points
                                };
                            })
                        };
                    },
                    cache: true
                }
            });

            $('#customer-select').on('select2:select', function(e) {
                $('#selected-customer-id').val(e.params.data.id);
            });

            $('#customer-select').on('select2:unselect', function() {
                $('#selected-customer-id').val('');
            });
        }
    }
}

// ============================================================================
// 2. FADE IN ANIMATIONS
// ============================================================================
function initializeFadeAnimations() {
    const cards = document.querySelectorAll('.card');
    const rows = document.querySelectorAll('.row');
    
    cards.forEach((card, index) => {
        card.style.animation = `slideUp 0.4s ease-out ${index * 0.1}s backwards`;
    });

    // Observe elements for scroll animations
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.card, .alert, .table').forEach(el => {
            observer.observe(el);
        });
    }
}

// ============================================================================
// 3. BOOTSTRAP TOOLTIPS
// ============================================================================
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ============================================================================
// 4. FORM VALIDATION
// ============================================================================
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showNotification('Please fill all required fields correctly', 'warning');
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Real-time validation for text inputs
    document.querySelectorAll('input[type="email"], input[type="number"], input[type="text"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.type === 'email' && this.value) {
                const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.value);
                this.classList.toggle('is-invalid', !isValid);
                this.classList.toggle('is-valid', isValid);
            }
        });
    });
}

// ============================================================================
// 5. TABLE ENHANCEMENTS
// ============================================================================
function initializeTableEnhancements() {
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(table => {
        // Add hover effects
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((row, index) => {
            row.style.animation = `slideUp 0.3s ease-out ${index * 0.05}s backwards`;
            
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = 'rgba(0, 212, 255, 0.05)';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });

        // Add striping
        rows.forEach((row, index) => {
            if (index % 2 === 0) {
                row.style.backgroundColor = 'rgba(0, 0, 0, 0.01)';
            }
        });
    });
}

// ============================================================================
// 6. BUTTON EFFECTS
// ============================================================================
function initializeButtonEffects() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mousedown', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
            ripple.style.animation = 'ripple 0.6s ease-out';
            ripple.style.pointerEvents = 'none';

            if (this.style.position === 'static') {
                this.style.position = 'relative';
            }

            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// ============================================================================
// 7. SCROLL ANIMATIONS
// ============================================================================
function initializeScrollAnimations() {
    const scrollButtons = document.querySelectorAll('a[href^="#"], a[href*="scroll"]');
    
    scrollButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });
}

// ============================================================================
// 8. EVENT DELEGATION & GLOBAL HANDLERS
// ============================================================================
function setupEventDelegation() {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert:not(.keep-alert)').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Handle modal confirmations
    document.querySelectorAll('[data-confirm]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Handle AJAX forms if any
    document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
        form.addEventListener('submit', handleAjaxForm);
    });
}

// ============================================================================
// 9. NOTIFICATION SYSTEM
// ============================================================================
function showNotification(message, type = 'info', duration = 3000) {
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show shadow-lg`;
    alertEl.style.position = 'fixed';
    alertEl.style.top = '20px';
    alertEl.style.right = '20px';
    alertEl.style.zIndex = '9999';
    alertEl.style.maxWidth = '400px';
    alertEl.style.animation = 'slideDown 0.3s ease-out';
    
    const icon = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    }[type] || 'info-circle';

    alertEl.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        <strong>${message}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertEl);

    if (duration > 0) {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertEl);
            bsAlert.close();
        }, duration);
    }

    return alertEl;
}

// ============================================================================
// 10. AJAX FORM HANDLER
// ============================================================================
function handleAjaxForm(e) {
    e.preventDefault();
    
    const form = this;
    const url = form.getAttribute('action');
    const method = form.getAttribute('method') || 'POST';
    const formData = new FormData(form);

    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Operation completed successfully', 'success');
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } else {
            showNotification(data.message || 'An error occurred', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred. Please try again.', 'error');
    });
}

// ============================================================================
// 11. UTILITY FUNCTIONS
// ============================================================================

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Format date
function formatDate(date, format = 'short') {
    const options = format === 'short' 
        ? { year: 'numeric', month: 'short', day: 'numeric' }
        : { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(date).toLocaleDateString('en-US', options);
}

// Stock status badge
function getStockBadge(quantity, threshold = 5) {
    if (quantity === 0) return '<span class="badge bg-danger">Out of Stock</span>';
    if (quantity <= threshold) return '<span class="badge bg-warning">Low Stock</span>';
    return '<span class="badge bg-success">In Stock</span>';
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================================
// 12. KEYBOARD SHORTCUTS
// ============================================================================
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K: Open search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchBtn = document.querySelector('[href*="search"]');
        if (searchBtn) searchBtn.click();
    }

    // Escape: Close modals
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.show').forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
});

// ============================================================================
// 13. PERFORMANCE OPTIMIZATION
// ============================================================================
if ('performance' in window) {
    window.addEventListener('load', () => {
        const perfData = performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        console.log('📊 Page Load Time:', pageLoadTime + 'ms');
    });
}

// ============================================================================
// 14. LEGACY SUPPORT
// ============================================================================
function requestStock(medicineName) {
    showNotification(`Stock request for ${medicineName} has been noted.`, 'info');
} 