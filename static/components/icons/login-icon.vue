<template>
  <LogIn :size="size" :stroke-width="strokeWidth" :color="color" />
</template>

<script setup>
import { LogIn } from "lucide-vue-next";

defineProps({
  size: { type: [Number, String], default: 18 },
  strokeWidth: { type: [Number, String], default: 2 },
  color: { type: String, default: "currentColor" },
});
</script>
