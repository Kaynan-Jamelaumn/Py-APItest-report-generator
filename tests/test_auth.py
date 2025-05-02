from PyTestDocx import BaseAPITest
import unittest
import time

class TestAuthentication(BaseAPITest):
    """Tests for login/logout functionality"""
    
    def test_successful_login(self):
        """Valid credentials should return access token"""
        response = self.login()
        self.assert_response(response, 200)
        self.assertIsNotNone(self.access_token)
        self.assertIsNotNone(self.user_id)

    def test_invalid_login(self):
        """Invalid credentials should be rejected"""
        response = self.login('invalid_user', 'wrong_password')
        self.assertNotEqual(response.status_code, 200)

    def test_invalid_login_with_specific_code(self):
        """Invalid credentials should return specific error code"""
        response = self.login('invalid_user', 'wrong_password')
        self.assertEqual(response.status_code, 460)

    def test_logout_flow(self):
        """Test complete login/logout cycle"""
        # Successful login
        login_response = self.login()
        self.assert_response(login_response, 200)
        
        # Logout - using make_request instead of direct session call
        logout_response = self.make_request(
            'GET',
            f"{self.base_url}/logout",
            expected_status=200,
            headers=self.auth_headers()
        )
        self.assertIn('success', logout_response.json())
        
        # Verify session is invalidated
        check_response = self.make_request(
            'GET',
            f"{self.base_url}/get-transaction-data/1",
            headers=self.auth_headers()
        )
        self.assertNotEqual(check_response.status_code, 200)