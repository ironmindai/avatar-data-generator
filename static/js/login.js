/**
 * Login Page JavaScript
 * Handles form validation and user interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('.login-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const submitButton = loginForm.querySelector('button[type="submit"]');

    // Form validation
    loginForm.addEventListener('submit', function(e) {
        let isValid = true;

        // Email validation
        if (!emailInput.value || !isValidEmail(emailInput.value)) {
            showError(emailInput, 'Please enter a valid email address');
            isValid = false;
        } else {
            clearError(emailInput);
        }

        // Password validation
        if (!passwordInput.value || passwordInput.value.length < 6) {
            showError(passwordInput, 'Password must be at least 6 characters');
            isValid = false;
        } else {
            clearError(passwordInput);
        }

        if (!isValid) {
            e.preventDefault();
        } else {
            // Show loading state on submit button
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner" style="width: 20px; height: 20px; border-width: 2px;"></span> Signing in...';
        }
    });

    // Real-time validation on blur
    emailInput.addEventListener('blur', function() {
        if (this.value && !isValidEmail(this.value)) {
            showError(this, 'Please enter a valid email address');
        } else {
            clearError(this);
        }
    });

    passwordInput.addEventListener('blur', function() {
        if (this.value && this.value.length < 6) {
            showError(this, 'Password must be at least 6 characters');
        } else {
            clearError(this);
        }
    });

    // Clear error on input
    emailInput.addEventListener('input', function() {
        clearError(this);
    });

    passwordInput.addEventListener('input', function() {
        clearError(this);
    });

    // Helper functions
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function showError(input, message) {
        clearError(input);

        input.style.borderColor = 'var(--color-error)';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.style.color = 'var(--color-error)';
        errorDiv.style.fontSize = 'var(--font-size-body-sm)';
        errorDiv.style.marginTop = 'var(--spacing-xs)';
        errorDiv.textContent = message;

        input.parentElement.appendChild(errorDiv);
    }

    function clearError(input) {
        input.style.borderColor = '';

        const errorDiv = input.parentElement.querySelector('.form-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

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
});
