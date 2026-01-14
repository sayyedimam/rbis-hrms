import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const user = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const token = user.token;

    let authReq = req;
    if (token) {
      authReq = req.clone({
        headers: req.headers.set('Authorization', `Bearer ${token}`)
      });
    }

    return next.handle(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          // Session expired or unauthorized
          console.log('Session expired. Redirecting to login...');
          
          // Clear user data
          localStorage.removeItem('currentUser');
          
          // Redirect to login
          this.router.navigate(['/login']);
        }
        
        // Handle other errors
        if (error.status === 403) {
          console.error('Access forbidden:', error.message);
        }
        
        if (error.status === 500) {
          console.error('Server error:', error.message);
        }
        
        return throwError(() => error);
      })
    );
  }
}
