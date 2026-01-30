/**
 * History Page - JavaScript
 * Handles copy to clipboard, error modal, and interactive features
 * Adheres to brandbook specifications in docs/brandbook.md
 * Last Updated: 2026-01-30
 */

(function() {
  'use strict';

  // ========================================
  // INITIALIZATION
  // ========================================

  document.addEventListener('DOMContentLoaded', function() {
    initializeCopyButtons();
    initializeErrorModal();
    initializeFeatherIcons();
  });

  // ========================================
  // COPY TO CLIPBOARD FUNCTIONALITY
  // ========================================

  function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.btn-copy');

    copyButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const taskId = this.getAttribute('data-task-id');

        // Copy to clipboard
        copyToClipboard(taskId)
          .then(() => {
            // Show success state
            showCopySuccess(this);
          })
          .catch(err => {
            console.error('Failed to copy task ID:', err);
            alert('Failed to copy Task ID to clipboard');
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
  // ERROR MODAL FUNCTIONALITY
  // ========================================

  function initializeErrorModal() {
    const modal = document.getElementById('errorModal');
    if (!modal) return;

    const errorTaskIdElement = document.getElementById('errorTaskId');
    const errorMessageElement = document.getElementById('errorMessage');
    const closeButtons = modal.querySelectorAll('.btn-modal-close');
    const backdrop = modal.querySelector('.modal-backdrop');

    // Desktop error buttons
    const errorButtons = document.querySelectorAll('.btn-view-error');
    errorButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const taskId = this.getAttribute('data-task-id');
        const errorLog = this.getAttribute('data-error');

        showErrorModal(modal, errorTaskIdElement, errorMessageElement, taskId, errorLog);
      });
    });

    // Mobile error buttons
    const mobileErrorButtons = document.querySelectorAll('.btn-view-error-mobile');
    mobileErrorButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const taskId = this.getAttribute('data-task-id');
        const errorLog = this.getAttribute('data-error');

        showErrorModal(modal, errorTaskIdElement, errorMessageElement, taskId, errorLog);
      });
    });

    // Close button handlers
    closeButtons.forEach(button => {
      button.addEventListener('click', function() {
        closeErrorModal(modal);
      });
    });

    // Backdrop click handler
    if (backdrop) {
      backdrop.addEventListener('click', function() {
        closeErrorModal(modal);
      });
    }

    // Escape key handler
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) {
        closeErrorModal(modal);
      }
    });
  }

  /**
   * Show error modal with task details
   */
  function showErrorModal(modal, taskIdElement, messageElement, taskId, errorLog) {
    // Set content
    taskIdElement.textContent = taskId;
    messageElement.textContent = errorLog || 'No error details available';

    // Show modal
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Re-initialize Feather icons for modal content
    feather.replace();

    // Focus modal for accessibility
    modal.focus();
  }

  /**
   * Close error modal
   */
  function closeErrorModal(modal) {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');

    // Restore body scroll
    document.body.style.overflow = '';
  }

  // ========================================
  // FEATHER ICONS INITIALIZATION
  // ========================================

  function initializeFeatherIcons() {
    // Initialize Feather icons (loaded from base.html)
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }

  // ========================================
  // AUTO-REFRESH (Optional Feature)
  // ========================================

  /**
   * Optional: Auto-refresh page to check for task status updates
   * Uncomment to enable auto-refresh every 30 seconds
   */
  /*
  function initializeAutoRefresh() {
    const AUTO_REFRESH_INTERVAL = 30000; // 30 seconds

    // Only auto-refresh if there are tasks in progress
    const hasActiveTasks = document.querySelector('.status-pending, .status-generating');

    if (hasActiveTasks) {
      setInterval(() => {
        // Reload page to fetch latest task statuses
        window.location.reload();
      }, AUTO_REFRESH_INTERVAL);
    }
  }

  // Call on page load
  document.addEventListener('DOMContentLoaded', initializeAutoRefresh);
  */

})();
