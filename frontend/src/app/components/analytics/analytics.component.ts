import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';
import { LeaveService } from '../../services/leave.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.css'
})
export class AnalyticsComponent implements OnInit, OnDestroy {
  searchTerm = '';
  startDate = '';
  endDate = '';
  searchPerformed = false;
  loading = false;
  
  employeeStats: any = null;
  attendanceHistory: any[] = [];
  
  private rawData: any[] = [];
  private subs = new Subscription();

  holidays: any[] = [];

  constructor(
    private attendanceService: AttendanceService,
    private authService: AuthService,
    private notificationService: NotificationService,
    private leaveService: LeaveService
  ) {}

  canViewAll = false;

  ngOnInit() {
    this.canViewAll = this.authService.isAtLeastHR();
    
    // For non-admin employees, default searchTerm to their own ID
    if (!this.canViewAll && this.authService.currentUser?.emp_id) {
        this.searchTerm = this.authService.currentUser.emp_id;
    }

    // Fetch holidays
    this.leaveService.getHolidays().subscribe(data => {
        this.holidays = data;
        if (this.attendanceService.attendanceData.length > 0) this.syncData();
    });

    this.attendanceService.fetchAttendance();
    this.subs.add(this.attendanceService.attendanceData$.subscribe(() => this.syncData()));
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  syncData() {
    this.rawData = this.attendanceService.attendanceData;
    if (this.searchPerformed) {
       this.performSearch(); // Refresh results if data updates
    }
  }

  performSearch() {
    const hasTerm = this.searchTerm.trim();
    const hasDateRange = this.startDate && this.endDate;

    if (!hasTerm && !hasDateRange) {
      this.notificationService.showAlert('Please enter Employee ID/Name or select a Date Range', 'info');
      return;
    }

    if (hasTerm && !hasTerm.toLowerCase().startsWith('rbis') && /^\d/.test(hasTerm)) {
        this.notificationService.showAlert('Employee IDs must start with "RBIS" (e.g. RBIS0059)', 'info');
        this.loading = false;
        return;
    }

    if (hasTerm && hasTerm.length < 3 && !/^\d/.test(hasTerm)) {
        this.notificationService.showAlert('Please enter at least 3 characters for a name search', 'info');
        this.loading = false;
        return;
    }

    this.loading = true;
    this.searchPerformed = true;

    const term = this.searchTerm.toLowerCase();
    let filtered = this.rawData;

    if (hasTerm) {
        filtered = filtered.filter(r => 
            (r.EmpID && r.EmpID.toLowerCase() === term) || 
            (r.Employee_Name && r.Employee_Name.toLowerCase().includes(term))
        );
    }

    if (this.startDate && this.endDate) {
      filtered = filtered.filter(r => {
        const d = String(r.Date).split('T')[0];
        return d >= this.startDate && d <= this.endDate;
      });
    }

    this.attendanceHistory = filtered.sort((a, b) => b.Date.localeCompare(a.Date));
    
    if (filtered.length > 0) {
      const present = filtered.filter(r => r.Attendance === 'Present').length;
      const absent = filtered.filter(r => r.Attendance === 'Absent').length;
      const leave = filtered.filter(r => r.Attendance === 'On Leave').length;
      
      const isSingleEmp = (this.searchTerm.trim() || !this.canViewAll) && filtered.every(r => r.EmpID === filtered[0].EmpID);
      
      this.employeeStats = {
        total: filtered.length,
        present,
        absent,
        leave,
        name: isSingleEmp 
          ? (filtered.find(r => r.Employee_Name)?.Employee_Name || filtered[0].EmpID)
          : (this.canViewAll ? 'Organization Summary' : 'My Attendance Summary'),
        id: isSingleEmp ? filtered[0].EmpID : 'Multiple Employees'
      };
    } else {
      this.employeeStats = null;
    }

    this.loading = false;
  }

  clearSearch() {
    this.searchTerm = '';
    this.startDate = '';
    this.endDate = '';
    this.searchPerformed = false;
    this.attendanceHistory = [];
    this.employeeStats = null;
  }
}
