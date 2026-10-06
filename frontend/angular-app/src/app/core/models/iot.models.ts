export type DeviceStatus = 'online' | 'offline' | 'unknown';
export type DeviceType =
  | 'multi_sensor'
  | 'temperature'
  | 'humidity'
  | 'pressure'
  | 'motion';

export interface Device {
  id: number;
  device_code: string;
  name: string;
  type: DeviceType;
  location: string | null;
  status: DeviceStatus;
  created_at: string;
  last_seen_at: string | null;
}

export interface Measurement {
  id: number;
  device_id: number;
  timestamp: string;
  temperature: number | null;
  humidity: number | null;
  pressure: number | null;
  motion: boolean | null;
  battery: number | null;
  created_at: string;
  device_code?: string | null;
}

export type AlertType =
  | 'temperature_threshold'
  | 'humidity_threshold'
  | 'battery_low'
  | 'connection'
  | 'anomaly';

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: number;
  device_id: number;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  created_at: string;
  resolved_at: string | null;
  device_code?: string | null;
}

export interface DashboardStats {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  open_alerts: number;
  critical_alerts: number;
  measurements_last_hour: number;
}

export interface WsEnvelope<T = unknown> {
  type: string;
  data: T;
  timestamp?: string;
}
