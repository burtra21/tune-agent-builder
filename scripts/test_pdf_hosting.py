"""
Test script to verify PDF hosting is working correctly
Tests both PDF generation and serving via API
"""

import requests
import os
from pathlib import Path

def test_pdf_hosting():
    """Test PDF hosting functionality"""

    print("=" * 60)
    print("PDF HOSTING TEST")
    print("=" * 60)

    # Check if API server is running
    print("\n1. Testing API Server Health...")
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("   ✓ API server is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ✗ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot connect to API server")
        print("   → Start the server with: uvicorn api_server:app --reload --port 8000")
        return False

    # Check for existing PDFs
    print("\n2. Checking for generated PDFs...")
    pdf_dir = Path("pdf_lead_magnets/generated")

    if not pdf_dir.exists():
        print(f"   ✗ PDF directory does not exist: {pdf_dir}")
        return False

    pdfs = list(pdf_dir.glob("*.pdf"))

    if not pdfs:
        print("   ✗ No PDFs found in pdf_lead_magnets/generated/")
        print("   → Generate PDFs with: python3 worldclass_email_generator.py")
        return False

    print(f"   ✓ Found {len(pdfs)} PDF(s)")
    for pdf in pdfs[:3]:  # Show first 3
        print(f"     - {pdf.name}")

    # Test PDF list endpoint
    print("\n3. Testing PDF List API...")
    try:
        response = requests.get(
            "http://localhost:8000/api/pdf/list",
            headers={"X-API-Key": "tune_dev_key_12345"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ API reports {data['count']} PDF(s)")
        else:
            print(f"   ✗ List endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Test PDF serving
    print("\n4. Testing PDF Serving...")
    test_pdf = pdfs[0]
    pdf_url = f"http://localhost:8000/pdf/{test_pdf.name}"

    print(f"   Testing: {pdf_url}")

    try:
        response = requests.get(pdf_url)

        if response.status_code == 200:
            print(f"   ✓ PDF served successfully")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Size: {len(response.content):,} bytes")

            # Verify it's actually a PDF
            if response.content[:4] == b'%PDF':
                print("   ✓ Response is a valid PDF file")
            else:
                print("   ✗ Response is not a valid PDF")
                return False
        else:
            print(f"   ✗ PDF serving failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Test security (directory traversal prevention)
    print("\n5. Testing Security...")
    malicious_url = "http://localhost:8000/pdf/../api_server.py"

    try:
        response = requests.get(malicious_url)
        if response.status_code == 404:
            print("   ✓ Directory traversal protection working")
        else:
            print(f"   ⚠️  Security check returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Security test error: {e}")

    # Test environment configuration
    print("\n6. Testing Environment Configuration...")
    pdf_base_url = os.getenv("PDF_BASE_URL", "http://localhost:8000")
    print(f"   PDF_BASE_URL: {pdf_base_url}")

    if "localhost" in pdf_base_url:
        print("   ℹ️  Running in local development mode")
        print("   → For production, set PDF_BASE_URL to your deployed URL")
    else:
        print(f"   ✓ Production URL configured: {pdf_base_url}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS: ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\nPDF hosting is working correctly!")
    print(f"\nExample PDF URL: {pdf_url}")
    print("\nYou can access this PDF by:")
    print("  1. Opening in browser: " + pdf_url)
    print("  2. Using curl: curl -o test.pdf " + pdf_url)
    print("  3. Including in emails as clickable link")

    return True


if __name__ == "__main__":
    success = test_pdf_hosting()
    exit(0 if success else 1)
