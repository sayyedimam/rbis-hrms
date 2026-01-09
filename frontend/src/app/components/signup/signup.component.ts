import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  signupData = {
    email: '',
    password: '',
    confirmPassword: ''
  };
  verificationData = {
    email: '',
    code: ''
  };
  
  isVerificationStep = false;
  error = '';
  loading = false;

  constructor(private authService: AuthService, private router: Router) {}

  onSignupRequest() {
    this.error = '';
    if (this.signupData.password !== this.signupData.confirmPassword) {
      this.error = 'Passwords do not match';
      return;
    }

    this.loading = true;
    this.authService.signup({
      email: this.signupData.email,
      password: this.signupData.password
    }).subscribe({
      next: (res) => {
        this.loading = false;
        this.isVerificationStep = true;
        this.verificationData.email = this.signupData.email;
        alert(res.message);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Signup failed. Please try again.';
      }
    });
  }

  onVerify() {
    this.error = '';
    this.loading = true;
    this.authService.verify(this.verificationData).subscribe({
      next: () => {
        this.loading = false;
        alert('Verification successful! Please login.');
        this.router.navigate(['/login']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Verification failed.';
      }
    });
  }
}
