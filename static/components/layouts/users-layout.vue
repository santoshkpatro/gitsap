<template>
  <div class="d-flex align-items-center justify-content-center vh-100 bg-grid">
    <div class="w-100" style="max-width: 420px">
      <!-- Brand -->
      <h2 class="text-center mb-4 fw-bold" style="color: #6f42c1">
        gitsap.com
      </h2>

      <!-- Page content -->
      <slot></slot>

      <!-- Footer links -->
      <div class="text-center mt-4">
        <a href="#" class="text-decoration-none small text-muted me-3"
          >Privacy</a
        >
        <a href="#" class="text-decoration-none small text-muted"
          >Terms & Conditions</a
        >
      </div>
    </div>
  </div>
</template>

<script setup>
// no props, fixed layout
</script>

<style scoped>
/* Subtle grid background */
.bg-grid {
  background:
    linear-gradient(to right, rgba(111, 66, 193, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(111, 66, 193, 0.06) 1px, transparent 1px);
  background-size: 20px 20px;
}
</style>
