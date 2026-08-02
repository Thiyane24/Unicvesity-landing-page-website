# Unicvesity Worldwide — Full-Stack Lead Generation System

A complete, end-to-end lead generation architecture built for **Unicvesity Worldwide**. This system captures mobile and social media traffic — primarily from Instagram Reels and TikTok — via a high-converting frontend landing page, and routes captured leads through a secure, serverless backend API into a CRM or automated WhatsApp pipeline.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [License](#license)

---

## System Architecture

The system is built on a **decoupled frontend/backend architecture** to maximise speed, security, and scalability across each layer independently.

```
[Instagram Reels / TikTok Traffic]
            │
            ▼
  ┌─────────────────────┐
  │   Landing Page      │  ← HTML5 + Tailwind CSS + Vanilla JS
  │   (GitHub Pages /   │     Custom video player, lead form,
  │    Vercel Edge)     │     zero-distraction UI
  └────────┬────────────┘
           │ POST /api/leads (JSON)
           ▼
  ┌─────────────────────┐
  │   Backend API       │  ← FastAPI (Python) or Express (Node.js)
  │   (Vercel           │     Data validation, CORS enforcement,
  │    Serverless)      │     webhook routing
  └────────┬────────────┘
           │
           ▼
  ┌─────────────────────┐
  │   CRM / Database    │  ← SQL Database or WhatsApp API
  │                     │     Validated leads routed instantly
  └─────────────────────┘
```

### 1. Frontend — Landing Page

| Property | Detail |
|---|---|
| **Stack** | HTML5, Vanilla JavaScript (ES6+), Tailwind CSS |
| **Hosting** | GitHub Pages or Vercel Edge Network |
| **Design** | Premium black-and-gold UI, mobile-first, zero navigation distractions |

The landing page is engineered as a **single conversion funnel**. Standard corporate navigation is removed entirely to force one action: form submission. The UI pacing and video structure are designed to match the consumption pattern of short-form social content, reducing drop-off from paid traffic.

### 2. Backend API — Data Pipeline

| Property | Detail |
|---|---|
| **Stack** | Python (FastAPI) or Node.js (Express) as Serverless Functions |
| **Hosting** | Vercel Serverless |
| **Responsibility** | JSON validation, CORS enforcement, lead routing |

The API receives the lead payload from the frontend, validates all required fields (Name, Email, WhatsApp number, Study Destination), enforces strict CORS policies, and routes the data downstream to the CRM or WhatsApp automation layer.

### 3. CRM / Database Integration

The backend is engineered to instantly route validated leads into one or both of the following:

- A structured **SQL database** for persistent lead storage and reporting
- **Unicvesity's CRM or WhatsApp Automation API** via secure webhooks for instant follow-up

---

## Key Features

**Algorithmic Marketing Sync**
The frontend video pacing and UI structure are designed to match short-form social media content (Instagram Reels, TikTok) for high viewer retention and lower bounce rates from paid campaigns.

**Anti-Leaky Bucket Strategy**
All standard website navigation is removed. The page has one entry point and one exit: the lead capture form. Every design decision reduces friction toward submission.

**Custom Video Overlay**
A premium gold-UI play button manages native browser audio security restrictions, ensuring the promotional video plays with sound upon user interaction without triggering browser autoplay blocks.

**Asynchronous Form Submission**
Lead data is POSTed to the API without a page reload. On success, a smooth success UI and loading animations confirm submission, maintaining a premium user experience throughout.

**CORS & Security**
The backend is strictly configured to accept cross-origin requests only from the approved frontend domain. No other origin can submit data to the API.

---

## Project Structure

```
unicvesity-landing/
├── index.html              # Main landing page
├── 0802.mp4                # Promotional video asset
├── assets/
│   └── *.webp              # Optimised image assets
├── api/
│   ├── main.py             # FastAPI entry point (or index.js for Express)
│   ├── requirements.txt    # Python dependencies
│   └── vercel.json         # Vercel serverless routing config
└── README.md
```

---

## Local Development

### Prerequisites

- Python 3.9+ or Node.js 18+
- Git
- VS Code with Live Server extension (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Thiyane24/Unicvesity-landing-page-website.git
cd Unicvesity-landing-page-website
```

### 2. Run the Frontend

Start a local server to prevent CORS and file path errors. Choose one of the following:

**VS Code (recommended):**
Install the [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) extension and click **Go Live** in the status bar.

**Python:**
```bash
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser. Ensure `0802.mp4` and all `.webp` image assets are present in the root directory.

### 3. Run the Backend API

Navigate to the API directory:

```bash
cd api
```

Install dependencies:

```bash
# FastAPI
pip install fastapi uvicorn

# or Express
npm install
```

Start the development server:

```bash
# FastAPI
uvicorn main:app --reload

# Express
node index.js
```

### 4. Connect Frontend to Local API

In `index.html`, update the `API_BASE_URL` variable in the script section:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000"; // or your local port
```

---

## Deployment

### Frontend

Push to the `main` branch and enable **GitHub Pages** under repository Settings → Pages, or link the root directory to **Vercel** for edge deployment.

### Backend

Link the `api/` directory to **Vercel**. Ensure `vercel.json` is correctly configured for serverless function routing:

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/main.py" }
  ]
}
```

### Post-Deployment CORS Update

Once both services are live:

1. Update the backend CORS `allow_origins` to the live frontend URL (e.g. `https://thiyane24.github.io`)
2. Update the frontend `API_BASE_URL` to the live Vercel API URL (e.g. `https://your-api.vercel.app`)

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `ALLOWED_ORIGIN` | Approved frontend domain for CORS | `https://thiyane24.github.io` |
| `CRM_WEBHOOK_URL` | Downstream CRM or WhatsApp API endpoint | `https://crm.example.com/webhook` |
| `DATABASE_URL` | SQL database connection string (if applicable) | `postgresql://user:pass@host/db` |

Create a `.env` file in the `api/` directory and never commit it to version control.

---

## License

This codebase and system architecture are **proprietary** and built specifically for **Unicvesity Worldwide**. Unauthorised reproduction, distribution, or modification is strictly prohibited.

---

*Built by [Thiyane Xavier](https://github.com/Thiyane24) — WebSimples.mz*
