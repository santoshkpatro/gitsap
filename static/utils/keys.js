export const convertKeys = (obj, converter) => {
  if (Array.isArray(obj)) {
    return obj.map((item) => convertKeys(item, converter));
  } else if (obj && typeof obj === "object") {
    return Object.keys(obj).reduce((acc, key) => {
      acc[converter(key)] = convertKeys(obj[key], converter);
      return acc;
    }, {});
  }
  return obj;
};
