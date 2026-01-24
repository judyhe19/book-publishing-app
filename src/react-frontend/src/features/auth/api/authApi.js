import { apiFetch } from "../../../shared/api/http";

export function login({ username, password }) {
  return apiFetch("/api/user/login", { method: "POST", body: { username, password } });
}

export function logout() {
  return apiFetch("/api/user/logout", { method: "POST" });
}

export function me() {
  return apiFetch("/api/user/me");
}

export function changePassword({ old_password, new_password }) {
  return apiFetch("/api/user/changepassword", { method: "POST", body: { old_password, new_password } });
}

export function register({ username, email, password, password2 }) {
  return apiFetch("/api/user/register", { method: "POST", body: { username, email, password, password2 } });
}