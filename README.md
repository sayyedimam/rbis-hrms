# 📊 RBIS HR Management System (HRMS)

RBIS HRMS is a comprehensive, premium management suite designed to modernize workforce coordination and biometric data intelligence. Transformed from a simple dashboard into a full-scale enterprise application, it provides robust employee onboarding, secure authentication, and deep workforce analytics.

---

## ✨ Key Features

- **🔐 Enterprise Authentication**: Secure JWT-based login system with mandatory email verification flow.
- **📈 Unified Analytics Engine**:
  - Real-time visualization of attendance trends using Chart.js.
  - Automatic normalization of complex biometric logs (Type A & Type B formats).
  - **Cumulative Intelligence**: Dynamic calculation of presence, absence, and average efficiency over custom durations.
- **👥 Employee Lifecycle Management**:
  - Professional onboarding module with automated `RBISXXXX` ID generation.
  - Secure profile management with dynamic initials-based avatars.
- **📂 Digital Vault (Records)**: Permanent cloud-agnostic storage for raw biometric logs with direct download capabilities.
- **🛡️ Secure Data Engine**: Transitioned from stateless processing to permanent **SQL Server** storage with transactional integrity.
- **💎 Premium UI/UX**: Professional Angular-based interface featuring a unified horizontal navigation layout and a responsive dashboard shell.

---

## 🛠️ Tech Stack

### Backend

- **FastAPI**: High-performance Python framework for modern APIs.
- **SQLAlchemy & MS SQL Server**: Enterprise-grade relational data management.
- **Pandas**: Advanced data cleaning and normalization for heterogeneous report formats.
- **JWT & Passlib**: Secure industry-standard authentication and password hashing.

### Frontend

- **Angular (Latest)**: Professional standalone architecture and modular component design.
- **Chart.js**: Dynamic, high-density data visualizations.
- **Modern CSS**: Custom premium UI system with glassmorphism and subtle micro-animations.
- **Lucide Icons**: Sleek, professional iconography.

---

## 🚀 Quick Start

### 1. Backend Configuration

1. Navigate to the `backend` directory.
2. Create a `.env` file based on `.env.example`:
   ```env
   DATABASE_URL=mssql+pyodbc://localhost/attendix_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
   SECRET_KEY=your_secret_key
   ```
3. Install dependencies and start:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

### 2. Frontend Setup

1. Navigate to the `frontend` directory.
2. Install and launch:
   ```bash
   npm install
   npm start
   ```
   _Access the dashboard at `http://localhost:4200`_

---

## 📈 Module Overview

1. **Dashboard**: Central intelligence hub for workforce analytics.
2. **Onboarding**: Strategic module for enrolling new workforce members.
3. **Upload**: Unified ingestion zone for multiple biometric file types.
4. **Records**: Historical vault for auditing and downloading original logs.
5. **Profile**: Personalized user space for managing professional credentials.

---

**Developed with ❤️ for RBIS Tech Pvt Ltd**
