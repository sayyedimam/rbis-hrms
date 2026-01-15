import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin.service';
import { NotificationService } from '../../services/notification.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-employee-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './employee-management.component.html',
  styleUrls: ['./employee-management.component.css']
})
export class EmployeeManagementComponent implements OnInit {
  employees: any[] = [];
  filteredEmployees: any[] = [];
  searchTerm: string = '';
  editingEmployee: any = null;
  canEdit: boolean = false;

  constructor(
    private adminService: AdminService,
    private notificationService: NotificationService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const role = this.authService.getUserRole();
    this.canEdit = role === 'SUPER_ADMIN' || role === 'CEO';
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.adminService.getEmployees().subscribe({
      next: (data) => {
        this.employees = data.sort((a, b) => {
            const idA = a.emp_id || '';
            const idB = b.emp_id || '';
            return idA.localeCompare(idB, undefined, { numeric: true, sensitivity: 'base' });
        });
        this.filterEmployees();
      },
      error: (err) => this.notificationService.showAlert('Failed to load employees', 'error')
    });
  }

  filterEmployees(): void {
    if (!this.searchTerm) {
      this.filteredEmployees = this.employees;
    } else {
      const term = this.searchTerm.toLowerCase();
      this.filteredEmployees = this.employees.filter(e => 
        (e.full_name && e.full_name.toLowerCase().includes(term)) || 
        (e.emp_id && e.emp_id.toLowerCase().includes(term)) ||
        (e.email && e.email.toLowerCase().includes(term)) ||
        (e.phone_number && e.phone_number.toLowerCase().includes(term)) ||
        (e.designation && e.designation.toLowerCase().includes(term))
      );
    }
  }

  editEmployee(emp: any): void {
    this.editingEmployee = { ...emp };
  }

  cancelEdit(): void {
    this.editingEmployee = null;
  }

  saveEmployee(): void {
    if (this.editingEmployee) {
      this.adminService.updateEmployee(this.editingEmployee.id, this.editingEmployee).subscribe({
        next: () => {
          this.notificationService.showAlert('Employee updated successfully', 'success');
          this.editingEmployee = null;
          this.loadEmployees();
        },
        error: (err) => this.notificationService.showAlert(err.error?.detail || 'Update failed', 'error')
      });
    }
  }

  deleteEmployee(id: number): void {
    if (confirm('Are you sure you want to delete this employee? Information will be permanently removed.')) {
      this.adminService.deleteEmployee(id).subscribe({
        next: () => {
          this.notificationService.showAlert('Employee record deleted', 'success');
          this.loadEmployees();
        },
        error: (err) => this.notificationService.showAlert('Delete failed', 'error')
      });
    }
  }
}
