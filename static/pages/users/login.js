import LoginApp from "@/components/users/login/index.vue";
import { createApp } from "vue";
import { propParser } from "@/utils/parser";
import { createNotivue } from "notivue";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/css/styles.scss";

const initialProps = window.__PROPS__ || {};
const loginApp = createApp(LoginApp, propParser(initialProps));

const notivue = createNotivue({
  position: "bottom-right",
});

loginApp.use(notivue);
loginApp.mount("#app");
