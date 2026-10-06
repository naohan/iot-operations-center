export type UserRole = 'admin' | 'operator' | 'viewer';

export interface AuthUser {
  email: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  email: string;
}

export interface MeResponse {
  id: number;
  email: string;
  role: UserRole;
}
