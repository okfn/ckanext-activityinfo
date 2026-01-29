// handle format selection at the resource create form
document.addEventListener('DOMContentLoaded', function() {
    // Update hidden field when checkboxes change
    function updateFormatsField() {
        var checkboxes = document.querySelectorAll('.ai-format-checkbox:checked');
        var formats = Array.from(checkboxes).map(cb => cb.value);
        document.getElementById('ai-formats-field').value = formats.join(',');

        // Show/hide error
        var errorDiv = document.getElementById('ai-format-error');
        if (formats.length === 0) {
            errorDiv.style.display = 'block';
        } else {
            errorDiv.style.display = 'none';
        }
    }

    // Attach change listeners to checkboxes
    document.querySelectorAll('.ai-format-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', updateFormatsField);
    });

    // Initialize on load
    updateFormatsField();

    // Validate before form submission
    var form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            var urlType = document.querySelector('input[name="url_type"]:checked');
            if (urlType && urlType.value === 'activityinfo') {
                var checkboxes = document.querySelectorAll('.ai-format-checkbox:checked');
                if (checkboxes.length === 0) {
                    e.preventDefault();
                    document.getElementById('ai-format-error').style.display = 'block';
                    return false;
                }
            }
        });
    }
});