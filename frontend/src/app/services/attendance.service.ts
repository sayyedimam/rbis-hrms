import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AttendanceService {
  private apiUrl = 'http://localhost:8000';

  // Subjects for in-memory data state
  private typeADataSubject = new BehaviorSubject<any[]>([]);
  private typeBDataSubject = new BehaviorSubject<any[]>([]);
  private hasDataSubject = new BehaviorSubject<boolean>(false);

  // Observables
  typeAData$ = this.typeADataSubject.asObservable();
  typeBData$ = this.typeBDataSubject.asObservable();
  hasData$ = this.hasDataSubject.asObservable();

  get typeAData() { return this.typeADataSubject.value; }
  get typeBData() { return this.typeBDataSubject.value; }

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

  fetchAttendance(): void {
    this.http.get<any[]>(`${this.apiUrl}/attendance/`).subscribe({
      next: (data) => {
        // Distribute data based on source or type
        // For now, we'll put all into typeA if it has In_Duration, otherwise typeB
        const typeA = data.filter(d => d.in_duration && d.in_duration.includes(':'));
        const typeB = data.filter(d => !d.in_duration || !d.in_duration.includes(':'));
        
        // Map backend fields to frontend expected fields (Shared for both)
        const mappedA = typeA.map(d => ({
          id: d.id,
          Date: d.date,
          EmpID: d.emp_id,
          In_Duration: d.in_duration,
          Out_Duration: d.out_duration,
          Total_Duration: d.total_duration,
          First_In: d.first_in,
          Last_Out: d.last_out,
          Punch_Records: d.punch_records,
          Attendance: d.attendance_status
        }));

        const mappedB = typeB.map(d => ({
          id: d.id,
          Date: d.date,
          EmpID: d.emp_id,
          In_Duration: d.in_duration,
          Out_Duration: d.out_duration,
          Total_Duration: d.total_duration,
          First_In: d.first_in,
          Last_Out: d.last_out,
          Punch_Records: d.punch_records,
          Attendance: d.attendance_status
        }));

        this.typeADataSubject.next(mappedA);
        this.typeBDataSubject.next(mappedB);
        this.checkDataAvailability();
      },
      error: (err) => console.error('Error fetching attendance', err)
    });
  }

  setAttendanceData(type: 'typeA' | 'typeB', data: any[]) {
    if (type === 'typeA') {
      this.typeADataSubject.next(data);
    } else {
      this.typeBDataSubject.next(data);
    }
    this.checkDataAvailability();
  }

  setDataAvailable(available: boolean) {
    this.hasDataSubject.next(available);
  }

  private checkDataAvailability() {
    const hasA = this.typeADataSubject.value.length > 0;
    const hasB = this.typeBDataSubject.value.length > 0;
    this.hasDataSubject.next(hasA || hasB);
  }

  getCurrentData() {
    return {
      typeA: this.typeADataSubject.value,
      typeB: this.typeBDataSubject.value
    };
  }
}
