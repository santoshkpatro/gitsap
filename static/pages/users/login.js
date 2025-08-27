import LoginApp from "@/components/users/login/index.vue";
import { createApp } from "vue";
import { propParser } from "@/utils/parser";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/css/styles.scss";

const initialProps = window.__PROPS__ || {};
const loginApp = createApp(LoginApp, propParser(initialProps));

loginApp.mount("#app");
