import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RealtimeStore } from '../../core/services/realtime-store.service';
import { LiveChartComponent } from '../../shared/components/live-chart/live-chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [LiveChartComponent, DatePipe, DecimalPipe, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  readonly store = inject(RealtimeStore);
}
