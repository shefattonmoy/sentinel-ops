# apps/accounts/two_factor.py
import secrets
import pyotp
import qrcode
import io
import base64
from django.conf import settings

class TwoFactorService:
    """Two-Factor Authentication service using TOTP"""
    
    def __init__(self, user):
        self.user = user
        self.issuer = "SentinelOps"
    
    def generate_secret(self):
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def get_totp(self, secret=None):
        """Get TOTP object for user"""
        secret = secret or self.user.two_factor_secret
        if not secret:
            return None
        return pyotp.TOTP(secret, interval=30)
    
    def get_qr_code(self):
        """Generate QR code for Google Authenticator"""
        if not self.user.two_factor_secret:
            return None
        
        totp = self.get_totp()
        provisioning_uri = totp.provisioning_uri(
            name=self.user.email or self.user.username,
            issuer_name=self.issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, token):
        """Verify a TOTP token"""
        if not self.user.two_factor_secret:
            return False
        
        totp = self.get_totp()
        return totp.verify(token)
    
    def generate_backup_codes(self, count=8):
        """Generate backup codes"""
        import secrets
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()[:8]
            codes.append(code)
        return codes
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if not self.user.two_factor_backup_codes:
            return False
        
        if code in self.user.two_factor_backup_codes:
            codes = self.user.two_factor_backup_codes.copy()
            codes.remove(code)
            self.user.two_factor_backup_codes = codes
            self.user.save(update_fields=['two_factor_backup_codes'])
            return True
        
        return False
    
    def setup_2fa(self):
        """Setup 2FA for user"""
        secret = self.generate_secret()
        qr_code = self.get_qr_code_with_secret(secret)
        backup_codes = self.generate_backup_codes()
        
        # Store temporarily (not enabled until verified)
        self.user.two_factor_secret = secret
        self.user.two_factor_backup_codes = backup_codes
        self.user.save(update_fields=['two_factor_secret', 'two_factor_backup_codes'])
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes,
        }
    
    def get_qr_code_with_secret(self, secret):
        """Generate QR code with specific secret"""
        totp = pyotp.TOTP(secret, interval=30)
        provisioning_uri = totp.provisioning_uri(
            name=self.user.email or self.user.username,
            issuer_name=self.issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    def enable_2fa(self):
        """Enable 2FA after verification"""
        self.user.two_factor_enabled = True
        self.user.save(update_fields=['two_factor_enabled'])
    
    def disable_2fa(self):
        """Disable 2FA"""
        self.user.two_factor_enabled = False
        self.user.two_factor_secret = None
        self.user.two_factor_backup_codes = []
        self.user.save(update_fields=['two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes'])