#!/usr/bin/env python3
"""
Debug script to decode JWT tokens and inspect claims for Azure AD group mapping.
"""

import base64
import json
import sys

def decode_jwt_payload(token):
    """Decode JWT payload without signature verification."""
    try:
        # Split token into parts
        parts = token.split('.')
        if len(parts) < 2:
            print("Invalid JWT token format - need at least header.payload")
            return None
            
        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode base64
        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)
        
        return token_data
        
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def analyze_token_claims(token_data):
    """Analyze token claims for group information."""
    print("=== JWT TOKEN ANALYSIS ===")
    print(f"Issuer: {token_data.get('iss', 'Unknown')}")
    print(f"Subject: {token_data.get('sub', 'Unknown')}")
    print(f"Audience: {token_data.get('aud', 'Unknown')}")
    print(f"Email: {token_data.get('email', 'Not found')}")
    print(f"Preferred Username: {token_data.get('preferred_username', 'Not found')}")
    
    print("\n=== GROUP/ROLE CLAIMS ===")
    
    # Check various possible locations for groups
    groups_locations = [
        ('groups', token_data.get('groups')),
        ('roles', token_data.get('roles')),
        ('realm_access.roles', token_data.get('realm_access', {}).get('roles')),
        ('resource_access', token_data.get('resource_access')),
        ('wids', token_data.get('wids')),  # Azure AD group IDs
        ('scp', token_data.get('scp')),    # Scopes
    ]
    
    for location, value in groups_locations:
        if value:
            print(f"{location}: {value}")
        else:
            print(f"{location}: NOT FOUND")
    
    print("\n=== AZURE AD SPECIFIC CLAIMS ===")
    # Look for Azure AD specific claims that might contain groups
    azure_claims = [
        'groups',
        'wids', 
        'hasgroups',
        'group_membership',
        'oid',  # Object ID
        'tid',  # Tenant ID
    ]
    
    for claim in azure_claims:
        value = token_data.get(claim)
        if value:
            print(f"Azure AD {claim}: {value}")
        else:
            print(f"Azure AD {claim}: NOT FOUND")
    
    print("\n=== SCOPE ANALYSIS ===")
    scope = token_data.get('scope', '')
    print(f"Requested scopes: {scope}")
    if 'groups' not in scope:
        print("⚠️  WARNING: 'groups' scope not requested - this may prevent group claims")
    
    print("\n=== FULL TOKEN PAYLOAD ===")
    print(json.dumps(token_data, indent=2))

if __name__ == "__main__":
    # Complete token from logs with proper signature part
    sample_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJScHJoNWtWWE5NUTRraTBfLXpxUURXRGVRejZNR3FwMjBsc01xa3gtSS1rIn0.eyJleHAiOjE3NDg1NTUxNzgsImlhdCI6MTc0ODU1NDg3OCwiYXV0aF90aW1lIjoxNzQ4NTU0ODc4LCJqdGkiOiI1ZjhhMjQ4ZS02Y2M1LTRjY2ItOTE3ZS01Yjc3MDBhNGE1NWQiLCJpc3MiOiJodHRwczovL2F1dGguaGNjYy5lZHUvcmVhbG1zL2hjY2MtYXBwcy1yZWFsbSIsImF1ZCI6WyJvYXV0aDItcHJveHktY2xpZW50IiwiYWNjb3VudCJdLCJzdWIiOiIxOTFiMzhiOC0wZDNiLTQ1NTctOGFkMS0yZDBkMmMzZDA4M2UiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJvYXV0aDItcHJveHktY2xpZW50Iiwic2Vzc2lvbl9zdGF0ZSI6IjhmZjA2MzFkLWU4OTgtNDQ0My04ZDU0LTJkMDM2MzBiNjEwNiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cHM6Ly93ZWIuaGNjYy5lZHUiLCJodHRwczovL2F1dGguaGNjYy5lZHUiLCJodHRwczovL3dlYmhvc3QuaGNjYy5lZHUiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIiwiZGVmYXVsdC1yb2xlcy1oY2NjLWFwcHMtcmVhbG0iLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUiLCJzaWQiOiI4ZmYwNjMxZC1lODk4LTQ0NDMtOGQ1NC0yZDAzNjMwYjYxMDYiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJKYXkgU2luZ2giLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJqc2luZ2hAaGNjYy5lZHUiLCJnaXZlbl9uYW1lIjoiSmF5IiwiZmFtaWx5X25hbWUiOiJTaW5naCIsImVtYWlsIjoianNpbmdoQGhjY2MuZWR1In0.dummy_signature"
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("Usage: python debug_jwt_token.py <jwt_token>")
        print("Using sample token from logs...")
        token = sample_token
    
    token_data = decode_jwt_payload(token)
    if token_data:
        analyze_token_claims(token_data) 