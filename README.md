# 📊 RBIS HR Management System (HRMS)

**A Premium Enterprise Workforce Intelligence Suite**

RBIS HRMS is a state-of-the-art, role-based Human Resource Management System designed to streamline attendance tracking, employee operations, and workforce analytics. Built with a focus on data integrity ("Strict ID" enforcement) and user experience (Glassmorphism UI), it serves as a central hub for managing the entire employee lifecycle.

---

## 🌟 Key Features

### 🔐 Role-Based Access Control (RBAC)

The system strictly segregates functionality based on user roles, ensuring data security and operational clarity:

- **Super Admin**: Full control over all modules, including the exclusive **Operations** console for data ingestion and correction.
- **HR Manager**: Access to Onboarding, Employee Master, and detailed Analytics for workforce management.
- **CEO**: High-level overview with access to Records and Organization-wide statistics.
- **Employee**: Personal dashboard view with self-service leave management and attendance history.

### 🚀 Core Modules

#### 1. 🖥️ Interactive Dashboard

- **Real-Time Insight**: Instant visualization of Present, Absent, and On-Leave statistics.
- **Context-Aware Drilling**: Clickable cards revealing detailed tables for specific statuses.
- **Individual Focus Mode**: Smart profile isolation—searching for an ID instantly transforms the dashboard into a personal stats hub, hiding organization-wide noise.
- **Active Profile Header**: Prominent, dynamically placed profile bar for focused individual analysis.

#### 2. 📈 Advanced Analytics

- **Deep Data Mining**: Filter attendance logs by Date Range or specific Employee ID.
- **Strict Validation**: Enforces standard `RBIS` prefix format for all ID searches to ensure data consistency.
- **Contextual Intelligence**:
  - **Admins/HR**: View "Organization Summary" across all employees.
  - **Employees**: View "My Attendance Summary" and personal trends with automatic self-ID filtering.

#### 3. ⚙️ Attendance Operations (Admin Only)

- **Strict White-List Ingestion**: Only supports the "In Out Duration Report" format with real-time synchronous validation and error reporting.
- **Centralized Console**: A powerful hub for ingesting raw biometric data types.
- **Correction Console**: An overlay interface for manually correcting attendance anomalies.
- **Data Export**: One-click export functionalities for processing and reporting.

#### 4. 👥 Onboarding & Master Data

- **Streamlined Registration**: simplified "One-Flow" onboarding process.
- **Validation Gates**: Built-in checks to prevent malformed IDs or duplicate records.
- **Master Table**: A comprehensive, searchable directory of all workforce members.

#### 5. 📅 Leave Management

- **Self-Service Portal**: Employees can request leaves and view balances directly.
- **Holiday Calendar CRUD (Admin Only)**: Full management suite to Create, Edit, or Delete holidays with automatic day-of-week calculation.
- **Approval Workflow**: HR/Admin approval pipeline for managing leave applications.

---

## 🏗️ Technical Architecture

The application follows a **Clean Architecture** pattern to ensure scalability and maintainability.

### 🎨 Frontend (Angular 18+)

- **Standalone Components**: Modular architecture for faster load times.
- **Reactive State**: RxJS-powered data streams for real-time UI updates.
- **Premium UI/UX**:
  - **Glassmorphism**: Modern, semi-transparent aesthetic.
  - **Lucide Icons**: Professional, consistent iconography.
  - **Chart.js**: Interactive, responsive data visualizations.

### ⚙️ Backend (Python FastAPI)

- **Layered Design**: Distinct separation of API, Service, and Repository layers.
- **Data Consistency**: Enforces **IST (UTC+5:30)** timezone across all attendance timestamps and reports.
- **SQLAlchemy**: Robust ORM for MS SQL Server interactions.
- **Azure Blob Storage**: Secure, scalable storage for uploaded attendance reports and documents.
- **Security**: JWT-based stateless authentication with role-based access control.

---

## 🛠️ Installation & Setup

### Prerequisites

- Node.js (v18+)
- Python (v3.10+)
- MS SQL Server

### 1. Backend Setup

```bash
cd backend
# Create virtual environment
python -m venv venv
# Activate (Windows)
.\venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Configure .env (see .env.example)
# Run Server
uvicorn main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend
# Install packages
npm install
# Launch Application
ng serve
```

_Access the application at `http://localhost:4200`_

---

## 🔒 Security Standards

- **Strict ID Enforcement**: All employee IDs must adhere to the `RBISxxxx` format.
- **Session Persistence**: Secure, auto-expiring JWT tokens.
- **Input Sanitization**: Comprehensive validation on all search and input fields.

---

**© 2026 RBIS Tech Pvt Ltd. All Rights Reserved.**
