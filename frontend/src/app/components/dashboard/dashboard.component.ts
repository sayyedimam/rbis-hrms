import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, Chart, registerables } from 'chart.js';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { RouterModule } from '@angular/router';
import { NotificationService } from '../../services/notification.service';

Chart.register(...registerables);

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterModule, BaseChartDirective],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit, OnDestroy {
    loading = false;
    hasData = false;
    isAdmin = false;
    canViewAll = false;
    showStatsCards = false;
    
    // Drill Down State
    showDrillDown = false;
    drillDownTitle = '';
    drillDownList: any[] = [];
    hideTimings = false;

    // Raw Data Storage
    private rawData: any[] = [];
    private filteredData: any[] = [];

    availableDates: string[] = [];
    availableEmps: string[] = [];

    // Selected Filters
    fromDate: string = '';
    toDate: string = '';
    selectedEmp: string = '';
    searchTerm: string = '';
    
    // UI Metadata
    activeEmployee: any = null;

    // Chart Configuration
    public pieChartOptions: ChartOptions<'pie'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
    };

    public barChartOptions: ChartOptions<'bar'> = {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0 } },
        plugins: { 
            legend: { display: true },
            tooltip: {
                callbacks: {
                    label: (context) => {
                        const index = context.dataIndex;
                        const label = context.dataset.label || '';
                        const val = (context.parsed && typeof context.parsed.y === 'number') ? context.parsed.y : 0;
                        
                        // Access the cached dailyStats via a private ref or recalculate
                        // For simplicity, we can store dailyStats in a component property
                        const stats = this.dailyChartStats[index];
                        if (stats) {
                            if (this.activeEmployee) {
                                return `Hours: ${val.toFixed(1)}h`;
                            }
                            return [
                                `${label}: ${val}`,
                                `Absent: ${stats.absent}`,
                                `Avg Hours: ${stats.avgH.toFixed(1)}h`
                            ];
                        }
                        return `${label}: ${val}`;
                    }
                }
            }
        }
    };

    public lineChartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0 } },
        plugins: { 
            legend: { display: true },
            tooltip: {
                callbacks: {
                    label: (context) => {
                        const val = (context.parsed && typeof context.parsed.y === 'number') ? context.parsed.y : 0;
                        return `Avg Hours: ${val.toFixed(1)}h`;
                    }
                }
            }
        }
    };

    public barData: ChartConfiguration<'bar'>['data'] = { labels: [], datasets: [] };
    public lineData: ChartConfiguration<'line'>['data'] = { labels: [], datasets: [] };
    public pieData: ChartConfiguration<'pie'>['data'] = { labels: [], datasets: [] };
    showTrendChart = false;

    private subs = new Subscription();

    public stats = { 
        present: 0, 
        absent: 0, 
        onLeave: 0,
        avgHours: 0, 
        label: 'Latest'
    };

    private dailyChartStats: any[] = [];

    constructor(
        private attendanceService: AttendanceService,
        public authService: AuthService,
        private notificationService: NotificationService
    ) { }

    ngOnInit() {
        const user = this.authService.currentUser;
        this.isAdmin = this.authService.getUserRole() === 'SUPER_ADMIN';
        const role = this.authService.getUserRole();
        this.canViewAll = this.isAdmin || role === 'HR' || role === 'CEO';
        
        if (!this.canViewAll && user) {
            this.selectedEmp = user.emp_id;
        }

        this.attendanceService.fetchAttendance();

        this.subs.add(this.attendanceService.typeAData$.subscribe(() => this.syncData()));
        this.subs.add(this.attendanceService.typeBData$.subscribe(() => this.syncData()));
        this.subs.add(this.attendanceService.hasData$.subscribe(has => this.hasData = has));

        this.subs.add(this.authService.currentUser$.subscribe(u => {
            if (u) {
                const r = u.role;
                this.isAdmin = r === 'SUPER_ADMIN';
                this.canViewAll = this.isAdmin || r === 'HR' || r === 'CEO';
                
                if (!this.canViewAll) {
                    this.selectedEmp = u.emp_id;
                    this.applyFilters();
                }
            }
        }));
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
        this.updateFilterOptions();
        this.applyFilters();
    }

    ngOnDestroy() {
        this.subs.unsubscribe();
    }

    updateFilterOptions() {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const d = String(now.getDate()).padStart(2, '0');
        const todayStr = `${y}-${m}-${d}`;
        
        this.availableDates = [...new Set(this.rawData.map(d => String(d.Date).split('T')[0]))]
            .filter(d => d && d !== "null" && d <= todayStr)
            .sort();
            
        this.availableEmps = [...new Set(this.rawData.map(d => String(d['EmpID'])))]
            .filter(id => id && id !== "null" && id !== "undefined")
            .sort();
    }

    resetFilters() {
        this.fromDate = '';
        this.toDate = '';
        this.searchTerm = '';
        
        if (this.canViewAll) {
            this.selectedEmp = '';
        } else {
            const user = this.authService.currentUser;
            this.selectedEmp = user?.emp_id || '';
        }
        this.activeEmployee = null;
        this.showStatsCards = false;
        this.applyFilters();
    }

    applyFilters() {
        // Validation: If no filters, show organization-wide for latest date (handled in calculateStats)
        let filtered = [...this.rawData];

        // 1. Date Range Filtering
        if (this.fromDate) {
            const start = this.fromDate;
            const end = this.toDate || this.fromDate; // If "To" is blank, use "From" for single day
            filtered = filtered.filter(d => {
                const dateStr = String(d.Date).split('T')[0];
                return dateStr >= start && dateStr <= end;
            });
        } else {
            // Default: Only past/present dates
            const todayStr = new Date().toISOString().split('T')[0];
            filtered = filtered.filter(d => String(d.Date).split('T')[0] <= todayStr);
        }
        
        // 2. Employee Filtering
        if (this.selectedEmp) {
            filtered = filtered.filter(d => String(d['EmpID']) === this.selectedEmp);
        } else if (this.searchTerm.trim()) {
            const term = this.searchTerm.trim().toLowerCase();
            filtered = filtered.filter(r => {
                const empIdMatch = (r.EmpID && r.EmpID.toLowerCase() === term);
                const nameMatch = r.Employee_Name && r.Employee_Name.toLowerCase().includes(term);
                return empIdMatch || nameMatch;
            });
        }

        this.filteredData = filtered;
        
        // 3. Visibility and Metadata
        const isIndividualSearch = this.selectedEmp || (this.searchTerm.trim() && filtered.length > 0 && this.isExactMatch(filtered));
        this.showStatsCards = !!(this.fromDate && !this.toDate) || !!isIndividualSearch;
        
        if (isIndividualSearch) {
            const firstWithInfo = filtered.find(r => r.Employee_Name);
            if (firstWithInfo) {
                this.activeEmployee = {
                    EmpID: firstWithInfo.EmpID,
                    Name: firstWithInfo.Employee_Name
                };
            } else if (filtered.length > 0) {
                this.activeEmployee = { EmpID: filtered[0].EmpID, Name: 'Unknown Employee' };
            }
        } else {
            this.activeEmployee = null;
        }

        this.calculateStats(filtered);
        this.processChartData(filtered);
    }

    private calculateStats(data: any[]) {
        if (!data || data.length === 0) {
            this.stats = { present: 0, absent: 0, onLeave: 0, avgHours: 0, label: 'No Data' };
            return;
        }

        const dates = [...new Set(data.map(d => String(d.Date).split('T')[0]))].sort();
        
        if (this.fromDate || this.selectedEmp || this.searchTerm) {
            // Filtered view
            const present = data.filter(d => d.Attendance === 'Present').length;
            const absent = data.filter(d => d.Attendance === 'Absent').length;
            const onLeave = data.filter(d => d.Attendance === 'On Leave').length;
            
            const hours = data.filter(d => d.Attendance === 'Present').map(r => this.parseDuration(r.Total_Duration || r.In_Duration));
            let avgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (avgH === 0 && present > 0) avgH = 8.0;

            this.stats = {
                present,
                absent,
                onLeave,
                avgHours: avgH,
                label: this.fromDate && !this.toDate ? this.fromDate : 'Filtered'
            };
        } else {
            // Default: Show latest date summary
            const latestDate = dates[dates.length - 1];
            const latestRecords = data.filter(d => String(d.Date).split('T')[0] === latestDate);
            
            const present = latestRecords.filter(d => d.Attendance === 'Present').length;
            const absent = latestRecords.filter(d => d.Attendance === 'Absent').length;
            const onLeave = latestRecords.filter(d => d.Attendance === 'On Leave').length;
            
            const hours = latestRecords.filter(d => d.Attendance === 'Present').map(r => this.parseDuration(r.Total_Duration || r.In_Duration));
            let avgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (avgH === 0 && present > 0) avgH = 8.0;

            this.stats = {
                present,
                absent,
                onLeave,
                avgHours: avgH,
                label: 'Latest'
            };
        }
    }

    private processChartData(data: any[]) {
        if (!data || data.length === 0) {
            this.barData = { labels: [], datasets: [] };
            this.lineData = { labels: [], datasets: [] };
            this.pieData = { labels: [], datasets: [] };
            return;
        }

        const labels = [...new Set(data.map(d => String(d.Date).split('T')[0]))].sort();
        this.showTrendChart = labels.length > 1;

        const dailyStats = labels.map(date => {
            const dayRecords = data.filter(d => String(d.Date).split('T')[0] === date);
            const present = dayRecords.filter(d => d.Attendance === 'Present').length;
            const absent = dayRecords.filter(d => d.Attendance === 'Absent').length;
            const onLeave = dayRecords.filter(d => d.Attendance === 'On Leave').length;

            const presentRecords = dayRecords.filter(d => d.Attendance === 'Present');
            const hours = presentRecords.map(r => this.parseDuration(r.Total_Duration || r.In_Duration));
            let avgH = hours.length > 0 ? hours.reduce((a, b) => a + b, 0) / hours.length : 0;
            if (avgH === 0 && present > 0) avgH = 8.0;

            return { date, present, absent, onLeave, avgH };
        });

        this.dailyChartStats = dailyStats;

        // For single employee (ID or specific search match)
        const isSingleEmp = this.selectedEmp || (this.activeEmployee && labels.length > 1);

        this.barData = {
            labels: labels,
            datasets: [
                { 
                    data: isSingleEmp 
                        ? dailyStats.map(s => s.avgH) // Show duration (avgH is actual hour for single emp)
                        : dailyStats.map(s => s.present), 
                    label: isSingleEmp ? 'Office Hours' : 'Present Count', 
                    backgroundColor: isSingleEmp ? '#10b981' : '#4f46e5', 
                    borderRadius: 6 
                },
                { 
                    data: isSingleEmp 
                        ? [] // No on-leave count for single employee duration bar
                        : dailyStats.map(s => s.onLeave), 
                    label: 'On Leave', 
                    backgroundColor: '#93c5fd', 
                    borderRadius: 6,
                    hidden: isSingleEmp
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

        const currentSnapshot = dailyStats[dailyStats.length - 1];
        this.pieData = {
            labels: ['Present', 'Absent', 'On Leave'],
            datasets: [{
                data: [currentSnapshot.present, currentSnapshot.absent, currentSnapshot.onLeave],
                backgroundColor: ['#4f46e5', '#f87171', '#93c5fd'],
                borderWidth: 0
            }]
        };
    }

    private isExactMatch(data: any[]): boolean {
        if (data.length === 0) return false;
        const firstId = data[0].EmpID;
        return data.every((r: any) => r.EmpID === firstId);
    }

    viewStatusDetails(status: string) {
        // Allowed for everyone (individual or admin)
        
        let targetData = this.filteredData;
        if (!this.fromDate && !this.activeEmployee && !this.selectedEmp) {
            const dates = [...new Set(this.filteredData.map(d => String(d.Date).split('T')[0]))].sort();
            const latestDate = dates[dates.length - 1];
            targetData = this.filteredData.filter(d => String(d.Date).split('T')[0] === latestDate);
        }

        this.drillDownTitle = `${status} List`;
        this.hideTimings = status === 'Absent' || status === 'On Leave';
        this.drillDownList = targetData
            .filter((d: any) => d.Attendance === status)
            .map((d: any) => ({
                Date: String(d.Date).split('T')[0],
                EmpID: d.EmpID,
                Name: d.Employee_Name || '--',
                status: d.Attendance,
                in: d.First_In,
                out: d.Last_Out,
                duration: d.Total_Duration
            }));
        this.showDrillDown = true;
    }

    closeDrillDown() {
        this.showDrillDown = false;
        this.drillDownList = [];
    }

    private parseDuration(d: any): number {
        if (!d) return 0;
        const s = String(d).trim();
        if (s === '' || s === '0' || s.toLowerCase() === 'nan' || s === '00:00') return 0;
        try {
            if (s.includes(':')) {
                const parts = s.split(':').map(Number);
                if (parts.length >= 2) return parts[0] + (parts[1] / 60);
            }
            return isNaN(Number(s)) ? 0 : Number(s);
        } catch { return 0; }
    }
}
