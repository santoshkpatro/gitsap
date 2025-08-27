<script setup>
const props = defineProps(["nextUrl"]);
import { userProfileAPI } from "@/utils/api";
import { onMounted } from "vue";

const loadProfile = async () => {
  const profile = await userProfileAPI();
  console.log("User Profile:", profile.data);
};

onMounted(async () => {
  loadProfile();
  console.log("Props:", props);
});
</script>

<template>
  <div></div>
</template>
