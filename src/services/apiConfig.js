const configuredBaseURL = import.meta.env.VITE_API_URL?.trim();

export const API_BASE_URL = (
  configuredBaseURL || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "")
).replace(/\/$/, "");

export const resolveApiUrl = (path) => {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
};
