import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Device, Measurement } from '../../core/models/iot.models';
import { ApiService } from '../../core/services/api.service';
import { RealtimeStore } from '../../core/services/realtime-store.service';
import { LiveChartComponent } from '../../shared/components/live-chart/live-chart.component';

@Component({
  selector: 'app-device-detail',
  standalone: true,
  imports: [RouterLink, DatePipe, DecimalPipe, LiveChartComponent],
  templateUrl: './device-detail.component.html',
  styleUrl: './device-detail.component.scss',
})
export class DeviceDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  private readonly store = inject(RealtimeStore);

  readonly device = signal<Device | null>(null);
  readonly measurements = signal<Measurement[]>([]);
  readonly loading = signal(true);

  readonly chartPoints = computed(() =>
    [...this.measurements()]
      .reverse()
      .filter((m) => m.temperature != null)
      .map((m) => ({
        t: new Date(m.timestamp).getTime(),
        v: m.temperature as number,
        device: m.device_code ?? '',
      }))
  );

  readonly liveForDevice = computed(() => {
    const code = this.device()?.device_code;
    if (!code) {
      return this.chartPoints();
    }
    const live = this.store.liveTemps().filter((p) => p.device === code);
    return live.length ? live : this.chartPoints();
  });

  async ngOnInit(): Promise<void> {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    try {
      const [device, measurements] = await Promise.all([
        firstValueFrom(this.api.getDevice(id)),
        firstValueFrom(this.api.getMeasurements(60, id)),
      ]);
      this.device.set(device);
      this.measurements.set(measurements);
    } finally {
      this.loading.set(false);
    }
  }
}
