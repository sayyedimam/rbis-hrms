import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@rbistech.com")

def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email: str, otp: str, purpose: str = "SIGNUP") -> bool:
    """
    Send OTP email to user
    
    Args:
        to_email: Recipient email address
        otp: The OTP code to send
        purpose: Either 'SIGNUP' or 'PASSWORD_RESET'
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        
        if purpose == "SIGNUP":
            msg['Subject'] = "RBIS HRMS - Verify Your Email"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                        <h2 style="color: #4f46e5; text-align: center;">Welcome to RBIS HRMS</h2>
                        <p>Thank you for signing up! Please verify your email address to complete your registration.</p>
                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                            <p style="margin: 0; font-size: 14px; color: #64748b;">Your verification code is:</p>
                            <h1 style="color: #4f46e5; font-size: 36px; letter-spacing: 8px; margin: 10px 0;">{otp}</h1>
                        </div>
                        <p style="color: #64748b; font-size: 14px;">This code will expire in 10 minutes.</p>
                        <p style="color: #64748b; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
                        <p style="font-size: 12px; color: #94a3b8; text-align: center;">RBIS HR Management System</p>
                    </div>
                </body>
            </html>
            """
        else:  # PASSWORD_RESET
            msg['Subject'] = "RBIS HRMS - Password Reset Request"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                        <h2 style="color: #4f46e5; text-align: center;">Password Reset Request</h2>
                        <p>We received a request to reset your password. Use the code below to proceed:</p>
                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                            <p style="margin: 0; font-size: 14px; color: #64748b;">Your reset code is:</p>
                            <h1 style="color: #4f46e5; font-size: 36px; letter-spacing: 8px; margin: 10px 0;">{otp}</h1>
                        </div>
                        <p style="color: #64748b; font-size: 14px;">This code will expire in 10 minutes.</p>
                        <p style="color: #ef4444; font-size: 14px;"><strong>If you didn't request a password reset, please ignore this email and ensure your account is secure.</strong></p>
                        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
                        <p style="font-size: 12px; color: #94a3b8; text-align: center;">RBIS HR Management System</p>
                    </div>
                </body>
            </html>
            """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Check if SMTP credentials are configured
        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"⚠️  Email not configured. OTP for {to_email}: {otp}")
            return True  # Return True in dev mode for testing
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ OTP email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        print(f"📧 Development OTP for {to_email}: {otp}")
        return True  # Return True in dev mode for testing
