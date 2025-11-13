import os
import unittest
from app import app, db, AUTH_DEBUG
from sqlalchemy import text
from werkzeug.security import generate_password_hash

class SigninTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a predictable test user (independent of SEED_TEST_USER logic)
        with app.app_context():
            db.session.execute(text("DELETE FROM leads WHERE username = 'authtest' OR email='authtest@example.com'"))
            db.session.execute(text("""INSERT INTO leads (company_name, contact_name, email, username, password_hash, subscription_status, credits_balance)
                                      VALUES (:company_name,:contact_name,:email,:username,:password_hash,'free',0)"""), {
                'company_name': 'Auth Test Co',
                'contact_name': 'Auth Tester',
                'email': 'authtest@example.com',
                'username': 'authtest',
                'password_hash': generate_password_hash('AuthPass!123')
            })
            db.session.commit()

    def setUp(self):
        self.client = app.test_client()

    def test_signin_invalid(self):
        resp = self.client.post('/signin', data={'username': 'nope', 'password': 'wrong'}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Invalid username or password', resp.data)

    def test_signin_valid_username(self):
        resp = self.client.post('/signin', data={'username': 'authtest', 'password': 'AuthPass!123'}, follow_redirects=False)
        # Expect redirect to customer_leads on success
        self.assertIn(resp.status_code, (302, 303))
        self.assertIn('/customer-leads', resp.headers.get('Location',''))

    def test_signin_valid_email(self):
        resp = self.client.post('/signin', data={'username': 'authtest@example.com', 'password': 'AuthPass!123'}, follow_redirects=False)
        self.assertIn(resp.status_code, (302, 303))
        self.assertIn('/customer-leads', resp.headers.get('Location',''))

if __name__ == '__main__':
    unittest.main()
