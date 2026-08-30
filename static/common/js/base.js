document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();

    document.querySelectorAll('[data-bs-toggle="popover"]').forEach((el) => {
        new bootstrap.Popover(el);
    });
});
