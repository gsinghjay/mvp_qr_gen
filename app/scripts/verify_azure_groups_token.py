#!/usr/bin/env python3
"""
Verify Azure AD Group Claims in JWT Tokens

This script helps verify whether Azure AD is emitting group claims
in tokens received through Keycloak identity provider.
"""

import json
import base64
import sys
from typing import Dict, Any, Optional

def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token payload without signature verification.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload as dictionary, or None if invalid
    """
    try:
        # Split token into parts
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ Invalid JWT format - expected 3 parts separated by dots")
            return None
            
        # Decode payload (second part)
        payload = parts[1]
        
        # Add padding if needed for base64 decoding
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
            
        # Decode base64
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_json = json.loads(decoded_bytes.decode('utf-8'))
        
        return decoded_json
        
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return None

def analyze_token_claims(payload: Dict[str, Any]) -> None:
    """
    Analyze JWT payload for Azure AD group claims and other relevant information.
    
    Args:
        payload: Decoded JWT payload
    """
    print("🔍 JWT Token Analysis")
    print("=" * 50)
    
    # Check issuer
    issuer = payload.get('iss', 'Unknown')
    print(f"📍 Issuer: {issuer}")
    
    if 'auth.hccc.edu' in issuer:
        print("   ✅ Token issued by Keycloak")
    elif 'login.microsoftonline.com' in issuer:
        print("   ✅ Token issued by Azure AD")
    else:
        print("   ⚠️  Unknown issuer")
    
    # Check audience
    audience = payload.get('aud', [])
    if isinstance(audience, str):
        audience = [audience]
    print(f"🎯 Audience: {audience}")
    
    # Check user information
    print("\n👤 User Information:")
    email = payload.get('email', payload.get('preferred_username', 'Not found'))
    print(f"   📧 Email: {email}")
    
    username = payload.get('preferred_username', payload.get('upn', 'Not found'))
    print(f"   👤 Username: {username}")
    
    # Check for group claims (multiple possible claim names)
    print("\n🏷️  Group Claims Analysis:")
    
    group_claims = [
        'groups',           # Standard Azure AD groups claim
        'roles',            # Keycloak roles
        'realm_access',     # Keycloak realm roles
        'resource_access',  # Keycloak client roles
        'wids',            # Azure AD directory roles
        'constituency'      # Custom claims
    ]
    
    found_groups = False
    for claim_name in group_claims:
        if claim_name in payload:
            found_groups = True
            claim_value = payload[claim_name]
            print(f"   ✅ {claim_name}: {claim_value}")
            
            # Analyze group content
            if isinstance(claim_value, list):
                print(f"      📊 Count: {len(claim_value)} groups/roles")
                for group in claim_value:
                    if 'constituency' in str(group).lower():
                        print(f"      🎯 Azure AD Group Found: {group}")
            elif isinstance(claim_value, dict):
                print(f"      📊 Structure: {list(claim_value.keys())}")
    
    if not found_groups:
        print("   ❌ No group/role claims found in token")
        print("   💡 This confirms Enterprise Application is required")
    
    # Check for Azure AD specific claims
    print("\n🔵 Azure AD Specific Claims:")
    azure_claims = ['oid', 'tid', 'wids', 'groups', 'hasgroups']
    azure_found = False
    
    for claim in azure_claims:
        if claim in payload:
            azure_found = True
            print(f"   ✅ {claim}: {payload[claim]}")
    
    if not azure_found:
        print("   ❌ No Azure AD specific claims found")
        print("   💡 Token likely processed only by Keycloak")
    
    # Full payload for debugging
    print("\n📋 Full Token Payload (for debugging):")
    print(json.dumps(payload, indent=2))

def main():
    """
    Main function to analyze JWT token from command line or interactive input.
    """
    print("🔐 Azure AD Group Claims Verification Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("\n📝 Instructions:")
        print("1. Login to https://web.hccc.edu/hello-secure")
        print("2. Open browser developer tools (F12)")
        print("3. Go to Application/Storage → Cookies → web.hccc.edu")
        print("4. Copy the value of '_oauth2_proxy' cookie")
        print("5. Paste it below (or pass as command line argument)")
        print("\nAlternatively, check the X-Forwarded-Access-Token header in the hello-secure page")
        print("\n" + "=" * 50)
        
        token = input("Enter JWT token: ").strip()
    
    if not token:
        print("❌ No token provided")
        sys.exit(1)
    
    # Remove Bearer prefix if present
    if token.startswith('Bearer '):
        token = token[7:]
    
    # Decode and analyze
    payload = decode_jwt_payload(token)
    if payload:
        analyze_token_claims(payload)
        
        # Conclusion
        print("\n" + "=" * 50)
        print("🎯 CONCLUSION:")
        
        has_azure_groups = any(
            'constituency' in str(payload.get(claim, '')).lower() 
            for claim in ['groups', 'wids', 'roles']
        )
        
        if has_azure_groups:
            print("✅ Azure AD groups are being emitted - Enterprise App may not be required!")
        else:
            print("❌ No Azure AD groups found in token")
            print("💡 This confirms Enterprise Application is required for group claims")
            print("📋 Current token only contains Keycloak default roles")
    else:
        print("❌ Failed to decode token")

if __name__ == "__main__":
    main() 