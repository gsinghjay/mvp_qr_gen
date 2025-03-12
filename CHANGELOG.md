# CHANGELOG


## v0.11.0 (2025-03-12)

### Documentation

- **tests**: Enhance testing documentation with utility function examples
  ([`45b7645`](https://github.com/gsinghjay/mvp_qr_gen/commit/45b764596c2fc2aee3b6b21492fd80e22a3f0838))

### Features

- **tests**: Add validation utility functions for colors, URLs, and scan statistics
  ([`6f95507`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f9550721a5099cf676e38b8d2b201f9f6ee2b4b))

- **tests**: Add validation utility functions for colors, URLs, and scan statistics
  ([`c875961`](https://github.com/gsinghjay/mvp_qr_gen/commit/c875961d35efccf2e23f82998bf05f4a54291be7))

### Refactoring

- **tests**: Update test files to use new validation utilities
  ([`a8e450a`](https://github.com/gsinghjay/mvp_qr_gen/commit/a8e450a805c59b88d0a0c4edde4e414aa42de109))


## v0.10.0 (2025-03-12)

### Chores

- Remove obsolete optimization tasks file
  ([`807064b`](https://github.com/gsinghjay/mvp_qr_gen/commit/807064bfa8caa3afceb0e8a79eb65e6f6e739693))

- Updated docs
  ([`d06d707`](https://github.com/gsinghjay/mvp_qr_gen/commit/d06d707339b4f98a5c82c104a594f52be3b3cc7c))

### Documentation

- Mark HTTP method decorator task as complete
  ([`388b56d`](https://github.com/gsinghjay/mvp_qr_gen/commit/388b56d5123d3f66ad8860d4b76b5dca59d3c06b))

- Update task tracking for completed test fixtures
  ([`f108ad5`](https://github.com/gsinghjay/mvp_qr_gen/commit/f108ad5fc04dcee276228d6405d3cc9672ce49ef))

- **tests**: Add comprehensive testing documentation
  ([`c99a1f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/c99a1f4b130c0d5389471139119700ca3ad308b6))

### Features

- **tests**: Add comprehensive test fixtures for QR code testing
  ([`a99f12e`](https://github.com/gsinghjay/mvp_qr_gen/commit/a99f12eab8579215e0bfaf11eef04a9f7447bdb3))

- **tests**: Add reusable test utilities and assertions
  ([`7b01d4e`](https://github.com/gsinghjay/mvp_qr_gen/commit/7b01d4e8207f62c0cdbbfd227c2f9d9f8872b2c9))

### Refactoring

- Update redirect endpoint with proper status code and response documentation
  ([`3cb20a9`](https://github.com/gsinghjay/mvp_qr_gen/commit/3cb20a90b2d572753ad6c67bf34eaa7ece81b942))

### Testing

- Add HTTP method decorator tests
  ([`3008600`](https://github.com/gsinghjay/mvp_qr_gen/commit/3008600c453baa59c0ba8751adf5d571ec1349ac))


## v0.9.0 (2025-03-10)

### Chores

- Following fastapi_optimization_tasks.md
  ([`ea3b248`](https://github.com/gsinghjay/mvp_qr_gen/commit/ea3b248a6d505013de66e4b5e1aa5db15a090874))

### Documentation

- **tasks**: Mark middleware simplification task as completed
  ([`5872a8e`](https://github.com/gsinghjay/mvp_qr_gen/commit/5872a8e2d589e741426b2e8ea7f7f38dee19169e))

### Features

- **app**: Implement modern lifespan approach for FastAPI lifecycle management
  ([`9a22572`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a2257218acd76bde99f42c97d78ce779b0de0df))

### Refactoring

- **app**: Replace custom middleware loader with direct FastAPI middleware calls
  ([`787e06b`](https://github.com/gsinghjay/mvp_qr_gen/commit/787e06b1b6f9eebd080ad4f23139d4968d030c2a))

- **config**: Remove complex middleware configuration dictionary
  ([`1fc5b53`](https://github.com/gsinghjay/mvp_qr_gen/commit/1fc5b53e28a4158a956c893eddb8c14eb7991a87))

### Testing

- **middleware**: Add comprehensive tests for middleware functionality
  ([`00dd091`](https://github.com/gsinghjay/mvp_qr_gen/commit/00dd091912d66ae02b785acdf8948747cb19ae06))


## v0.8.0 (2025-03-10)

### Features

- **api**: Improve router tags and remove prefix duplication
  ([`de50cd4`](https://github.com/gsinghjay/mvp_qr_gen/commit/de50cd442e608142fac7f3d8026d8dfd35fdc082))

### Refactoring

- **router**: Reorganize router initialization with proper parent routers
  ([`ca9af0f`](https://github.com/gsinghjay/mvp_qr_gen/commit/ca9af0f6bb5dac9601310c6b3a01c474c6d8538c))

### Testing

- **router**: Add test_router_structure.py to verify API path accessibility
  ([`628be3d`](https://github.com/gsinghjay/mvp_qr_gen/commit/628be3d1d56e68e720a039bd25d5878417381adf))


## v0.7.0 (2025-03-10)

### Bug Fixes

- **api**: Update endpoint status codes to follow REST conventions
  ([`19b6246`](https://github.com/gsinghjay/mvp_qr_gen/commit/19b624678e684c96c0bbcce6177d756cd71ead8e))

- **health**: Adjust health service implementation for test compatibility
  ([`572262b`](https://github.com/gsinghjay/mvp_qr_gen/commit/572262b9666c445551f57880c2862511d4147fbf))

- **qr**: Ensure dynamic QR codes always use redirect path as content
  ([`6e1398c`](https://github.com/gsinghjay/mvp_qr_gen/commit/6e1398cbcd316faea490e0565e9284638950f666))

- **services**: Convert HttpUrl to string before saving to database
  ([`ec2e4ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/ec2e4efa28cd475668e33d94b2ddab92891ed94d))

- **tasks**: Handle background task error states correctly
  ([`f79d1ed`](https://github.com/gsinghjay/mvp_qr_gen/commit/f79d1ed1e9a4b86785b73999a4173be42082c1f9))

- **tests**: Correct dependency injection and redirect status code in test_main.py
  ([`510cd23`](https://github.com/gsinghjay/mvp_qr_gen/commit/510cd239a27119fac8214c99003882687267b041))

- **tests**: Improve concurrent reads test with session isolation
  ([`57aaf74`](https://github.com/gsinghjay/mvp_qr_gen/commit/57aaf74073bc2a869af06cdba0d686bdd9955b92))

- **tests**: Replace UTC import with timezone.utc for compatibility
  ([`dd5057a`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd5057ad9cc0591db8e6e15383390aa8cdfc17d6))

- **tests**: Resolve SQLite concurrency and WAL mode test failures
  ([`9d9e355`](https://github.com/gsinghjay/mvp_qr_gen/commit/9d9e355491d7b110b70016072b7605ed0d190871))

- **tests**: Update concurrent test assertion for dynamic test count
  ([`f6a243b`](https://github.com/gsinghjay/mvp_qr_gen/commit/f6a243bacb718c8ad4943de2c385bff74a7697ff))

- **tests**: Update SQLite UTC functions to return consistent Z-suffix format
  ([`533028f`](https://github.com/gsinghjay/mvp_qr_gen/commit/533028fd3be0a9eac48ddb085507e835b7e1e34b))

### Build System

- **deps**: Add aiosqlite dependency for async SQLite support
  ([`866c14f`](https://github.com/gsinghjay/mvp_qr_gen/commit/866c14f8f96611c463eaad99f22fb3ca54fad5eb))

### Documentation

- Complete test refactoring plan
  ([`907c31e`](https://github.com/gsinghjay/mvp_qr_gen/commit/907c31ee297a7790d4f312ab2ce7ccd67f24f029))

- Mark SQLite test refactoring tasks as completed
  ([`70c8b15`](https://github.com/gsinghjay/mvp_qr_gen/commit/70c8b15d5ded3d5d43b8c8e6c85014d53af2a7be))

- **refactor**: Mark dependency injection standardization task as completed
  ([`c033150`](https://github.com/gsinghjay/mvp_qr_gen/commit/c033150f728928ec181ac76d13467721825aa86f))

- **scripts**: Update API test script documentation
  ([`67d3d5d`](https://github.com/gsinghjay/mvp_qr_gen/commit/67d3d5d0810a502cd17e42b6f439c199ff494dcf))

### Features

- **core**: Add centralized exception handling system
  ([`1d59159`](https://github.com/gsinghjay/mvp_qr_gen/commit/1d5915998d5f311f86f504a5ad8f774cdff7eb0f))

- **schemas**: Update schema exports to include parameter models
  ([`a9c2f7e`](https://github.com/gsinghjay/mvp_qr_gen/commit/a9c2f7e6db72d760cc35589d336387eebbbd50c9))

- **tests**: Add helper functions for DRY test assertions
  ([`9fb6e87`](https://github.com/gsinghjay/mvp_qr_gen/commit/9fb6e87bbeb22991f28343635b2f0c9b17f3af1c))

- **tests**: Implement DependencyOverrideManager for standardized dependency injection
  ([`ca5011e`](https://github.com/gsinghjay/mvp_qr_gen/commit/ca5011e01d709c48ba1889b9bfd3c3b0709cc7eb))

- **tests**: Implement factory pattern for test data generation
  ([`86a93fe`](https://github.com/gsinghjay/mvp_qr_gen/commit/86a93fe9ecfe9afacce2d16612ba31540099f06f))

- **validation**: Add parameter models with validation for QR code creation
  ([`989ae4d`](https://github.com/gsinghjay/mvp_qr_gen/commit/989ae4d974da4c22095541c4ece408f0d4e677f1))

### Refactoring

- **api**: Update API endpoints to use parameter models
  ([`18940cb`](https://github.com/gsinghjay/mvp_qr_gen/commit/18940cb7b98c29477518cbde9829de0da2a9d4c3))

- **routers**: Update QR routers to use parameter models
  ([`19ef336`](https://github.com/gsinghjay/mvp_qr_gen/commit/19ef3366795314f207897b5c555d3782c938a0f4))

- **tests**: Consolidate QR service tests from real_db variant
  ([`ed63efc`](https://github.com/gsinghjay/mvp_qr_gen/commit/ed63efcdf2975a6fe68a4efa04a290925e22778b))

- **tests**: Enhance integration tests with consistent dependency handling
  ([`3c3b34e`](https://github.com/gsinghjay/mvp_qr_gen/commit/3c3b34e418140862664aef909ba68a8e65afc8fb))

- **tests**: Improve background task testing with proper async handling
  ([`e56fdd4`](https://github.com/gsinghjay/mvp_qr_gen/commit/e56fdd45cb54255a6569c0f262d6fca0feaae29d))

- **tests**: Improve database session management in conftest.py
  ([`abedc0b`](https://github.com/gsinghjay/mvp_qr_gen/commit/abedc0b430c68cc2a212eb80e8512910269225bf))

- **tests**: Parameterize QR service tests for better coverage
  ([`0e12eb4`](https://github.com/gsinghjay/mvp_qr_gen/commit/0e12eb4e59bf63e86d3dd9f233f1fa5df1f85e16))

- **tests**: Parameterize validation tests to reduce duplication
  ([`3e19e04`](https://github.com/gsinghjay/mvp_qr_gen/commit/3e19e04e270392323c6f15266a3af96202ee5e07))

- **tests**: Remove redundant real_db test files
  ([`618bb83`](https://github.com/gsinghjay/mvp_qr_gen/commit/618bb831779c318d8bcb5a619df9e37f911affca))

- **tests**: Replace in-memory SQLite with file-based SQLite for integration tests
  ([`3ffb813`](https://github.com/gsinghjay/mvp_qr_gen/commit/3ffb8138ee4f5c3ea268c83812f0a30d625e4199))

### Testing

- Add real database tests for background tasks
  ([`2e5f81a`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e5f81a9219d46739f7789ced2b3991457753b83))

- Add real database tests for QR service
  ([`59b792c`](https://github.com/gsinghjay/mvp_qr_gen/commit/59b792c9bb7253a992bada870594fc1d12d27854))

- Add SQLite-specific functionality tests
  ([`0b41d74`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b41d748a1c49bcbe80a3819a6439b85514c7ea0))

- Add unit tests for factory pattern implementation
  ([`59eb9e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/59eb9e392b6f48d2f476069009cd8fc533908f6e))

- Implement response model validation tests
  ([`ad64279`](https://github.com/gsinghjay/mvp_qr_gen/commit/ad64279e2a3a772c85e988079de9e6ba9a3cd9c6))

- **api**: Add comprehensive examples for dependency injection patterns
  ([`19d75fe`](https://github.com/gsinghjay/mvp_qr_gen/commit/19d75fe457fdc8116de9cf84112ea1e09d267467))

- **framework**: Improve test fixtures and dependency overrides
  ([`c626f3e`](https://github.com/gsinghjay/mvp_qr_gen/commit/c626f3ef184533f8780aa5baa2cd8cc50a332340))

- **integration**: Fix test assertions to expect correct status codes
  ([`5aa6b3d`](https://github.com/gsinghjay/mvp_qr_gen/commit/5aa6b3df1a15a335e2b3897808c7e491799ffd02))

- **response**: Update response model tests for parameter validation
  ([`a7b342b`](https://github.com/gsinghjay/mvp_qr_gen/commit/a7b342b1c3698eefab1434ee1e212379f7a8531f))


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
