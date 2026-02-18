import axios, { AxiosHeaders, InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "../store/authStore";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 10000,
});

const refreshApi = axios.create({
  baseURL,
  timeout: 10000,
});

let refreshPromise: Promise<string | null> | null = null;

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    if (!config.headers) {
      config.headers = new AxiosHeaders();
    }
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

function isAuthRoute(url?: string): boolean {
  if (!url) return false;
  return url.startsWith("/auth/login") || url.startsWith("/auth/register") || url.startsWith("/auth/refresh");
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status as number | undefined;
    const original = error?.config as RetryableConfig | undefined;
    const auth = useAuthStore.getState();

    if (status === 401 && original && !original._retry && auth.accessToken && !isAuthRoute(original.url)) {
      original._retry = true;

      if (!refreshPromise) {
        refreshPromise = (async () => {
          if (!auth.refreshToken) return null;
          try {
            const { data } = await refreshApi.post("/auth/refresh", { refresh_token: auth.refreshToken });
            useAuthStore.setState({
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
            });
            return data.access_token as string;
          } catch {
            return null;
          } finally {
            refreshPromise = null;
          }
        })();
      }

      const newAccessToken = await refreshPromise;
      if (newAccessToken) {
        if (!original.headers) {
          original.headers = new AxiosHeaders();
        }
        original.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(original);
      }

      useAuthStore.getState().logout();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);
