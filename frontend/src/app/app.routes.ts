import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { SignupComponent } from './components/signup/signup.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { OnboardingComponent } from './components/onboarding/onboarding.component';
import { RecordsComponent } from './components/records/records.component';
import { ProfileComponent } from './components/profile/profile.component';
import { LeaveManagementComponent } from './components/leave-management/leave-management.component';
import { EmployeeManagementComponent } from './components/employee-management/employee-management.component';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [AuthGuard] },
  { path: 'onboarding', component: OnboardingComponent, canActivate: [AuthGuard] },
  { path: 'records', component: RecordsComponent, canActivate: [AuthGuard] },
  { path: 'employee-management', component: EmployeeManagementComponent, canActivate: [AuthGuard] },
  { path: 'profile', component: ProfileComponent, canActivate: [AuthGuard] },
  { path: 'leave-management', component: LeaveManagementComponent, canActivate: [AuthGuard] },
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: '/dashboard' }
];
