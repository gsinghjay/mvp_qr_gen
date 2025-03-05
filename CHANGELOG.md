# CHANGELOG


## v0.6.0 (2025-03-05)

### Features

- **api**: Add DELETE endpoint for QR codes
  ([`675041f`](https://github.com/gsinghjay/mvp_qr_gen/commit/675041f63ecac96eadcfb90e500064d716aa6a06))

- **background-tasks**: Implement non-blocking scan statistics updates
  ([`e57f3c6`](https://github.com/gsinghjay/mvp_qr_gen/commit/e57f3c69d204445c95d7222aecb7fade4d3c85a4))

- **frontend**: Implement deleteQR function in API service
  ([`abe628c`](https://github.com/gsinghjay/mvp_qr_gen/commit/abe628cbfc049a47c02f8196fb0ce077c94ad727))

- **qr**: Add delete_qr method to QRCodeService
  ([`3b1f563`](https://github.com/gsinghjay/mvp_qr_gen/commit/3b1f56384cb705fe80f92f43e1188ce42d1131c7))

### Testing

- **background-tasks**: Add comprehensive tests for background task functionality
  ([`126f058`](https://github.com/gsinghjay/mvp_qr_gen/commit/126f0588fdb7ab89b305e60430f24ab5509d85e1))


## v0.5.1 (2025-03-03)

### Bug Fixes

- **api**: Improve test reliability for background tasks
  ([`e48a250`](https://github.com/gsinghjay/mvp_qr_gen/commit/e48a2500adc20db32af3e9b426d16fdd0e4e7bbe))

- **api**: Resolve dependency import issues and optimize database operations
  ([`ad0c6d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/ad0c6d2c353a63bd691a85cfda299b105bea46b0))

- Fix import path for get_db dependency in redirect router - Implement optimized database operations
  with retry functionality - Enhance error handling for database operations - Improve concurrency
  handling with SQLite

### Chores

- Added curl test workflow
  ([`2e8dca9`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e8dca9e8eea26aec9b9dc66c6b218870a9b719e))

### Refactoring

- Reorganize models and schemas into modular directory structure
  ([`80ceae6`](https://github.com/gsinghjay/mvp_qr_gen/commit/80ceae651afb2a64d02db880500a08e8fe94054e))

### Testing

- Add tests for refactored models and schemas
  ([`f5a6813`](https://github.com/gsinghjay/mvp_qr_gen/commit/f5a681318a9a9983dee13bbf64de8488687ed018))


## v0.5.0 (2025-03-03)

### Bug Fixes

- **database**: Resolve dependency injection pattern for FastAPI compatibility
  ([`adc806c`](https://github.com/gsinghjay/mvp_qr_gen/commit/adc806c3d26d775c7521d4a30f3ea7ee0860a379))

### Chores

- **deps**: Add psutil dependency for system metrics collection
  ([`e95135f`](https://github.com/gsinghjay/mvp_qr_gen/commit/e95135f35a518e8494f68f8e65478a8fc030d1ed))

- **services**: Update service module initialization
  ([`21af576`](https://github.com/gsinghjay/mvp_qr_gen/commit/21af576017e5b033af6dd56b0a2269c890599ab2))

### Features

- **app**: Configure health check endpoints and exception handling
  ([`3818fa7`](https://github.com/gsinghjay/mvp_qr_gen/commit/3818fa723169bfb91120d29703d16425d662a94b))

- **health**: Implement synchronous health check service and endpoints
  ([`c42cf07`](https://github.com/gsinghjay/mvp_qr_gen/commit/c42cf07120dd1e62715dd615f1f8da15cf052013))

- **routers**: Register health check router in the application
  ([`0cfe182`](https://github.com/gsinghjay/mvp_qr_gen/commit/0cfe18210b3d18916d76b0761213c73fa1d50ede))

- **schemas**: Add health check response models and status enums
  ([`08f36e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/08f36e35c5e10c749394b2838697a741d3ecb35e))

### Testing

- **health**: Add tests for health check endpoints
  ([`856e535`](https://github.com/gsinghjay/mvp_qr_gen/commit/856e5356b6b0a68b673bcc4c5dca26d6c03dd758))


## v0.4.0 (2025-03-03)

### Bug Fixes

- **database**: Resolve database initialization and connection issues
  ([`81d0aed`](https://github.com/gsinghjay/mvp_qr_gen/commit/81d0aed872a39427ce6619a09f683461dd1a9b47))

- **schemas**: Update QRCodeCreate schema to include qr_type field
  ([`c977c39`](https://github.com/gsinghjay/mvp_qr_gen/commit/c977c394f1b64afa93bb884a53cc66f47e33acc6))

- **scripts**: Enhance database management script for reliability
  ([`ddea10e`](https://github.com/gsinghjay/mvp_qr_gen/commit/ddea10eb5cab91e901cc70fc4c00351c2bcc960d))

- **web**: Update web pages router to use new dependency injection pattern
  ([`1ba68d3`](https://github.com/gsinghjay/mvp_qr_gen/commit/1ba68d30e04bb591d9b2cfbc8d7efc7d5f8f9672))

### Chores

- Added SPEC.md and formatted files with black
  ([`224f01a`](https://github.com/gsinghjay/mvp_qr_gen/commit/224f01ad3e0e17f767d705e14e617e3f7774f72e))

- Formatted more files with black
  ([`0cc520a`](https://github.com/gsinghjay/mvp_qr_gen/commit/0cc520a8bf59bd79c9b9217c9b287a7bcb419859))

### Documentation

- Add static folder documentation and update main README
  ([`65b9a0f`](https://github.com/gsinghjay/mvp_qr_gen/commit/65b9a0f9d00a36d21e7179d0a944b7b844675c8a))

- Update main README with project changes
  ([`0ff5630`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ff56304d459df90f3ee56487c7362762c8a2be8))

- **infrastructure**: Update infrastructure documentation
  ([`a86cdf1`](https://github.com/gsinghjay/mvp_qr_gen/commit/a86cdf1016ad29a0aba50734033dadefad1cbf04))

- **story**: Update story to reflect the status of the project
  ([`b453d98`](https://github.com/gsinghjay/mvp_qr_gen/commit/b453d9834aa81889dc804ccfadc2b37c7bac45c6))

### Features

- **api**: Implement health check endpoint and improve error handling
  ([`3560143`](https://github.com/gsinghjay/mvp_qr_gen/commit/356014394e5a6b7d2ce9f86f8ccd30115f359c20))

- **api**: Implement QRCodeService for service-layer dependency injection
  ([`9a1e259`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a1e25951f7074138e67948a4429c542ab0499cb))

### Refactoring

- **api**: Update API endpoints to use QRCodeService
  ([`9569d11`](https://github.com/gsinghjay/mvp_qr_gen/commit/9569d1164bcc87abc21b559be4ae942f62a20ece))

- **middleware**: Optimize middleware configuration and implementation
  ([`c2bb364`](https://github.com/gsinghjay/mvp_qr_gen/commit/c2bb364bd1fdb9d8155898cda1e11d25e8e4a086))

- **models**: Update database models for improved schema integrity
  ([`bb64fb2`](https://github.com/gsinghjay/mvp_qr_gen/commit/bb64fb2c231e5de970a94edf54537323949dca24))

- **routers**: Update QR routers to use service layer
  ([`cbddae0`](https://github.com/gsinghjay/mvp_qr_gen/commit/cbddae03ab594311ea658d9425a4295f10265133))

- **security**: Enforce HTTPS and improve code quality
  ([`3e304ea`](https://github.com/gsinghjay/mvp_qr_gen/commit/3e304ea7d968e1e07adb25e49b8d064f7d263f79))

- feat(security): enforce HTTPS for all routes and redirects - refactor(schemas): update to Pydantic
  V2 style validators - refactor(imports): fix incorrect database dependency imports -
  style(formatting): apply Black code formatting - style(lint): fix Ruff linting issues -
  docs(comments): improve docstrings and comments

- **service**: Remove deprecated service file in favor of new service layer
  ([`8717ec9`](https://github.com/gsinghjay/mvp_qr_gen/commit/8717ec9f5208c3c449efb0619b5ed800ed18b1f3))

### Testing

- **api**: Add service layer tests and integration tests
  ([`5d1ec4e`](https://github.com/gsinghjay/mvp_qr_gen/commit/5d1ec4e8da6a758d00cdc4b0defae0aa5db842f1))

- **api**: Refactor API tests to use proper dependency injection
  ([`cb8ad76`](https://github.com/gsinghjay/mvp_qr_gen/commit/cb8ad764704eed63d809c662149f76ab5c832b57))

- **integration**: Update integration tests to use test database session
  ([`eace9b9`](https://github.com/gsinghjay/mvp_qr_gen/commit/eace9b9cd9d4c989f24b4e18726697907a2a25f3))


## v0.3.3 (2025-02-20)

### Bug Fixes

- **security**: Enforce HTTPS for static files and standardize code formatting
  ([`6c8237e`](https://github.com/gsinghjay/mvp_qr_gen/commit/6c8237e85e4397391230fd64767db9aaf7324536))

### Chores

- Add development tools (black, ruff, mypy) with configurations
  ([`700ffc4`](https://github.com/gsinghjay/mvp_qr_gen/commit/700ffc48d764a68cb8838ae5b177a2d805dd54a6))


## v0.3.2 (2025-02-20)

### Bug Fixes

- **backend**: Enforce HTTPS for static files and template URLs
  ([`d6279ea`](https://github.com/gsinghjay/mvp_qr_gen/commit/d6279ea5837b48fa300378e40373df4782ef19eb))

- **frontend**: Update API calls and URL handling for HTTPS support
  ([`566c6ad`](https://github.com/gsinghjay/mvp_qr_gen/commit/566c6ad6b18786ead4ae968d110214ad60e64fbd))

- **infra**: Configure traefik for HTTPS and CORS handling
  ([`a99faa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/a99faa0cab94e48089b3c4ea158c7f16d2cabe23))

### Chores

- Ignore certificates directory for local development
  ([`df07a97`](https://github.com/gsinghjay/mvp_qr_gen/commit/df07a97dc92e0894fecb4fc87e76835061457660))


## v0.3.1 (2025-02-20)

### Bug Fixes

- **db**: Ensure database initialization completes before app startup
  ([`c703557`](https://github.com/gsinghjay/mvp_qr_gen/commit/c703557e11c5c0e6219f8f8658f2646ca39f1f47))


## v0.3.0 (2025-02-20)

### Chores

- Updated project status
  ([`23f72d1`](https://github.com/gsinghjay/mvp_qr_gen/commit/23f72d1202a0c29f58c8bf8bd01265ec854699a0))

### Code Style

- **ui**: Optimize CSS with better table styling and empty state improvements
  ([`4da8113`](https://github.com/gsinghjay/mvp_qr_gen/commit/4da8113479349dae22e395f8c9716d98c91c4867))

### Features

- **api**: Enhance API service with comprehensive TypeScript documentation and error handling
  ([`f79a141`](https://github.com/gsinghjay/mvp_qr_gen/commit/f79a141f0e3ddaab2d8447bd801d086bc07293bb))

### Refactoring

- **ui**: Streamline QR list section with improved header and search functionality
  ([`5f037e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/5f037e438c304fad373324aa31df9ae3866d817e))


## v0.2.0 (2025-02-20)

### Features

- **routers**: Add modular router structure for API, web, and QR code operations
  ([`546a37b`](https://github.com/gsinghjay/mvp_qr_gen/commit/546a37b5e2dc8219e03722083766881a25030d3d))

### Refactoring

- **db**: Improve database session handling and error logging
  ([`db4e237`](https://github.com/gsinghjay/mvp_qr_gen/commit/db4e2370ee2cb41cb4bd49062111db7eb161cfc4))

- **main**: Migrate routes to dedicated router modules
  ([`4b528f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/4b528f42e0ab0b0a16ea857183984170e8658ce2))

### Testing

- **config**: Update test configuration for router migration
  ([`bbfc084`](https://github.com/gsinghjay/mvp_qr_gen/commit/bbfc084fde71f1a0581b019cae0848395802d4b5))


## v0.1.0 (2025-02-19)

### Chores

- Update gitignore to exclude private development files
  ([`4b2aaf9`](https://github.com/gsinghjay/mvp_qr_gen/commit/4b2aaf9830d483ce3cd145d14d9be8461c5ce859))

- **config**: Add project dependencies and configuration files
  ([`52205ac`](https://github.com/gsinghjay/mvp_qr_gen/commit/52205aca5685a03a05589e9a7d735657ca977e8a))

- **infra**: Add docker and traefik configuration files
  ([`6d81d8a`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d81d8a9232c833199d1a1afba0101806270ddf9))

### Continuous Integration

- Add semantic release workflow
  ([`f621e30`](https://github.com/gsinghjay/mvp_qr_gen/commit/f621e30abcb1f79697b095b31f1d61a0d600b5a1))

### Documentation

- Add project documentation, research, and development tools configuration
  ([`d66da94`](https://github.com/gsinghjay/mvp_qr_gen/commit/d66da945f35f220a568948de0805071c5c4affff))

- Update project documentation and status
  ([`67a4b13`](https://github.com/gsinghjay/mvp_qr_gen/commit/67a4b13c1c92e56562e9a56cea433670f9f75eb1))

### Features

- **app**: Add initial application code and API tests
  ([`dd1104c`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd1104ca30251934093c7d3f1f7f924645d6eea7))

- **db**: Add alembic migration configuration and scripts
  ([`80d2be2`](https://github.com/gsinghjay/mvp_qr_gen/commit/80d2be2e0893b6bde2046c1adf06bc78a52d7bb6))

### Testing

- Remove redundant test_api_endpoints.py
  ([`44b8941`](https://github.com/gsinghjay/mvp_qr_gen/commit/44b8941cfa3917ddd9c2645148544e1e059e2825))
