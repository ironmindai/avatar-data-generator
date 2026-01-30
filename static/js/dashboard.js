/**
 * Dashboard JavaScript
 * Handles dashboard interactivity and data updates
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Highlight active navigation item based on current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-link');

    navLinks.forEach(function(link) {
        // Remove all active classes first
        link.classList.remove('active');
        link.removeAttribute('aria-current');

        // Add active class to matching link
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });

    // Add smooth hover effects to cards
    const cards = document.querySelectorAll('.card-hover');
    cards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.2s ease';
        });
    });

    // Initialize stats counters with animation (if values are present)
    animateCounters();

    // Function to animate number counters
    function animateCounters() {
        const counters = document.querySelectorAll('[style*="font-size: var(--font-size-h2)"]');

        counters.forEach(function(counter) {
            const target = parseInt(counter.textContent) || 0;
            const duration = 1000; // 1 second
            const increment = target / (duration / 16); // 60fps
            let current = 0;

            if (target > 0) {
                const timer = setInterval(function() {
                    current += increment;
                    if (current >= target) {
                        counter.textContent = target;
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current);
                    }
                }, 16);
            }
        });
    }

    // Handle logout with confirmation
    const logoutButton = document.querySelector('a[href="/logout"]');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            const confirmLogout = confirm('Are you sure you want to log out?');
            if (!confirmLogout) {
                e.preventDefault();
            }
        });
    }

    // Add keyboard navigation for cards
    const actionCards = document.querySelectorAll('.card');
    actionCards.forEach(function(card) {
        const button = card.querySelector('.btn');
        if (button) {
            card.setAttribute('tabindex', '0');
            card.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    button.click();
                }
            });
        }
    });

    // Mobile sidebar toggle (for responsive design)
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }

    // Refresh data periodically (optional - can be enabled later)
    // setInterval(function() {
    //     refreshDashboardData();
    // }, 30000); // Refresh every 30 seconds

    // Function to refresh dashboard data via AJAX (to be implemented with backend)
    function refreshDashboardData() {
        // Fetch updated stats from backend API
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                // Update dashboard values
                console.log('Dashboard data refreshed:', data);
            })
            .catch(error => {
                console.error('Error refreshing dashboard data:', error);
            });
    }
});
