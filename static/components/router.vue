<template>
  <a :href="href" v-bind="$attrs">
    <slot />
  </a>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  path: { type: String, required: true },
  query: { type: Object, default: () => ({}) },
});

const href = computed(() => {
  const url = new URL(props.path, window.location.origin);
  Object.entries(props.query).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, value);
    }
  });
  // internal path → strip origin
  return url.pathname + url.search + url.hash;
});
</script>
