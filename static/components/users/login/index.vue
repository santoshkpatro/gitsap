<template>
  <users-layout>
    <div
      class="card p-4 border-0 shadow-sm bg-white"
      style="border-radius: 12px"
    >
      <form @submit.prevent="handleLogin" novalidate>
        <!-- Username/Email -->
        <div class="mb-3">
          <label for="username" class="form-label">Username or Email</label>
          <div class="input-group">
            <span class="input-group-text bg-white">
              <user-icon :size="18" />
            </span>
            <input
              type="text"
              id="username"
              v-model.trim="form.username"
              class="form-control"
              placeholder="you@gitsap.com"
              autocomplete="username"
              required
            />
          </div>
        </div>

        <!-- Password -->
        <div class="mb-3">
          <div class="d-flex justify-content-between align-items-center">
            <label for="password" class="form-label mb-0">Password</label>
            <a href="#" class="small text-decoration-none">Forgot password?</a>
          </div>
          <div class="input-group">
            <span class="input-group-text bg-white">
              <lock-icon :size="18" />
            </span>
            <input
              type="password"
              id="password"
              v-model="form.password"
              class="form-control"
              placeholder="••••••••"
              autocomplete="current-password"
              required
            />
          </div>
        </div>

        <!-- Remember me -->
        <div class="mb-3 form-check">
          <input
            type="checkbox"
            class="form-check-input"
            id="remember"
            v-model="form.remember"
          />
          <label class="form-check-label" for="remember">Remember me</label>
        </div>

        <!-- Submit -->
        <button
          type="submit"
          class="btn btn-primary w-100 d-flex align-items-center justify-content-center"
        >
          <login-icon :size="18" class="me-2" /> Sign in
        </button>
      </form>

      <!-- Register link -->
      <div class="text-center mt-3">
        <span class="text-muted small">Don’t have an account?</span>
        <router
          path="/users/register"
          class="small fw-semibold ms-1 text-decoration-none"
          >Register</router
        >
      </div>
    </div>
  </users-layout>
</template>

<script setup>
import { reactive } from "vue";

import UsersLayout from "@/components/layouts/users-layout.vue";
import UserIcon from "@/components/icons/user-icon.vue";
import LockIcon from "@/components/icons/lock-icon.vue";
import LoginIcon from "@/components/icons/login-icon.vue";
import Router from "@/components/router.vue";

const form = reactive({
  username: "",
  password: "",
  remember: true,
});

const handleLogin = () => {
  // TODO: replace with your API call
  console.log("Login attempt:", { ...form });
};
</script>
