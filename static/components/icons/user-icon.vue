<template>
  <User :size="size" :stroke-width="strokeWidth" :color="color" />
</template>

<script setup>
import { User } from "lucide-vue-next";

defineProps({
  size: { type: [Number, String], default: 18 },
  strokeWidth: { type: [Number, String], default: 2 },
  color: { type: String, default: "currentColor" },
});
</script>
