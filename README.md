# 📊 RBIS HR Management System (HRMS)

RBIS HRMS is a comprehensive, premium management suite designed to modernize workforce coordination and biometric data intelligence. Transformed from a simple dashboard into a full-scale enterprise application, it provides robust employee onboarding, secure authentication, and deep workforce analytics.

---

## ✨ Key Features

- **🔐 Enterprise Authentication**: Secure JWT-based login system with mandatory **6-digit OTP verification** for registration and password resets.
- **📈 Unified Analytics Engine**:
  - Real-time visualization of attendance trends using Chart.js.
  - Automatic normalization of complex biometric logs (Type A & Type B formats).
  - **Cumulative Intelligence**: Dynamic calculation of presence, absence, and average efficiency.
- **👥 Employee Lifecycle Management**:
  - Professional onboarding module with automated `RBISXXXX` ID generation.
  - Secure profile management with dynamic initials-based avatars.
- **📂 Digital Vault (Records)**: Permanent cloud-agnostic storage for raw biometric logs.
- **🛡️ Clean Architecture**: Fully refactored backend using **Layered Architecture** (API, Service, Repository) for maximum maintainability and scalability.
- **💎 Premium UI/UX**: Professional Angular-based interface featuring:
  - **Interactive Particle Background**: A custom, minimalist tech-stack-themed canvas animation.
  - **Glassmorphism**: Modern semi-transparent interfaces for a high-end SaaS feel.
  - **Session Persistence**: Automatic redirection to login on session expiration.

---

## 🏗️ Backend Architecture (v1)

The backend follows **Clean Architecture** principles:

- **API Layer (`app/api/v1`)**: Thin route handlers using FastAPI.
- **Service Layer (`app/services`)**: Encapsulated business logic.
- **Repository Layer (`app/repositories`)**: Abstraction over SQLAlchemy database operations.
- **Models Layer (`app/models`)**: Domain-led database schemas split by module (Employee, Attendance, Leave, etc.).

---

## 🛠️ Tech Stack

### Backend

- **FastAPI**: High-performance Python framework.
- **SQLAlchemy & MS SQL Server**: Enterprise-grade relational data management.
- **Pandas**: Advanced data cleaning and normalization.
- **JWT & Passlib**: Secure authentication and password hashing.
- **SMTPLib**: Integrated OTP email service.

### Frontend

- **Angular (Latest)**: Professional standalone architecture.
- **Chart.js**: Dynamic data visualizations.
- **Custom Canvas Engine**: Interactive background effects.
- **Modern CSS**: Custom design system with glassmorphism.
- **Lucide Icons**: Sleek iconography.

---

## 🚀 Quick Start

### 1. Backend Configuration

1. Navigate to the `backend` directory.
2. Create a `.env` file based on `.env.example`:
   ```env
   DATABASE_URL=mssql+pyodbc://...
   SECRET_KEY=your_secret_key
   SMTP_HOST=...
   SMTP_USER=...
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
   _Access at `http://localhost:4200`_

---

## 🌍 Deployment

For detailed deployment instructions, please refer to the [Deployment Guide](./backend/deployment_guide.md) (or check the project artifacts).

---

**Developed with ❤️ for RBIS Tech Pvt Ltd**
