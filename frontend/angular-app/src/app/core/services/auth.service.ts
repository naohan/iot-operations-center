import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthUser, LoginResponse, MeResponse, UserRole } from '../models/auth.models';
import { WebsocketService } from './websocket.service';

const TOKEN_KEY = 'iot_ops_token';
const USER_KEY = 'iot_ops_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly ws = inject(WebsocketService);

  private readonly userSignal = signal<AuthUser | null>(this.readStoredUser());
  readonly user = this.userSignal.asReadonly();
  readonly isAuthenticated = computed(() => !!this.getToken() && !!this.userSignal());
  readonly role = computed(() => this.userSignal()?.role ?? null);

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  canResolveAlerts(): boolean {
    const role = this.role();
    return role === 'admin' || role === 'operator';
  }

  canManageDevices(): boolean {
    return this.role() === 'admin';
  }

  async login(email: string, password: string): Promise<void> {
    const res = await firstValueFrom(
      this.http.post<LoginResponse>(`${environment.apiUrl}/auth/login`, { email, password })
    );
    localStorage.setItem(TOKEN_KEY, res.access_token);
    const user: AuthUser = { email: res.email, role: res.role };
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    this.userSignal.set(user);
    this.ws.disconnect();
    this.ws.connect(res.access_token);
  }

  async restoreSession(): Promise<boolean> {
    const token = this.getToken();
    if (!token) {
      return false;
    }
    try {
      const me = await firstValueFrom(
        this.http.get<MeResponse>(`${environment.apiUrl}/auth/me`)
      );
      const user: AuthUser = { email: me.email, role: me.role };
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      this.userSignal.set(user);
      this.ws.connect(token);
      return true;
    } catch {
      this.clearSession();
      return false;
    }
  }

  logout(): void {
    this.clearSession();
    void this.router.navigateByUrl('/login');
  }

  hasRole(...roles: UserRole[]): boolean {
    const role = this.role();
    return !!role && roles.includes(role);
  }

  private clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.userSignal.set(null);
    this.ws.disconnect();
  }

  private readStoredUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }
}
