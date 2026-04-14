import requests
import sys
from datetime import datetime

class TuningTalalkozoAPITester:
    def __init__(self, base_url="https://autotune-central.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('api/') else f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            print(f"   Status: {response.status_code}")
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Expected: {expected_status}, Got: {response.status_code}")
                try:
                    response_data = response.json()
                    if 'token' in response_data:
                        print("   Contains auth token ✓")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected: {expected_status}, Got: {response.status_code}")
                self.failed_tests.append({
                    'test': name,
                    'endpoint': endpoint,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'error': response.text[:200] if response.text else 'No error message'
                })
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Network/Connection Error: {str(e)}")
            self.failed_tests.append({
                'test': name,
                'endpoint': endpoint,
                'error': f"Connection error: {str(e)}"
            })
            return False, {}

    def test_registration(self):
        """Test user registration"""
        test_user_data = {
            "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'token' in response:
            self.registration_token = response['token']
            self.test_user_id = response.get('user_id')
            print(f"   Registered user ID: {self.test_user_id}")
            return True
        return False

    def test_login_verified_user(self):
        """Test login with verified user credentials"""
        login_data = {
            "email": "test123@example.com",
            "password": "Test123!"
        }
        
        success, response = self.run_test(
            "Login Verified User",
            "POST",
            "auth/login", 
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Logged in user: {response.get('user', {}).get('username', 'Unknown')}")
            return True
        return False

    def test_login_unverified_error(self):
        """Test login with unverified email should return 403"""
        # Register a new user (unverified by default)
        test_user_data = {
            "username": f"unverified_{datetime.now().strftime('%H%M%S')}",
            "email": f"unverified_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }
        
        # First register
        reg_success, _ = self.run_test(
            "Register Unverified User",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if not reg_success:
            return False
            
        # Then try to login - should fail with 403
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        success, response = self.run_test(
            "Login Unverified User (Should Fail)",
            "POST",
            "auth/login",
            403,  # Expecting 403 for unverified email
            data=login_data
        )
        
        return success

    def test_authenticated_endpoints(self):
        """Test endpoints that require authentication"""
        if not self.token:
            print("❌ No auth token available for authenticated tests")
            return False
            
        # Test /api/auth/me
        success, _ = self.run_test(
            "Get Current User",
            "GET", 
            "auth/me",
            200
        )
        
        if not success:
            return False
            
        # Test feed endpoint
        success, _ = self.run_test(
            "Get Feed",
            "GET",
            "posts/feed", 
            200
        )
        
        return success

    def print_summary(self):
        """Print test summary"""
        print(f"\n" + "="*50)
        print(f"📊 Test Summary")
        print(f"="*50)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['test']}")
                print(f"   Endpoint: {test.get('endpoint', 'N/A')}")
                print(f"   Error: {test.get('error', 'Unknown error')}")
                if 'expected' in test and 'actual' in test:
                    print(f"   Expected: {test['expected']}, Got: {test['actual']}")
        
        return len(self.failed_tests) == 0

def main():
    print("🚀 Starting TuningTalálkozó API Tests...")
    tester = TuningTalalkozoAPITester()
    
    success = True
    
    # Test registration
    if not tester.test_registration():
        print("❌ Registration test failed")
        success = False
    
    # Test login with verified user 
    if not tester.test_login_verified_user():
        print("❌ Verified user login test failed")
        success = False
    
    # Test unverified user login error
    if not tester.test_login_unverified_error():
        print("❌ Unverified user error test failed")
        success = False
    
    # Test authenticated endpoints
    if not tester.test_authenticated_endpoints():
        print("❌ Authenticated endpoints test failed")
        success = False
    
    # Print summary
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())