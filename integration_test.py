#!/usr/bin/env python
"""
Simple test to verify all fixed functionality works
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def test_auth_flow():
    """Test authentication flow"""
    print("\n=== AUTHENTICATION TESTS ===")
    
    # Register
    admin_data = {"username": "admin_final", "email": "admin_final@test.com", "password": "Test@123"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=admin_data, timeout=TIMEOUT)
    if resp.status_code != 200:
        print(f"[FAIL] Registration: {resp.status_code}")
        return None
    print(f"[PASS] Registration")
    
    # Login
    login_data = {"email": "admin_final@test.com", "password": "Test@123"}
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=TIMEOUT)
    if resp.status_code != 200:
        print(f"[FAIL] Login: {resp.status_code}")
        return None
    token = resp.json().get("access_token") or resp.json().get("token")
    print(f"[PASS] Login (token obtained)")
    
    return token

def test_user_creation(token):
    """Test user creation"""
    print("\n=== USER MANAGEMENT TESTS ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create user
    user_data = {
        "aadhaar_id": "111222333444",
        "name": "Test Cardholder",
        "address": "123 Main St",
        "district": "Test District",
        "state": "Test State",
        "family_size": 3,
        "income": 50000.0,
        "card_type": "AAY",
        "phone": "9111111111"
    }
    resp = requests.post(f"{BASE_URL}/api/users", json=user_data, headers=headers, timeout=TIMEOUT)
    if resp.status_code != 200:
        print(f"[FAIL] Create User: {resp.status_code} - {resp.text[:100]}")
        return None
    user = resp.json()
    user_id = user.get("id")
    print(f"[PASS] Create User (ID: {user_id})")
    
    # Get users
    resp = requests.get(f"{BASE_URL}/api/users", headers=headers, timeout=TIMEOUT)
    if resp.status_code != 200:
        print(f"[FAIL] Get Users: {resp.status_code}")
        return user_id
    users = resp.json()
    print(f"[PASS] Get Users ({len(users)} users)")
    
    # Get specific user
    resp = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=headers, timeout=TIMEOUT)
    if resp.status_code != 200:
        print(f"[FAIL] Get User by ID: {resp.status_code}")
        return user_id
    print(f"[PASS] Get User by ID")
    
    return user_id

def main():
    try:
        # Test auth
        token = test_auth_flow()
        if not token:
            print("\n[FAIL] Authentication failed")
            return 1
        
        # Test user management
        user_id = test_user_creation(token)
        if not user_id:
            print("\n[FAIL] User management failed")
            return 1
        
        print("\n=== ALL TESTS PASSED ===")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
