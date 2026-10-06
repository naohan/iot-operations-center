import { DatePipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RealtimeStore } from '../../core/services/realtime-store.service';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './devices.component.html',
  styleUrl: './devices.component.scss',
})
export class DevicesComponent {
  readonly store = inject(RealtimeStore);
  readonly devices = computed(() => this.store.devices());
}
