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
  templateUrl: './records.component.html',
  styleUrl: './records.component.css'
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
