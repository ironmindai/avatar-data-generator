/**
 * Generate Avatars Page - JavaScript
 * Avatar Data Generator by Galacticos AI
 * Last Updated: 2026-01-30
 */

(function() {
  'use strict';

  // ========================================
  // DOM READY
  // ========================================

  document.addEventListener('DOMContentLoaded', function() {
    initializeSelect2();
    initializeNumberInputSync();
    initializeFormValidation();
    initializeFormSubmission();
    initializeFormReset();
  });

  // ========================================
  // SELECT2 INITIALIZATION (Searchable Dropdown)
  // ========================================

  function initializeSelect2() {
    const languageSelect = $('#bio_language');

    if (languageSelect.length) {
      languageSelect.select2({
        placeholder: 'Select a language',
        allowClear: false,
        width: '100%',
        dropdownAutoWidth: false,
        minimumResultsForSearch: 0, // Always show search
        matcher: customMatcher
      });

      // Custom matcher for better search
      function customMatcher(params, data) {
        // If there are no search terms, return all data
        if ($.trim(params.term) === '') {
          return data;
        }

        // Skip if this is an optgroup
        if (!data.id) {
          return null;
        }

        const searchTerm = params.term.toLowerCase();
        const text = data.text.toLowerCase();

        // Search in both English name and native language name
        if (text.indexOf(searchTerm) > -1) {
          return data;
        }

        return null;
      }
    }
  }

  // ========================================
  // NUMBER INPUT & SLIDER SYNCHRONIZATION
  // ========================================

  function initializeNumberInputSync() {
    const numberInput = document.getElementById('number_to_generate');
    const rangeSlider = document.getElementById('number_slider');

    if (numberInput && rangeSlider) {
      // Sync slider to number input
      numberInput.addEventListener('input', function() {
        let value = parseInt(this.value, 10);

        // Enforce min/max
        if (value < 10) value = 10;
        if (value > 300) value = 300;

        // Round to nearest increment of 5
        value = Math.round(value / 5) * 5;

        // Update both inputs
        this.value = value;
        rangeSlider.value = value;
      });

      // Sync number input to slider
      rangeSlider.addEventListener('input', function() {
        const value = parseInt(this.value, 10);
        numberInput.value = value;
      });

      // Validate on blur
      numberInput.addEventListener('blur', function() {
        let value = parseInt(this.value, 10);

        if (isNaN(value) || value < 10) {
          value = 10;
        } else if (value > 300) {
          value = 300;
        } else {
          value = Math.round(value / 5) * 5;
        }

        this.value = value;
        rangeSlider.value = value;
      });
    }
  }

  // ========================================
  // FORM VALIDATION
  // ========================================

  function initializeFormValidation() {
    const form = document.getElementById('generateForm');

    if (form) {
      form.addEventListener('submit', function(event) {
        if (!validateForm()) {
          event.preventDefault();
          return false;
        }
      });
    }
  }

  function validateForm() {
    let isValid = true;
    const errors = [];

    // Validate persona description
    const personaDescription = document.getElementById('persona_description');
    if (personaDescription && personaDescription.value.trim().length < 10) {
      errors.push('Persona description must be at least 10 characters');
      isValid = false;
      highlightError(personaDescription);
    } else if (personaDescription) {
      clearError(personaDescription);
    }

    // Validate language selection
    const bioLanguage = document.getElementById('bio_language');
    if (bioLanguage && !bioLanguage.value) {
      errors.push('Please select a bio language');
      isValid = false;
      highlightError(bioLanguage);
    } else if (bioLanguage) {
      clearError(bioLanguage);
    }

    // Validate number to generate
    const numberToGenerate = document.getElementById('number_to_generate');
    const numValue = parseInt(numberToGenerate.value, 10);
    if (numberToGenerate && (isNaN(numValue) || numValue < 10 || numValue > 300 || numValue % 5 !== 0)) {
      errors.push('Number to generate must be between 10-300 in increments of 5');
      isValid = false;
      highlightError(numberToGenerate);
    } else if (numberToGenerate) {
      clearError(numberToGenerate);
    }

    // Validate images per persona selection
    const imagesPerPersona = document.querySelector('input[name="images_per_persona"]:checked');
    if (!imagesPerPersona) {
      errors.push('Please select images per persona');
      isValid = false;
    }

    // Display errors if any
    if (!isValid && errors.length > 0) {
      alert('Please fix the following errors:\n\n' + errors.join('\n'));
    }

    return isValid;
  }

  function highlightError(element) {
    if (element) {
      element.style.borderColor = 'var(--color-error)';
      element.style.boxShadow = '0 0 20px rgba(255, 68, 102, 0.3)';
    }
  }

  function clearError(element) {
    if (element) {
      element.style.borderColor = '';
      element.style.boxShadow = '';
    }
  }

  // ========================================
  // FORM SUBMISSION (with loading state)
  // ========================================

  function initializeFormSubmission() {
    const form = document.getElementById('generateForm');
    const loadingOverlay = document.getElementById('loadingState');

    if (form && loadingOverlay) {
      form.addEventListener('submit', function(event) {
        if (validateForm()) {
          // Show loading overlay
          loadingOverlay.style.display = 'flex';

          // Disable form inputs to prevent duplicate submission
          disableFormInputs(form);

          // Note: Form will submit naturally, backend will handle the generation
          // Loading overlay will be visible until page reload/redirect
        }
      });
    }
  }

  function disableFormInputs(form) {
    const inputs = form.querySelectorAll('input, textarea, select, button');
    inputs.forEach(function(input) {
      input.disabled = true;
    });
  }

  // ========================================
  // FORM RESET
  // ========================================

  function initializeFormReset() {
    const form = document.getElementById('generateForm');

    if (form) {
      form.addEventListener('reset', function() {
        // Reset Select2
        const languageSelect = $('#bio_language');
        if (languageSelect.length) {
          languageSelect.val('').trigger('change');
        }

        // Reset number input and slider to default (50)
        setTimeout(function() {
          const numberInput = document.getElementById('number_to_generate');
          const rangeSlider = document.getElementById('number_slider');

          if (numberInput) numberInput.value = 50;
          if (rangeSlider) rangeSlider.value = 50;

          // Clear any error highlights
          clearAllErrors();
        }, 10);
      });
    }
  }

  function clearAllErrors() {
    const inputs = document.querySelectorAll('.form-input, .form-textarea, .form-select, .form-number');
    inputs.forEach(function(input) {
      clearError(input);
    });
  }

  // ========================================
  // UTILITY FUNCTIONS
  // ========================================

  /**
   * Show loading overlay manually
   */
  window.showLoading = function() {
    const loadingOverlay = document.getElementById('loadingState');
    if (loadingOverlay) {
      loadingOverlay.style.display = 'flex';
    }
  };

  /**
   * Hide loading overlay manually
   */
  window.hideLoading = function() {
    const loadingOverlay = document.getElementById('loadingState');
    if (loadingOverlay) {
      loadingOverlay.style.display = 'none';
    }
  };

  /**
   * Log form data for debugging
   */
  window.logFormData = function() {
    const form = document.getElementById('generateForm');
    if (form) {
      const formData = new FormData(form);
      console.log('=== Generate Form Data ===');
      for (let [key, value] of formData.entries()) {
        console.log(key + ':', value);
      }
    }
  };

})();
