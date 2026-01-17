import { Component, OnInit } from '@angular/core';
import { RouterModule, RouterOutlet, Router } from '@angular/router';
import { UploadComponent } from './components/upload/upload.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { CommonModule } from '@angular/common';
import { NotificationService, Alert } from './services/notification.service';
import { AttendanceService } from './services/attendance.service';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule, RouterOutlet, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'Employee Attendance Analytics';
  alerts: Alert[] = [];
  isAdmin = false;
  isHr = false;
  isCeo = false;
  hasDashboardData = false;
  profileMenuOpen = false;
  currentUser: any = null;

  constructor(
    public notificationService: NotificationService,
    public attendanceService: AttendanceService,
    public authService: AuthService,
    public router: Router
  ) {}

  ngOnInit() {
    this.notificationService.alerts$.subscribe((alerts: Alert[]) => {
      this.alerts = alerts;
    });

    // Subscribe to current user for navigation and profile display
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      this.isAdmin = user?.role === 'SUPER_ADMIN';
      this.isHr = user?.role === 'HR' || user?.role === 'SUPER_ADMIN';
      this.isCeo = user?.role === 'CEO' || user?.role === 'SUPER_ADMIN';
    });

    // Subscribe to data availability
    this.attendanceService.hasData$.subscribe((available: boolean) => {
      this.hasDashboardData = available;
    });
  }

  getInitials(user: any): string {
    const target = user || this.currentUser;
    if (!target) return '??';
    const name = target.full_name || target.email?.split('@')[0] || '';
    if (!name) return '??';
    const parts = name.split(/[. \-_]/).filter((p: string) => p.length > 0);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  getUserDisplayName(user: any): string {
    const target = user || this.currentUser;
    if (!target) return 'User';
    return target.full_name || target.email?.split('@')[0] || 'User';
  }

  toggleProfileMenu() {
    this.profileMenuOpen = !this.profileMenuOpen;
  }

  logout() {
    this.profileMenuOpen = false;
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  removeAlert(id: number) {
    this.notificationService.removeAlert(id);
  }
}
