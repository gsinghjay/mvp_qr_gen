#!/usr/bin/env python3
"""
Quick test script to validate ContentService implementation.
This is a temporary file for testing Task 1.1 completion.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.content_service import ContentService, ContentNotFoundError, ContentParsingError

def test_content_service():
    """Test the ContentService implementation."""
    print("🧪 Testing ContentService Implementation...")
    
    # Initialize the service
    service = ContentService()
    
    # Test 1: Parse the test page
    print("\n1️⃣ Testing page parsing...")
    try:
        page_data = service.get_page_data("test-page")
        print(f"✅ Successfully parsed page!")
        print(f"   Title: {page_data['meta'].get('title', 'N/A')}")
        print(f"   Author: {page_data['meta'].get('author', 'N/A')}")
        print(f"   Tags: {page_data['meta'].get('tags', 'N/A')}")
        print(f"   Content length: {len(page_data['content'])} characters")
        print(f"   Content preview: {page_data['content'][:100]}...")
    except Exception as e:
        print(f"❌ Error parsing page: {e}")
        return False
    
    # Test 2: Test caching
    print("\n2️⃣ Testing cache functionality...")
    try:
        # First call (should be cached now)
        cache_info_before = service.get_cache_info()
        print(f"   Cache before: {cache_info_before}")
        
        # Second call (should hit cache)
        page_data_cached = service.get_page_data("test-page")
        cache_info_after = service.get_cache_info()
        print(f"   Cache after: {cache_info_after}")
        
        if cache_info_after['hits'] > cache_info_before['hits']:
            print("✅ Caching is working!")
        else:
            print("⚠️ Cache behavior unexpected")
    except Exception as e:
        print(f"❌ Error testing cache: {e}")
    
    # Test 3: Test error handling
    print("\n3️⃣ Testing error handling...")
    try:
        service.get_page_data("non-existent-page")
        print("❌ Should have thrown ContentNotFoundError")
    except ContentNotFoundError:
        print("✅ ContentNotFoundError handled correctly")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 4: List available pages
    print("\n4️⃣ Testing page listing...")
    try:
        pages = service.list_available_pages()
        print(f"✅ Found {len(pages)} pages: {pages}")
    except Exception as e:
        print(f"❌ Error listing pages: {e}")
    
    print("\n🎉 ContentService testing complete!")
    return True

if __name__ == "__main__":
    success = test_content_service()
    sys.exit(0 if success else 1) 