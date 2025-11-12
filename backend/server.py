from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import random
from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - with fallback to mock database
mongo_available = False
client = None
db = None

try:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    from pymongo import MongoClient
    # Quick check if MongoDB is running
    try_client = MongoClient(mongo_url, serverSelectionTimeoutMS=1000)
    try_client.server_info()  # This will raise if server not available
    try_client.close()
    
    # If we got here, MongoDB is available
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'ration_fraud_detection')]
    mongo_available = True
    print("[INFO] Connected to MongoDB successfully")
except Exception as e:
    print(f"[INFO] MongoDB not available: {str(e)[:100]}")
    mongo_available = False

# If MongoDB is not available, use mock database
if not mongo_available:
    print("[INFO] Using mock in-memory database instead")
    from mock_db import MockDatabase
    db = MockDatabase()
    client = None

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ==================== Models ====================

class AdminUser(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    role: str = "admin"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminUserCreate(BaseModel):
    username: str
    email: str
    password: str

class AdminLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class RationUser(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    aadhaar_id: str
    name: str
    address: str
    district: str
    state: str
    family_size: int
    income: float
    card_type: str  # APL, BPL, Antyodaya
    phone: str
    status: str = "active"  # active, suspended, flagged
    verification_status: str = "pending"  # pending, verified, rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RationUserCreate(BaseModel):
    aadhaar_id: str
    name: str
    address: str
    district: str
    state: str
    family_size: int
    income: float
    card_type: str
    phone: str

class RationCard(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    card_number: str
    user_id: str
    issue_date: datetime
    validity: datetime
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RationShop(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    shop_id: str
    name: str
    district: str
    state: str
    location: Dict[str, float]  # lat, lng
    officer_name: str
    phone: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    card_number: str
    user_id: str
    shop_id: str
    items: List[Dict[str, Any]]  # [{name, quantity, price}]
    total_amount: float
    transaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    card_number: str
    user_id: str
    shop_id: str
    items: List[Dict[str, Any]]
    total_amount: float

class FraudAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    fraud_type: str
    confidence_score: float
    details: Dict[str, Any]
    status: str = "pending"  # pending, confirmed, dismissed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class FraudAlertUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== Fraud Detection Engine ====================

class FraudDetectionEngine:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
    
    async def detect_fraud_rules(self, user_id: str) -> List[Dict[str, Any]]:
        """Rule-based fraud detection"""
        alerts = []
        
        # Get user data
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            return alerts
        
        # Rule 1: Check for duplicate Aadhaar
        duplicate_aadhaar = await db.users.count_documents({
            "aadhaar_id": user["aadhaar_id"],
            "id": {"$ne": user_id}
        })
        if duplicate_aadhaar > 0:
            alerts.append({
                "fraud_type": "Duplicate Aadhaar",
                "confidence_score": 0.95,
                "details": {
                    "message": f"Found {duplicate_aadhaar} other users with same Aadhaar ID",
                    "aadhaar_id": user["aadhaar_id"]
                }
            })
        
        # Rule 2: Check for duplicate address
        duplicate_address = await db.users.count_documents({
            "address": user["address"],
            "id": {"$ne": user_id}
        })
        if duplicate_address > 1:
            alerts.append({
                "fraud_type": "Duplicate Address",
                "confidence_score": 0.75,
                "details": {
                    "message": f"Found {duplicate_address} other users with same address",
                    "address": user["address"]
                }
            })
        
        # Rule 3: Check transaction frequency
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        transactions = await db.transactions.find({
            "user_id": user_id,
            "transaction_date": {"$gte": thirty_days_ago.isoformat()}
        }).to_list(None)
        
        if len(transactions) > 40:  # More than 40 transactions in 30 days
            alerts.append({
                "fraud_type": "Abnormal Transaction Frequency",
                "confidence_score": 0.85,
                "details": {
                    "message": f"Unusually high transaction frequency: {len(transactions)} in 30 days",
                    "transaction_count": len(transactions)
                }
            })
        
        # Rule 4: Check for multiple cards
        cards = await db.cards.count_documents({"user_id": user_id, "status": "active"})
        if cards > 1:
            alerts.append({
                "fraud_type": "Multiple Active Cards",
                "confidence_score": 0.90,
                "details": {
                    "message": f"User has {cards} active ration cards",
                    "card_count": cards
                }
            })
        
        # Rule 5: Income vs card type mismatch
        if user.get("card_type") == "BPL" and user.get("income", 0) > 100000:
            alerts.append({
                "fraud_type": "Income-Card Type Mismatch",
                "confidence_score": 0.70,
                "details": {
                    "message": f"BPL card holder with income: ₹{user.get('income')}",
                    "income": user.get("income"),
                    "card_type": user.get("card_type")
                }
            })
        
        return alerts
    
    async def train_model(self):
        """Train ML model with transaction data"""
        try:
            transactions = await db.transactions.find({}, {"_id": 0}).to_list(None)
            if len(transactions) < 10:
                return False
            
            # Feature engineering
            features = []
            for txn in transactions:
                feature_vector = [
                    len(txn.get("items", [])),
                    txn.get("total_amount", 0),
                    datetime.fromisoformat(txn["transaction_date"]).hour if isinstance(txn.get("transaction_date"), str) else txn.get("transaction_date").hour,
                ]
                features.append(feature_vector)
            
            X = np.array(features)
            self.model.fit(X)
            self.is_trained = True
            return True
        except Exception as e:
            logging.error(f"Model training error: {e}")
            return False
    
    def predict_anomaly(self, transaction_features: List[float]) -> float:
        """Predict if transaction is anomalous"""
        if not self.is_trained:
            return 0.5
        
        try:
            X = np.array([transaction_features])
            prediction = self.model.predict(X)
            score = self.model.score_samples(X)
            
            # Convert to confidence score (0-1)
            confidence = 1 / (1 + np.exp(score[0]))
            return float(confidence)
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return 0.5

fraud_engine = FraudDetectionEngine()

# ==================== Authentication Routes ====================

@api_router.post("/auth/register", response_model=AdminUser)
async def register_admin(admin: AdminUserCreate):
    try:
        # Check if user exists
        existing = await db.admins.find_one({"email": admin.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        admin_obj = AdminUser(
            username=admin.username,
            email=admin.email,
            password_hash=hash_password(admin.password)
        )
        
        doc = admin_obj.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.admins.insert_one(doc)
        
        return admin_obj
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = str(e)
        tb = traceback.format_exc()
        print(f"[ERROR] Registration error: {error_msg}")
        print(f"[TRACEBACK] {tb}")
        raise HTTPException(status_code=500, detail=f"Registration error: {error_msg}")

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: AdminLogin):
    admin = await db.admins.find_one({"email": credentials.email}, {"_id": 0})
    if not admin or not verify_password(credentials.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": admin["id"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": admin["id"],
            "username": admin["username"],
            "email": admin["email"],
            "role": admin.get("role", "admin")
        }
    }

# ==================== User Management Routes ====================

@api_router.post("/users", response_model=RationUser)
async def create_user(user: RationUserCreate, current_user: str = Depends(get_current_user)):
    # Check for duplicate Aadhaar
    existing = await db.users.find_one({"aadhaar_id": user.aadhaar_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Aadhaar ID already registered")
    
    user_obj = RationUser(**user.model_dump())
    doc = user_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Run fraud detection
    alerts = await fraud_engine.detect_fraud_rules(user_obj.id)
    for alert in alerts:
        fraud_alert = FraudAlert(
            user_id=user_obj.id,
            fraud_type=alert["fraud_type"],
            confidence_score=alert["confidence_score"],
            details=alert["details"]
        )
        fraud_doc = fraud_alert.model_dump()
        fraud_doc['created_at'] = fraud_doc['created_at'].isoformat()
        await db.fraud_alerts.insert_one(fraud_doc)
    
    return user_obj

@api_router.get("/users", response_model=List[RationUser])
async def get_users(current_user: str = Depends(get_current_user), 
                   status: Optional[str] = None,
                   search: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"aadhaar_id": {"$regex": search, "$options": "i"}}
        ]
    
    users = await db.users.find(query, {"_id": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

@api_router.get("/users/{user_id}", response_model=RationUser)
async def get_user(user_id: str, current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    return user

@api_router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str, current_user: str = Depends(get_current_user)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Status updated successfully"}

@api_router.post("/users/{user_id}/verify")
async def verify_user(user_id: str, current_user: str = Depends(get_current_user)):
    """Simulate Aadhaar verification"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simulate verification (90% success rate)
    verified = random.random() < 0.9
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"verification_status": "verified" if verified else "rejected"}}
    )
    
    return {
        "verified": verified,
        "message": "Aadhaar verification successful" if verified else "Aadhaar verification failed"
    }

# ==================== Transaction Routes ====================

@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction: TransactionCreate, current_user: str = Depends(get_current_user)):
    txn_obj = Transaction(**transaction.model_dump())
    doc = txn_obj.model_dump()
    doc['transaction_date'] = doc['transaction_date'].isoformat()
    await db.transactions.insert_one(doc)
    
    # Check for anomalies using ML
    features = [
        len(transaction.items),
        transaction.total_amount,
        datetime.now(timezone.utc).hour
    ]
    anomaly_score = fraud_engine.predict_anomaly(features)
    
    if anomaly_score > 0.7:
        fraud_alert = FraudAlert(
            user_id=transaction.user_id,
            fraud_type="Anomalous Transaction Pattern",
            confidence_score=anomaly_score,
            details={
                "message": "Transaction flagged as potentially fraudulent by ML model",
                "transaction_id": txn_obj.id,
                "amount": transaction.total_amount
            }
        )
        fraud_doc = fraud_alert.model_dump()
        fraud_doc['created_at'] = fraud_doc['created_at'].isoformat()
        await db.fraud_alerts.insert_one(fraud_doc)
    
    return txn_obj

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: str = Depends(get_current_user), user_id: Optional[str] = None):
    query = {}
    if user_id:
        query["user_id"] = user_id
    
    transactions = await db.transactions.find(query, {"_id": 0}).sort("transaction_date", -1).to_list(500)
    for txn in transactions:
        if isinstance(txn.get('transaction_date'), str):
            txn['transaction_date'] = datetime.fromisoformat(txn['transaction_date'])
    return transactions

# ==================== Fraud Alert Routes ====================

@api_router.get("/fraud-alerts", response_model=List[FraudAlert])
async def get_fraud_alerts(current_user: str = Depends(get_current_user), status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    
    alerts = await db.fraud_alerts.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    for alert in alerts:
        if isinstance(alert.get('created_at'), str):
            alert['created_at'] = datetime.fromisoformat(alert['created_at'])
        if alert.get('resolved_at') and isinstance(alert['resolved_at'], str):
            alert['resolved_at'] = datetime.fromisoformat(alert['resolved_at'])
    return alerts

@api_router.patch("/fraud-alerts/{alert_id}")
async def update_fraud_alert(alert_id: str, update: FraudAlertUpdate, current_user: str = Depends(get_current_user)):
    update_data = {"status": update.status}
    if update.status in ["confirmed", "dismissed"]:
        update_data["resolved_at"] = datetime.now(timezone.utc).isoformat()
        update_data["resolved_by"] = current_user
    
    result = await db.fraud_alerts.update_one(
        {"id": alert_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # If confirmed, update user status
    if update.status == "confirmed":
        alert = await db.fraud_alerts.find_one({"id": alert_id}, {"_id": 0})
        if alert:
            await db.users.update_one(
                {"id": alert["user_id"]},
                {"$set": {"status": "flagged"}}
            )
    
    return {"message": "Alert updated successfully"}

@api_router.post("/fraud-alerts/scan/{user_id}")
async def scan_user_for_fraud(user_id: str, current_user: str = Depends(get_current_user)):
    """Manually trigger fraud scan for a user"""
    alerts = await fraud_engine.detect_fraud_rules(user_id)
    
    for alert in alerts:
        # Check if similar alert already exists
        existing = await db.fraud_alerts.find_one({
            "user_id": user_id,
            "fraud_type": alert["fraud_type"],
            "status": "pending"
        }, {"_id": 0})
        
        if not existing:
            fraud_alert = FraudAlert(
                user_id=user_id,
                fraud_type=alert["fraud_type"],
                confidence_score=alert["confidence_score"],
                details=alert["details"]
            )
            fraud_doc = fraud_alert.model_dump()
            fraud_doc['created_at'] = fraud_doc['created_at'].isoformat()
            await db.fraud_alerts.insert_one(fraud_doc)
    
    return {
        "alerts_created": len(alerts),
        "message": f"Found {len(alerts)} potential fraud indicators"
    }

# ==================== Analytics Routes ====================

@api_router.get("/analytics/dashboard")
async def get_dashboard_stats(current_user: str = Depends(get_current_user)):
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"status": "active"})
    flagged_users = await db.users.count_documents({"status": "flagged"})
    pending_verifications = await db.users.count_documents({"verification_status": "pending"})
    
    total_transactions = await db.transactions.count_documents({})
    pending_alerts = await db.fraud_alerts.count_documents({"status": "pending"})
    confirmed_frauds = await db.fraud_alerts.count_documents({"status": "confirmed"})
    
    # Recent activity
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_users = await db.users.count_documents({
        "created_at": {"$gte": seven_days_ago.isoformat()}
    })
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "flagged_users": flagged_users,
        "pending_verifications": pending_verifications,
        "total_transactions": total_transactions,
        "pending_alerts": pending_alerts,
        "confirmed_frauds": confirmed_frauds,
        "recent_users": recent_users
    }

@api_router.get("/analytics/fraud-by-type")
async def get_fraud_by_type(current_user: str = Depends(get_current_user)):
    """Get fraud cases grouped by type"""
    alerts = await db.fraud_alerts.find({}, {"_id": 0}).to_list(None)
    
    fraud_types = {}
    for alert in alerts:
        fraud_type = alert.get("fraud_type", "Unknown")
        if fraud_type not in fraud_types:
            fraud_types[fraud_type] = 0
        fraud_types[fraud_type] += 1
    
    return [{"type": k, "count": v} for k, v in fraud_types.items()]

@api_router.get("/analytics/fraud-by-district")
async def get_fraud_by_district(current_user: str = Depends(get_current_user)):
    """Get fraud hotspots by district"""
    alerts = await db.fraud_alerts.find({}, {"_id": 0}).to_list(None)
    
    district_map = {}
    for alert in alerts:
        user = await db.users.find_one({"id": alert["user_id"]}, {"_id": 0})
        if user:
            district = user.get("district", "Unknown")
            if district not in district_map:
                district_map[district] = 0
            district_map[district] += 1
    
    return [{"district": k, "count": v} for k, v in district_map.items()]

@api_router.get("/analytics/transactions-trend")
async def get_transactions_trend(current_user: str = Depends(get_current_user)):
    """Get transaction trends over last 30 days"""
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    transactions = await db.transactions.find({
        "transaction_date": {"$gte": thirty_days_ago.isoformat()}
    }, {"_id": 0}).to_list(None)
    
    daily_counts = {}
    for txn in transactions:
        date_str = txn["transaction_date"][:10]  # Get date part
        if date_str not in daily_counts:
            daily_counts[date_str] = 0
        daily_counts[date_str] += 1
    
    return [{"date": k, "count": v} for k, v in sorted(daily_counts.items())]

# ==================== ML Model Routes ====================

@api_router.post("/ml/train")
async def train_model(current_user: str = Depends(get_current_user)):
    """Train fraud detection ML model"""
    success = await fraud_engine.train_model()
    return {
        "success": success,
        "message": "Model trained successfully" if success else "Insufficient data for training"
    }

@api_router.get("/ml/status")
async def get_model_status(current_user: str = Depends(get_current_user)):
    return {
        "is_trained": fraud_engine.is_trained,
        "model_type": "Isolation Forest"
    }

# ==================== Shops Routes ====================

@api_router.get("/shops", response_model=List[RationShop])
async def get_shops(current_user: str = Depends(get_current_user)):
    shops = await db.shops.find({}, {"_id": 0}).to_list(500)
    for shop in shops:
        if isinstance(shop.get('created_at'), str):
            shop['created_at'] = datetime.fromisoformat(shop['created_at'])
    return shops

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    if client is not None:
        client.close()
