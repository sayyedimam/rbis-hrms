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

  // UI State
  expandedRequestId: number | null = null;
  expandedExplorerId: number | null = null;

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
    if (this.isHr || this.isCeo) {
      this.loadGeneralExplorer();
    }
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
    const term = this.explorerSearchTerm.trim();
    if (!term) {
      this.notificationService.showAlert('Please enter an Employee ID', 'info');
      return;
    }

    this.searchLoading = true;
    this.explorerData = null;

    this.leaveService.getEmployeeSummary(term).subscribe({
      next: (data) => {
        this.explorerData = data;
        this.searchLoading = false;
      },
      error: (err) => {
        const msg = err.error?.detail || err.message || 'Employee not found';
        this.notificationService.showAlert(msg, 'error');
        this.searchLoading = false;
      }
    });
  }

  loadGeneralExplorer(): void {
    if (this.explorerData && this.explorerSearchTerm) return; // Don't override active search
    
    this.searchLoading = true;
    this.leaveService.getGeneralSummary().subscribe({
      next: (data) => {
        this.explorerData = data;
        this.searchLoading = false;
      },
      error: (err) => {
        this.searchLoading = false;
      }
    });
  }

  clearExplorer(): void {
    this.explorerSearchTerm = '';
    this.loadGeneralExplorer();
  }

  switchTab(tab: any): void {
    this.activeTab = tab;
    this.expandedRequestId = null;
    this.expandedExplorerId = null;
    if (tab === 'explorer') {
      this.loadGeneralExplorer();
    }
  }

  toggleRow(id: number): void {
    this.expandedRequestId = this.expandedRequestId === id ? null : id;
  }

  toggleExplorerRow(id: number): void {
    this.expandedExplorerId = this.expandedExplorerId === id ? null : id;
  }

  getLeaveTypeName(id: number): string {
    return this.leaveTypes.find(t => t.id === id)?.name || 'Unknown';
  }

  applyLeave(): void {
    if (!this.newRequest.leave_type_id || !this.newRequest.start_date || !this.newRequest.end_date || !this.newRequest.reason?.trim()) {
      this.notificationService.showAlert('All fields including reason are mandatory', 'error');
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

  approve(req: any, remarks: string): void {
    if (!remarks?.trim()) {
      this.notificationService.showAlert('Approval remarks are mandatory', 'error');
      return;
    }
    
    if (this.isCeo && req.status === 'APPROVED_BY_HR') {
      this.leaveService.approveCeo({ request_id: req.id, action: 'APPROVE', remarks }).subscribe({
        next: () => {
          this.notificationService.showAlert('Leave approved by CEO', 'success');
          this.loadInitialData();
        },
        error: () => this.notificationService.showAlert('Approval failed', 'error')
      });
    } else if (this.isHr && req.status === 'PENDING') {
      this.leaveService.approveHr({ request_id: req.id, action: 'APPROVE', remarks }).subscribe({
        next: () => {
          this.notificationService.showAlert('Leave approved by HR', 'success');
          this.loadInitialData();
        },
        error: () => this.notificationService.showAlert('Approval failed', 'error')
      });
    }
  }

  reject(req: any, remarks: string): void {
    if (!remarks?.trim()) {
      this.notificationService.showAlert('Rejection remarks are mandatory', 'error');
      return;
    }
    
    if (this.isCeo && req.status === 'APPROVED_BY_HR') {
      this.leaveService.approveCeo({ request_id: req.id, action: 'REJECT', remarks }).subscribe({
        next: () => {
          this.notificationService.showAlert('Leave request rejected by CEO', 'success');
          this.loadInitialData();
        },
        error: () => this.notificationService.showAlert('Rejection failed', 'error')
      });
    } else if (this.isHr && req.status === 'PENDING') {
      this.leaveService.approveHr({ request_id: req.id, action: 'REJECT', remarks }).subscribe({
        next: () => {
          this.notificationService.showAlert('Leave request rejected by HR', 'success');
          this.loadInitialData();
        },
        error: () => this.notificationService.showAlert('Rejection failed', 'error')
      });
    }
  }
}
