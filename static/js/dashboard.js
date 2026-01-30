/**
 * Dashboard JavaScript
 * Handles dashboard statistics and chart visualization
 * Adheres to brandbook specifications in docs/brandbook.md
 * Last Updated: 2026-01-30
 */

// Store chart instances globally
let tasksChart = null;
let personasChart = null;
let imagesChart = null;

// Auto-refresh interval (30 seconds)
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();

    // Load dashboard data
    loadDashboardData();

    // Set up auto-refresh for in-progress tasks (every 30 seconds)
    refreshInterval = setInterval(function() {
        loadDashboardData(true); // silent refresh
    }, 30000);
});

/**
 * Load dashboard statistics and charts data
 * @param {boolean} silent - If true, skip loading animations
 */
function loadDashboardData(silent = false) {
    fetch('/api/dashboard/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch dashboard data');
            }
            return response.json();
        })
        .then(data => {
            // Update overview statistics
            updateStatistics(data.overview);

            // Initialize or update charts
            updateCharts(data.last_7_days);
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
            showErrorState();
        });
}

/**
 * Update statistics card values with animation
 * @param {Object} overview - Overview statistics object
 */
function updateStatistics(overview) {
    // Helper function to format numbers with commas
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    // Helper function to animate counter
    function animateCounter(element, targetValue, decimals = 0) {
        const startValue = 0;
        const duration = 1000; // 1 second
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = startValue + (targetValue - startValue) * easeOut;

            if (decimals > 0) {
                element.textContent = currentValue.toFixed(decimals);
            } else {
                element.textContent = formatNumber(Math.floor(currentValue));
            }

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                // Final value
                if (decimals > 0) {
                    element.textContent = targetValue.toFixed(decimals);
                } else {
                    element.textContent = formatNumber(targetValue);
                }
                // Remove skeleton class
                element.classList.remove('skeleton-text');
            }
        }

        requestAnimationFrame(update);
    }

    // Update each statistic with animation
    animateCounter(
        document.getElementById('total-tasks'),
        overview.total_tasks || 0
    );

    animateCounter(
        document.getElementById('total-personas'),
        overview.total_personas || 0
    );

    animateCounter(
        document.getElementById('total-images'),
        overview.total_images || 0
    );

    animateCounter(
        document.getElementById('tasks-in-progress'),
        overview.tasks_in_progress || 0
    );

    animateCounter(
        document.getElementById('completed-tasks'),
        overview.completed_tasks || 0
    );

    animateCounter(
        document.getElementById('failed-tasks'),
        overview.failed_tasks || 0
    );

    animateCounter(
        document.getElementById('avg-personas'),
        overview.average_personas_per_task || 0,
        1 // 1 decimal place
    );

    animateCounter(
        document.getElementById('avg-images'),
        overview.average_images_per_persona || 0,
        1 // 1 decimal place
    );
}

/**
 * Update or initialize all charts
 * @param {Object} last7Days - Last 7 days data object
 */
function updateCharts(last7Days) {
    // Process data for charts
    const tasksDates = last7Days.tasks_by_date.map(item => formatDate(item.date));
    const tasksCounts = last7Days.tasks_by_date.map(item => item.count);

    const personasDates = last7Days.personas_by_date.map(item => formatDate(item.date));
    const personasCounts = last7Days.personas_by_date.map(item => item.count);

    const imagesDates = last7Days.images_by_date.map(item => formatDate(item.date));
    const imagesCounts = last7Days.images_by_date.map(item => item.count);

    // Initialize or update tasks chart
    initializeChart(
        'tasks-chart',
        tasksChart,
        tasksDates,
        tasksCounts,
        'Tasks',
        '#00d9ff' // neon cyan
    );

    // Initialize or update personas chart
    initializeChart(
        'personas-chart',
        personasChart,
        personasDates,
        personasCounts,
        'Personas',
        '#00ff88' // neon green
    );

    // Initialize or update images chart
    initializeChart(
        'images-chart',
        imagesChart,
        imagesDates,
        imagesCounts,
        'Images',
        '#c77dff' // neon purple
    );
}

/**
 * Initialize or update a Chart.js line chart
 * @param {string} canvasId - Canvas element ID
 * @param {Object} chartInstance - Existing chart instance (or null)
 * @param {Array} labels - X-axis labels
 * @param {Array} data - Y-axis data points
 * @param {string} label - Dataset label
 * @param {string} color - Line color
 */
function initializeChart(canvasId, chartInstance, labels, data, label, color) {
    const canvas = document.getElementById(canvasId);
    const skeleton = document.getElementById(canvasId + '-skeleton');

    // Hide skeleton, show canvas
    if (skeleton) {
        skeleton.style.display = 'none';
    }
    canvas.style.display = 'block';

    // If chart exists, update data
    if (chartInstance) {
        chartInstance.data.labels = labels;
        chartInstance.data.datasets[0].data = data;
        chartInstance.update('none'); // Update without animation
        return;
    }

    // Create new chart
    const ctx = canvas.getContext('2d');

    const chartConfig = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '20', // 20% opacity
                borderWidth: 2,
                tension: 0.4, // Smooth curves
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: color,
                pointBorderColor: '#1a1a1a',
                pointBorderWidth: 2,
                pointHoverBackgroundColor: color,
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#242424',
                    titleColor: '#ffffff',
                    bodyColor: '#cccccc',
                    borderColor: color,
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return label + ': ' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#333333',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#999999',
                        font: {
                            family: 'Inter, sans-serif',
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#333333',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#999999',
                        font: {
                            family: 'JetBrains Mono, monospace',
                            size: 11
                        },
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    };

    // Store chart instance
    if (canvasId === 'tasks-chart') {
        tasksChart = new Chart(ctx, chartConfig);
    } else if (canvasId === 'personas-chart') {
        personasChart = new Chart(ctx, chartConfig);
    } else if (canvasId === 'images-chart') {
        imagesChart = new Chart(ctx, chartConfig);
    }
}

/**
 * Format date string to readable format
 * @param {string} dateString - Date string (YYYY-MM-DD)
 * @returns {string} Formatted date (MMM DD)
 */
function formatDate(dateString) {
    const date = new Date(dateString + 'T00:00:00');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[date.getMonth()] + ' ' + date.getDate();
}

/**
 * Show error state when data loading fails
 */
function showErrorState() {
    // Update all stat values to show error
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(function(element) {
        element.textContent = 'Error';
        element.classList.remove('skeleton-text');
        element.style.color = 'var(--color-error)';
    });

    // Hide chart skeletons
    const skeletons = document.querySelectorAll('.skeleton-chart');
    skeletons.forEach(function(skeleton) {
        skeleton.style.display = 'none';
    });

    // Show error message in charts
    const chartBodies = document.querySelectorAll('.chart-body');
    chartBodies.forEach(function(body) {
        const canvas = body.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'none';
        }

        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'display: flex; align-items: center; justify-content: center; height: 250px; color: var(--color-error); font-size: var(--font-size-small);';
        errorDiv.textContent = 'Failed to load chart data';
        body.appendChild(errorDiv);
    });

    // Stop auto-refresh
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

/**
 * Cleanup when page is unloaded
 */
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
