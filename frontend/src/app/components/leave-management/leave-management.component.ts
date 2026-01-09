import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-leave-management',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './leave-management.component.html',
  styleUrls: ['./leave-management.component.css']
})
export class LeaveManagementComponent {
  isAdmin = false;
  constructor(public authService: AuthService) {
    this.isAdmin = this.authService.getUserRole() === 'SUPER_ADMIN';
  }
}
