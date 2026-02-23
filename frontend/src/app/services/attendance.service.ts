import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable, Subject, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AttendanceService {
  private apiUrl = environment.apiUrl;

  // Subjects for in-memory data state
  private attendanceDataSubject = new BehaviorSubject<any[]>([]);
  private hasDataSubject = new BehaviorSubject<boolean>(false);

  // Observables
  attendanceData$ = this.attendanceDataSubject.asObservable();
  hasData$ = this.hasDataSubject.asObservable();

  get attendanceData() { return this.attendanceDataSubject.value; }

  // Backward compatibility for old components (will return filtered versions of the same stream)
  get typeAData() { return this.attendanceDataSubject.value.filter(d => d.In_Duration && d.In_Duration.includes(':')); }
  get typeBData() { return this.attendanceDataSubject.value.filter(d => !d.In_Duration || !d.In_Duration.includes(':')); }
  typeAData$ = this.attendanceData$;
  typeBData$ = this.attendanceData$;

  constructor(private http: HttpClient) { }

  uploadFile(file: File, type: 'a' | 'b'): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/upload/${type}`, formData);
  }

  uploadFiles(files: File[]): Observable<any> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return this.http.post(`${this.apiUrl}/attendance/upload/files`, formData);
  }

  getRecords(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/records/`);
  }

  downloadRecord(fileId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/records/download/${fileId}`, { responseType: 'blob' });
  }

  getProfile(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/profile/`);
  }

  getNextId(): Observable<{ next_id: string }> {
    return this.http.get<{ next_id: string }>(`${this.apiUrl}/onboarding/next-id`);
  }

  onboardEmployee(employeeData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/onboarding/onboard`, employeeData);
  }

  updateAttendance(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/attendance/${id}`, data);
  }

  deleteAttendance(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/attendance/${id}`);
  }

  fetchAttendance(startDate?: string, endDate?: string): void {
    let params = {};
    if (startDate) params = { ...params, start_date: startDate };
    if (endDate) params = { ...params, end_date: endDate };

    this.http.get<any[]>(`${this.apiUrl}/attendance/`, { params }).subscribe({
      next: (data) => {
        // Map backend fields to frontend expected fields
        const mappedData = data.map(d => ({
          id: d.id,
          Date: d.date,
          EmpID: d.emp_id,
          In_Duration: d.in_duration,
          Out_Duration: d.out_duration,
          Total_Duration: d.total_duration,
          First_In: d.first_in,
          Last_Out: d.last_out,
          Punch_Records: d.punch_records,
          Attendance: d.attendance_status,
          Employee_Name: d.employee_name,
          has_duration_details: d.has_duration_details
        }));

        this.attendanceDataSubject.next(mappedData);
        this.checkDataAvailability();
      },
      error: (err) => console.error('Error fetching attendance', err)
    });
  }

  setAttendanceData(data: any[]) {
    this.attendanceDataSubject.next(data);
    this.checkDataAvailability();
  }

  setDataAvailable(available: boolean) {
    this.hasDataSubject.next(available);
  }

  private checkDataAvailability() {
    this.hasDataSubject.next(this.attendanceDataSubject.value.length > 0);
  }

  getCurrentData() {
    return {
      attendance: this.attendanceDataSubject.value
    };
  }
}
