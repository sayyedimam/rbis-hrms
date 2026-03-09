import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { UploadComponent } from '../upload/upload.component';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-attendance-operations',
  standalone: true,
  imports: [CommonModule, FormsModule, UploadComponent],
  templateUrl: './attendance-operations.component.html',
  styleUrl: './attendance-operations.component.css'
})
export class AttendanceOperationsComponent implements OnInit, OnDestroy {
  isAdmin = false;
  isHr = false;
  isCeo = false;
  
  // Edit State
  isEditMode = false;
  editSearchEmpId = '';
  fromDate = '';
  toDate = '';
  editingRecord: any = null;
  isSaving = false;

  // Disambiguation Search State
  matchingEmployees: any[] = [];
  showEmployeeDropdown = false;
  searchNoResults = false;
  selectedEmpId = '';

  private rawData: any[] = [];
  private subs = new Subscription();

  constructor(
    private attendanceService: AttendanceService,
    public authService: AuthService,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    this.isAdmin = this.authService.isSuperAdmin();
    this.isHr = this.authService.isAtLeastHR();
    this.isCeo = this.authService.hasRole('CEO') || this.isAdmin;

    this.attendanceService.fetchAttendance();
    this.subs.add(this.attendanceService.attendanceData$.subscribe(() => this.syncData()));
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  syncData() {
    this.rawData = this.attendanceService.attendanceData;
  }

  get editBoardData() {
    let d = this.rawData;
    if (this.editSearchEmpId.trim()) {
      const term = this.editSearchEmpId.trim().toLowerCase();
      
      // Check for multiple matches if no specific employee selected
      if (!this.selectedEmpId) {
        const matches = this.rawData.reduce((acc: any[], r: any) => {
          if ((r.EmpID && r.EmpID.toLowerCase() === term) || (r.Employee_Name && r.Employee_Name.toLowerCase().includes(term))) {
            if (!acc.find(a => a.EmpID === r.EmpID)) {
              acc.push({ EmpID: r.EmpID, Name: r.Employee_Name || 'Unknown' });
            }
          }
          return acc;
        }, []);

        if (matches.length > 1) {
          this.matchingEmployees = matches.sort((a, b) => a.Name.localeCompare(b.Name));
          this.showEmployeeDropdown = true;
          this.searchNoResults = false;
          return []; // Don't show mixed data
        }
      }

      this.showEmployeeDropdown = false;
      const idToMatch = this.selectedEmpId || term;
      const prevLength = d.length;
      d = d.filter(r => 
        (r.EmpID && r.EmpID.toLowerCase() === idToMatch) || 
        (!this.selectedEmpId && r.Employee_Name && r.Employee_Name.toLowerCase().includes(term))
      );
      
      this.searchNoResults = d.length === 0 && !!this.editSearchEmpId;
    } else {
      this.showEmployeeDropdown = false;
      this.searchNoResults = false;
      this.selectedEmpId = '';
    }
    if (this.fromDate) {
      const start = this.fromDate;
      const end = this.toDate || this.fromDate;
      d = d.filter(r => {
        const dateStr = String(r.Date).split('T')[0];
        return dateStr >= start && dateStr <= end;
      });
    }
    if (!this.editSearchEmpId && !this.fromDate) {
      return d.slice(0, 50); 
    }
    return d;
  }

  toggleEditMode() {
    this.isEditMode = !this.isEditMode;
    // Reset search and date filters when closing the console
    if (!this.isEditMode) {
      this.editSearchEmpId = '';
      this.fromDate = '';
      this.toDate = '';
      this.matchingEmployees = [];
      this.showEmployeeDropdown = false;
      this.searchNoResults = false;
      this.selectedEmpId = '';
    }
  }

  openEditModal(record: any) {
    this.editingRecord = { ...record };
  }

  closeEditModal() {
    this.editingRecord = null;
  }

  deleteRecord(id: number) {
    if (!confirm('Are you sure you want to delete this record?')) return;
    this.attendanceService.deleteAttendance(id).subscribe({
      next: () => {
        this.notificationService.showAlert('Record deleted', 'success');
        this.attendanceService.fetchAttendance();
      },
      error: (err) => this.notificationService.showAlert(err.error?.detail || 'Delete failed', 'error')
    });
  }

  saveRecord() {
    if (!this.editingRecord) return;
    if (!this.editingRecord.First_In) this.editingRecord.First_In = '00:00';
    if (!this.editingRecord.Last_Out) this.editingRecord.Last_Out = '00:00';
    
    const isValidTime = (t: any) => !t || /^([0-1]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$/.test(String(t).trim());

    if (!isValidTime(this.editingRecord.First_In) || !isValidTime(this.editingRecord.Last_Out)) {
      this.notificationService.showAlert('Invalid time format', 'error');
      return;
    }

    this.isSaving = true;
    const fin = this.editingRecord.First_In;
    const lout = this.editingRecord.Last_Out;

    if (fin === '00:00' && lout === '00:00') {
      this.editingRecord.Attendance = 'Absent';
    } else if (fin !== '00:00' && lout !== '00:00') {
      this.editingRecord.Attendance = 'Present';
    }

    const payload = {
      first_in: this.editingRecord.First_In,
      last_out: this.editingRecord.Last_Out,
      in_duration: this.editingRecord.In_Duration,
      out_duration: this.editingRecord.Out_Duration,
      attendance_status: this.editingRecord.Attendance
    };

    this.attendanceService.updateAttendance(this.editingRecord.id, payload).subscribe({
      next: () => {
        this.notificationService.showAlert('Record updated successfully', 'success');
        this.isSaving = false;
        this.closeEditModal();
        this.attendanceService.fetchAttendance();
      },
      error: (err) => {
        this.isSaving = false;
        this.notificationService.showAlert(err.error?.detail || 'Update failed', 'error');
      }
    });
  }

  exportToCSV() {
    if (this.rawData.length === 0) return;
    const exportHeaders = ['Date', 'empID', 'first In', 'Last out', 'In duration', 'out duration', 'Attendance', 'total office duration'];
    const csvRows = [
      exportHeaders.join(','),
      ...this.rawData.map(row => [
        row.Date, row.EmpID, row['First_In'] || '--:--', row['Last_Out'] || '--:--', 
        row.In_Duration, row.Out_Duration, row.Attendance, row['Total_Duration'] || '--:--'
      ].map(val => String(val).includes(',') ? `"${val}"` : val).join(','))
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `Attendance_Operations_Export_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  selectEmployee(emp: any) {
    this.selectedEmpId = emp.EmpID;
    this.editSearchEmpId = emp.Name;
    this.showEmployeeDropdown = false;
    this.matchingEmployees = [];
  }

  onSearchChange() {
    this.selectedEmpId = '';
    this.showEmployeeDropdown = false;
    this.searchNoResults = false;
  }
}
