import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-role-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './role-management.component.html',
  styleUrls: ['./role-management.component.css']
})
export class RoleManagementComponent implements OnInit {
  employees: any[] = [];
  filteredEmployees: any[] = [];
  searchTerm: string = '';
  loading: boolean = false;
  roles: string[] = ['CEO', 'HR', 'EMPLOYEE'];

  constructor(
    private adminService: AdminService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.loading = true;
    this.adminService.getEmployees().subscribe({
      next: (data) => {
        this.employees = data;
        this.applyFilter();
        this.loading = false;
      },
      error: (err) => {
        this.notificationService.showAlert('Failed to load employees', 'error');
        this.loading = false;
      }
    });
  }

  applyFilter(): void {
    if (!this.searchTerm.trim()) {
      this.filteredEmployees = [...this.employees];
    } else {
      const term = this.searchTerm.toLowerCase();
      this.filteredEmployees = this.employees.filter(emp => 
        emp.emp_id?.toLowerCase().includes(term) || 
        emp.email?.toLowerCase().includes(term) ||
        emp.full_name?.toLowerCase().includes(term)
      );
    }
  }

  updateRole(employee: any, newRole: string): void {
    if (confirm(`Are you sure you want to change the role of ${employee.full_name || employee.email} to ${newRole}?`)) {
      this.adminService.updateEmployee(employee.id, { role: newRole }).subscribe({
        next: () => {
          this.notificationService.showAlert(`Role updated successfully for ${employee.emp_id}`, 'success');
          employee.role = newRole; // Update local state
        },
        error: (err) => {
          const errMsg = err.error?.detail || 'Failed to update role';
          this.notificationService.showAlert(errMsg, 'error');
        }
      });
    } else {
      // Reset the select value to previous role if cancelled
      this.loadEmployees();
    }
  }
}
