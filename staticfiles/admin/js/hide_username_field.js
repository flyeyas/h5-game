document.addEventListener('DOMContentLoaded', function() {
    // Check if current URL contains password change page path
    if (window.location.pathname.includes('/admin/auth/user/') && window.location.pathname.includes('/password/')) {
        // Find all input boxes with value "testuser2" and hide them
        const inputs = document.querySelectorAll('input[type="text"]');
        inputs.forEach(function(input) {
            if (input.value === 'testuser2') {
                input.style.display = 'none';
            }
        });
    }
}); 