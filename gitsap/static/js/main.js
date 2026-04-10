document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();

    // Bootstrap tooltips
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });
});
