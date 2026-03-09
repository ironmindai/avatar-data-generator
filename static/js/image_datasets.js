/**
 * Image Datasets Page - JavaScript
 * Handles dataset creation, deletion, and sharing
 * Adheres to brandbook specifications in docs/brandbook.md
 */

(function() {
  'use strict';

  // ========================================
  // GLOBAL STATE
  // ========================================

  const elements = {
    createDatasetBtn: document.getElementById('createDatasetBtn'),
    createDatasetBtnEmpty: document.getElementById('createDatasetBtnEmpty'),
    createDatasetModal: document.getElementById('createDatasetModal'),
    createDatasetModalOverlay: document.getElementById('createDatasetModalOverlay'),
    createDatasetModalClose: document.getElementById('createDatasetModalClose'),
    createDatasetForm: document.getElementById('createDatasetForm'),
    createDatasetCancelBtn: document.getElementById('createDatasetCancelBtn'),
    createDatasetSubmitBtn: document.getElementById('createDatasetSubmitBtn'),
    datasetName: document.getElementById('datasetName'),
    datasetNameError: document.getElementById('datasetNameError')
  };

  // ========================================
  // INITIALIZATION
  // ========================================

  document.addEventListener('DOMContentLoaded', function() {
    initializeCreateDatasetModal();
    initializeDeleteButtons();
    initializeShareButtons();
    initializeFeatherIcons();
  });

  // ========================================
  // CREATE DATASET MODAL
  // ========================================

  function initializeCreateDatasetModal() {
    if (!elements.createDatasetModal) return;

    // Open modal
    [elements.createDatasetBtn, elements.createDatasetBtnEmpty]
      .filter(btn => btn)
      .forEach(btn => {
        btn.addEventListener('click', openCreateDatasetModal);
      });

    // Close modal
    [elements.createDatasetModalClose, elements.createDatasetModalOverlay, elements.createDatasetCancelBtn]
      .filter(el => el)
      .forEach(el => {
        el.addEventListener('click', closeCreateDatasetModal);
      });

    // Escape key to close
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && elements.createDatasetModal.classList.contains('active')) {
        closeCreateDatasetModal();
      }
    });

    // Form submission
    if (elements.createDatasetForm) {
      elements.createDatasetForm.addEventListener('submit', handleCreateDatasetSubmit);
    }

    // Real-time validation
    if (elements.datasetName) {
      elements.datasetName.addEventListener('input', validateDatasetName);
    }
  }

  function openCreateDatasetModal() {
    elements.createDatasetModal.classList.add('active');
    elements.createDatasetModal.setAttribute('aria-hidden', 'false');

    // Focus on name input
    if (elements.datasetName) {
      setTimeout(() => elements.datasetName.focus(), 100);
    }
  }

  function closeCreateDatasetModal() {
    elements.createDatasetModal.classList.remove('active');
    elements.createDatasetModal.setAttribute('aria-hidden', 'true');

    // Reset form
    if (elements.createDatasetForm) {
      elements.createDatasetForm.reset();
      clearValidationErrors();
    }
  }

  function validateDatasetName() {
    const name = elements.datasetName.value.trim();

    if (!name) {
      showValidationError('datasetNameError', 'Dataset name is required');
      return false;
    }

    if (name.length > 200) {
      showValidationError('datasetNameError', 'Dataset name must be 200 characters or less');
      return false;
    }

    clearValidationError('datasetNameError');
    return true;
  }

  function showValidationError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    const inputElement = document.getElementById(elementId.replace('Error', ''));

    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }

    if (inputElement) {
      inputElement.classList.add('is-invalid');
    }
  }

  function clearValidationError(elementId) {
    const errorElement = document.getElementById(elementId);
    const inputElement = document.getElementById(elementId.replace('Error', ''));

    if (errorElement) {
      errorElement.textContent = '';
      errorElement.style.display = 'none';
    }

    if (inputElement) {
      inputElement.classList.remove('is-invalid');
    }
  }

  function clearValidationErrors() {
    clearValidationError('datasetNameError');
  }

  async function handleCreateDatasetSubmit(e) {
    e.preventDefault();

    // Validate
    if (!validateDatasetName()) {
      return;
    }

    // Get form data
    const formData = new FormData(elements.createDatasetForm);
    const data = {
      name: formData.get('name').trim(),
      description: formData.get('description').trim() || null,
      is_public: formData.get('is_public') === 'on'
    };

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    if (!csrfToken) {
      showToast('Error: CSRF token missing. Please refresh the page.', 'error');
      return;
    }

    // Disable submit button
    elements.createDatasetSubmitBtn.disabled = true;
    const originalText = elements.createDatasetSubmitBtn.innerHTML;
    elements.createDatasetSubmitBtn.innerHTML = '<i data-feather="loader"></i> Creating...';
    feather.replace();

    try {
      const response = await fetch('/api/image-datasets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('Dataset created successfully!', 'success');
        closeCreateDatasetModal();

        // Redirect to new dataset
        setTimeout(() => {
          window.location.href = `/image-datasets/${result.dataset_id}`;
        }, 500);
      } else {
        showToast(result.message || 'Failed to create dataset', 'error');

        // Re-enable submit button
        elements.createDatasetSubmitBtn.disabled = false;
        elements.createDatasetSubmitBtn.innerHTML = originalText;
        feather.replace();
      }
    } catch (error) {
      console.error('Error creating dataset:', error);
      showToast('An error occurred while creating the dataset', 'error');

      // Re-enable submit button
      elements.createDatasetSubmitBtn.disabled = false;
      elements.createDatasetSubmitBtn.innerHTML = originalText;
      feather.replace();
    }
  }

  // ========================================
  // DELETE FUNCTIONALITY
  // ========================================

  function initializeDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.btn-delete, .btn-delete-mobile');

    deleteButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const datasetId = this.getAttribute('data-dataset-id');
        handleDeleteDataset(datasetId, this);
      });
    });
  }

  async function handleDeleteDataset(datasetId, button) {
    // Confirmation
    const confirmed = confirm(
      'Are you sure you want to delete this dataset?\n\n' +
      'This action cannot be undone. All images and permissions will be permanently deleted.'
    );

    if (!confirmed) return;

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    if (!csrfToken) {
      showToast('Error: CSRF token missing. Please refresh the page.', 'error');
      return;
    }

    // Disable button and show loading state
    button.disabled = true;
    const originalIcon = button.querySelector('i[data-feather]');
    const originalIconName = originalIcon?.getAttribute('data-feather') || 'trash-2';

    if (originalIcon) {
      originalIcon.setAttribute('data-feather', 'loader');
      feather.replace();
    }

    try {
      const response = await fetch(`/api/image-datasets/${datasetId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('Dataset deleted successfully', 'success');

        // Remove row/card from DOM
        const row = document.querySelector(`.dataset-row[data-dataset-id="${datasetId}"]`);
        const card = document.querySelector(`.dataset-card[data-dataset-id="${datasetId}"]`);

        if (row) {
          row.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
          row.style.opacity = '0';
          row.style.transform = 'translateX(-20px)';
          setTimeout(() => row.remove(), 300);
        }

        if (card) {
          card.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
          card.style.opacity = '0';
          card.style.transform = 'translateY(-20px)';
          setTimeout(() => card.remove(), 300);
        }

        // Check if page is empty after deletion
        setTimeout(checkIfEmpty, 400);
      } else {
        showToast(result.message || 'Failed to delete dataset', 'error');

        // Re-enable button
        button.disabled = false;
        if (originalIcon) {
          originalIcon.setAttribute('data-feather', originalIconName);
          feather.replace();
        }
      }
    } catch (error) {
      console.error('Error deleting dataset:', error);
      showToast('An error occurred while deleting the dataset', 'error');

      // Re-enable button
      button.disabled = false;
      if (originalIcon) {
        originalIcon.setAttribute('data-feather', originalIconName);
        feather.replace();
      }
    }
  }

  function checkIfEmpty() {
    const rows = document.querySelectorAll('.dataset-row');
    const cards = document.querySelectorAll('.dataset-card');

    if (rows.length === 0 && cards.length === 0) {
      // Reload page to show empty state
      window.location.reload();
    }
  }

  // ========================================
  // SHARE FUNCTIONALITY
  // ========================================

  function initializeShareButtons() {
    const shareButtons = document.querySelectorAll('.btn-share, .btn-share-mobile');

    shareButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const datasetId = this.getAttribute('data-dataset-id');
        // Redirect to detail page where share modal can be opened
        window.location.href = `/image-datasets/${datasetId}?action=share`;
      });
    });
  }

  // ========================================
  // TOAST NOTIFICATIONS
  // ========================================

  function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
      existingToast.remove();
    }

    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <i data-feather="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info'}"></i>
      <span>${message}</span>
    `;

    // Add styles
    Object.assign(toast.style, {
      position: 'fixed',
      bottom: '2rem',
      right: '2rem',
      zIndex: '9999',
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '0.75rem 1rem',
      backgroundColor: 'var(--color-bg-elevated)',
      border: '1px solid',
      borderLeft: '3px solid',
      borderRadius: '0',
      color: type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-info)',
      borderColor: type === 'success' ? 'rgba(0, 255, 136, 0.3)' : type === 'error' ? 'rgba(255, 68, 102, 0.3)' : 'rgba(0, 217, 255, 0.3)',
      borderLeftColor: type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-info)',
      boxShadow: type === 'success' ? '0 0 30px rgba(0, 255, 136, 0.3)' : type === 'error' ? '0 0 30px rgba(255, 68, 102, 0.3)' : '0 0 30px rgba(0, 217, 255, 0.3)',
      fontSize: 'var(--font-size-body)',
      fontWeight: 'var(--font-weight-medium)',
      animation: 'slideIn 0.3s ease-out'
    });

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);

    // Add to page
    document.body.appendChild(toast);
    feather.replace();

    // Auto-remove after 4 seconds
    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ========================================
  // FEATHER ICONS
  // ========================================

  function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }

})();
