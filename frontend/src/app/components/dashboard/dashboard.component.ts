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
import { NotificationService } from '../../services/notification.service';

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
    
    // Edit State
    editingRecord: any = null;
    isSaving = false;

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

    public pieChartOptions: ChartOptions<'pie'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
    };

    // Chart Data Objects
    public barData: ChartConfiguration<'bar'>['data'] = { labels: [], datasets: [] };
    public lineData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
    public pieData: ChartConfiguration<'pie'>['data'] = { labels: [], datasets: [] };
    public stats = { 
        present: 0, 
        absent: 0, 
        onLeave: 0,
        avgHours: 0, 
        label: 'Latest', 
        firstIn: '', 
        lastOut: '',
        inDuration: '',
        outDuration: '',
        totalDuration: ''
    };

    public barChartOptions: ChartOptions<'bar'> = {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0, title: { display: true, text: 'Count' } } },
        plugins: { 
            legend: { display: true },
            tooltip: {
                callbacks: {
                    footer: (tooltipItems: any) => {
                        const date = tooltipItems[0].label;
                        if (this.selectedEmp) {
                            const rec = this.rawData.find(d => String(d.Date) === date && String(d.EmpID) === this.selectedEmp);
                            if (rec) {
                                return [
                                    `In: ${rec.First_In || '--:--'}`,
                                    `Out: ${rec.Last_Out || '--:--'}`,
                                    `Duration: ${rec.Total_Duration || '--:--'}`
                                ].join('\n');
                            }
                        }
                        return '';
                    }
                }
            }
        }
    };

    public lineChartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true } },
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Hours' } } }
    };

    constructor(
        private attendanceService: AttendanceService,
        public authService: AuthService,
        private notificationService: NotificationService
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
        const today = new Date().toISOString().split('T')[0];
        
        this.availableDates = [...new Set(this.rawData.map(d => String(d.Date)))]
            .filter(d => d && d !== "null" && d <= today)
            .sort();
            
        this.availableEmps = [...new Set(this.rawData.map(d => String(d['EmpID'])))]
            .filter(id => id && id !== "null" && id !== "undefined")
            .sort();
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
        const today = new Date().toISOString().split('T')[0];
        let filtered = this.rawData.filter(d => String(d.Date) <= today);
        
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
            this.stats = { 
                present: 0, absent: 0, onLeave: 0, avgHours: 0, label: 'No Data', 
                firstIn: '--:--', lastOut: '--:--', inDuration: '--:--', outDuration: '--:--', totalDuration: '00:00' 
            };
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
            const onLeave = dayRecords.filter(d => d.Attendance === 'On Leave').length;

            const presentRecords = dayRecords.filter(d => d.Attendance === 'Present');
            const hours = presentRecords.map(r => this.parseDuration(r.Total_Duration || r.In_Duration));
            let avgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (avgH === 0 && present > 0) avgH = 8.0;

            return { date, present, absent, onLeave, avgH };
        });

        // Determine context for stats
        if (this.selectedDate && this.selectedEmp) {
            // Specific day for specific employee
            const rec = data[0]; 
            this.stats = {
                present: rec.Attendance === 'Present' ? 1 : 0,
                absent: rec.Attendance === 'Absent' ? 1 : 0,
                onLeave: rec.Attendance === 'On Leave' ? 1 : 0,
                avgHours: rec.Attendance === 'Present' ? this.parseDuration(rec.Total_Duration || rec.In_Duration) : 0,
                label: 'Selected Day',
                firstIn: rec.First_In || '--:--',
                lastOut: rec.Last_Out || '--:--',
                inDuration: rec.In_Duration || '--:--',
                outDuration: rec.Out_Duration || '--:--',
                totalDuration: rec.Total_Duration || '--:--'
            };
        } else if (this.selectedEmp) {
            // Cumulative for employee
            const latestRecord = data[data.length - 1];
            const totalPresent = data.filter(d => d.Attendance === 'Present').length;
            const totalOnLeave = data.filter(d => d.Attendance === 'On Leave').length;
            const totalAbsent = data.filter(d => d.Attendance === 'Absent').length;
            const hours = data.filter(d => d.Attendance === 'Present').map(r => this.parseDuration(r.Total_Duration || r.In_Duration));
            let totalAvgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (totalAvgH === 0 && totalPresent > 0) totalAvgH = 8.0;

            this.stats = { 
                present: totalPresent, 
                absent: totalAbsent, 
                onLeave: totalOnLeave,
                avgHours: totalAvgH, 
                label: 'Cumulative',
                firstIn: latestRecord?.First_In || '--:--',
                lastOut: latestRecord?.Last_Out || '--:--',
                inDuration: latestRecord?.In_Duration || '--:--',
                outDuration: latestRecord?.Out_Duration || '--:--',
                totalDuration: latestRecord?.Total_Duration || '--:--'
            };
        } else {
            // Latest day for organization or specific day for organization
            const targetDay = this.selectedDate ? dailyStats[0] : dailyStats[dailyStats.length - 1];
            const latestRecords = data.filter(d => String(d.Date) === targetDay.date);
            const pulseRecord = latestRecords[0]; 

            this.stats = { 
                present: targetDay.present, 
                absent: targetDay.absent, 
                onLeave: targetDay.onLeave,
                avgHours: targetDay.avgH, 
                label: this.selectedDate ? 'Selected Day' : 'Latest Day',
                firstIn: pulseRecord?.First_In || '--:--',
                lastOut: pulseRecord?.Last_Out || '--:--',
                inDuration: pulseRecord?.In_Duration || '--:--',
                outDuration: pulseRecord?.Out_Duration || '--:--',
                totalDuration: pulseRecord?.Total_Duration || '--:--'
            };
        }

        this.barData = {
            labels: labels,
            datasets: [
                {
                    data: dailyStats.map(s => s.present),
                    label: 'Present',
                    backgroundColor: '#4f46e5',
                    borderRadius: 6,
                    barThickness: labels.length > 10 ? undefined : 30
                },
                {
                    data: dailyStats.map(s => s.onLeave),
                    label: 'On Leave',
                    backgroundColor: '#93c5fd', // Light blue for leave
                    borderRadius: 6,
                    barThickness: labels.length > 10 ? undefined : 30
                }
            ]
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

        const currentSnapshot = this.selectedEmp ? { present: this.stats.present, absent: this.stats.absent, onLeave: this.stats.onLeave } : (dailyStats[dailyStats.length - 1] || { present: 0, absent: 0, onLeave: 0 });
        this.pieData = {
            labels: ['Present', 'Absent', 'On Leave'],
            datasets: [{
                data: [currentSnapshot.present, currentSnapshot.absent, currentSnapshot.onLeave],
                backgroundColor: ['#4f46e5', '#f87171', '#93c5fd'],
                borderWidth: 0
            }]
        };
    }

    exportToCSV() {
        if (!this.filteredData || this.filteredData.length === 0) return;
        
        // Specific headers requested by user
        const exportHeaders = [
            'Date', 'empID', 'first In', 'Last out', 
            'In duration', 'out duration', 'Attendance', 'total office duration'
        ];
        
        const csvRows = [
            exportHeaders.join(','),
            ...this.filteredData.map(row => [
                row.Date,
                row.EmpID,
                row['First_In'] || '--:--',
                row['Last_Out'] || '--:--',
                row.In_Duration,
                row.Out_Duration,
                row.Attendance,
                row['Total_Duration'] || '--:--'
            ].map(val => {
                const sVal = String(val);
                return sVal.includes(',') ? `"${sVal}"` : sVal;
            }).join(','))
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

    get tableData() {
        return this.filteredData;
    }

    openEditModal(record: any) {
        // Clone to prevent direct mutation
        this.editingRecord = { ...record };
    }

    closeEditModal() {
        this.editingRecord = null;
    }

    saveRecord() {
        if (!this.editingRecord) return;
        this.isSaving = true;

        const payload = {
            first_in: this.editingRecord.First_In,
            last_out: this.editingRecord.Last_Out,
            attendance_status: this.editingRecord.Attendance
        };

        this.attendanceService.updateAttendance(this.editingRecord.id, payload).subscribe({
            next: () => {
                this.notificationService.showAlert('Record updated successfully', 'success');
                this.isSaving = false;
                this.closeEditModal();
                this.attendanceService.fetchAttendance(); // Refresh data
            },
            error: (err) => {
                this.isSaving = false;
                this.notificationService.showAlert('Failed to update record', 'error');
            }
        });
    }
}
