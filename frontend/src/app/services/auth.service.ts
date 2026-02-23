import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
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
  private apiUrl = `${environment.apiUrl}/auth`;
  private currentUserSubject = new BehaviorSubject<any>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  
  // High-level role-based subjects/observables
  private userRoleSubject = new BehaviorSubject<string>(this.getInitialRole());
  public userRole$ = this.userRoleSubject.asObservable();

  get currentUser() {
    return this.currentUserSubject.value;
  }

  get userRole() {
    return this.userRoleSubject.value;
  }

  constructor(private http: HttpClient) {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      const user = JSON.parse(savedUser);
      this.currentUserSubject.next(user);
      this.userRoleSubject.next(user.role || '');
    }
  }

  private getInitialRole(): string {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      try {
        return JSON.parse(savedUser).role || '';
      } catch (e) {
        return '';
      }
    }
    return '';
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
    this.userRoleSubject.next('');
  }

  private setSession(authRes: AuthResponse) {
    const sessionData = {
      ...authRes.user,
      token: authRes.access_token
    };
    localStorage.setItem('currentUser', JSON.stringify(sessionData));
    // Update role FIRST so downstream subscribers see correct role immediately
    this.userRoleSubject.next(sessionData.role);
    this.currentUserSubject.next(sessionData);
  }

  isLoggedIn(): boolean {
    return !!this.currentUser;
  }

  getUserRole(): string {
    return this.userRole;
  }

  hasRole(roles: string | string[]): boolean {
    const currentRole = this.userRole;
    if (Array.isArray(roles)) {
      return roles.includes(currentRole);
    }
    return currentRole === roles;
  }

  isSuperAdmin(): boolean {
    return this.userRole === 'SUPER_ADMIN';
  }

  isCeo(): boolean {
    return this.userRole === 'CEO';
  }

  isHrOrAdmin(): boolean {
    return ['SUPER_ADMIN', 'HR'].includes(this.userRole);
  }

  isAtLeastHR(): boolean {
    return ['SUPER_ADMIN', 'HR', 'CEO'].includes(this.userRole);
  }
}
