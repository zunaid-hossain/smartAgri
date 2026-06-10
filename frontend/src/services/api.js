import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 15000,
});

export const getLatestData = async () => (await api.get("/latest-data")).data;
export const getHistory = async (limit = 100) => (await api.get(`/history?limit=${limit}`)).data;
export const getRecommendation = async () => (await api.get("/ai-recommendation")).data;
export const getSystemStatus = async () => (await api.get("/system-status")).data;
