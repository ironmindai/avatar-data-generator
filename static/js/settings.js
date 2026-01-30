/**
 * Settings Page JavaScript
 * Handles form state tracking, AJAX submission, and user notifications
 * Brandbook Compliant - Charcoal & Neon Developer Tools Aesthetic
 */

(function() {
    'use strict';

    // ========================================
    // State Management
    // ========================================

    const state = {
        originalValues: {},
        isDirty: false,
        isSubmitting: false
    };

    // ========================================
    // DOM Elements
    // ========================================

    const elements = {
        form: document.getElementById('settingsForm'),
        saveButton: document.getElementById('saveButton'),
        resetButton: document.getElementById('resetButton'),
        toast: document.getElementById('toast'),
        toastIcon: document.getElementById('toastIcon'),
        toastMessage: document.getElementById('toastMessage'),
        textareas: {
            facebook: document.getElementById('bio_prompt_facebook'),
            instagram: document.getElementById('bio_prompt_instagram'),
            x: document.getElementById('bio_prompt_x'),
            tiktok: document.getElementById('bio_prompt_tiktok')
        }
    };

    // ========================================
    // Initialization
    // ========================================

    function init() {
        // Store original values
        storeOriginalValues();

        // Initialize character counters
        updateAllCharCounts();

        // Attach event listeners
        attachEventListeners();

        console.log('[Settings] Initialized');
    }

    // ========================================
    // Store Original Form Values
    // ========================================

    function storeOriginalValues() {
        Object.keys(elements.textareas).forEach(key => {
            const textarea = elements.textareas[key];
            state.originalValues[textarea.id] = textarea.value.trim();
        });
        console.log('[Settings] Original values stored:', state.originalValues);
    }

    // ========================================
    // Event Listeners
    // ========================================

    function attachEventListeners() {
        // Form input events
        Object.values(elements.textareas).forEach(textarea => {
            textarea.addEventListener('input', handleInput);
            textarea.addEventListener('blur', handleBlur);
        });

        // Form submission
        elements.form.addEventListener('submit', handleSubmit);

        // Reset button
        elements.resetButton.addEventListener('click', handleReset);
    }

    // ========================================
    // Input Handler
    // ========================================

    function handleInput(event) {
        const textarea = event.target;

        // Update character count
        updateCharCount(textarea);

        // Check if form is dirty
        checkDirtyState();
    }

    // ========================================
    // Blur Handler (cleanup)
    // ========================================

    function handleBlur(event) {
        const textarea = event.target;

        // Add visual feedback if value changed
        const currentValue = textarea.value.trim();
        const originalValue = state.originalValues[textarea.id];

        if (currentValue !== originalValue) {
            textarea.classList.add('dirty');
        } else {
            textarea.classList.remove('dirty');
        }
    }

    // ========================================
    // Check Dirty State
    // ========================================

    function checkDirtyState() {
        let hasChanges = false;

        Object.keys(elements.textareas).forEach(key => {
            const textarea = elements.textareas[key];
            const currentValue = textarea.value.trim();
            const originalValue = state.originalValues[textarea.id];

            if (currentValue !== originalValue) {
                hasChanges = true;
            }
        });

        state.isDirty = hasChanges;

        // Enable/disable save button
        elements.saveButton.disabled = !hasChanges;

        console.log('[Settings] Dirty state:', state.isDirty);
    }

    // ========================================
    // Character Count Update
    // ========================================

    function updateCharCount(textarea) {
        const charCount = textarea.value.length;
        const countElement = document.querySelector(`[data-target="${textarea.id}"]`);

        if (countElement) {
            countElement.textContent = `${charCount} character${charCount !== 1 ? 's' : ''}`;
        }
    }

    function updateAllCharCounts() {
        Object.values(elements.textareas).forEach(textarea => {
            updateCharCount(textarea);
        });
    }

    // ========================================
    // Form Submission Handler
    // ========================================

    async function handleSubmit(event) {
        event.preventDefault();

        if (state.isSubmitting) {
            console.log('[Settings] Already submitting, ignoring duplicate submission');
            return;
        }

        if (!state.isDirty) {
            console.log('[Settings] No changes to save');
            return;
        }

        state.isSubmitting = true;

        // Show loading state
        elements.saveButton.classList.add('loading');
        elements.saveButton.disabled = true;

        // Get CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;

        // Collect form data as JSON
        const formData = {
            bio_prompt_facebook: elements.textareas.facebook.value,
            bio_prompt_instagram: elements.textareas.instagram.value,
            bio_prompt_x: elements.textareas.x.value,
            bio_prompt_tiktok: elements.textareas.tiktok.value
        };

        try {
            console.log('[Settings] Submitting form data...');

            // Make AJAX request
            const response = await fetch('/settings/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                console.log('[Settings] Save successful:', result);

                // Update original values to current values
                storeOriginalValues();

                // Reset dirty state
                state.isDirty = false;
                elements.saveButton.disabled = true;

                // Remove dirty class from all textareas
                Object.values(elements.textareas).forEach(textarea => {
                    textarea.classList.remove('dirty');
                });

                // Show success notification
                showToast('Settings saved successfully', 'success');
            } else {
                console.error('[Settings] Save failed:', result);
                showToast(result.message || 'Failed to save settings', 'error');
            }
        } catch (error) {
            console.error('[Settings] Network error:', error);
            showToast('Network error. Please try again.', 'error');
        } finally {
            // Hide loading state
            elements.saveButton.classList.remove('loading');
            state.isSubmitting = false;

            // Re-check dirty state in case values changed during submission
            checkDirtyState();
        }
    }

    // ========================================
    // Reset Handler
    // ========================================

    function handleReset(event) {
        event.preventDefault();

        if (!state.isDirty) {
            console.log('[Settings] No changes to reset');
            return;
        }

        // Confirm reset
        const confirmReset = confirm('Are you sure you want to reset all fields to their original values? Unsaved changes will be lost.');

        if (!confirmReset) {
            return;
        }

        // Restore original values
        Object.keys(elements.textareas).forEach(key => {
            const textarea = elements.textareas[key];
            textarea.value = state.originalValues[textarea.id];
            textarea.classList.remove('dirty');
            updateCharCount(textarea);
        });

        // Reset dirty state
        state.isDirty = false;
        elements.saveButton.disabled = true;

        console.log('[Settings] Form reset to original values');
        showToast('Form reset to original values', 'success');
    }

    // ========================================
    // Toast Notification
    // ========================================

    function showToast(message, type = 'success') {
        // Update toast content
        elements.toastMessage.textContent = message;

        // Update toast styling based on type
        if (type === 'error') {
            elements.toast.classList.add('error');
            elements.toastIcon.setAttribute('data-feather', 'alert-circle');
        } else {
            elements.toast.classList.remove('error');
            elements.toastIcon.setAttribute('data-feather', 'check-circle');
        }

        // Reinitialize feather icons for the toast
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        // Show toast
        elements.toast.style.display = 'flex';
        elements.toast.classList.remove('hiding');

        // Auto-hide after 4 seconds
        setTimeout(() => {
            hideToast();
        }, 4000);
    }

    function hideToast() {
        elements.toast.classList.add('hiding');

        // Wait for animation to complete before hiding
        setTimeout(() => {
            elements.toast.style.display = 'none';
            elements.toast.classList.remove('hiding');
        }, 300);
    }

    // ========================================
    // Initialize on DOM Ready
    // ========================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
