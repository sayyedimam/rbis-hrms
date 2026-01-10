import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, Chart, registerables } from 'chart.js';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { UploadComponent } from '../upload/upload.component';
import { RouterModule } from '@angular/router';

Chart.register(...registerables);

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, BaseChartDirective, FormsModule, UploadComponent, RouterModule],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit, OnDestroy {
    loading = false;
    hasData = false;
    isAdmin = false;

    // Raw Data Storage
    private rawData: any[] = [];
    private filteredData: any[] = [];

    // Filter Options
    availableDates: string[] = [];
    availableEmps: string[] = [];

    // Selected Filters
    selectedDate: string = '';
    selectedEmp: string = '';

    // Intelligence State
    showTrendChart = true;

    private subs = new Subscription();

    // Shared Options
    public barChartOptions: ChartOptions<'bar'> = {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0, title: { display: true, text: 'Count' } } },
        plugins: { legend: { display: true } }
    };
    public lineChartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true } },
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Hours' } } }
    };
    public pieChartOptions: ChartOptions<'pie'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
    };

    // Chart Data Objects
    public barData: ChartConfiguration<'bar'>['data'] = { labels: [], datasets: [] };
    public lineData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
    public pieData: ChartConfiguration<'pie'>['data'] = { labels: [], datasets: [] };
    public stats = { present: 0, absent: 0, avgHours: 0, label: 'Latest' };

    constructor(
        private attendanceService: AttendanceService,
        public authService: AuthService
    ) { }

    ngOnInit() {
        this.isAdmin = this.authService.getUserRole() === 'SUPER_ADMIN';
        const user = this.authService.currentUser;
        if (!this.isAdmin && user) {
            this.selectedEmp = user.emp_id;
        }
        
        // Fetch data from DB on init
        this.attendanceService.fetchAttendance();

        this.subs.add(this.attendanceService.typeAData$.subscribe(data => this.syncData()));
        this.subs.add(this.attendanceService.typeBData$.subscribe(data => this.syncData()));
        this.subs.add(this.attendanceService.hasData$.subscribe(has => this.hasData = has));

        // Also subscribe to currentUser in case it updates
        this.subs.add(this.authService.currentUser$.subscribe(u => {
            if (!this.isAdmin && u) {
                this.selectedEmp = u.emp_id;
                this.applyFilters();
            }
        }));
    }

    syncData() {
        // Merge A and B data into a single view
        const dataA = this.attendanceService.typeAData;
        const dataB = this.attendanceService.typeBData;
        
        // Use a map to merge records for the same employee/date
        const mergeMap = new Map();
        
        [...dataA, ...dataB].forEach(rec => {
            const key = `${rec.EmpID}_${rec.Date}`;
            if (!mergeMap.has(key)) {
                mergeMap.set(key, { ...rec });
            } else {
                const existing = mergeMap.get(key);
                // Merge details, prefer Type A for durations if available
                existing.In_Duration = existing.In_Duration || rec.In_Duration;
                existing.Out_Duration = existing.Out_Duration || rec.Out_Duration;
                if (rec.Attendance === 'Present') existing.Attendance = 'Present';
            }
        });

        this.rawData = Array.from(mergeMap.values());
        this.updateFilterOptions();
        this.applyFilters();
    }

    ngOnDestroy() {
        this.subs.unsubscribe();
    }

    updateFilterOptions() {
        this.availableDates = [...new Set(this.rawData.map(d => String(d.Date)))].filter(d => d && d !== "null").sort();
        this.availableEmps = [...new Set(this.rawData.map(d => String(d['EmpID'])))].filter(id => id && id !== "null" && id !== "undefined").sort();
    }

    resetFilters() {
        this.selectedDate = '';
        if (this.isAdmin) {
            this.selectedEmp = '';
        } else {
            const user = this.authService.currentUser;
            this.selectedEmp = user?.emp_id || '';
        }
        this.applyFilters();
    }

    applyFilters() {
        let filtered = this.rawData;
        if (this.selectedDate) {
            filtered = filtered.filter(d => String(d.Date) === this.selectedDate);
        }
        if (this.selectedEmp) {
            filtered = filtered.filter(d => String(d['EmpID']) === this.selectedEmp);
        }
        this.filteredData = filtered;
        this.processChartData(filtered);
    }

    private processChartData(data: any[]) {
        if (!data || data.length === 0) {
            this.stats = { present: 0, absent: 0, avgHours: 0, label: 'No Data' };
            this.barData = { labels: [], datasets: [] };
            this.lineData = { labels: [], datasets: [] };
            this.pieData = { labels: [], datasets: [] };
            return;
        }

        const labels = [...new Set(data.map(d => String(d.Date)))].sort();
        this.showTrendChart = labels.length > 1;

        const dailyStats = labels.map(date => {
            const dayRecords = data.filter(d => String(d.Date) === date);
            const present = dayRecords.filter(d => d.Attendance === 'Present').length;
            const absent = dayRecords.filter(d => d.Attendance === 'Absent').length;

            const presentRecords = dayRecords.filter(d => d.Attendance === 'Present');
            const hours = presentRecords.map(r => this.parseDuration(r.In_Duration));
            let avgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (avgH === 0 && present > 0) avgH = 8.0;

            return { date, present, absent, avgH };
        });

        if (this.selectedEmp) {
            const totalPresent = data.filter(d => d.Attendance === 'Present').length;
            const totalAbsent = data.filter(d => d.Attendance === 'Absent').length;
            const hours = data.filter(d => d.Attendance === 'Present').map(r => this.parseDuration(r.In_Duration));
            let totalAvgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (totalAvgH === 0 && totalPresent > 0) totalAvgH = 8.0;

            this.stats = { present: totalPresent, absent: totalAbsent, avgHours: totalAvgH, label: 'Cumulative' };
        } else {
            const latest = dailyStats[dailyStats.length - 1] || { present: 0, absent: 0, avgH: 0 };
            this.stats = { present: latest.present, absent: latest.absent, avgHours: latest.avgH, label: 'Latest Day' };
        }

        this.barData = {
            labels: labels,
            datasets: [{
                data: dailyStats.map(s => s.present),
                label: 'Present',
                backgroundColor: '#4f46e5',
                borderRadius: 6,
                barThickness: labels.length > 10 ? undefined : 30
            }]
        };

        this.lineData = {
            labels: labels,
            datasets: [{
                data: dailyStats.map(s => s.avgH),
                label: 'Avg Hours',
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            }]
        };

        const currentSnapshot = this.selectedEmp ? { present: this.stats.present, absent: this.stats.absent } : (dailyStats[dailyStats.length - 1] || { present: 0, absent: 0 });
        this.pieData = {
            labels: ['Present', 'Absent'],
            datasets: [{
                data: [currentSnapshot.present, currentSnapshot.absent],
                backgroundColor: ['#4f46e5', '#f87171'],
                borderWidth: 0
            }]
        };
    }

    exportToCSV() {
        if (!this.filteredData || this.filteredData.length === 0) return;
        const headers = Object.keys(this.filteredData[0]);
        const csvRows = [
            headers.join(','),
            ...this.filteredData.map(row =>
                headers.map(header => {
                    const val = row[header];
                    return typeof val === 'string' && val.includes(',') ? `"${val}"` : val;
                }).join(',')
            )
        ];
        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        link.setAttribute('href', url);
        link.setAttribute('download', `Attendance_Export_HRMS_${timestamp}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    private parseDuration(d: any): number {
        if (!d) return 0;
        const s = String(d).trim();
        if (s === '' || s === '0' || s.toLowerCase() === 'nan' || s === '00:00' || s === '0:00') return 0;
        try {
            if (s.includes(':')) {
                const parts = s.split(':').map(Number);
                if (parts.length >= 2) return parts[0] + (parts[1] / 60);
            }
            const num = Number(s);
            return isNaN(num) ? 0 : num;
        } catch { return 0; }
    }
}
