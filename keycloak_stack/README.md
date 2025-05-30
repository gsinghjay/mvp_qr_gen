# Keycloak SSO Setup

This directory contains the Docker Compose configuration for setting up Keycloak SSO with a PostgreSQL database.

## Configuration

- **Keycloak Version**: 24.0.1
- **PostgreSQL Version**: 15
- **External Access**: https://auth.hccc.edu (configured in the docker-compose file)
- **Initial Admin Access**: http://localhost:8180 or http://<VM_IP>:8180 (direct port mapping)

## Setup Instructions

1. Make sure to update the `.env` file with secure credentials before starting
2. Ensure the Docker network `qr_generator_network` exists
3. Start the Keycloak stack:

```bash
cd keycloak_stack
docker-compose -f docker-compose.keycloak.yml up -d
```

4. Access the Keycloak Admin Console at `http://localhost:8180` or `http://<VM_IP>:8180`
5. Log in using the admin credentials specified in the `.env` file

## Volumes

- `keycloak_postgres_data`: Persistent storage for the PostgreSQL database
- `keycloak_data`: Persistent storage for Keycloak data

## Network

The stack connects to the existing `qr_generator_network` to allow communication with the QR Generator application.

## Next Steps

After launching Keycloak, proceed with:

1. Creating the `hccc-apps-realm` in Keycloak Admin Console
2. Configuring Azure AD as an OIDC Identity Provider
3. Setting up the OIDC client for `oauth2-proxy` 