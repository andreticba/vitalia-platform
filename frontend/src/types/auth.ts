// frontend/src/types/auth.ts
import { components } from "@/lib/api-schema";

export type UserProfile = components["schemas"]["UserProfile"];
export type Role = components["schemas"]["Role"];
export type Organization = components["schemas"]["OrganizationSimple"];

// AuthState do Redux (este é do Front, mantém manual)
export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  user: UserProfile | null;
}