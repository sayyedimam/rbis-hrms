import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AttendanceService } from '../../services/attendance.service';
import { NotificationService } from '../../services/notification.service';
import { AuthService } from '../../services/auth.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './onboarding.component.html',
  styleUrls: ['./onboarding.component.css']
})
export class OnboardingComponent implements OnInit {
  employee = {
    first_name: '',
    last_name: '',
    full_name: '',
    phone_number: '',
    email: '',
    designation: '',
    emp_id: ''
  };

  loading = false;
  uploadingMaster = false;

  constructor(
    private attendanceService: AttendanceService,
    private notificationService: NotificationService,
    public authService: AuthService
  ) {}

  ngOnInit() {
    this.suggestNextId();
  }

  suggestNextId() {
    this.attendanceService.getNextId().subscribe({
      next: (res) => {
        this.employee.emp_id = res.next_id;
      },
      error: () => {
        this.notificationService.showAlert('Error fetching next ID', 'error');
      }
    });
  }

  onNameChange() {
    // Auto-update full name
    this.employee.full_name = `${this.employee.first_name} ${this.employee.last_name}`.trim();
    
    // Auto-suggest email: firstname + lastname[0] + @rbistech.com
    if (this.employee.first_name && this.employee.last_name) {
        const first = this.employee.first_name.toLowerCase().trim();
        const lastChar = this.employee.last_name.trim().charAt(0).toLowerCase();
        this.employee.email = `${first}${lastChar}@rbistech.com`;
    }
  }

  onSubmit() {
    this.loading = true;
    this.attendanceService.onboardEmployee(this.employee).subscribe({
      next: (res) => {
        this.loading = false;
        this.notificationService.showAlert(res.message, 'success');
        this.resetForm();
        this.suggestNextId();
      },
      error: (err) => {
        this.loading = false;
        const msg = err.error?.detail || 'Onboarding failed';
        this.notificationService.showAlert(msg, 'error');
      }
    });
  }

  onEmployeeMasterSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.uploadingMaster = true;
      this.attendanceService.uploadFiles([file]).subscribe({
        next: (res: any) => {
          this.uploadingMaster = false;
          this.notificationService.showAlert(res.message, 'success');
          this.suggestNextId();
        },
        error: (err: any) => {
          this.uploadingMaster = false;
          const errorMsg = err.error?.detail || 'Error uploading employee master.';
          this.notificationService.showAlert(errorMsg, 'error');
        }
      });
    }
  }

  resetForm() {
    this.employee = {
      first_name: '',
      last_name: '',
      full_name: '',
      phone_number: '',
      email: '',
      designation: '',
      emp_id: ''
    };
  }
}
