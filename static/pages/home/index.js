import IndexApp from "@/components/home/index.vue";
import { createApp } from "vue";
import { propParser } from "@/utils/parser";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/css/styles.scss";

const initialProps = window.__PROPS__ || {};
const app = createApp(IndexApp, propParser(initialProps));
app.mount("#app");
