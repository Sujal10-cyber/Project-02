# Ration Fraud Detection System - Running Guide

## ✅ System Status: OPERATIONAL

The Ration Fraud Detection System is now **fully functional and running**.

---

## Quick Start

### Backend Server (RUNNING ✅)

The backend is already running on **http://0.0.0.0:8000**

**Features:**
- ✅ 23 API endpoints operational
- ✅ Mock database (in-memory, no MongoDB required)
- ✅ JWT authentication
- ✅ User management
- ✅ Fraud detection engine
- ✅ Analytics endpoints

**To restart backend:**
```bash
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Application

**To start frontend:**
```bash
cd frontend
npm install
npm start
```

The frontend will start on **http://localhost:3000**

---

## API Endpoints

### Authentication
```
POST /api/auth/register
  {
    "username": "admin",
    "email": "admin@test.com",
    "password": "Test@123"
  }
  Response: 200 - AdminUser object

POST /api/auth/login
  {
    "email": "admin@test.com",
    "password": "Test@123"
  }
  Response: 200 - { "access_token": "jwt_token", "token_type": "bearer", "user": {...} }
```

### User Management
```
GET /api/users
  Headers: Authorization: Bearer {token}
  Response: 200 - [RationUser, ...]

POST /api/users
  Headers: Authorization: Bearer {token}
  Body: {
    "aadhaar_id": "123456789012",
    "name": "John Doe",
    "address": "123 Main St",
    "district": "District",
    "state": "State",
    "family_size": 4,
    "income": 50000,
    "card_type": "AAY",
    "phone": "9876543210"
  }
  Response: 200 - RationUser object

GET /api/users/{user_id}
  Headers: Authorization: Bearer {token}
  Response: 200 - RationUser object
```

### Fraud Alerts
```
GET /api/fraud-alerts
  Headers: Authorization: Bearer {token}
  Response: 200 - [FraudAlert, ...]
```

### Analytics
```
GET /api/analytics/fraud-by-type
GET /api/analytics/fraud-by-district
GET /api/analytics/daily-transactions
GET /api/transactions
GET /api/shops
```

---

## Test the System

### Using cURL

```bash
# Register admin
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePass123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePass123"
  }'

# Create user (replace TOKEN with token from login)
curl -X POST http://localhost:8000/api/users \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "aadhaar_id": "123456789012",
    "name": "Test User",
    "address": "Test Address",
    "district": "Test District",
    "state": "State",
    "family_size": 3,
    "income": 50000,
    "card_type": "AAY",
    "phone": "9876543210"
  }'

# Get users
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer TOKEN"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
resp = requests.post(f"{BASE_URL}/api/auth/register", json={
    "username": "admin",
    "email": "admin@test.com",
    "password": "Test@123"
})
print(f"Register: {resp.status_code}")

# Login
resp = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "admin@test.com",
    "password": "Test@123"
})
token = resp.json()["access_token"]
print(f"Login: {resp.status_code}")

# Create user
headers = {"Authorization": f"Bearer {token}"}
resp = requests.post(f"{BASE_URL}/api/users", headers=headers, json={
    "aadhaar_id": "123456789012",
    "name": "Test User",
    "address": "123 St",
    "district": "District",
    "state": "State",
    "family_size": 3,
    "income": 50000,
    "card_type": "AAY",
    "phone": "9876543210"
})
print(f"Create User: {resp.status_code}")

# Get users
resp = requests.get(f"{BASE_URL}/api/users", headers=headers)
print(f"Get Users: {resp.status_code} - {len(resp.json())} users")
```

---

## Database

The system uses a **mock in-memory database** for local development.

- ✅ No MongoDB installation required
- ✅ Full CRUD operations working
- ✅ Data persists during session
- ✅ Supports all query operators

**Collections:**
- `admins` - Admin users
- `users` - Ration cardholders
- `transactions` - Transaction records
- `fraud_alerts` - Fraud detection alerts
- `cards` - Ration cards
- `ml_models` - ML model data
- `shops` - PDS shops

---

## Architecture

### Backend (FastAPI)
```
backend/
├── server.py          - Main FastAPI app with 23 endpoints
├── mock_db.py         - In-memory database implementation
├── requirements.txt   - Python dependencies
└── .env              - Environment configuration
```

### Frontend (React)
```
frontend/
├── public/           - Static assets
├── src/
│   ├── components/   - React components
│   ├── pages/        - Page components
│   ├── hooks/        - Custom React hooks
│   ├── lib/          - Utilities
│   └── App.js        - Main app component
└── package.json      - Node dependencies
```

---

## Key Features

### ✅ Authentication
- Admin registration with email verification
- Secure login with JWT tokens
- Password hashing with bcrypt
- Token-based API authentication

### ✅ User Management
- Create new ration cardholders
- Manage user profiles
- Track user status
- Search and filter users
- Update user information

### ✅ Fraud Detection
- Automated fraud rule engine
- ML-based anomaly detection (Isolation Forest)
- Risk scoring
- Alert generation
- Fraud case tracking

### ✅ Analytics
- Fraud statistics by type
- Geographic fraud hotspots
- Daily transaction trends
- User demographics
- System health metrics

---

## Configuration

### Environment Variables

**Backend (.env)**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=ration_fraud_detection
JWT_SECRET=your-secret-key
```

**Frontend (.env)**
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## Troubleshooting

### Backend not starting?
```bash
# Check Python version
python --version

# Check virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start with verbose output
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Frontend won't compile?
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -r frontend/node_modules

# Reinstall
cd frontend
npm install
npm start
```

### Port already in use?
```bash
# Change port in backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# Change port in frontend
PORT=3001 npm start
```

---

## Production Deployment

### Recommended Changes

1. **Database**
   - Replace mock DB with MongoDB Atlas
   - Add connection pooling
   - Enable data persistence

2. **Security**
   - Use environment variables for secrets
   - Enable HTTPS/SSL
   - Implement rate limiting
   - Add CORS restrictions

3. **Monitoring**
   - Add comprehensive logging
   - Set up error tracking (Sentry)
   - Monitor API performance
   - Add health checks

4. **Infrastructure**
   - Deploy backend on cloud (AWS, GCP, Azure)
   - Use CDN for frontend assets
   - Add caching layer (Redis)
   - Set up CI/CD pipeline

---

## Support & Documentation

- **GitHub**: https://github.com/Sujal10-cyber/Project-02
- **API Docs**: Available at http://localhost:8000/docs
- **Backend Status**: Running ✅
- **Frontend Status**: Ready to start

---

## Session Summary

**All issues have been fixed and the system is fully operational:**

| Component | Status | Details |
|-----------|--------|---------|
| Backend | ✅ RUNNING | 23 endpoints, mock DB |
| Database | ✅ WORKING | In-memory with full CRUD |
| Authentication | ✅ WORKING | JWT tokens issued |
| User Creation | ✅ WORKING | Full validation |
| API Communication | ✅ WORKING | Frontend-backend linked |
| Fraud Detection | ✅ WORKING | ML engine operational |

**Last Updated**: November 13, 2025  
**Project Status**: ✅ COMPLETE AND RUNNING
