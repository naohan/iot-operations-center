import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  Alert,
  DashboardStats,
  Device,
  Measurement,
} from '../models/iot.models';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { WebsocketService } from './websocket.service';

const MAX_LIVE_POINTS = 40;

@Injectable({ providedIn: 'root' })
export class RealtimeStore {
  private readonly api = inject(ApiService);
  private readonly ws = inject(WebsocketService);
  private readonly auth = inject(AuthService);

  readonly stats = signal<DashboardStats | null>(null);
  readonly devices = signal<Device[]>([]);
  readonly alerts = signal<Alert[]>([]);
  readonly recentMeasurements = signal<Measurement[]>([]);
  readonly liveTemps = signal<Array<{ t: number; v: number; device: string }>>([]);
  readonly flashAlertId = signal<number | null>(null);
  readonly loading = signal(false);
  readonly connected = this.ws.connected;

  readonly onlineCount = computed(() => this.stats()?.online_devices ?? 0);
  readonly openAlerts = computed(() => this.stats()?.open_alerts ?? 0);

  private bootstrapped = false;

  async bootstrap(): Promise<void> {
    const token = this.auth.getToken();
    if (this.bootstrapped) {
      if (token) {
        this.ws.connect(token);
      }
      return;
    }
    this.loading.set(true);
    try {
      const [stats, devices, alerts, measurements] = await Promise.all([
        firstValueFrom(this.api.getDashboardStats()),
        firstValueFrom(this.api.getDevices()),
        firstValueFrom(this.api.getAlerts(true, 30)),
        firstValueFrom(this.api.getMeasurements(40)),
      ]);
      this.stats.set(stats);
      this.devices.set(devices);
      this.alerts.set(alerts);
      this.recentMeasurements.set(measurements);
      this.liveTemps.set(
        [...measurements]
          .reverse()
          .filter((m) => m.temperature != null)
          .slice(-MAX_LIVE_POINTS)
          .map((m) => ({
            t: new Date(m.timestamp).getTime(),
            v: m.temperature as number,
            device: m.device_code ?? `dev-${m.device_id}`,
          }))
      );
      if (token) {
        this.ws.connect(token);
      }
      this.ws.messages$.subscribe((msg) => this.handleEvent(msg.type, msg.data));
      this.bootstrapped = true;
    } finally {
      this.loading.set(false);
    }
  }

  async refreshStats(): Promise<void> {
    this.stats.set(await firstValueFrom(this.api.getDashboardStats()));
  }

  async resolveAlert(id: number): Promise<void> {
    const updated = await firstValueFrom(this.api.resolveAlert(id));
    this.alerts.update((list) => list.filter((a) => a.id !== updated.id));
    await this.refreshStats();
  }

  private handleEvent(type: string, data: unknown): void {
    switch (type) {
      case 'measurement':
        this.onMeasurement(data as Measurement & { device_code: string });
        break;
      case 'alert':
        this.onAlert(data as Alert);
        break;
      case 'anomaly':
        // El alert asociado llega aparte; esto refuerza el flash visual
        this.flashAlertId.set((data as { id?: number }).id ?? -1);
        setTimeout(() => {
          if (this.flashAlertId() === ((data as { id?: number }).id ?? -1)) {
            this.flashAlertId.set(null);
          }
        }, 4000);
        break;
      case 'device_status':
        this.onDeviceStatus(data as Device);
        break;
      default:
        break;
    }
  }

  private onMeasurement(m: Measurement & { device_code?: string }): void {
    this.recentMeasurements.update((list) => [m, ...list].slice(0, 50));
    if (m.temperature != null) {
      this.liveTemps.update((points) =>
        [
          ...points,
          {
            t: new Date(m.timestamp).getTime(),
            v: m.temperature as number,
            device: m.device_code ?? `dev-${m.device_id}`,
          },
        ].slice(-MAX_LIVE_POINTS)
      );
    }
    this.stats.update((s) =>
      s
        ? {
            ...s,
            measurements_last_hour: s.measurements_last_hour + 1,
          }
        : s
    );
  }

  private onAlert(alert: Alert): void {
    this.alerts.update((list) => [alert, ...list.filter((a) => a.id !== alert.id)]);
    this.flashAlertId.set(alert.id);
    setTimeout(() => {
      if (this.flashAlertId() === alert.id) {
        this.flashAlertId.set(null);
      }
    }, 4000);
    this.stats.update((s) =>
      s
        ? {
            ...s,
            open_alerts: s.open_alerts + 1,
            critical_alerts:
              alert.severity === 'critical' || alert.severity === 'high'
                ? s.critical_alerts + 1
                : s.critical_alerts,
          }
        : s
    );
  }

  private onDeviceStatus(device: Partial<Device> & { device_code: string; status: Device['status'] }): void {
    this.devices.update((list) => {
      const idx = list.findIndex((d) => d.device_code === device.device_code);
      if (idx === -1) {
        return list;
      }
      const next = [...list];
      next[idx] = { ...next[idx], ...device };
      return next;
    });
  }
}
