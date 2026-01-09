# 📊 Attendix: Professional Attendance Dashboard

Attendix is a premium, "Data-First" attendance analytics suite designed to transform raw attendance reports (biometric logs) into actionable insights. It features a stateless, high-performance architecture that processes data entirely in-memory for maximum privacy and speed.

---

## ✨ Key Features

- **Dual Report Intelligence**: Specialized processing for both `In/Out Duration` (Type A) and `Monthly Detailed` (Type B) attendance formats.
- **Stateless In-Memory Model**: Zero disk storage. Files are cleaned in-memory and stored in the browser session, ensuring data privacy and instant processing.
- **Intelligent Analytics**:
  - **Dynamic Filtering**: Instantly filter by Date or Employee ID.
  - **Cumulative Intelligence**: When filtering by a specific employee, the dashboard automatically calculates their total presence, absence, and average efficiency across the entire report duration.
  - **Adaptive Visuals**: Charts automatically show/hide based on data density (e.g., hiding trends when viewing a single day).
- **Professional Export**: Export your currently filtered view to a clean CSV file on demand.
- **Premium UI/UX**: Sleek dark/light mode aesthetics with real-time stats cards, trend analytics, and a unified single-page workflow.

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework.
- **Pandas**: Advanced data manipulation for cleaning complex Excel/CSV reports.
- **Uvicorn**: ASGI server for lightning-fast request handling.

### Frontend
- **Angular (Latest)**: Modern standalone component architecture.
- **Chart.js & ng2-charts**: Dynamic data visualizations (Bar, Line, Pie).
- **Vanilla CSS**: Custom premium design system with modern typography and animations.
- **Lucide Icons**: Clean, professional vector iconography.

---

## 🚀 Quick Start

### 1. Backend Setup (Internal/Server)
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```
*The backend will run on `http://localhost:8000`*

### 2. Frontend Setup (Dashboard)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the dev server
npm start
```
*The dashboard will be available at `http://localhost:4200`*

---

## 📈 Usage Guide

1. **Upload**: Drag and drop your attendance file (CSV/XLSX) into the corresponding card (Type A or Type B).
2. **Explore**: Switch between report types using the header tabs.
3. **Filter**: Use the "Date" or "Employee ID" dropdowns to drill down into specific data.
4. **Analyze**: 
   - Observe the **Stat Cards** for immediate snapshot totals.
   - Use the **Charts** to identify efficiency trends over time.
5. **Export**: Click the primary **"Export CSV"** button in the header once you've applied your desired filters.

---

## 🛡️ Data Privacy Notice
Attendix is designed with a **Stateless Model**. No files are permanently saved to the server. Data is processed in RAM and sent to your browser's memory. Once you refresh or close the page, the session data is cleared, making it ideal for handling sensitive HR and biometric logs.

---

**Developed with ❤️ for Attendix**
"# RBIS_HRMS" 
