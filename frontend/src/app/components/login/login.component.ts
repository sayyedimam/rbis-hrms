import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginData = {
    email: '',
    password: ''
  };
  
  // Forgot Password Flow
  showForgotPasswordModal = false;
  forgotPasswordStep: 'email' | 'otp' | 'success' = 'email';
  forgotEmail = '';
  resetOtp = '';
  newPassword = '';
  confirmNewPassword = '';
  
  error = '';
  loading = false;

  constructor(private authService: AuthService, private router: Router) {}

  onLogin() {
    this.error = '';
    this.authService.login(this.loginData).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.error = err.error?.detail || 'Login failed. Please check your credentials.';
      }
    });
  }

  openForgotPassword() {
    this.showForgotPasswordModal = true;
    this.forgotPasswordStep = 'email';
    this.forgotEmail = '';
    this.resetOtp = '';
    this.newPassword = '';
    this.confirmNewPassword = '';
    this.error = '';
  }

  closeForgotPassword() {
    this.showForgotPasswordModal = false;
    this.error = '';
  }

  sendResetOtp() {
    this.error = '';
    this.loading = true;
    this.authService.forgotPassword(this.forgotEmail).subscribe({
      next: (res) => {
        this.loading = false;
        this.forgotPasswordStep = 'otp';
        alert(res.message || 'OTP sent to your email');
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Failed to send OTP';
      }
    });
  }

  resetPassword() {
    this.error = '';
    
    if (this.newPassword !== this.confirmNewPassword) {
      this.error = 'Passwords do not match';
      return;
    }

    if (this.newPassword.length < 6) {
      this.error = 'Password must be at least 6 characters';
      return;
    }

    this.loading = true;
    this.authService.resetPassword(this.forgotEmail, this.resetOtp, this.newPassword).subscribe({
      next: (res) => {
        this.loading = false;
        this.forgotPasswordStep = 'success';
        setTimeout(() => {
          this.closeForgotPassword();
        }, 2000);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Failed to reset password';
      }
    });
  }
}
