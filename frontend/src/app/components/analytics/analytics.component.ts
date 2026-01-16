import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';

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

  constructor(
    private attendanceService: AttendanceService,
    private authService: AuthService,
    private notificationService: NotificationService
  ) {}

  canViewAll = false;

  ngOnInit() {
    const role = this.authService.currentUser?.role;
    this.canViewAll = role === 'SUPER_ADMIN' || role === 'HR' || role === 'CEO';

    this.attendanceService.fetchAttendance();
    this.subs.add(this.attendanceService.typeAData$.subscribe(() => this.syncData()));
    this.subs.add(this.attendanceService.typeBData$.subscribe(() => this.syncData()));
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  syncData() {
    const dataA = this.attendanceService.typeAData;
    const dataB = this.attendanceService.typeBData;
    const mergeMap = new Map();
    
    [...dataA, ...dataB].forEach(rec => {
      const key = `${rec.EmpID}_${rec.Date}`;
      if (!mergeMap.has(key)) {
        mergeMap.set(key, { ...rec });
      } else {
        const existing = mergeMap.get(key);
        existing.In_Duration = existing.In_Duration || rec.In_Duration;
        existing.Out_Duration = existing.Out_Duration || rec.Out_Duration;
        existing.Total_Duration = existing.Total_Duration || rec.Total_Duration;
        if (rec.Attendance === 'Present') existing.Attendance = 'Present';
      }
    });
    this.rawData = Array.from(mergeMap.values()).filter((rec: any) => {
      const date = new Date(rec.Date);
      if (date.getDay() === 0) { // 0 is Sunday
        return rec.Attendance === 'Present';
      }
      return true;
    });
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
      
      const isSingleEmp = this.searchTerm.trim() && filtered.every(r => r.EmpID === filtered[0].EmpID);
      
      this.employeeStats = {
        total: filtered.length,
        present,
        absent,
        leave,
        name: isSingleEmp 
          ? (filtered.find(r => r.Employee_Name)?.Employee_Name || filtered[0].EmpID)
          : 'Organization Summary',
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
