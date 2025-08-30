import axios from "axios";
import Cookies from "js-cookie";
import NProgress from "nprogress";
import "nprogress/nprogress.css";
import { camelCase, snakeCase } from "change-case";
import { convertKeys } from "@/utils/keys";

NProgress.configure({ showSpinner: false, trickleSpeed: 120, minimum: 0.08 });

export const http = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": Cookies.get("csrftoken") || "",
  },
});

http.interceptors.request.use(
  (config) => {
    // always pick latest CSRF token
    config.headers["X-CSRFToken"] = Cookies.get("csrftoken") || "";

    // start bar
    NProgress.start();

    // skip snakeCase for FormData
    const isFormData =
      typeof FormData !== "undefined" && config.data instanceof FormData;

    if (!isFormData && config.data) {
      config.data = convertKeys(config.data, snakeCase);
    }
    if (config.params) {
      config.params = convertKeys(config.params, snakeCase);
    }
    return config;
  },
  (error) => {
    NProgress.done();
    return Promise.reject(error);
  }
);

http.interceptors.response.use(
  (response) => {
    NProgress.done();

    // backend already returns the envelope
    const envelope = response?.data ?? {};

    // camelCase only inside data/meta (leave top-level keys as-is)
    if (envelope && typeof envelope === "object") {
      const out = { ...envelope };
      if (out.data && typeof out.data === "object") {
        out.data = convertKeys(out.data, camelCase);
      }
      if (out.meta && typeof out.meta === "object") {
        out.meta = convertKeys(out.meta, camelCase);
      }
      return out;
    }

    // Fallback if something unexpected came back
    return {
      success: true,
      message: "OK",
      error_code: 0,
      data: {},
      meta: {},
    };
  },
  (error) => {
    NProgress.done();

    // If server responded, unwrap and normalize
    if (error?.response?.data) {
      const env = error.response.data;
      // Ensure envelope shape even if backend didn't send exactly as expected
      const normalized = {
        success: env.success ?? false,
        message: env.message ?? "Request failed",
        error_code: env.error_code ?? (error.response.status || -1),
        data: env.data ?? {},
        meta: env.meta ?? {},
      };
      // camelCase inner payloads for consistency
      normalized.data = convertKeys(normalized.data, camelCase);
      normalized.meta = convertKeys(normalized.meta, camelCase);
      return Promise.resolve(normalized);
    }

    // Network/timeouts or no structured response
    return Promise.resolve({
      success: false,
      message: "Network error",
      error_code: -1,
      data: {},
      meta: {},
    });
  }
);

export const userProfileAPI = () => http.get("/users/profile");
export const usersLoginAPI = (data) => http.post("/users/login", data);
