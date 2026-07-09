import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// 🔥 ADD THIS (JWT TOKEN)
API.interceptors.request.use((config) => {
  const user = JSON.parse(localStorage.getItem("user"));
  const token = user?.access_token || user?.token;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default API;
