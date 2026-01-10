import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LeaveService } from '../../services/leave.service';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-leave-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './leave-management.component.html',
  styleUrls: ['./leave-management.component.css']
})
export class LeaveManagementComponent implements OnInit {
  activeTab: 'balance' | 'apply' | 'history' | 'approvals' | 'explorer' = 'balance';
  
  leaveTypes: any[] = [];
  balances: any[] = [];
  myRequests: any[] = [];
  pendingRequests: any[] = [];
  
  // Explorer
  explorerSearchTerm: string = '';
  explorerData: any = null;
  searchLoading: boolean = false;

  // Application Form
  newRequest = {
    leave_type_id: null,
    start_date: '',
    end_date: '',
    reason: ''
  };

  // Roles
  isHr = false;
  isCeo = false;

  constructor(
    private leaveService: LeaveService,
    private authService: AuthService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    const role = this.authService.getUserRole();
    this.isHr = role === 'HR' || role === 'SUPER_ADMIN';
    this.isCeo = role === 'CEO' || role === 'SUPER_ADMIN';
    
    this.loadInitialData();
  }

  loadInitialData(): void {
    this.leaveService.getLeaveTypes().subscribe(data => this.leaveTypes = data);
    this.leaveService.getBalances().subscribe(data => this.balances = data);
    this.leaveService.getMyRequests().subscribe(data => this.myRequests = data);
    
    this.pendingRequests = []; // Reset before loading
    if (this.isHr) this.loadHrPending();
    if (this.isCeo) this.loadCeoPending();
  }

  loadHrPending(): void {
    this.leaveService.getHrPending().subscribe(data => {
      // Append only if not already present
      const existingIds = new Set(this.pendingRequests.map(r => r.id));
      const news = data.filter(r => !existingIds.has(r.id));
      this.pendingRequests = [...this.pendingRequests, ...news];
    });
  }

  loadCeoPending(): void {
    this.leaveService.getCeoPending().subscribe(data => {
      // Append only if not already present
      const existingIds = new Set(this.pendingRequests.map(r => r.id));
      const news = data.filter(r => !existingIds.has(r.id));
      this.pendingRequests = [...this.pendingRequests, ...news];
    });
  }

  // --- Explorer ---
  searchEmployee(): void {
    if (!this.explorerSearchTerm.trim()) {
      this.notificationService.showAlert('Please enter an Employee ID', 'info');
      return;
    }

    this.searchLoading = true;
    this.explorerData = null;

    this.leaveService.getEmployeeSummary(this.explorerSearchTerm).subscribe({
      next: (data) => {
        this.explorerData = data;
        this.searchLoading = false;
      },
      error: (err) => {
        this.notificationService.showAlert(err.error?.detail || 'Employee not found', 'error');
        this.searchLoading = false;
      }
    });
  }

  clearExplorer(): void {
    this.explorerSearchTerm = '';
    this.explorerData = null;
  }

  switchTab(tab: any): void {
    this.activeTab = tab;
  }

  getLeaveTypeName(id: number): string {
    return this.leaveTypes.find(t => t.id === id)?.name || 'Unknown';
  }

  applyLeave(): void {
    if (!this.newRequest.leave_type_id || !this.newRequest.start_date || !this.newRequest.end_date) {
      this.notificationService.showAlert('Please fill all required fields', 'error');
      return;
    }
    
    this.leaveService.applyLeave(this.newRequest).subscribe({
      next: () => {
        this.notificationService.showAlert('Leave applied successfully!', 'success');
        this.newRequest = { leave_type_id: null, start_date: '', end_date: '', reason: '' };
        this.loadInitialData();
        this.activeTab = 'history';
      },
      error: (err) => this.notificationService.showAlert(err.error?.detail || 'Application failed', 'error')
    });
  }

  approve(req: any, remarks: string = ''): void {
    const isSuper = this.authService.getUserRole() === 'SUPER_ADMIN';
    
    if (req.status === 'PENDING' && (this.isHr || isSuper)) {
      this.leaveService.approveHr({ request_id: req.id, action: 'APPROVE', remarks }).subscribe({
        next: () => {
          this.notificationService.showAlert(isSuper ? 'Advanced to CEO level' : 'Approved by HR', 'success');
          this.loadInitialData();
        },
        error: (err) => this.notificationService.showAlert('Action failed', 'error')
      });
    } else if (req.status === 'APPROVED_BY_HR' && (this.isCeo || isSuper)) {
      this.leaveService.approveCeo({ request_id: req.id, action: 'APPROVE', remarks }).subscribe({
        next: () => {
          this.notificationService.showAlert('Final Approval Granted', 'success');
          this.loadInitialData();
        },
        error: (err) => this.notificationService.showAlert('Action failed', 'error')
      });
    }
  }

  reject(req: any, remarks: string = ''): void {
    const isSuper = this.authService.getUserRole() === 'SUPER_ADMIN';
    const action = (req.status === 'PENDING' && (this.isHr || isSuper)) 
      ? this.leaveService.approveHr.bind(this.leaveService) 
      : this.leaveService.approveCeo.bind(this.leaveService);
    
    action({ request_id: req.id, action: 'REJECT', remarks }).subscribe({
      next: () => {
        this.notificationService.showAlert(isSuper ? 'Rejected by Super Admin' : 'Request rejected', 'info');
        this.loadInitialData();
      },
      error: (err) => this.notificationService.showAlert('Action failed', 'error')
    });
  }
}
