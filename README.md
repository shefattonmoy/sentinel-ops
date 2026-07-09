# SentinelOps - Enterprise Security Operations Platform

![SentinelOps](https://img.shields.io/badge/SentinelOps-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![Django](https://img.shields.io/badge/Django-5.0+-green)
![React](https://img.shields.io/badge/React-18+-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![PRs](https://img.shields.io/badge/PRs-Welcome-brightgreen)

**Collect. Detect. Investigate. Respond.**

SentinelOps is a comprehensive, open-source Security Operations Center (SOC) platform designed for monitoring, detecting, and responding to security threats across your infrastructure. Built with Django REST Framework, React with TypeScript, and PostgreSQL, it provides real-time security monitoring with advanced threat intelligence capabilities.

---

## 📖 Table of Contents
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Usage Examples](#-usage-examples)
- [WebSocket Events](#-websocket-events)
- [Detection Rules](#-detection-rules)
- [Playbooks](#-playbooks)
- [Gamification System](#-gamification-system)
- [Compliance Framework](#-compliance-framework)
- [Deployment](#-deployment)
- [Environment Variables](#-environment-variables)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

### Dashboard & Monitoring
┌─────────────────────────────────────────────────────────────┐
│ 🛡️ SentinelOps 🔔 🌙 👤 Admin │
├─────────┬───────────────────────────────────────────────────┤
│ Dashboard│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐│
│ Agents │ │ Agents │ │ Events │ │ Alerts │ │Score ││
│ Events │ │ 15/20 │ │ 45,231 │ │ 89 │ │ 92% ││
│ Alerts │ └──────────┘ └──────────┘ └──────────┘ └──────┘│
│ Rules │ │
│ Incidents│ 📈 Events Over Time │
│ Reports │ ████████████████░░░░░░░░░░ 3,800 │
│ Audit │ │
│ Threat │ 🎯 Top Source IPs │
│ MITRE │ 192.168.1.100 234 events │
│ Topology │ 10.0.0.55 189 events │
│ │ │
│ ⚙️ Profile│ │
└─────────┴───────────────────────────────────────────────────┘



---

## 🚀 Features

### 🔍 Core Monitoring & Detection
- **Agent-based Monitoring** - Lightweight Python agents for Linux/Windows servers with offline buffering
- **Real-time Event Streaming** - WebSocket-based live event feed with Django Channels
- **Multi-source Log Ingestion** - Parse SSH, Nginx, Docker, Django, System logs
- **Detection Rules Engine** - Threshold, correlation, pattern, frequency, sequence, and blacklist rules
- **Alert Management** - Full lifecycle (Open → Acknowledge → Investigate → Resolve → Close)
- **Event Correlation** - Auto-group related alerts into incidents

### 🛡️ Advanced Threat Intelligence
- **AI-Powered Threat Scoring** - ML-based IP reputation scoring (frequency, severity, pattern, reputation)
- **MITRE ATT&CK Framework** - 200+ techniques mapped with coverage matrix visualization
- **Honeypot Integration** - Deploy deception technology (SSH, HTTP, FTP, MySQL, Telnet)
- **Threat Intel Dashboard** - Top attackers, IP geolocation, threat score distribution

### 📊 Analytics & Forensics
- **User & Entity Behavior Analytics (UEBA)** - Detect anomalous user behavior patterns
- **Digital Forensics Timeline** - Reconstruct attack chains with visual timeline
- **Risk Scoring Dashboard** - Asset-based risk assessment with threat/vulnerability/exposure/impact scoring
- **Network Topology Map** - Auto-discovered SVG network visualization with real-time status

### ⚡ Automation & Response
- **Playbook Engine** - 7 action types (Block IP, Create Alert, Create Incident, Send Notification, Webhook, Wait, Update Agent)
- **Incident Management** - 9-stage lifecycle with SLA tracking, evidence collection, timeline
- **Export Scheduler** - Automated exports to Email, S3, Webhook, Local Storage (CSV, JSON, PDF)
- **Compliance Automation** - SOC2 & ISO27001 controls with auto-evidence generation

### 🎮 Engagement & Productivity
- **Gamification** - SOC analyst leaderboard (weekly/monthly), 8 achievement badges, point system
- **AI Chat Assistant (RAG)** - Natural language queries ("Show critical alerts today", "Top attacking IPs?")
- **Global Search** - Advanced query syntax (`severity:critical`, `ip:192.168.1.1`, `service:ssh`)
- **Reports** - Daily SOC, Weekly, Monthly, Executive Summary, Incident Summary (PDF, CSV, JSON)
- **Session Timeout** - Configurable inactivity timeout with 2-minute warning modal

### 🔐 Security & Compliance
- **JWT Authentication** - Token-based API authentication with refresh tokens
- **Role-Based Access Control (RBAC)** - Admin, Analyst, Viewer roles with granular permissions
- **Two-Factor Authentication (2FA)** - TOTP with QR code, backup codes, Google Authenticator support
- **Audit Logging** - Complete activity trail for all CRUD operations, logins, config changes
- **Password Policies** - Minimum length, complexity validation

### 🎨 User Experience
- **Dark/Light Theme** - Toggle with localStorage persistence
- **Responsive Design** - Collapsible sidebar, mobile-friendly
- **Profile Management** - Avatar upload, bio, phone, department, timezone preferences
- **Notification Center** - Browser, Email, Slack, Discord, Webhook channels
- **Advanced Filtering** - Multi-criteria filtering on all data tables

---

## 🏗️ Architecture

┌─────────────────────────────────────────────────────────────────────┐
│ SentinelOps Platform │
├────────────────┬───────────────────┬─────────────────┬──────────────┤
│ React 18 UI │ Django 5.0 API │ PostgreSQL 15 │ Python Agent│
│ TypeScript │ DRF + Channels │ + Redis Cache │ (Any Host) │
│ MUI v6 │ JWT + TOTP │ │ │
├────────────────┼───────────────────┼─────────────────┼──────────────┤
│ │
│ ┌─────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────┐ │
│ │Dashboard│◄──►│ Events API │◄──►│ Parser Engine │◄──│ Agent │ │
│ └─────────┘ └─────────────┘ └──────────────┘ └──────────┘ │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ ┌─────────┐ ┌─────────────┐ ┌──────────────┐ │
│ │ Alert UI│◄──►│ Rules Engine │───►│ Alert Creator │ │
│ └─────────┘ └─────────────┘ └──────────────┘ │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ ┌──────────┐ ┌──────────────┐ ┌─────────────────┐ │
│ │Incident │◄──│ Correlation │◄─│ Alert Aggregator │ │
│ │Manager │ │ Engine │ └─────────────────┘ │
│ └──────────┘ └──────────────┘ │
│ │
│ WebSocket (Django Channels) ◄──────► Real-time Event Stream │
│ │
└─────────────────────────────────────────────────────────────────────┘



### Data Flow

Agent (Log Watcher) → API Gateway → Redis Queue → Celery Worker
│
Parser Engine
│
Rule Evaluation
│
Alert Generation
│
Correlation Engine
│
Incident Creation
│
WebSocket → React Dashboard



---

## 📦 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | React 18 | UI components |
| **Frontend Language** | TypeScript 5.0 | Type-safe development |
| **UI Library** | MUI v6 (Material-UI) | Design system |
| **Charts** | Recharts | Data visualization |
| **Routing** | React Router v6 | Client-side routing |
| **HTTP Client** | Axios | API communication |
| **Backend Framework** | Django 5.0 | API server |
| **API Framework** | Django REST Framework 3.15 | REST API |
| **Real-time** | Django Channels 4.0 | WebSocket support |
| **ASGI Server** | Daphne | Async server |
| **Authentication** | SimpleJWT | JWT tokens |
| **2FA** | pyotp, qrcode, Pillow | TOTP authentication |
| **Database** | PostgreSQL 15 | Primary data store |
| **Cache** | Redis (optional) | Caching & message broker |
| **Task Queue** | Celery (optional) | Async processing |
| **ML/AI** | scikit-learn, numpy | Threat scoring |
| **PDF Generation** | ReportLab | Report export |
| **Agent** | Python 3.11+, requests | Monitoring agent |

---

## 🔧 Installation

### Prerequisites
- **Python** 3.11 or higher
- **Node.js** 18 or higher
- **PostgreSQL** 15 or higher
- **Git**

### Backend Setup

```
# Clone repository
git clone https://github.com/yourusername/sentinelops.git
cd sentinelops

# Create virtual environment
cd backend
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate
# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb sentinelops

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Import MITRE ATT&CK data
python manage.py import_mitre

# Import compliance frameworks
python manage.py shell -c "from apps.compliance.importer import import_compliance_data; import_compliance_data()"

# Start server
daphne sentinelops.asgi:application --port 8000

```


### Frontend Setup

```
# New terminal
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "REACT_APP_API_URL=http://127.0.0.1:8000/api" > .env

# Start development server
npm start

```

### Agent Setup (Optional)

```

# New terminal
cd agent

# Install agent
pip install -e .

# Run agent
sentinel-agent --server http://127.0.0.1:8000/api --name "my-server"

```



### Project Structure

```

sentinelops/
├── backend/                          # Django Backend
│   ├── apps/                         # Application modules
│   │   ├── accounts/                 # 👤 Authentication, RBAC, 2FA, Profile
│   │   ├── agents/                   # 🖥️ Agent registration, heartbeat, health
│   │   ├── ai_assistant/             # 🤖 AI Chat with RAG
│   │   ├── alerts/                   # 🚨 Alert lifecycle management
│   │   ├── analytics/                # 📊 User Behavior Analytics
│   │   ├── audit/                    # 📝 Audit logging trail
│   │   ├── compliance/               # ✅ SOC2/ISO27001 compliance
│   │   ├── dashboard/                # 📈 Dashboard statistics API
│   │   ├── events/                   # 📡 Event processing & WebSocket
│   │   ├── forensics/                # 🔍 Digital forensics timeline
│   │   ├── gamification/             # 🏆 Leaderboard & achievements
│   │   ├── honeypot/                 # 🍯 Honeypot management
│   │   ├── incidents/                # ⚠️ Incident management
│   │   ├── logs/                     # 📋 Raw log storage
│   │   ├── mitre/                    # 🎯 MITRE ATT&CK framework
│   │   ├── notifications/            # 🔔 Multi-channel notifications
│   │   ├── playbooks/                # ⚡ Automated response playbooks
│   │   ├── reports/                  # 📄 Report generation (PDF/CSV/JSON)
│   │   ├── risks/                    # 📉 Asset risk scoring
│   │   ├── rules/                    # 🛡️ Detection rules engine
│   │   ├── scheduler/                # ⏰ Export scheduler
│   │   ├── search/                   # 🔎 Global search engine
│   │   ├── threat_intel/             # 🌍 IP reputation & threat scoring
│   │   └── topology/                 # 🕸️ Network topology discovery
│   ├── sentinelops/                  # Django project settings
│   ├── static/                       # Static files
│   ├── media/                        # Uploaded files
│   ├── manage.py                     # Django management
│   └── requirements.txt              # Python dependencies
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── components/               # Reusable components
│   │   │   ├── common/               # SearchBar, NotificationBell, SessionTimeout
│   │   │   └── layout/               # MainLayout with sidebar
│   │   ├── pages/                    # Page components
│   │   │   ├── agents/               # Agent management page
│   │   │   ├── alerts/               # Alert list page
│   │   │   ├── analytics/            # User Behavior Analytics page
│   │   │   ├── audit/                # Audit log page
│   │   │   ├── auth/                 # Login page
│   │   │   ├── chat/                 # AI Chat page
│   │   │   ├── compliance/           # Compliance page
│   │   │   ├── dashboard/            # Main dashboard
│   │   │   ├── events/               # Events stream page
│   │   │   ├── forensics/            # Forensics timeline page
│   │   │   ├── gamification/         # Leaderboard page
│   │   │   ├── honeypot/             # Honeypot page
│   │   │   ├── incidents/            # Incident management page
│   │   │   ├── mitre/                # MITRE ATT&CK page
│   │   │   ├── playbooks/            # Playbooks page
│   │   │   ├── profile/              # Profile settings page
│   │   │   ├── reports/              # Reports page
│   │   │   ├── risk/                 # Risk scoring page
│   │   │   ├── rules/                # Detection rules page
│   │   │   ├── scheduler/            # Export scheduler page
│   │   │   ├── settings/             # App settings page
│   │   │   ├── threatintel/          # Threat intel page
│   │   │   └── topology/             # Network topology page
│   │   ├── services/                 # API service layer
│   │   ├── context/                  # React context providers
│   │   ├── types/                    # TypeScript interfaces
│   │   ├── App.tsx                   # Main app component
│   │   └── index.tsx                 # Entry point
│   ├── package.json
│   └── tsconfig.json
├── agent/                            # Monitoring Agent
│   ├── sentinel_agent/
│   │   ├── agent.py                  # Main agent class
│   │   ├── config.py                 # Configuration
│   │   ├── log_watcher.py            # Log file monitoring
│   │   ├── metrics_collector.py      # System metrics
│   │   ├── log_buffer.py             # Offline buffer
│   │   ├── api_client.py             # API communication
│   │   └── run.py                    # Entry point
│   └── setup.py
├── docker-compose.yml                # Docker deployment
└── README.md                         # This file


```
