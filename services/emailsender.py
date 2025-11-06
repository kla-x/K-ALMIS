from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
import sib_api_v3_sdk
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssetFlowEmailService:
    def __init__(self, api_key: str):
        """Initialize the email service with Sendinblue API key"""
        self.configuration = sib_api_v3_sdk.Configuration()
        self.configuration.api_key['api-key'] = api_key
        self.api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(self.configuration))
        self.sender = {
            "name": "AssetFlow System", 
            "email": "musauem98@gmail.com"
        }
    
    def send_account_created_email(self, user_email: str, username: str) -> bool:
        """Send account creation notification email"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to AssetFlow</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background-color: #2563eb; padding: 20px; text-align: center;">
                    <img src="https://res.cloudinary.com/duboyr09q/image/upload/v1753869958/logo_niwpon.png" alt="AssetFlow Logo" style="max-height: 50px;">
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h1 style="color: #333333; font-size: 28px; margin-bottom: 20px; text-align: center;">
                        Welcome to AssetFlow! 🎉
                    </h1>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Hi <strong>{username}</strong>,
                    </p>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Great news! Your AssetFlow account has been successfully created and is now awaiting activation by our administrators.
                    </p>
                    
                    <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 20px; margin: 30px 0;">
                        <h3 style="color: #2563eb; margin: 0 0 10px 0; font-size: 18px;">What's Next?</h3>
                        <p style="color: #666666; margin: 0; font-size: 14px; line-height: 1.5;">
                            Our team will review and activate your account shortly. Once activated, you'll receive another email confirmation, and you'll be able to:
                        </p>
                    </div>
                    
                    <ul style="color: #666666; font-size: 16px; line-height: 1.8; margin: 20px 0; padding-left: 20px;">
                        <li>Book chairs, rooms, and projectors</li>
                        <li>Manage your equipment reservations</li>
                        <li>Access our full range of facility assets</li>
                        <li>Track your booking history</li>
                    </ul>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                        If you have any questions while waiting for activation, feel free to contact our support team.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="color: #999999; font-size: 14px; margin: 0;">
                            Thank you for choosing AssetFlow for your equipment booking needs!
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #999999; font-size: 12px; margin: 0;">
                        © 2025 AssetFlow. All rights reserved.<br>
                        This email was sent to {user_email}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email = SendSmtpEmail(
            to=[{"email": user_email}],
            sender=self.sender,
            subject="Welcome to AssetFlow - Account Created Successfully!",
            html_content=html_content
        )
        
        return self._send_email(email)
    
    def send_account_activated_email(self, user_email: str, username: str) -> bool:
        """Send account activation confirmation email"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AssetFlow Account Activated</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background-color: #059669; padding: 20px; text-align: center;">
                    <img src="https://res.cloudinary.com/duboyr09q/image/upload/v1753869958/logo_niwpon.png" alt="AssetFlow Logo" style="max-height: 50px;">
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h1 style="color: #333333; font-size: 28px; margin-bottom: 20px; text-align: center;">
                        Your Account is Now Active! 🚀
                    </h1>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Hi <strong>{username}</strong>,
                    </p>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Excellent news! Your AssetFlow account has been successfully activated by our administrators. You can now start booking equipment and managing your reservations.
                    </p>
                    
                    <div style="background-color: #ecfdf5; border-left: 4px solid #059669; padding: 20px; margin: 30px 0;">
                        <h3 style="color: #059669; margin: 0 0 10px 0; font-size: 18px;">You Can Now:</h3>
                        <ul style="color: #666666; margin: 10px 0 0 0; font-size: 14px; line-height: 1.5; padding-left: 20px;">
                            <li>Book chairs, meeting rooms, and projectors</li>
                            <li>View available equipment in real-time</li>
                            <li>Manage and modify your reservations</li>
                            <li>Access your booking history and reports</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="localhost:5173/login" style="background-color: #059669; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                            Login to AssetFlow
                        </a>
                    </div>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                        If you need any assistance getting started or have questions about using AssetFlow, our support team is here to help.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="color: #999999; font-size: 14px; margin: 0;">
                            Ready to streamline your equipment booking experience!
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #999999; font-size: 12px; margin: 0;">
                        © 2025 AssetFlow. All rights reserved.<br>
                        This email was sent to {user_email}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email = SendSmtpEmail(
            to=[{"email": user_email}],
            sender=self.sender,
            subject="🎉 Your AssetFlow Account is Now Active!",
            html_content=html_content
        )
        
        return self._send_email(email)
    
    def send_password_reset_email(self, user_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email with token"""
        
        reset_link = f"localhost:5173/password-reset?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AssetFlow Password Reset</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background-color: #dc2626; padding: 20px; text-align: center;">
                    <img src="https://res.cloudinary.com/duboyr09q/image/upload/v1753869958/logo_niwpon.png" alt="AssetFlow Logo" style="max-height: 50px;">
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h1 style="color: #333333; font-size: 28px; margin-bottom: 20px; text-align: center;">
                        Password Reset Request 🔐
                    </h1>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        Hi <strong>{username}</strong>,
                    </p>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        We received a request to reset the password for your AssetFlow account. If you made this request, click the button below to reset your password.
                    </p>
                    
                    <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 20px; margin: 30px 0;">
                        <h3 style="color: #dc2626; margin: 0 0 10px 0; font-size: 18px;">Important Security Information:</h3>
                        <ul style="color: #666666; margin: 10px 0 0 0; font-size: 14px; line-height: 1.5; padding-left: 20px;">
                            <li>This reset link will expire in 24 hours</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your password will remain unchanged until you create a new one</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #dc2626; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                            Reset My Password
                        </a>
                    </div>
                    
                    <p style="color: #666666; font-size: 14px; line-height: 1.6; margin-bottom: 20px;">
                        If the button doesn't work, copy and paste this link into your browser:
                    </p>
                    
                    <div style="background-color: #f8fafc; border: 1px solid #e5e7eb; border-radius: 5px; padding: 15px; margin: 20px 0; word-break: break-all;">
                        <code style="color: #374151; font-size: 14px;">{reset_link}</code>
                    </div>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                        If you continue to have problems, please contact our support team for assistance.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="color: #999999; font-size: 14px; margin: 0;">
                            Stay secure with AssetFlow!
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #999999; font-size: 12px; margin: 0;">
                        © 2025 AssetFlow. All rights reserved.<br>
                        This email was sent to {user_email}<br>
                        For security reasons, this email was automatically generated.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email = SendSmtpEmail(
            to=[{"email": user_email}],
            sender=self.sender,
            subject="AssetFlow - Reset Your Password",
            html_content=html_content
        )
        
        return self._send_email(email)

    def send_mfa_code_email(self, user_email: str, username: str, mfa_code: str, expiry_minutes: int):
        subject = "Your MFA Code"
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>Your MFA code is: <strong>{mfa_code}</strong></p>
                <p>This code will expire in {expiry_minutes} minutes.</p>
                <p>If you did not request this code, please contact support immediately.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_new_device_login_notification(self, user_email: str, username: str, ip_address: str, device_info: dict):
        subject = "New Device Login Detected"
        device_str = device_info.get('user_agent', 'Unknown device')
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>A new device has logged into your account.</p>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p><strong>Device:</strong> {device_str}</p>
                <p>If this wasn't you, please reset your password immediately and contact support.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_account_temp_disabled_email(self, user_email: str, username: str, hours: int):
        subject = "Account Temporarily Disabled"
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>Your account has been temporarily disabled due to too many failed login attempts.</p>
                <p>Your account will be automatically reactivated in {hours} hours.</p>
                <p>If you did not attempt to login, please contact support immediately.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_account_suspended_email(self, user_email: str, username: str):
        subject = "Account Suspended"
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>Your account has been suspended due to suspicious activity or too many failed login attempts.</p>
                <p>Please contact support to reactivate your account.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_suspicious_login_blocked_email(self, user_email: str, username: str, ip_address: str, reason: str):
        subject = "Suspicious Login Blocked"
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>A suspicious login attempt to your account was blocked.</p>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p><strong>Reason:</strong> {reason}</p>
                <p>Your account has been temporarily disabled for security. If this was you, please contact support.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_timezone_mismatch_email(self, user_email: str, username: str, timezone: str, ip_address: str, device_info: dict, unlock_token: str):
        subject = "Login from Unexpected Timezone Detected"
        device_str = device_info.get('user_agent', 'Unknown device')
        unlock_url = f"https://your-domain.com/auth/unlock?token={unlock_token}"
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>A login attempt was detected from an unexpected timezone.</p>
                <p><strong>Timezone:</strong> {timezone}</p>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p><strong>Device:</strong> {device_str}</p>
                <p>If this was you, click the link below to unlock your account:</p>
                <p><a href="{unlock_url}">Unlock My Account</a></p>
                <p>If this wasn't you, please contact support immediately.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_out_of_hours_login_notification(self, user_email: str, username: str, ip_address: str, device_info: dict):
        subject = "Out of Hours Login Detected"
        device_str = device_info.get('user_agent', 'Unknown device')
        html_content = f"""
        <html>
            <body>
                <h2>Hello {username},</h2>
                <p>A login to your account was detected outside of normal working hours.</p>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p><strong>Device:</strong> {device_str}</p>
                <p>If this wasn't you, please contact support immediately.</p>
            </body>
        </html>
        """
        return self.send_email(user_email, subject, html_content)

    def send_out_of_hours_login_notification_admin(self, adm_email: str, admin_name: str, user_email: str, ip_address: str, device_info: dict):
        subject = "Out of Hours Login Alert"
        device_str = device_info.get('user_agent', 'Unknown device')
        html_content = f"""
        <html>
            <body>
                <h2>Hello {admin_name},</h2>
                <p>An out of hours login was detected for user: <strong>{user_email}</strong></p>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p><strong>Device:</strong> {device_str}</p>
                <p>Please review this activity if necessary.</p>
            </body>
        </html>
        """
        return self.send_email(adm_email, subject, html_content)




    def _send_email(self, email: SendSmtpEmail) -> bool:
        """Helper method to send email and handle exceptions"""
        try:
            response = self.api_instance.send_transac_email(email)
            logger.info(f"Email sent successfully: {response}")
            return True
        except ApiException as e:
            logger.error(f"Failed to send email: {e}")
            return False