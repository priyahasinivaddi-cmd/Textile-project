import axios from "axios";
import { API_BASE_URL } from "./apiConfig";

const API = axios.create({
  baseURL: API_BASE_URL,
});

// 🔥 ADD THIS (JWT TOKEN)
API.interceptors.request.use((config) => {
  if (!API_BASE_URL && import.meta.env.PROD) {
    return Promise.reject(
      new Error("The production API is not configured. Set PUBLIC_ORIGIN in .env.aws-demo and rebuild the AWS deployment."),
    );
  }

  const user = JSON.parse(localStorage.getItem("user"));
  const token = user?.access_token || user?.token;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

let refreshRequest = null;
API.interceptors.response.use(response => response, async (error) => {
  const request = error.config;
  const user = JSON.parse(localStorage.getItem("user"));
  if (error.response?.status !== 401 || request?._retried || !user?.refresh_token) return Promise.reject(error);
  request._retried = true;
  refreshRequest ||= axios.post(`${API_BASE_URL}/user/refresh`, { refresh_token: user.refresh_token })
    .then(({ data }) => {
      const updated = { ...user, ...data };
      localStorage.setItem("user", JSON.stringify(updated));
      window.dispatchEvent(new CustomEvent("auth-token-refreshed", { detail: updated }));
      return data.access_token;
    })
    .finally(() => { refreshRequest = null; });
  try {
    const token = await refreshRequest;
    request.headers.Authorization = `Bearer ${token}`;
    return API(request);
  } catch (refreshError) {
    localStorage.removeItem("user");
    window.dispatchEvent(new Event("auth-session-expired"));
    return Promise.reject(refreshError);
  }
});

export default API;
