import { camelCase } from "change-case";
import { convertKeys } from "@/utils/keys";

export const propParser = (props) => {
  return convertKeys(props, camelCase);
};
