export const formatNumber = (value, unit = "") =>
  value === undefined || value === null ? "No data" : `${Number(value).toFixed(1)}${unit}`;

export const formatTime = (value) =>
  value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "No update yet";
