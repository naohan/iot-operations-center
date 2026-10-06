import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { RealtimeStore } from '../../core/services/realtime-store.service';

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './alerts.component.html',
  styleUrl: './alerts.component.scss',
})
export class AlertsComponent {
  readonly store = inject(RealtimeStore);
  readonly auth = inject(AuthService);

  resolve(id: number): void {
    if (!this.auth.canResolveAlerts()) {
      return;
    }
    void this.store.resolveAlert(id);
  }
}
