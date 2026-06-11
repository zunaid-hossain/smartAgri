import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "https://smartagri-pv49.onrender.com",
  timeout: 15000,
});

const apiBaseUrl = api.defaults.baseURL;

export const getSensorStreamUrl = () => new URL("/sensor-data/stream", apiBaseUrl).toString();
export const getLatestData = async () => (await api.get("/latest-data")).data;
export const getHistory = async (limit = 100) => (await api.get(`/history?limit=${limit}`)).data;
export const getRecommendation = async () => (await api.get("/ai-recommendation")).data;
export const getRecommendationHistory = async (limit = 20) => (await api.get(`/ai-recommendations?limit=${limit}`)).data;
export const sendAiChatMessage = async (message) => (await api.post("/ai-chat", { message })).data;
export const getSystemStatus = async () => (await api.get("/system-status")).data;
