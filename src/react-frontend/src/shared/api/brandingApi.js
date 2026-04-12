// src/shared/api/brandingApi.js
import { apiFetch } from "./http";

/**
 * GET /api/branding/
 * Returns:
 * {
 *   publisher_name: string,
 *   app_title: string,
 *   publisher_logo_url: string,
 *   publisher_favicon_url: string
 * }
 */
export function getBranding() {
  return apiFetch("/api/branding/");
}

/**
 * Optional helper: normalize branding response
 * Ensures all expected fields exist
 */
export function normalizeBranding(data) {
  return {
    publisher_name: data?.publisher_name || "",
    app_title: data?.app_title || "",
    publisher_logo_url: data?.publisher_logo_url || "",
    publisher_favicon_url: data?.publisher_favicon_url || "",
  };
}