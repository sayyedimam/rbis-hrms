import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { NotificationService } from '../../services/notification.service';
import { AuthService } from '../../services/auth.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-records',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="module-view-padding">
        <section class="page-section">
          <div class="section-header">
            <div class="header-text">
              <h2>Digital Vault</h2>
              <p>Download and verify raw original biometric logs</p>
            </div>
          </div>

          <div class="records-grid" *ngIf="!loading; else loader">
            <div class="record-card" *ngFor="let record of records">
              <div class="record-icon">
                <i class="lucide-file-spreadsheet"></i>
              </div>
              <div class="record-info">
                <h3>{{ record.filename }}</h3>
                <div class="meta">
                  <span class="badge">{{ record.report_type }}</span>
                  <span class="date">{{ record.uploaded_at | date:'medium' }}</span>
                </div>
                <p class="uploader">Uploaded by: <strong>{{ record.uploaded_by }}</strong></p>
              </div>
              <button class="btn-download" (click)="download(record)">
                <i class="lucide-download"></i>
                Download
              </button>
            </div>

            <div class="no-records" *ngIf="records.length === 0">
              <i class="lucide-folder-open"></i>
              <p>No historical records found.</p>
            </div>
          </div>

          <ng-template #loader>
            <div class="loading-state">
              <div class="spinner"></div>
              <p>Fetching records from vault...</p>
            </div>
          </ng-template>
        </section>
    </div>
  `,
  styles: [`
    .records-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 1.5rem;
      margin-top: 1rem;
    }

    .record-card {
      background: white;
      border-radius: 15px;
      padding: 1.5rem;
      display: flex;
      align-items: center;
      gap: 1.5rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
      border: 1px solid #f1f5f9;
      transition: transform 0.2s;
    }

    .record-card:hover {
      transform: translateY(-3px);
      border-color: #4f46e5;
    }

    .record-icon {
      width: 50px;
      height: 50px;
      background: #eff6ff;
      color: #3b82f6;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
    }

    .record-info {
      flex: 1;
    }

    .record-info h3 {
      font-size: 1rem;
      font-weight: 700;
      color: #1e293b;
      margin-bottom: 0.4rem;
      word-break: break-all;
    }

    .meta {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.5rem;
    }

    .badge {
      font-size: 0.7rem;
      font-weight: 800;
      padding: 0.2rem 0.5rem;
      background: #f1f5f9;
      color: #475569;
      border-radius: 4px;
      text-transform: uppercase;
    }

    .date {
      font-size: 0.75rem;
      color: #94a3b8;
    }

    .uploader {
      font-size: 0.8rem;
      color: #64748b;
      margin: 0;
    }

    .btn-download {
      background: white;
      color: #4f46e5;
      border: 1px solid #e2e8f0;
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.8rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-download:hover {
      background: #eff6ff;
      border-color: #4f46e5;
    }

    .loading-state, .no-records {
      text-align: center;
      padding: 100px 20px;
      color: #94a3b8;
    }

    .no-records i {
      font-size: 3rem;
      margin-bottom: 1rem;
    }
  `]
})
export class RecordsComponent implements OnInit {
  records: any[] = [];
  loading = true;

  constructor(
    private attendanceService: AttendanceService,
    private notificationService: NotificationService,
    public authService: AuthService
  ) {}

  ngOnInit() {
    this.attendanceService.getRecords().subscribe({
      next: (res) => {
        this.records = res;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.notificationService.showAlert("Could not load records.", "error");
      }
    });
  }

  download(record: any) {
    this.attendanceService.downloadRecord(record.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = record.filename;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => {
        this.notificationService.showAlert("Download failed.", "error");
      }
    });
  }
}
