import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ErrorResponse, TokenResponse } from "./types";

const SK_ACCESS = "sf_at";
const SK_REFRESH = "sf_rt";

let accessToken: string | null = null;
let refreshToken: string | null = null;

const retriedRequests = new WeakSet<InternalAxiosRequestConfig>();

function persistToStorage() {
  try {
    if (accessToken && refreshToken) {
      sessionStorage.setItem(SK_ACCESS, accessToken);
      sessionStorage.setItem(SK_REFRESH, refreshToken);
    } else {
      sessionStorage.removeItem(SK_ACCESS);
      sessionStorage.removeItem(SK_REFRESH);
    }
  } catch {
    /* sessionStorage unavailable (e.g. some private-browsing modes) */
  }
}

try {
  accessToken = sessionStorage.getItem(SK_ACCESS);
  refreshToken = sessionStorage.getItem(SK_REFRESH);
} catch {
  /* sessionStorage unavailable */
}

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  persistToStorage();
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  persistToStorage();
}

export function getAccessToken() {
  return accessToken;
}

export class ApiError extends Error {
  code: string;
  details?: unknown;

  constructor(code: string, message: string, details?: unknown) {
    super(message);
    this.code = code;
    this.details = details;
    this.name = "ApiError";
  }
}

const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !retriedRequests.has(originalRequest)
    ) {
      const url = originalRequest.url ?? "";
      const isAuthAttempt =
        url.endsWith("/auth/login") || url.endsWith("/auth/mfa");

      if (!refreshToken) {
        // Do not redirect when login/MFA failed — let the page show the error
        if (!isAuthAttempt) {
          clearTokens();
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      retriedRequests.add(originalRequest);

      try {
        const { data } = await axios.post<
          TokenResponse & { refresh_token?: string }
        >("/api/v1/auth/refresh", { refresh_token: refreshToken });

        accessToken = data.access_token;
        if (data.refresh_token) {
          refreshToken = data.refresh_token;
        }
        persistToStorage();

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    if (error.response?.data?.error) {
      const apiError = error.response.data.error;
      return Promise.reject(
        new ApiError(apiError.code, apiError.message, apiError.details),
      );
    }

    const status = error.response?.status;
    const data = error.response?.data as
      | { code?: string; message?: string; detail?: { code?: string; message?: string } }
      | undefined;

    // 403 upgrade_required: preserve code so pages can show upgrade gate (not generic error)
    if (status === 403) {
      const code = data?.code ?? data?.detail?.code;
      const message =
        data?.message ?? data?.detail?.message ?? "Upgrade required";
      if (code === "upgrade_required") {
        return Promise.reject(new ApiError("upgrade_required", message));
      }
    }

    // Ensure auth failures always get a user-friendly message (e.g. wrong credentials)
    if (status === 401) {
      const message =
        data?.message && typeof data.message === "string"
          ? data.message
          : "Invalid email or password";
      return Promise.reject(new ApiError("unauthorized", message));
    }
    if (status && status >= 400) {
      const message =
        data?.message ??
        (data?.detail && typeof data.detail === "object" && "message" in data.detail
          ? (data.detail as { message?: string }).message
          : undefined);
      if (message && typeof message === "string") {
        const code =
          data?.detail && typeof data.detail === "object" && "code" in data.detail
            ? (data.detail as { code?: string }).code ?? "api_error"
            : "api_error";
        return Promise.reject(new ApiError(code, message));
      }
    }

    return Promise.reject(error);
  },
);

export default api;
