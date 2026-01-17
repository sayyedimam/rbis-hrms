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

  private rawData: any[] = [];
  private subs = new Subscription();

  constructor(
    private attendanceService: AttendanceService,
    public authService: AuthService,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    const role = this.authService.getUserRole();
    this.isAdmin = role === 'SUPER_ADMIN';
    this.isHr = role === 'HR' || this.isAdmin;
    this.isCeo = role === 'CEO' || this.isAdmin;

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
        if (rec.Attendance === 'Present') existing.Attendance = 'Present';
      }
    });
    this.rawData = Array.from(mergeMap.values());
  }

  get editBoardData() {
    let d = this.rawData;
    if (this.editSearchEmpId.trim()) {
      const term = this.editSearchEmpId.trim().toLowerCase();
      d = d.filter(r => 
        (r.EmpID && r.EmpID.toLowerCase() === term) || 
        (r.Employee_Name && r.Employee_Name.toLowerCase().includes(term))
      );
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
      error: () => this.notificationService.showAlert('Delete failed', 'error')
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
      error: () => {
        this.isSaving = false;
        this.notificationService.showAlert('Update failed', 'error');
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
}
