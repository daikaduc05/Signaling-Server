import smtplib
import secrets
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Gmail SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App Password từ Gmail
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send OTP code to user's email via Gmail SMTP
    
    Args:
        to_email: Email address to send OTP to
        otp_code: The OTP code to send
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.error("SMTP credentials not configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Mã xác thực OTP đăng ký tài khoản"
        
        # Email body
        body = f"""
        Xin chào,
        
        Bạn đã yêu cầu đăng ký tài khoản mới. Mã xác thực OTP của bạn là:
        
        {otp_code}
        
        Mã này có hiệu lực trong 10 phút. Vui lòng không chia sẻ mã này với bất kỳ ai.
        
        Nếu bạn không yêu cầu đăng ký, vui lòng bỏ qua email này.
        
        Trân trọng,
        Signaling Server
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(FROM_EMAIL, to_email, text)
        
        logger.info(f"OTP email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Please check your Gmail App Password")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        return False

