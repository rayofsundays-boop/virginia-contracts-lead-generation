import os
import unittest
from app import app, db, text, pyotp, decrypt_twofa_secret
from werkzeug.security import generate_password_hash

class TwoFATestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            # Create a fresh user (unique email/username)
            db.session.execute(text('DELETE FROM leads WHERE email = :e OR username = :u'), {'e': '2fauser@example.com', 'u': 'twofatest'})
            db.session.commit()
            db.session.execute(text('''INSERT INTO leads (company_name, contact_name, email, username, password_hash, subscription_status, credits_balance)
                                        VALUES (:company_name, :contact_name, :email, :username, :password_hash, 'free', 0)'''), {
                'company_name': '2FA Co',
                'contact_name': 'Two Factor',
                'email': '2fauser@example.com',
                'username': 'twofatest',
                'password_hash': generate_password_hash('TestPass123!')
            })
            db.session.commit()

    def login(self, username, password):
        return self.client.post('/signin', data={'username': username, 'password': password}, follow_redirects=False)

    def test_enable_and_use_2fa(self):
        # Initial login (no 2FA yet)
        rv = self.login('twofatest', 'TestPass123!')
        self.assertIn(rv.status_code, (302, 303))
        # Visit enable 2FA page
        rv = self.client.get('/enable-2fa')
        self.assertEqual(rv.status_code, 200)
        # Extract secret from session
        with self.client.session_transaction() as sess:
            secret = sess.get('provisioning_2fa_secret')
        self.assertTrue(secret)
        token = pyotp.TOTP(secret).now()
        # Enable 2FA
        rv = self.client.post('/enable-2fa', data={'code': token}, follow_redirects=False)
        self.assertIn(rv.status_code, (302, 303))
        # Logout
        self.client.get('/logout')
        # Login again - should require second factor now
        rv = self.login('twofatest', 'TestPass123!')
        # Should redirect to verify_2fa
        self.assertIn('/verify-2fa', rv.headers.get('Location',''))
        # Fetch secret from DB
        with self.app.app_context():
            row = db.session.execute(text('SELECT twofa_secret FROM leads WHERE username = :u'), {'u': 'twofatest'}).fetchone()
            self.assertTrue(row and row[0])
            secret_db_enc = row[0]
            secret_plain = decrypt_twofa_secret(secret_db_enc)
        code = pyotp.TOTP(secret_plain).now()
        # Submit correct code
        rv = self.client.post('/verify-2fa', data={'code': code}, follow_redirects=False)
        self.assertIn(rv.status_code, (302, 303))
        # Attempt invalid code path
        self.client.get('/logout')
        rv = self.login('twofatest', 'TestPass123!')
        self.assertIn('/verify-2fa', rv.headers.get('Location',''))
        bad_code = '000000'
        rv_bad = self.client.post('/verify-2fa', data={'code': bad_code}, follow_redirects=True)
        self.assertIn(b'Invalid authentication code', rv_bad.data)

    def test_recovery_codes_flow(self):
        # Login & enable 2FA
        self.login('twofatest', 'TestPass123!')
        rv = self.client.get('/enable-2fa')
        with self.client.session_transaction() as sess:
            secret = sess.get('provisioning_2fa_secret')
        token = pyotp.TOTP(secret).now()
        self.client.post('/enable-2fa', data={'code': token})
        # Generate recovery codes
        gen = self.client.post('/generate-2fa-recovery-codes', follow_redirects=True)
        self.assertEqual(gen.status_code, 200)
        with self.client.session_transaction() as sess:
            codes = sess.get('recent_recovery_codes')
        self.assertTrue(codes and len(codes) == 10)
        rc = codes[0]
        # Logout then login and use recovery code
        self.client.get('/logout')
        rv = self.login('twofatest', 'TestPass123!')
        self.assertIn('/verify-2fa', rv.headers.get('Location',''))
        use_rc = self.client.post('/verify-2fa', data={'code': rc}, follow_redirects=False)
        self.assertIn(use_rc.status_code, (302,303))

if __name__ == '__main__':
    unittest.main()
