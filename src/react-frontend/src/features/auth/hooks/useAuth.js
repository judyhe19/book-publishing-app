import { useAuthContext } from "../store/authStore";
export function useAuth() {
  return useAuthContext();
}