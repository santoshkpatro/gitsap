<script setup>
import { reactive } from "vue";
import useVuelidate from "@vuelidate/core";
import { required, minLength } from "@vuelidate/validators";

import UsersLayout from "@/components/layouts/users-layout.vue";
import UserIcon from "@/components/icons/user-icon.vue";
import LockIcon from "@/components/icons/lock-icon.vue";
import LoginIcon from "@/components/icons/login-icon.vue";
import Router from "@/components/router.vue";
import { usersLoginAPI } from "@/utils/api.js";
import { push } from "notivue";
import { redirect } from "@/utils/router";

// form state
const form = reactive({
  identity: "",
  password: "",
  remember: true,
});

// validation rules
const rules = {
  identity: { required },
  password: { required, minLength: minLength(6) },
};

// setup vuelidate
const v$ = useVuelidate(rules, form);

const handleLogin = async () => {
  const valid = await v$.value.$validate();
  if (!valid) {
    push.warning("Please fix validation errors.");
    return;
  }

  const response = await usersLoginAPI({ ...form });
  if (!response.success) {
    push.warning(response.message);
    return;
  }

  redirect("/");
};
</script>

<template>
  <users-layout>
    <div
      class="card p-4 border-0 shadow-sm bg-white"
      style="border-radius: 12px"
    >
      <form @submit.prevent="handleLogin" novalidate>
        <!-- Identity -->
        <div class="mb-3">
          <label for="identity" class="form-label">Username or Email</label>
          <div class="input-group">
            <span class="input-group-text bg-white">
              <user-icon :size="18" />
            </span>
            <input
              type="text"
              id="identity"
              v-model.trim="form.identity"
              class="form-control"
              placeholder="you@gitsap.com"
              :class="{ 'is-invalid': v$.identity.$error }"
            />
            <div v-if="v$.identity.$error" class="invalid-feedback d-block">
              <div v-for="err in v$.identity.$errors" :key="err.$uid">
                {{ err.$message || "Invalid input" }}
              </div>
            </div>
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
              :class="{ 'is-invalid': v$.password.$error }"
            />
            <div v-if="v$.password.$error" class="invalid-feedback d-block">
              <div v-for="err in v$.password.$errors" :key="err.$uid">
                {{ err.$message || "Invalid input" }}
              </div>
            </div>
          </div>
        </div>

        <!-- Remember -->
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

      <!-- Register -->
      <div class="text-center mt-3">
        <span class="text-muted small">Don’t have an account?</span>
        <router
          path="/users/register"
          class="small fw-semibold ms-1 text-decoration-none"
        >
          Register
        </router>
      </div>
    </div>
  </users-layout>
</template>
