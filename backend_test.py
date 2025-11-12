#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import random
import string

class RationFraudDetectionAPITester:
    def __init__(self, base_url="https://rationfraudwatch.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_id = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                return False, error_msg

        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def generate_test_data(self):
        """Generate test data"""
        timestamp = datetime.now().strftime('%H%M%S')
        return {
            "admin": {
                "username": f"testadmin_{timestamp}",
                "email": f"admin_{timestamp}@test.gov.in",
                "password": "TestAdmin123!"
            },
            "user": {
                "aadhaar_id": f"1234-5678-{timestamp}",
                "name": f"Test User {timestamp}",
                "address": f"Test Address {timestamp}",
                "district": "Test District",
                "state": "Test State",
                "family_size": 4,
                "income": 50000,
                "card_type": "BPL",
                "phone": f"9876543{timestamp[-3:]}"
            }
        }

    def test_admin_registration(self):
        """Test admin registration"""
        test_data = self.generate_test_data()
        success, response = self.make_request('POST', 'auth/register', test_data["admin"], 200)
        
        if success:
            self.admin_id = response.get('id')
            self.log_test("Admin Registration", True, f"Admin ID: {self.admin_id}")
            return test_data["admin"]
        else:
            self.log_test("Admin Registration", False, response)
            return None

    def test_admin_login(self, admin_data):
        """Test admin login"""
        if not admin_data:
            self.log_test("Admin Login", False, "No admin data available")
            return False

        login_data = {
            "email": admin_data["email"],
            "password": admin_data["password"]
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            user_info = response.get('user', {})
            self.log_test("Admin Login", True, f"Token received, User: {user_info.get('username')}")
            return True
        else:
            self.log_test("Admin Login", False, response)
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.make_request('GET', 'analytics/dashboard', expected_status=200)
        
        if success:
            required_fields = ['total_users', 'active_users', 'flagged_users', 'pending_alerts', 'total_transactions']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_test("Dashboard Stats", True, f"All stats available: {list(response.keys())}")
            else:
                self.log_test("Dashboard Stats", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Dashboard Stats", False, response)

    def test_create_user(self):
        """Test user creation"""
        test_data = self.generate_test_data()
        success, response = self.make_request('POST', 'users', test_data["user"], 200)
        
        if success:
            self.test_user_id = response.get('id')
            self.log_test("Create User", True, f"User ID: {self.test_user_id}")
            return True
        else:
            self.log_test("Create User", False, response)
            return False

    def test_get_users(self):
        """Test get users list"""
        success, response = self.make_request('GET', 'users', expected_status=200)
        
        if success:
            user_count = len(response) if isinstance(response, list) else 0
            self.log_test("Get Users", True, f"Retrieved {user_count} users")
        else:
            self.log_test("Get Users", False, response)

    def test_user_search(self):
        """Test user search functionality"""
        success, response = self.make_request('GET', 'users?search=Test', expected_status=200)
        
        if success:
            self.log_test("User Search", True, f"Search returned {len(response)} results")
        else:
            self.log_test("User Search", False, response)

    def test_user_status_filter(self):
        """Test user status filtering"""
        success, response = self.make_request('GET', 'users?status=active', expected_status=200)
        
        if success:
            self.log_test("User Status Filter", True, f"Filter returned {len(response)} active users")
        else:
            self.log_test("User Status Filter", False, response)

    def test_aadhaar_verification(self):
        """Test Aadhaar verification (mocked)"""
        if not self.test_user_id:
            self.log_test("Aadhaar Verification", False, "No test user available")
            return

        success, response = self.make_request('POST', f'users/{self.test_user_id}/verify', expected_status=200)
        
        if success:
            verified = response.get('verified')
            message = response.get('message', '')
            self.log_test("Aadhaar Verification", True, f"Verified: {verified}, Message: {message}")
        else:
            self.log_test("Aadhaar Verification", False, response)

    def test_fraud_scan(self):
        """Test fraud detection scan"""
        if not self.test_user_id:
            self.log_test("Fraud Scan", False, "No test user available")
            return

        success, response = self.make_request('POST', f'fraud-alerts/scan/{self.test_user_id}', expected_status=200)
        
        if success:
            alerts_created = response.get('alerts_created', 0)
            message = response.get('message', '')
            self.log_test("Fraud Scan", True, f"Alerts created: {alerts_created}, Message: {message}")
        else:
            self.log_test("Fraud Scan", False, response)

    def test_user_status_update(self):
        """Test user status update"""
        if not self.test_user_id:
            self.log_test("User Status Update", False, "No test user available")
            return

        success, response = self.make_request('PATCH', f'users/{self.test_user_id}/status?status=suspended', expected_status=200)
        
        if success:
            self.log_test("User Status Update", True, "User status updated to suspended")
        else:
            self.log_test("User Status Update", False, response)

    def test_get_fraud_alerts(self):
        """Test get fraud alerts"""
        success, response = self.make_request('GET', 'fraud-alerts', expected_status=200)
        
        if success:
            alert_count = len(response) if isinstance(response, list) else 0
            self.log_test("Get Fraud Alerts", True, f"Retrieved {alert_count} alerts")
        else:
            self.log_test("Get Fraud Alerts", False, response)

    def test_fraud_alert_filter(self):
        """Test fraud alert filtering"""
        success, response = self.make_request('GET', 'fraud-alerts?status=pending', expected_status=200)
        
        if success:
            self.log_test("Fraud Alert Filter", True, f"Filter returned {len(response)} pending alerts")
        else:
            self.log_test("Fraud Alert Filter", False, response)

    def test_get_transactions(self):
        """Test get transactions"""
        success, response = self.make_request('GET', 'transactions', expected_status=200)
        
        if success:
            txn_count = len(response) if isinstance(response, list) else 0
            self.log_test("Get Transactions", True, f"Retrieved {txn_count} transactions")
        else:
            self.log_test("Get Transactions", False, response)

    def test_analytics_fraud_by_type(self):
        """Test fraud analytics by type"""
        success, response = self.make_request('GET', 'analytics/fraud-by-type', expected_status=200)
        
        if success:
            self.log_test("Analytics - Fraud by Type", True, f"Retrieved {len(response)} fraud types")
        else:
            self.log_test("Analytics - Fraud by Type", False, response)

    def test_analytics_fraud_by_district(self):
        """Test fraud analytics by district"""
        success, response = self.make_request('GET', 'analytics/fraud-by-district', expected_status=200)
        
        if success:
            self.log_test("Analytics - Fraud by District", True, f"Retrieved {len(response)} districts")
        else:
            self.log_test("Analytics - Fraud by District", False, response)

    def test_analytics_transactions_trend(self):
        """Test transaction trends analytics"""
        success, response = self.make_request('GET', 'analytics/transactions-trend', expected_status=200)
        
        if success:
            self.log_test("Analytics - Transaction Trends", True, f"Retrieved {len(response)} data points")
        else:
            self.log_test("Analytics - Transaction Trends", False, response)

    def test_ml_status(self):
        """Test ML model status"""
        success, response = self.make_request('GET', 'ml/status', expected_status=200)
        
        if success:
            is_trained = response.get('is_trained', False)
            model_type = response.get('model_type', 'Unknown')
            self.log_test("ML Model Status", True, f"Trained: {is_trained}, Type: {model_type}")
        else:
            self.log_test("ML Model Status", False, response)

    def test_ml_training(self):
        """Test ML model training"""
        success, response = self.make_request('POST', 'ml/train', expected_status=200)
        
        if success:
            training_success = response.get('success', False)
            message = response.get('message', '')
            self.log_test("ML Model Training", True, f"Training success: {training_success}, Message: {message}")
        else:
            self.log_test("ML Model Training", False, response)

    def run_all_tests(self):
        """Run all API tests"""
        print("[ROCKET] Starting Ration Fraud Detection API Tests")
        print("=" * 60)
        
        # Authentication Tests
        print("\n[CLIPBOARD] Authentication Tests")
        admin_data = self.test_admin_registration()
        if not self.test_admin_login(admin_data):
            print("[FAIL] Cannot proceed without authentication")
            return self.generate_report()

        # Dashboard Tests
        print("\n[CHART] Dashboard Tests")
        self.test_dashboard_stats()

        # User Management Tests
        print("\n[USERS] User Management Tests")
        self.test_create_user()
        self.test_get_users()
        self.test_user_search()
        self.test_user_status_filter()
        self.test_aadhaar_verification()
        self.test_user_status_update()

        # Fraud Detection Tests
        print("\n[SEARCH] Fraud Detection Tests")
        self.test_fraud_scan()
        self.test_get_fraud_alerts()
        self.test_fraud_alert_filter()

        # Transaction Tests
        print("\n[CARD] Transaction Tests")
        self.test_get_transactions()

        # Analytics Tests
        print("\n[GRAPH] Analytics Tests")
        self.test_analytics_fraud_by_type()
        self.test_analytics_fraud_by_district()
        self.test_analytics_transactions_trend()

        # ML Tests
        print("\n[ML] Machine Learning Tests")
        self.test_ml_status()
        self.test_ml_training()

        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("[REPORT] TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n[FAILED] Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = RationFraudDetectionAPITester()
    report = tester.run_all_tests()
    
    # Save detailed report
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n[REPORT] Detailed report saved to: /app/test_reports/backend_test_results.json")
    
    # Return appropriate exit code
    return 0 if report['failed_tests'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())