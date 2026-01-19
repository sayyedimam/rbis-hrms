import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LeaveService {
  private apiUrl = 'http://localhost:8000/leave';

  constructor(private http: HttpClient) { }

  getLeaveTypes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/types`);
  }

  getBalances(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/balances`);
  }

  getHolidays(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/holidays`);
  }

  addHoliday(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/holidays`, data);
  }

  updateHoliday(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/holidays/${id}`, data);
  }

  deleteHoliday(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/holidays/${id}`);
  }


  applyLeave(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/apply`, data);
  }

  getMyRequests(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/my-requests`);
  }

  getHrPending(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/hr/pending`);
  }

  getCeoPending(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/ceo/pending`);
  }

  approveHr(data: { request_id: number, action: string, remarks?: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/approve-hr`, data);
  }

  approveCeo(data: { request_id: number, action: string, remarks?: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/approve-ceo`, data);
  }

  getEmployeeSummary(empId: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/admin/employee-summary/${empId}`);
  }

  getGeneralSummary(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/admin/summary`);
  }
}
