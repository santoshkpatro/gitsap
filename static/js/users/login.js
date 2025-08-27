import LoginApp from "@/components/users/login/index.vue";
import { createApp } from "vue";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/css/styles.scss";

const initialProps = window.__PROPS__ || {};
const loginApp = createApp(LoginApp, initialProps);

loginApp.mount("#app");
