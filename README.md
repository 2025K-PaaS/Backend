---

<p align="center">
  <img src="https://k-paas.dajeong.shop/uploads/logo-eeum.png" width="110" alt="Project banner" />
</p>

<h1 align="center">eeum • Backend</h1>
<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/SQLAlchemy-FCA121?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Uvicorn-121212?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white">
</p>

<p align="center">
  <b>eeum Backend</b> is the core API server of the circular resource matching platform,  
  providing user/resource management, AI analysis integration, matching, point rewards, and notifications.
</p>

---

## 🚀 Key Features

* **AI Image Analysis** – Sends uploaded resource images to AI server → extracts type, material, title, and estimated value
* **Resource / Request Registration** – Save uploads and metadata, apply AI analysis results
* **Matching System** – Fetches candidate matches from AI server for automatic or manual matching
* **Point System** – Automatically awards points on confirmed matches (`award_points_if_matched`)
* **Notification System** – Sends alerts for proposals, accept/decline events, and point rewards
* **Static File Serving** – Publicly serves uploaded images (`uploads/`) via FastAPI static mount

---

## ⚙️ Tech Stack (Backend)

**Framework & Language**
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi\&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python\&logoColor=white)

**Database & ORM**
![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql\&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-FCA121?logo=python\&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-444444?logo=python\&logoColor=white)

**Infra & Deployment**
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker\&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes\&logoColor=white)
![NaverCloud](https://img.shields.io/badge/NaverCloudPlatform-03C75A?logoColor=white)

---

## 🧩 Service Architecture

```mermaid
flowchart LR
  A[Web] --> B[eeum_Backend_FastAPI]
  B --> C[AI_Server_GPT4oMini_Vision]
  B --> D[(MySQL_DB)]
  B --> E[(File_Storage_uploads)]
  C --> B
  B --> A
```

---

## 🪄 Main API Endpoints

### 📦 Resource

* `POST /resources` – Register new resource (AI-analyzed)
* `GET /resources/me` – List my resources
* `GET /resources/all` – List all resources

### 💬 Request

* `POST /requests` – Register new request (image + description)
* `GET /requests/pending` – View pending requests
* `GET /requests/me` – List my requests

### 🤝 Match / Notification

* `GET /notifications` – List match proposals
* `POST /notifications/confirm` – Accept or decline proposal
* `POST /notifications/manual-match` – Create manual match

### 💰 Points

* Automatically awarded when a match is confirmed (`award_points_if_matched`)

---

## 🗂️ Directory Overview

```text
eeum-backend/
├─ main.py
├─ routers/
│  ├─ resources.py
│  ├─ requests.py
│  ├─ notifications.py
│  ├─ auth.py
│  └─ friends.py
├─ services/
│  ├─ ai_client.py
│  ├─ resource_service.py
│  ├─ request_service.py
│  └─ point_service.py
├─ schemas/
├─ models/
├─ core/
└─ uploads/
```

---

## ⚡ Quick Start

### 1️⃣ Environment Setup

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/eeum
AI_SERVER_URL=http://ai-server:8000
SECRET_KEY=your_secret_key
CORS_ORIGINS=*
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run Migrations

```bash
alembic upgrade head
```

### 4️⃣ Start Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧠 AI Integration Flow

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant BE as Backend
  participant AI as AI_Server
  participant DB as MySQL

  FE->>BE: POST /requests (image + description)
  BE->>AI: Send image URL
  AI-->>BE: Return analysis (item_type, material_type, title, value)
  BE->>DB: Save results
  BE-->>FE: Return created request with AI data
```

---

## 📦 Deployment

* **Platform**: Naver Cloud Kubernetes Service (NKS)
* **Registry**: Naver Container Registry (NCR)
* **Structure**:

  * `eeum-backend` → Deployment + Service + Ingress
  * `eeum-ai` → Separate Deployment
  * `mysql` → PersistentVolume + Service
  * `uploads` → PVC-mounted shared storage

---

## 🪪 License & Credits

* Part of the **K-PaaS (eeum)** project — a circular economy platform using AI image analysis and resource matching.
* © 2025 eeum team. All rights reserved.

---
