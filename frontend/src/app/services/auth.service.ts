import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    emp_id: string;
    email: string;
    role: string;
    full_name?: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000/auth';
  private currentUserSubject = new BehaviorSubject<any>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  get currentUser() {
    return this.currentUserSubject.value;
  }

  constructor(private http: HttpClient) {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      this.currentUserSubject.next(JSON.parse(savedUser));
    }
  }

  signup(userData: { email: string; password: string }): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/signup`, userData);
  }

  verify(verifyData: { email: string; code: string }): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/verify`, verifyData);
  }

  verifyOtp(email: string, otp: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/verify-otp`, { email, code: otp });
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/forgot-password`, null, {
      params: { email }
    });
  }

  resetPassword(email: string, otp: string, newPassword: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/reset-password`, null, {
      params: { email, otp, new_password: newPassword }
    });
  }

  login(credentials: { email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap(res => this.setSession(res))
    );
  }

  logout() {
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
  }

  private setSession(authRes: AuthResponse) {
    // Store the nested user object for easier access
    const sessionData = {
      ...authRes.user,
      token: authRes.access_token
    };
    localStorage.setItem('currentUser', JSON.stringify(sessionData));
    this.currentUserSubject.next(sessionData);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('currentUser');
  }

  getUserRole(): string {
    const user = JSON.parse(localStorage.getItem('currentUser') || '{}');
    return user.role || '';
  }
}
