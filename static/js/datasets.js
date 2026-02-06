/**
 * Datasets Page - JavaScript
 * Handles copy to clipboard, real-time updates, pagination, image preview, and exports
 * Adheres to brandbook specifications in docs/brandbook.md
 * Last Updated: 2026-01-30
 */

(function() {
  'use strict';

  // ========================================
  // GLOBAL STATE
  // ========================================

  let currentPage = 1;
  let totalPages = 1;
  let isPolling = false;
  let pollInterval = null;
  const POLL_INTERVAL_MS = 3000; // 3 seconds
  const RESULTS_PER_PAGE = 20;

  // ========================================
  // INITIALIZATION
  // ========================================

  document.addEventListener('DOMContentLoaded', function() {
    initializeCopyButtons();
    initializeFeatherIcons();

    // Check if we're on the detail page
    const taskIdElement = document.querySelector('[data-task-id]');
    if (taskIdElement && window.location.pathname.includes('/datasets/')) {
      const taskId = taskIdElement.getAttribute('data-task-id');
      if (taskId) {
        initializeDetailPage(taskId);
      }
    }
  });

  // ========================================
  // DATASETS LIST PAGE - COPY FUNCTIONALITY
  // ========================================

  function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.btn-copy, .btn-copy-large');

    copyButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const taskId = this.getAttribute('data-task-id');

        // Copy to clipboard
        copyToClipboard(taskId)
          .then(() => {
            showCopySuccess(this);
          })
          .catch(err => {
            console.error('Failed to copy task ID:', err);
            showToast('Failed to copy Task ID to clipboard', 'error');
          });
      });
    });
  }

  /**
   * Copy text to clipboard using modern Clipboard API with fallback
   */
  function copyToClipboard(text) {
    // Try modern Clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }

    // Fallback for older browsers
    return new Promise((resolve, reject) => {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();

      try {
        const successful = document.execCommand('copy');
        document.body.removeChild(textarea);

        if (successful) {
          resolve();
        } else {
          reject(new Error('Copy command failed'));
        }
      } catch (err) {
        document.body.removeChild(textarea);
        reject(err);
      }
    });
  }

  /**
   * Show visual feedback for successful copy
   */
  function showCopySuccess(button) {
    // Add success class
    button.classList.add('copied');

    // Change icon to check mark
    const icon = button.querySelector('i[data-feather]');
    if (icon) {
      icon.setAttribute('data-feather', 'check');
      feather.replace();
    }

    // Reset after 2 seconds
    setTimeout(() => {
      button.classList.remove('copied');

      if (icon) {
        icon.setAttribute('data-feather', 'copy');
        feather.replace();
      }
    }, 2000);
  }

  // ========================================
  // DATASET DETAIL PAGE - INITIALIZATION
  // ========================================

  function initializeDetailPage(taskId) {
    // Get current page from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentPage = parseInt(urlParams.get('page')) || 1;

    // Load initial data
    loadTaskData(taskId, currentPage);

    // Initialize error log toggle
    initializeErrorLogToggle();

    // Initialize export buttons
    initializeExportButtons(taskId);

    // Initialize image modal
    initializeImageModal();

    // Start polling for updates
    startPolling(taskId);
  }

  // ========================================
  // DATA FETCHING AND UPDATES
  // ========================================

  /**
   * Load task data from API
   */
  function loadTaskData(taskId, page) {
    const apiUrl = `/datasets/${taskId}/data?page=${page}`;

    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        updateTaskHeader(data.task);
        updateStatistics(data.task, data.progress);
        updateProgressBar(data.task, data.progress);
        updateErrorSection(data.task);
        updateExportButtons(data.task);
        updateResults(data.results, data.pagination);
        updatePagination(data.pagination, taskId);

        // Stop polling if task is completed or failed
        if (data.task.status === 'completed' || data.task.status === 'failed') {
          stopPolling();
        }

        // Re-initialize Feather icons
        feather.replace();
      })
      .catch(error => {
        console.error('Error loading task data:', error);
        showErrorState('Failed to load dataset. Please refresh the page.');
        stopPolling();
      });
  }

  /**
   * Update task header with status and metadata
   */
  function updateTaskHeader(task) {
    // Update status badge
    const statusContainer = document.getElementById('taskStatus');
    if (statusContainer) {
      statusContainer.innerHTML = getStatusBadgeHTML(task.status);
    }

    // Update metadata
    const metadataContainer = document.getElementById('taskMetadata');
    if (metadataContainer) {
      metadataContainer.innerHTML = `
        <div class="metadata-item">
          <span class="metadata-label">Persona Description:</span>
          <div class="metadata-value">${escapeHtml(task.persona_description)}</div>
        </div>
        <div class="metadata-item">
          <span class="metadata-label">Language:</span>
          <div class="metadata-value monospace">${escapeHtml(task.bio_language).toUpperCase()}</div>
        </div>
      `;
    }
  }

  /**
   * Update statistics panel
   */
  function updateStatistics(task, progress) {
    const panel = document.getElementById('statisticsPanel');
    if (!panel) return;

    const totalPersonas = task.number_to_generate;
    const totalImages = task.number_to_generate * task.images_per_persona;
    const personasGenerated = progress.completed_personas || 0;
    const imagesGenerated = progress.completed_images || 0;

    panel.innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Personas</div>
        <div class="stat-value">${personasGenerated} / ${totalPersonas}</div>
        <div class="stat-description">Generated personas</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Images</div>
        <div class="stat-value">${imagesGenerated} / ${totalImages}</div>
        <div class="stat-description">Generated images</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Time Elapsed</div>
        <div class="stat-value">${progress.time_elapsed}</div>
        <div class="stat-description">Duration</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Status</div>
        <div class="stat-value" style="font-size: 1rem;">${getStatusText(task.status)}</div>
        <div class="stat-description">${getStatusDescription(task.status, personasGenerated, imagesGenerated)}</div>
      </div>
    `;
  }

  /**
   * Update progress bar
   */
  function updateProgressBar(task, progress) {
    const section = document.getElementById('progressSection');
    if (!section) return;

    const percentage = Math.round(progress.progress_percentage || 0);
    const completedPersonas = progress.completed_personas || 0;
    const totalPersonas = task.number_to_generate;
    const completedImages = progress.completed_images || 0;
    const totalImages = task.number_to_generate * task.images_per_persona;

    const statusClass = task.status === 'completed' ? 'completed' :
                       task.status === 'failed' ? 'failed' :
                       'generating';

    section.innerHTML = `
      <div class="progress-header">
        <span class="progress-label">Overall Progress</span>
        <span class="progress-percentage">${percentage}%</span>
      </div>
      <div class="progress-bar-container">
        <div class="progress-bar ${statusClass}" style="width: ${percentage}%"></div>
      </div>
      <div class="progress-details">
        ${completedPersonas} / ${totalPersonas} personas, ${completedImages} / ${totalImages} images
      </div>
    `;
  }

  /**
   * Update error section
   */
  function updateErrorSection(task) {
    const section = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');

    if (task.status === 'failed' && task.error_log) {
      section.style.display = 'block';
      errorMessage.textContent = task.error_log;
    } else {
      section.style.display = 'none';
    }
  }

  /**
   * Update export buttons state
   */
  function updateExportButtons(task) {
    const exportJson = document.getElementById('exportJson');
    const exportCsv = document.getElementById('exportCsv');
    const exportZip = document.getElementById('exportZip');

    const isCompleted = task.status === 'completed';

    if (exportJson) exportJson.disabled = !isCompleted;
    if (exportCsv) exportCsv.disabled = !isCompleted;
    if (exportZip) exportZip.disabled = !isCompleted;
  }

  /**
   * Update results grid
   */
  function updateResults(results, pagination) {
    const grid = document.getElementById('resultsGrid');
    if (!grid) return;

    if (!results || results.length === 0) {
      grid.innerHTML = `
        <div class="results-empty">
          <i data-feather="inbox" class="results-empty-icon"></i>
          <p class="results-empty-text">No results generated yet. Please wait while data is being generated...</p>
        </div>
      `;
      feather.replace();
      return;
    }

    grid.innerHTML = results.map(result => createResultCardHTML(result)).join('');

    // Initialize bio tabs and image previews
    initializeBioTabs();
    initializeImagePreviews();

    // Re-initialize Feather icons
    feather.replace();
  }

  // Placeholder for missing images - defined at module level
  const IMAGE_PLACEHOLDER = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"%3E%3Crect fill="%231a1a1a" width="200" height="200"/%3E%3Ctext x="50%25" y="50%25" font-family="sans-serif" font-size="14" fill="%23666" text-anchor="middle" dominant-baseline="middle"%3EGenerating...%3C/text%3E%3C/svg%3E';

  /**
   * Handle image load error - replace with placeholder
   * Attached to window object so it's accessible from inline onerror handlers
   */
  window.handleImageError = function(imgElement) {
    if (imgElement.src !== IMAGE_PLACEHOLDER) {
      imgElement.src = IMAGE_PLACEHOLDER;
    }
  };

  /**
   * Create HTML for a result card
   */
  function createResultCardHTML(result) {
    const genderClass = result.gender.toLowerCase();
    const genderIcon = result.gender.toLowerCase() === 'male' ? 'user' : 'user';

    // Use random image from split images for display (not base_image)
    const displayImage = result.images && result.images.length > 0
      ? result.images[Math.floor(Math.random() * result.images.length)]
      : IMAGE_PLACEHOLDER;

    // Helper to check if value exists and is not empty
    const hasValue = (val) => val && val.trim() !== '';

    // Build supplementary info sections
    const supp = result.supplementary || {};
    const hasJobInfo = hasValue(supp.job_title) || hasValue(supp.workplace);
    const hasEducation = hasValue(supp.edu_establishment) || hasValue(supp.edu_study);
    const hasCurrentLocation = hasValue(supp.current_city) || hasValue(supp.current_state);
    const hasPrevLocation = hasValue(supp.prev_city) || hasValue(supp.prev_state);
    const hasLocation = hasCurrentLocation || hasPrevLocation;
    const hasAbout = hasValue(supp.about);

    const showSupplementaryInfo = hasJobInfo || hasEducation || hasLocation || hasAbout;

    return `
      <div class="result-card" data-result-id="${result.id || ''}">
        <div class="result-image-container" data-image-url="${displayImage}" data-name="${escapeHtml(result.firstname)} ${escapeHtml(result.lastname)}">
          <img src="${displayImage}" alt="${escapeHtml(result.firstname)} ${escapeHtml(result.lastname)}" class="result-image" loading="lazy" onerror="handleImageError(this)">
        </div>
        <div class="result-content">
          <h3 class="result-name">${escapeHtml(result.firstname)} ${escapeHtml(result.lastname)}</h3>
          <div class="result-gender ${genderClass}">
            <i data-feather="${genderIcon}"></i>
            ${escapeHtml(result.gender)}
          </div>

          ${showSupplementaryInfo ? `
          <div class="persona-supplementary">
            ${hasAbout ? `
            <div class="persona-section">
              <div class="persona-section-header">
                <i data-feather="file-text"></i>
                <span class="persona-section-title">About</span>
              </div>
              <div class="persona-section-content">
                <p class="persona-about">${escapeHtml(supp.about)}</p>
              </div>
            </div>
            ` : ''}

            ${hasJobInfo ? `
            <div class="persona-section">
              <div class="persona-section-header">
                <i data-feather="briefcase"></i>
                <span class="persona-section-title">Work</span>
              </div>
              <div class="persona-section-content">
                ${hasValue(supp.job_title) ? `<div class="persona-info-item"><span class="info-label">Title:</span> <span class="info-value">${escapeHtml(supp.job_title)}</span></div>` : ''}
                ${hasValue(supp.workplace) ? `<div class="persona-info-item"><span class="info-label">Workplace:</span> <span class="info-value">${escapeHtml(supp.workplace)}</span></div>` : ''}
              </div>
            </div>
            ` : ''}

            ${hasEducation ? `
            <div class="persona-section">
              <div class="persona-section-header">
                <i data-feather="book"></i>
                <span class="persona-section-title">Education</span>
              </div>
              <div class="persona-section-content">
                ${hasValue(supp.edu_establishment) ? `<div class="persona-info-item"><span class="info-label">School:</span> <span class="info-value">${escapeHtml(supp.edu_establishment)}</span></div>` : ''}
                ${hasValue(supp.edu_study) ? `<div class="persona-info-item"><span class="info-label">Study:</span> <span class="info-value">${escapeHtml(supp.edu_study)}</span></div>` : ''}
              </div>
            </div>
            ` : ''}

            ${hasLocation ? `
            <div class="persona-section">
              <div class="persona-section-header">
                <i data-feather="map-pin"></i>
                <span class="persona-section-title">Location</span>
              </div>
              <div class="persona-section-content">
                ${hasCurrentLocation ? `<div class="persona-info-item"><span class="info-label">Current:</span> <span class="info-value">${escapeHtml(supp.current_city || '')}${hasValue(supp.current_city) && hasValue(supp.current_state) ? ', ' : ''}${escapeHtml(supp.current_state || '')}</span></div>` : ''}
                ${hasPrevLocation ? `<div class="persona-info-item"><span class="info-label">Previous:</span> <span class="info-value">${escapeHtml(supp.prev_city || '')}${hasValue(supp.prev_city) && hasValue(supp.prev_state) ? ', ' : ''}${escapeHtml(supp.prev_state || '')}</span></div>` : ''}
              </div>
            </div>
            ` : ''}
          </div>
          ` : ''}

          ${result.bios ? `
          <div class="result-bios">
            <div class="bio-tabs">
              <button class="bio-tab active" data-platform="facebook">Facebook</button>
              <button class="bio-tab" data-platform="instagram">Instagram</button>
              <button class="bio-tab" data-platform="x">X</button>
              <button class="bio-tab" data-platform="tiktok">TikTok</button>
            </div>
            <div class="bio-content active" data-platform="facebook">${escapeHtml(result.bios.facebook || 'N/A')}</div>
            <div class="bio-content" data-platform="instagram">${escapeHtml(result.bios.instagram || 'N/A')}</div>
            <div class="bio-content" data-platform="x">${escapeHtml(result.bios.x || 'N/A')}</div>
            <div class="bio-content" data-platform="tiktok">${escapeHtml(result.bios.tiktok || 'N/A')}</div>
          </div>
          ` : ''}

          <div class="result-gallery">
            <div class="gallery-label">Images ${result.images && result.images.length > 0 ? `(${result.images.length})` : ''}</div>
            <div class="gallery-grid">
              ${result.images && result.images.length > 0 ? result.images.map((img, idx) => `
                <div class="gallery-thumbnail" data-image-url="${img}" data-name="${escapeHtml(result.firstname)} ${escapeHtml(result.lastname)} - Image ${idx + 1}">
                  <img src="${img}" alt="Image ${idx + 1}" loading="lazy" onerror="handleImageError(this)">
                </div>
              `).join('') : `
                <div class="gallery-placeholder" style="grid-column: 1/-1; text-align: center; padding: 1rem; color: #666;">
                  <i data-feather="clock" style="width: 24px; height: 24px;"></i>
                  <p style="margin: 0.5rem 0 0 0; font-size: 0.875rem;">Images generating...</p>
                </div>
              `}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Update pagination controls
   */
  function updatePagination(pagination, taskId) {
    if (!pagination) return;

    totalPages = pagination.total_pages;
    currentPage = pagination.current_page;

    const paginationHTML = createPaginationHTML(pagination, taskId);

    const topPagination = document.getElementById('paginationTop');
    const bottomPagination = document.getElementById('paginationBottom');

    if (topPagination) topPagination.innerHTML = paginationHTML;
    if (bottomPagination) bottomPagination.innerHTML = paginationHTML;

    // Add event listeners to pagination buttons
    initializePaginationButtons(taskId);

    // Re-initialize Feather icons
    feather.replace();
  }

  /**
   * Create pagination HTML
   */
  function createPaginationHTML(pagination) {
    if (pagination.total_pages <= 1) return '';

    const start = (pagination.current_page - 1) * RESULTS_PER_PAGE + 1;
    const end = Math.min(pagination.current_page * RESULTS_PER_PAGE, pagination.total_results);

    let html = `
      <div class="pagination-info">
        Showing ${start}-${end} of ${pagination.total_results} results
      </div>
      <div class="pagination-controls">
        <button class="pagination-btn" data-page="${pagination.current_page - 1}" ${pagination.current_page === 1 ? 'disabled' : ''}>
          <i data-feather="chevron-left"></i>
        </button>
    `;

    // Generate page numbers
    const pages = generatePageNumbers(pagination.current_page, pagination.total_pages);
    pages.forEach(page => {
      if (page === '...') {
        html += '<span class="pagination-ellipsis">...</span>';
      } else {
        const isActive = page === pagination.current_page ? 'active' : '';
        html += `<button class="pagination-btn ${isActive}" data-page="${page}">${page}</button>`;
      }
    });

    html += `
        <button class="pagination-btn" data-page="${pagination.current_page + 1}" ${pagination.current_page === pagination.total_pages ? 'disabled' : ''}>
          <i data-feather="chevron-right"></i>
        </button>
      </div>
    `;

    return html;
  }

  /**
   * Generate page numbers for pagination (with ellipsis)
   */
  function generatePageNumbers(current, total) {
    const pages = [];
    const maxVisible = 7;

    if (total <= maxVisible) {
      for (let i = 1; i <= total; i++) {
        pages.push(i);
      }
    } else {
      if (current <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i);
        pages.push('...');
        pages.push(total);
      } else if (current >= total - 3) {
        pages.push(1);
        pages.push('...');
        for (let i = total - 4; i <= total; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = current - 1; i <= current + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(total);
      }
    }

    return pages;
  }

  /**
   * Initialize pagination button click handlers
   */
  function initializePaginationButtons(taskId) {
    const buttons = document.querySelectorAll('.pagination-btn[data-page]');
    buttons.forEach(button => {
      button.addEventListener('click', function() {
        const page = parseInt(this.getAttribute('data-page'));
        if (page > 0 && page <= totalPages && page !== currentPage) {
          currentPage = page;
          updateURL(page);
          loadTaskData(taskId, page);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    });
  }

  /**
   * Update URL with page parameter
   */
  function updateURL(page) {
    const url = new URL(window.location);
    if (page > 1) {
      url.searchParams.set('page', page);
    } else {
      url.searchParams.delete('page');
    }
    window.history.pushState({}, '', url);
  }

  // ========================================
  // BIO TABS
  // ========================================

  function initializeBioTabs() {
    const bioTabs = document.querySelectorAll('.bio-tab');

    bioTabs.forEach(tab => {
      tab.addEventListener('click', function() {
        const platform = this.getAttribute('data-platform');
        const card = this.closest('.result-card');

        // Remove active class from all tabs and contents in this card
        card.querySelectorAll('.bio-tab').forEach(t => t.classList.remove('active'));
        card.querySelectorAll('.bio-content').forEach(c => c.classList.remove('active'));

        // Add active class to clicked tab and corresponding content
        this.classList.add('active');
        card.querySelector(`.bio-content[data-platform="${platform}"]`).classList.add('active');
      });
    });
  }

  // ========================================
  // IMAGE PREVIEW MODAL
  // ========================================

  function initializeImageModal() {
    const modal = document.getElementById('imageModal');
    if (!modal) return;

    const modalImage = document.getElementById('modalImage');
    const imageCaption = document.getElementById('imageCaption');
    const closeBtn = modal.querySelector('.btn-image-close');
    const backdrop = modal.querySelector('.image-modal-backdrop');

    // Close button
    if (closeBtn) {
      closeBtn.addEventListener('click', () => closeImageModal(modal));
    }

    // Backdrop click
    if (backdrop) {
      backdrop.addEventListener('click', () => closeImageModal(modal));
    }

    // Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) {
        closeImageModal(modal);
      }
    });
  }

  function initializeImagePreviews() {
    // Main images
    const imageContainers = document.querySelectorAll('.result-image-container');
    imageContainers.forEach(container => {
      container.addEventListener('click', function() {
        const imageUrl = this.getAttribute('data-image-url');
        const name = this.getAttribute('data-name');
        showImageModal(imageUrl, name);
      });
    });

    // Gallery thumbnails
    const thumbnails = document.querySelectorAll('.gallery-thumbnail');
    thumbnails.forEach(thumbnail => {
      thumbnail.addEventListener('click', function() {
        const imageUrl = this.getAttribute('data-image-url');
        const name = this.getAttribute('data-name');
        showImageModal(imageUrl, name);
      });
    });
  }

  function showImageModal(imageUrl, caption) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const imageCaption = document.getElementById('imageCaption');

    if (modal && modalImage) {
      modalImage.src = imageUrl;
      modalImage.alt = caption;
      if (imageCaption) {
        imageCaption.textContent = caption;
      }

      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';

      // Re-initialize Feather icons
      feather.replace();
    }
  }

  function closeImageModal(modal) {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  // ========================================
  // ERROR LOG TOGGLE
  // ========================================

  function initializeErrorLogToggle() {
    const toggleBtn = document.getElementById('toggleErrorLog');
    const errorContent = document.getElementById('errorContent');

    if (toggleBtn && errorContent) {
      const errorHeader = toggleBtn.closest('.error-header');

      errorHeader.addEventListener('click', function() {
        errorContent.classList.toggle('collapsed');
        toggleBtn.classList.toggle('collapsed');
        feather.replace();
      });
    }
  }

  // ========================================
  // EXPORT FUNCTIONALITY
  // ========================================

  function initializeExportButtons(taskId) {
    const exportJson = document.getElementById('exportJson');
    const exportCsv = document.getElementById('exportCsv');
    const exportZip = document.getElementById('exportZip');

    if (exportJson) {
      exportJson.addEventListener('click', () => handleExport(taskId, 'json', exportJson));
    }

    if (exportCsv) {
      exportCsv.addEventListener('click', () => handleExport(taskId, 'csv', exportCsv));
    }

    if (exportZip) {
      exportZip.addEventListener('click', () => handleExport(taskId, 'zip', exportZip));
    }
  }

  function handleExport(taskId, format, button) {
    // Show loading state
    button.classList.add('loading');
    const originalText = button.innerHTML;
    button.innerHTML = '<i data-feather="loader"></i> Exporting...';
    feather.replace();

    // Download file
    const downloadUrl = `/datasets/${taskId}/export/${format}`;

    fetch(downloadUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Export failed: ${response.statusText}`);
        }
        return response.blob();
      })
      .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dataset_${taskId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast(`Dataset exported successfully as ${format.toUpperCase()}`, 'success');
      })
      .catch(error => {
        console.error('Export error:', error);
        showToast(`Failed to export dataset: ${error.message}`, 'error');
      })
      .finally(() => {
        // Reset button state
        button.classList.remove('loading');
        button.innerHTML = originalText;
        feather.replace();
      });
  }

  // ========================================
  // POLLING FOR REAL-TIME UPDATES
  // ========================================

  function startPolling(taskId) {
    if (isPolling) return;

    isPolling = true;
    pollInterval = setInterval(() => {
      loadTaskData(taskId, currentPage);
    }, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
      isPolling = false;
    }
  }

  // Stop polling when user leaves page
  window.addEventListener('beforeunload', stopPolling);

  // ========================================
  // UTILITY FUNCTIONS
  // ========================================

  function getStatusBadgeHTML(status) {
    const statusMap = {
      'completed': { icon: 'check-circle', label: 'Completed', class: 'status-completed' },
      'failed': { icon: 'x-circle', label: 'Failed', class: 'status-failed' },
      'generating-data': { icon: 'cpu', label: 'Generating Data', class: 'status-generating' },
      'generating-images': { icon: 'image', label: 'Generating Images', class: 'status-generating' },
      'pending': { icon: 'clock', label: 'Pending', class: 'status-pending' }
    };

    const config = statusMap[status] || { icon: 'help-circle', label: status, class: 'status-pending' };

    return `
      <span class="status-badge ${config.class}">
        <i data-feather="${config.icon}"></i>
        ${config.label}
      </span>
    `;
  }

  function getStatusText(status) {
    const statusMap = {
      'completed': 'Completed',
      'failed': 'Failed',
      'generating-data': 'Generating',
      'generating-images': 'Generating',
      'pending': 'Pending'
    };
    return statusMap[status] || status;
  }

  function getStatusDescription(status, personas, images) {
    if (status === 'completed') {
      return 'All data generated successfully';
    } else if (status === 'failed') {
      return 'Generation failed - see error log';
    } else if (status === 'generating-data') {
      return `Generating persona data: ${personas} done`;
    } else if (status === 'generating-images') {
      return `Generating images: ${images} done`;
    } else if (status === 'pending') {
      return 'Waiting to start generation';
    }
    return 'Status unknown';
  }

  function formatDuration(startTime, endTime) {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end - start;

    const hours = Math.floor(diffMs / 3600000);
    const minutes = Math.floor((diffMs % 3600000) / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function showErrorState(message) {
    const grid = document.getElementById('resultsGrid');
    if (grid) {
      grid.innerHTML = `
        <div class="results-empty">
          <i data-feather="alert-circle" class="results-empty-icon" style="color: var(--color-error);"></i>
          <p class="results-empty-text">${escapeHtml(message)}</p>
        </div>
      `;
      feather.replace();
    }
  }

  function showToast(message, type = 'info') {
    // Simple toast notification (can be enhanced with a proper toast component)
    const alertClass = type === 'success' ? 'alert-success' :
                       type === 'error' ? 'alert-error' : 'alert-info';

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass}`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '10000';
    alertDiv.style.minWidth = '300px';
    alertDiv.style.animation = 'slideIn 0.3s ease-out';

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'alert-circle' : 'info';

    alertDiv.innerHTML = `
      <i data-feather="${icon}"></i>
      ${escapeHtml(message)}
    `;

    document.body.appendChild(alertDiv);
    feather.replace();

    // Auto-remove after 4 seconds
    setTimeout(() => {
      alertDiv.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => {
        document.body.removeChild(alertDiv);
      }, 300);
    }, 4000);
  }

  // ========================================
  // FEATHER ICONS INITIALIZATION
  // ========================================

  function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }

  // Add CSS animation for toast
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);

})();
