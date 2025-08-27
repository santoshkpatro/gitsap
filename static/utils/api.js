import axios from "axios";
import { camelCase, snakeCase } from "change-case";
import { convertKeys } from "@/utils/keys";

export const http = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: camelCase ➝ kebab_case (or snake_case)
http.interceptors.request.use((config) => {
  if (config.data) {
    config.data = convertKeys(config.data, snakeCase);
  }
  if (config.params) {
    config.params = convertKeys(config.params, snakeCase);
  }
  return config;
});

// Response interceptor: kebab_case ➝ camelCase
http.interceptors.response.use((response) => {
  if (response.data) {
    response.data = convertKeys(response.data, camelCase);
  }
  return response;
});

export const userProfileAPI = () => http.get("/users/profile");
