# CloudSecure E-Commerce

A complete learning/demo e-commerce website built with Python Flask and SQLite.

## Features

- Professional responsive storefront
- Product search and category filters
- Product detail pages
- Shopping cart
- Quantity update/remove
- Checkout form
- SQLite order persistence
- Order confirmation
- Health endpoint: `/api/health`
- Product API: `/api/products`
- Gunicorn production server
- Nginx reverse-proxy configuration
- Cloudflare-ready architecture

## 1. Run locally on Windows PowerShell

```powershell
cd CloudSecure-Ecommerce
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:

`http://127.0.0.1:8000`

Health:

`http://127.0.0.1:8000/api/health`

Expected:

```json
{
  "service": "CloudSecure E-Commerce",
  "status": "healthy",
  "database": "connected"
}
```

## 2. Production architecture

User
-> Cloudflare DNS/Proxy
-> Cloudflare WAF / Rate Limiting / DDoS
-> HTTPS
-> AWS EC2 Ubuntu
-> Nginx
-> Gunicorn
-> Flask
-> SQLite

## 3. AWS deployment

The `deploy/` directory contains:

- `cloudsecure.service` for systemd + Gunicorn
- `nginx.conf` for Nginx reverse proxy

These are templates. Change the domain and secret before production use.

## Important

This is a portfolio/interview/demo project. The checkout is intentionally a demo and does not process real payments. For a real store, use a production database, proper authentication, CSRF protection, secure secret management, HTTPS, payment gateway, inventory transactions, backups and monitoring.
