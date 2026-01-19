import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AttendanceService } from '../../services/attendance.service';
import { NotificationService } from '../../services/notification.service';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-upload',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './upload.component.html',
    styleUrl: './upload.component.css'
})
export class UploadComponent {
    uploading = false;
    isDragging = false;
    results: any[] = [];

    constructor(
        private attendanceService: AttendanceService,
        private notificationService: NotificationService
    ) { }

    onDragOver(event: DragEvent) {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging = true;
    }

    onDragLeave(event: DragEvent) {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging = false;
    }

    onDrop(event: DragEvent) {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging = false;
        
        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            this.handleUpload(Array.from(files));
        }
    }

    onFilesSelected(event: any) {
        const files: FileList = event.target.files;
        if (files.length > 0) {
            this.handleUpload(Array.from(files));
        }
    }

    private handleUpload(fileArray: File[]) {
        this.uploading = true;
        this.results = [];

        this.attendanceService.uploadFiles(fileArray).subscribe({
            next: (res) => {
                this.uploading = false;
                this.results = res.results || [];
                this.attendanceService.fetchAttendance();
                this.notificationService.showAlert(res.message || "Files processed successfully", 'success');
            },
            error: (err) => {
                this.uploading = false;
                const errorMsg = err.error?.detail || 'Error uploading files.';
                this.notificationService.showAlert(errorMsg, 'error');
            }
        });
    }
}
