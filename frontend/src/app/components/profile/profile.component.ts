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
  template: `
    <div class="module-view-padding">
        <section class="page-section" *ngIf="!loading; else loader">
          <div class="profile-card">
            <div class="profile-header">
              <div class="large-avatar">
                <i class="lucide-user"></i>
              </div>
              <div class="header-info">
                <h2>{{ profile.full_name }}</h2>
                <span class="designation">{{ profile.designation }}</span>
                <span class="id-badge">{{ profile.emp_id }}</span>
              </div>
            </div>

            <div class="profile-details">
              <div class="detail-group">
                <label>Office Email</label>
                <p>{{ profile.email }}</p>
              </div>
              <div class="detail-group">
                <label>Phone Number</label>
                <p>{{ profile.phone_number }}</p>
              </div>
              <div class="detail-group">
                <label>System Role</label>
                <p>{{ profile.role }}</p>
              </div>
              <div class="detail-group">
                <label>Member Since</label>
                <p>{{ profile.joined_at | date:'longDate' }}</p>
              </div>
            </div>
          </div>
        </section>

        <ng-template #loader>
          <div class="loading-state">
            <div class="spinner"></div>
            <p>Loading your profile...</p>
          </div>
        </ng-template>
      </div>
  `,
  styles: [`
    .profile-card {
      background: white;
      border-radius: 20px;
      max-width: 800px;
      margin: 2rem auto;
      overflow: hidden;
      box-shadow: 0 10px 25px rgba(0,0,0,0.05);
      border: 1px solid #f1f5f9;
    }

    .profile-header {
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      padding: 3rem;
      display: flex;
      align-items: center;
      gap: 2rem;
      color: white;
    }

    .large-avatar {
      width: 100px;
      height: 100px;
      background: rgba(255,255,255,0.2);
      border-radius: 25px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
      backdrop-filter: blur(10px);
    }

    .header-info h2 {
      margin: 0;
      font-size: 2rem;
      font-weight: 800;
    }

    .designation {
      display: block;
      font-size: 1.1rem;
      opacity: 0.9;
      margin-bottom: 0.5rem;
    }

    .id-badge {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      background: rgba(255,255,255,0.2);
      border-radius: 50px;
      font-size: 0.8rem;
      font-weight: 700;
    }

    .profile-details {
      padding: 3rem;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
    }

    .detail-group label {
      display: block;
      font-size: 0.75rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.5rem;
    }

    .detail-group p {
      font-size: 1rem;
      color: #1e293b;
      font-weight: 600;
      margin: 0;
    }
  `]
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
