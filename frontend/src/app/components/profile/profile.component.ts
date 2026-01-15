import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { NotificationService } from '../../services/notification.service';
import { AuthService } from '../../services/auth.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css'
})
export class ProfileComponent implements OnInit {
  profile: any = {};
  loading = true;
  isAdmin = false;

  constructor(
    private attendanceService: AttendanceService,
    private notificationService: NotificationService,
    public authService: AuthService
  ) {}

  ngOnInit() {
    this.isAdmin = this.authService.getUserRole() === 'SUPER_ADMIN';
    this.attendanceService.getProfile().subscribe({
      next: (res) => {
        this.profile = res;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.notificationService.showAlert("Could not load profile.", "error");
      }
    });
  }
}
