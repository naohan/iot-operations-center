import { Injectable, OnDestroy, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { WsEnvelope } from '../models/iot.models';

@Injectable({ providedIn: 'root' })
export class WebsocketService implements OnDestroy {
  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;
  private attempts = 0;
  private token: string | null = null;

  readonly connected = signal(false);
  readonly lastError = signal<string | null>(null);

  private readonly messagesSubject = new Subject<WsEnvelope>();
  readonly messages$ = this.messagesSubject.asObservable();

  connect(token?: string): void {
    if (token) {
      this.token = token;
    }
    if (!this.token) {
      this.lastError.set('Sin token para WebSocket');
      return;
    }
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this.intentionalClose = false;
    const url = `${environment.wsUrl}?token=${encodeURIComponent(this.token)}`;
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      this.connected.set(true);
      this.lastError.set(null);
      this.attempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as WsEnvelope;
        this.messagesSubject.next(payload);
      } catch {
        // ignore malformed frames
      }
    };

    this.socket.onerror = () => {
      this.lastError.set('Error de WebSocket');
    };

    this.socket.onclose = () => {
      this.connected.set(false);
      this.socket = null;
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
    this.connected.set(false);
  }

  ngOnDestroy(): void {
    this.disconnect();
    this.messagesSubject.complete();
  }

  private scheduleReconnect(): void {
    this.attempts += 1;
    const delay = Math.min(1000 * 2 ** Math.min(this.attempts, 4), 15000);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }
}
