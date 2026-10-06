import { Component, Input } from '@angular/core';

export interface ChartPoint {
  t: number;
  v: number;
  device: string;
}

@Component({
  selector: 'app-live-chart',
  standalone: true,
  templateUrl: './live-chart.component.html',
  styleUrl: './live-chart.component.scss',
})
export class LiveChartComponent {
  @Input({ required: true }) points: ChartPoint[] = [];
  @Input() height = 220;

  get pathD(): string {
    return this.buildPath(this.points);
  }

  get areaD(): string {
    return this.buildArea(this.points);
  }

  get lastValue(): number | null {
    return this.points.at(-1)?.v ?? null;
  }

  private buildPath(points: ChartPoint[]): string {
    if (points.length < 2) {
      return '';
    }
    const w = 1000;
    const h = this.height;
    const pad = 16;
    const min = Math.min(...points.map((p) => p.v));
    const max = Math.max(...points.map((p) => p.v));
    const span = Math.max(max - min, 0.5);
    return points
      .map((p, i) => {
        const x = pad + (i / (points.length - 1)) * (w - pad * 2);
        const y = h - pad - ((p.v - min) / span) * (h - pad * 2);
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }

  private buildArea(points: ChartPoint[]): string {
    const line = this.buildPath(points);
    if (!line) {
      return '';
    }
    const w = 1000;
    const h = this.height;
    const pad = 16;
    return `${line} L${w - pad},${h - pad} L${pad},${h - pad} Z`;
  }
}
