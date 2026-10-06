import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Alert,
  DashboardStats,
  Device,
  Measurement,
} from '../models/iot.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getHealth(): Observable<{ status: string; service: string }> {
    return this.http.get<{ status: string; service: string }>(`${this.base}/health`);
  }

  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.base}/stats/dashboard`);
  }

  getDevices(): Observable<Device[]> {
    return this.http.get<Device[]>(`${this.base}/devices`);
  }

  getDevice(id: number): Observable<Device> {
    return this.http.get<Device>(`${this.base}/devices/${id}`);
  }

  getMeasurements(limit = 50, deviceId?: number): Observable<Measurement[]> {
    let params = new HttpParams().set('limit', limit);
    if (deviceId != null) {
      params = params.set('device_id', deviceId);
    }
    return this.http.get<Measurement[]>(`${this.base}/measurements`, { params });
  }

  getAlerts(onlyOpen = false, limit = 50): Observable<Alert[]> {
    const params = new HttpParams()
      .set('only_open', onlyOpen)
      .set('limit', limit);
    return this.http.get<Alert[]>(`${this.base}/alerts`, { params });
  }

  resolveAlert(id: number): Observable<Alert> {
    return this.http.post<Alert>(`${this.base}/alerts/${id}/resolve`, {});
  }
}
