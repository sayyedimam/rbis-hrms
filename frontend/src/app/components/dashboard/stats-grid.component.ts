import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stats-grid',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="stats-grid" *ngIf="stats">
      <div class="stat-card clickable" (click)="onStatusClick.emit('Present')">
        <div class="stat-icon"><i data-lucide="check-circle"></i></div>
        <div class="stat-info">
          <span class="label">Present Days</span>
          <span class="value">{{ stats.present }}</span>
        </div>
      </div>
      <div class="stat-card clickable" (click)="onStatusClick.emit('Absent')">
        <div class="stat-icon alert"><i data-lucide="x-circle"></i></div>
        <div class="stat-info">
          <span class="label">Absent Days</span>
          <span class="value">{{ stats.absent }}</span>
        </div>
      </div>
      <div class="stat-card clickable" *ngIf="stats.onLeave > 0" (click)="onStatusClick.emit('On Leave')">
        <div class="stat-icon leave"><i data-lucide="calendar-off"></i></div>
        <div class="stat-info">
          <span class="label">On Leave</span>
          <span class="value">{{ stats.onLeave }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon efficiency"><i data-lucide="zap"></i></div>
        <div class="stat-info">
          <span class="label">Avg working hours</span>
          <span class="value">{{ stats.avgHours | number : "1.1-1" }}h</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      padding: 1.5rem;
      backdrop-filter: blur(10px);
      transition: all 0.3s ease;
      cursor: pointer;
    }
    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    .stat-icon {
      font-size: 2rem;
      margin-bottom: 0.5rem;
      color: #4f46e5;
    }
    .stat-info .label {
      display: block;
      font-size: 0.9rem;
      color: #6b7280;
      margin-bottom: 0.25rem;
    }
    .stat-info .value {
      font-size: 1.5rem;
      font-weight: bold;
      color: #1f2937;
    }
  `]
})
export class StatsGridComponent {
  @Input() stats: any;
  @Output() onStatusClick = new EventEmitter<string>();
}
