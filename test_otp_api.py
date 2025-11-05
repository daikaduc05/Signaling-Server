"""
Script test OTP API endpoints
Chạy script này để test tính năng OTP đăng ký
"""
import requests
import json
import time
from typing import Optional

# Cấu hình
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/auth"

def print_step(step_num: int, message: str):
    """In bước test"""
    print(f"\n{'='*60}")
    print(f"BƯỚC {step_num}: {message}")
    print(f"{'='*60}")

def print_response(response):
    """In response từ API"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response Text: {response.text}")

def test_request_otp(email: str) -> Optional[str]:
    """Test endpoint request-otp"""
    print_step(1, "Gửi yêu cầu OTP")
    
    url = f"{API_BASE}/request-otp"
    data = {"email": email}
    
    print(f"POST {url}")
    print(f"Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Thành công! Kiểm tra email của bạn để lấy mã OTP")
            print(f"   Mã OTP có hiệu lực trong {result.get('expires_in', 600)} giây")
            return "success"
        else:
            print(f"\n❌ Lỗi: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("\n❌ Lỗi: Không thể kết nối đến server!")
        print("   Đảm bảo server đang chạy: python -m uvicorn app.main:app --reload")
        return None
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return None

def test_verify_otp_and_register(email: str, otp_code: str, password: str) -> bool:
    """Test endpoint verify-otp-and-register"""
    print_step(2, "Xác thực OTP và Đăng ký")
    
    url = f"{API_BASE}/verify-otp-and-register"
    data = {
        "email": email,
        "otp_code": otp_code,
        "password": password
    }
    
    print(f"POST {url}")
    print(f"Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Đăng ký thành công!")
            print(f"   User ID: {result.get('user', {}).get('id')}")
            print(f"   Email: {result.get('user', {}).get('email')}")
            print(f"   Email Verified: {result.get('user', {}).get('email_verified')}")
            return True
        else:
            print(f"\n❌ Lỗi: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return False

def main():
    """Hàm main để chạy test"""
    print("\n" + "="*60)
    print("TEST OTP VERIFICATION API")
    print("="*60)
    
    # Nhập thông tin
    print("\n📝 Nhập thông tin để test:")
    email = input("Email: ").strip()
    
    if not email:
        print("❌ Email không được để trống!")
        return
    
    # Test request OTP
    result = test_request_otp(email)
    
    if result != "success":
        print("\n❌ Không thể gửi OTP. Kiểm tra lại cấu hình và server.")
        return
    
    # Nhập OTP từ email
    print("\n" + "-"*60)
    print("📧 Kiểm tra email của bạn để lấy mã OTP")
    print("-"*60)
    
    otp_code = input("\nNhập mã OTP từ email: ").strip()
    password = input("Nhập password cho tài khoản: ").strip()
    
    if not otp_code or not password:
        print("❌ OTP và password không được để trống!")
        return
    
    # Test verify OTP
    success = test_verify_otp_and_register(email, otp_code, password)
    
    if success:
        print("\n" + "="*60)
        print("✅ TEST THÀNH CÔNG!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ TEST THẤT BẠI!")
        print("="*60)
        print("\nKiểm tra lại:")
        print("  - Mã OTP đã đúng chưa?")
        print("  - Mã OTP còn hiệu lực không? (10 phút)")
        print("  - Email đã được đăng ký trước đó chưa?")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Đã hủy test")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

