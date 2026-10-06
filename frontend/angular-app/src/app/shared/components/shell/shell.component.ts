import { Component, OnInit, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { RealtimeStore } from '../../../core/services/realtime-store.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
})
export class ShellComponent implements OnInit {
  readonly store = inject(RealtimeStore);
  readonly auth = inject(AuthService);

  ngOnInit(): void {
    void this.store.bootstrap();
  }

  logout(): void {
    this.auth.logout();
  }
}
