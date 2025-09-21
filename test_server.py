#!/usr/bin/env python3
"""
Test script for the Signaling Server API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_api():
    """Test the API endpoints"""
    print("Testing Signaling Server API...")

    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Register user
    print("\n2. Testing user registration...")
    user_data = {"email": "test@example.com", "password": "testpassword123"}
    try:
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        user_id = response.json().get("id")
    except Exception as e:
        print(f"Error: {e}")
        return

    # Test 3: Login user
    print("\n3. Testing user login...")
    login_data = {"email": "test@example.com", "password": "testpassword123"}
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"Error: {e}")
        return

    # Test 4: Create organization
    print("\n4. Testing organization creation...")
    org_data = {"name": "Test Organization", "subnet": "10.0.0.0/24"}
    try:
        response = requests.post(
            f"{BASE_URL}/organizations", json=org_data, headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        org_id = response.json().get("id")
    except Exception as e:
        print(f"Error: {e}")
        return

    # Test 5: List organizations
    print("\n5. Testing list organizations...")
    try:
        response = requests.get(f"{BASE_URL}/organizations", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 6: Allocate virtual IP
    print("\n6. Testing virtual IP allocation...")
    try:
        response = requests.post(
            f"{BASE_URL}/organizations/{org_id}/allocate_ip", json={}, headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 7: List allocated IPs
    print("\n7. Testing list allocated IPs...")
    try:
        response = requests.get(
            f"{BASE_URL}/organizations/{org_id}/ips", headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\nAPI testing completed!")


if __name__ == "__main__":
    test_api()
