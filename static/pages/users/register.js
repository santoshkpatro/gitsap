import RegisterApp from "@/components/users/register/index.vue";
import { createApp } from "vue";
import { propParser } from "@/utils/parser";
import { createNotivue } from "notivue";

import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/css/styles.scss";

const initialProps = window.__PROPS__ || {};
const app = createApp(RegisterApp, propParser(initialProps));

const notivue = createNotivue({
  position: "bottom-right",
});

app.use(notivue);
app.mount("#app");
