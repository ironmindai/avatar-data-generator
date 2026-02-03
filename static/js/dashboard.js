/**
 * Dashboard JavaScript
 * Handles dashboard statistics and chart visualization
 * Adheres to brandbook specifications in docs/brandbook.md
 * Last Updated: 2026-01-30
 */

// Store unified chart instance globally
let unifiedChart = null;

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
 * Update or initialize unified chart with all 3 series
 * @param {Object} last7Days - Last 7 days data object
 */
function updateCharts(last7Days) {
    // Process data for unified chart - all series share the same dates
    const dates = last7Days.tasks_by_date.map(item => formatDate(item.date));
    const tasksCounts = last7Days.tasks_by_date.map(item => item.count);
    const personasCounts = last7Days.personas_by_date.map(item => item.count);
    const imagesCounts = last7Days.images_by_date.map(item => item.count);

    // Initialize or update unified chart
    initializeUnifiedChart(dates, tasksCounts, personasCounts, imagesCounts);
}

/**
 * Initialize or update unified Chart.js line chart with all 3 series
 * @param {Array} labels - X-axis labels (dates)
 * @param {Array} tasksData - Tasks data points
 * @param {Array} personasData - Personas data points
 * @param {Array} imagesData - Images data points
 */
function initializeUnifiedChart(labels, tasksData, personasData, imagesData) {
    const canvas = document.getElementById('unified-chart');
    const skeleton = document.getElementById('unified-chart-skeleton');

    // Hide skeleton, show canvas
    if (skeleton) {
        skeleton.style.display = 'none';
    }
    canvas.style.display = 'block';

    // If chart exists, update data
    if (unifiedChart) {
        unifiedChart.data.labels = labels;
        unifiedChart.data.datasets[0].data = tasksData;
        unifiedChart.data.datasets[1].data = personasData;
        unifiedChart.data.datasets[2].data = imagesData;
        unifiedChart.update('none'); // Update without animation
        return;
    }

    // Create new unified chart with 3 series
    const ctx = canvas.getContext('2d');

    const chartConfig = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Tasks',
                    data: tasksData,
                    borderColor: '#00d9ff', // neon cyan
                    backgroundColor: '#00d9ff20', // 20% opacity
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00d9ff',
                    pointBorderColor: '#1a1a1a',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#00d9ff',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                },
                {
                    label: 'Personas',
                    data: personasData,
                    borderColor: '#00ff88', // neon green
                    backgroundColor: '#00ff8820', // 20% opacity
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00ff88',
                    pointBorderColor: '#1a1a1a',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#00ff88',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                },
                {
                    label: 'Images',
                    data: imagesData,
                    borderColor: '#0088ff', // neon blue
                    backgroundColor: '#0088ff20', // 20% opacity
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#0088ff',
                    pointBorderColor: '#1a1a1a',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#0088ff',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        font: {
                            family: 'Inter, sans-serif',
                            size: 12,
                            weight: '500'
                        },
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'line',
                        boxWidth: 40,
                        boxHeight: 3,
                        generateLabels: function(chart) {
                            // Custom label generator to color each label text to match its line
                            const datasets = chart.data.datasets;
                            return datasets.map((dataset, i) => ({
                                text: dataset.label,
                                fillStyle: dataset.borderColor, // Use line color for the indicator
                                strokeStyle: dataset.borderColor,
                                lineWidth: 2,
                                hidden: !chart.isDatasetVisible(i),
                                index: i,
                                // Color the text to match the line color
                                fontColor: dataset.borderColor
                            }));
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#242424',
                    titleColor: '#ffffff',
                    bodyColor: '#cccccc',
                    borderColor: '#00d9ff',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toLocaleString();
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
    unifiedChart = new Chart(ctx, chartConfig);
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

    // Hide chart skeleton
    const skeleton = document.getElementById('unified-chart-skeleton');
    if (skeleton) {
        skeleton.style.display = 'none';
    }

    // Show error message in chart
    const canvas = document.getElementById('unified-chart');
    if (canvas) {
        canvas.style.display = 'none';
    }

    const chartBody = document.querySelector('.chart-body');
    if (chartBody) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'display: flex; align-items: center; justify-content: center; height: 350px; color: var(--color-error); font-size: var(--font-size-small);';
        errorDiv.textContent = 'Failed to load chart data';
        chartBody.appendChild(errorDiv);
    }

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
