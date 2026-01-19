import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Alert {
    message: string;
    type: 'success' | 'error' | 'info';
    id: number;
}

@Injectable({
    providedIn: 'root'
})
export class NotificationService {
    private alertsSubject = new BehaviorSubject<Alert[]>([]);
    alerts$ = this.alertsSubject.asObservable();
    private counter = 0;

    showAlert(message: string, type: 'success' | 'error' | 'info' = 'info') {
        const id = this.counter++;
        const alert: Alert = { message, type, id };
        const currentAlerts = this.alertsSubject.value;
        this.alertsSubject.next([...currentAlerts, alert]);

        setTimeout(() => {
            this.removeAlert(id);
        }, 5000);
    }

    removeAlert(id: number) {
        const currentAlerts = this.alertsSubject.value;
        this.alertsSubject.next(currentAlerts.filter(a => a.id !== id));
    }
}
