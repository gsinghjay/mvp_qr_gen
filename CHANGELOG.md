# CHANGELOG


## v1.12.1 (2025-05-28)

### Chores

* chore: add .env.example template for environment variables

- Create example environment file with proper structure
- Replace sensitive values with descriptive placeholders
- Maintain all required configuration sections
- Add comments explaining variable purposes
- Ensure example file is git-tracked while .env remains ignored ([`eca1f2a`](https://github.com/gsinghjay/mvp_qr_gen/commit/eca1f2a92fc37edfc059a5909423944b2b708e7d))

### Fixes

* fix: qr code using size outside defined model ([`10ea752`](https://github.com/gsinghjay/mvp_qr_gen/commit/10ea752f770873205ff4765aef071684acd538b4))

* fix: use environment variables for auth in test_qr_paths.py ([`f61eb89`](https://github.com/gsinghjay/mvp_qr_gen/commit/f61eb89b66c6667a5970b655d12aff60f21ebbd4))

* fix: use environment variables for auth in test_paths_metrics.py ([`dbc2a19`](https://github.com/gsinghjay/mvp_qr_gen/commit/dbc2a190a29b935d1f6c7421ab3ec4d95e52f071))

* fix: use environment variables for auth in test_circuit_breaker.py ([`4cb8cfa`](https://github.com/gsinghjay/mvp_qr_gen/commit/4cb8cfa68a9d1a0e1f2fa61e728266eea00d5116))

* fix: add proper auth variable checking to check_health.sh ([`8edefc0`](https://github.com/gsinghjay/mvp_qr_gen/commit/8edefc00eca16085a838b475856e6a1cd61f31f7))

* fix: remove hardcoded credential defaults from safe_restore.sh ([`22a240c`](https://github.com/gsinghjay/mvp_qr_gen/commit/22a240c7db31099087e0b868fe133c9436de96c4))

* fix: remove hardcoded credentials from rollback.sh error messages ([`207616b`](https://github.com/gsinghjay/mvp_qr_gen/commit/207616b78c4edf46581d22404328d49abea01077))

* fix: remove hardcoded credential defaults from performance_test.sh ([`24d808e`](https://github.com/gsinghjay/mvp_qr_gen/commit/24d808e87992d70073bb88bc8f4365cf02e89242))

* fix: remove hardcoded credentials from alerts.yml ([`5008acf`](https://github.com/gsinghjay/mvp_qr_gen/commit/5008acfaf8d24f2d206e50298afbdb992d586817))

### Unknown

* Merge pull request #59 from gsinghjay/fix/hardcoded-credentials

Remove Hardcoded Credentials From Codebase ([`4e67b5a`](https://github.com/gsinghjay/mvp_qr_gen/commit/4e67b5a5ff687c7b5d016ec63af59c9eb1e21695))


## v1.12.0 (2025-05-27)

### Build System

* build: configure container for code changes without rebuilds ([`2e5647b`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e5647b152eec5e8638827fe9726b5e9e2cb935b))

### Chores

* chore: add aiobreaker dependency for async circuit breaker implementation ([`bc82000`](https://github.com/gsinghjay/mvp_qr_gen/commit/bc820009c2073d4e620611fe13bc86f76fb1b17d))

### Features

* feat: add verification script for circuit breaker refactoring ([`4232993`](https://github.com/gsinghjay/mvp_qr_gen/commit/4232993395b89ff4e38829494607822fd5f9024a))

### Fixes

* fix: add size limits to QR download options in UI ([`2b1e58c`](https://github.com/gsinghjay/mvp_qr_gen/commit/2b1e58c1944f3c661e56ffecebabe88bc2e1436b))

* fix: update _calculate_precise_scale to properly handle size parameter ([`9c5210d`](https://github.com/gsinghjay/mvp_qr_gen/commit/9c5210d41cce9d344d1b16c5e8e2cc44a89d17dd))

* fix: pass correct scale factor to QRImageParameters in QR generation service ([`ed32c6e`](https://github.com/gsinghjay/mvp_qr_gen/commit/ed32c6e661207c509e97fdae1e39854618ed9aa7))

* fix: update QRImageParameters.size max limit to 50 ([`d7630aa`](https://github.com/gsinghjay/mvp_qr_gen/commit/d7630aa897dfec328dd987d1c0769529d5ef9792))

* fix: update QRCodeService to use decorator pattern with aiobreaker ([`acbf5f9`](https://github.com/gsinghjay/mvp_qr_gen/commit/acbf5f94f80f3f2bfb51f271f289fb606c75905c))

* fix: update circuit breaker to use aiobreaker correctly ([`9057a8c`](https://github.com/gsinghjay/mvp_qr_gen/commit/9057a8c9e3239ed66491525c0a37e6299a3f171a))

* fix: update circuit breaker to use timeout_duration instead of reset_timeout for aiobreaker compatibility

- Changed reset_timeout parameter to timeout_duration as required by aiobreaker
- Added proper datetime.timedelta conversion for timeout value
- Updated test_circuit_breaker.py to use aiobreaker and async functions
- Verified changes with enhanced_smoke_test.sh ([`02faba2`](https://github.com/gsinghjay/mvp_qr_gen/commit/02faba24586faf542ab58cda4a8aee550f18ffa8))

### Refactoring

* refactor: remove deprecated circuit breaker test script ([`b63e4f2`](https://github.com/gsinghjay/mvp_qr_gen/commit/b63e4f257efe0d830ea413758fc5a621093932e4))

* refactor: update API endpoints to await async service methods ([`429d454`](https://github.com/gsinghjay/mvp_qr_gen/commit/429d45452cb7040e119738f6e020b0811925857f))

* refactor: convert service methods to async and use aiobreaker context manager ([`eb0d9f5`](https://github.com/gsinghjay/mvp_qr_gen/commit/eb0d9f563016a5eb4b64da8b61e58b0c27e10c33))

* refactor: remove create_and_format_qr_sync method in favor of direct async calls ([`39ee011`](https://github.com/gsinghjay/mvp_qr_gen/commit/39ee0117454b7dc66123a6a4494830b8c7570d9d))

* refactor: update circuit breaker implementation to use aiobreaker with async support ([`d2fe774`](https://github.com/gsinghjay/mvp_qr_gen/commit/d2fe774a4c6499320c69901cf6d0ad31b2e430f3))

### Testing

* test: add unit tests for aiobreaker implementation ([`9fee07a`](https://github.com/gsinghjay/mvp_qr_gen/commit/9fee07a0af55d224377104a8d035bfe9b01abba6))

* test: update E2E circuit breaker tests for aiobreaker compatibility ([`be33bf6`](https://github.com/gsinghjay/mvp_qr_gen/commit/be33bf65e9ade96db7cf62d27d142fe949c67903))

### Unknown

* Merge pull request #58 from gsinghjay/feat/aiobreaker

Replace pybreaker with aiobreaker for Asynchronous Circuit Breaking ([`17b74ec`](https://github.com/gsinghjay/mvp_qr_gen/commit/17b74ec647dff62d6c9d2c54bcb5a3aa5cb0d4c4))


## v1.11.1 (2025-05-27)

### Chores

* chore: update docker-compose.yml with volume mounts for testing ([`08d20e0`](https://github.com/gsinghjay/mvp_qr_gen/commit/08d20e000c65eafbd88965f67a2b83c8e266367f))

* chore: update Dockerfile for testing environment improvements ([`378de44`](https://github.com/gsinghjay/mvp_qr_gen/commit/378de44ee8144f61f9af6528775c4caa1ce9fc48))

### Fixes

* fix: improve enhanced smoke test with proper Prometheus connectivity ([`7ed5821`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ed58212c1967afbf73f49853fd0e6484bd9f1da))

* fix: resolve asyncio.run() error in create_and_format_qr_sync method ([`b1c085a`](https://github.com/gsinghjay/mvp_qr_gen/commit/b1c085a5ba5d1d0cc7d6423921b59e26e078fbe6))

### Refactoring

* refactor: enhance metrics logger for more accurate path-specific measurements ([`760644d`](https://github.com/gsinghjay/mvp_qr_gen/commit/760644d6c8214b5eeb06c2e38c6a5e51eb38377d))

* refactor: improve circuit breaker implementation with better error handling ([`1c41389`](https://github.com/gsinghjay/mvp_qr_gen/commit/1c4138930e9ac9872435c504e64da07924fe9b9d))

### Testing

* test: implement comprehensive E2E test suite ([`b99c7ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/b99c7ef99ee262957178b5da1b017b72a8c4188d))

* test: add circuit breaker test script ([`e4d1564`](https://github.com/gsinghjay/mvp_qr_gen/commit/e4d156484498496533dfd16922fd0ef0a22ab4e1))

### Unknown

* Merge pull request #57 from gsinghjay/task-1.4

Internal Testing Plan & Initial Tests ([`c149a11`](https://github.com/gsinghjay/mvp_qr_gen/commit/c149a113dea8703abc1a13d0f88bdf314ec3e2a4))


## v1.11.0 (2025-05-27)

### Chores

* chore: removed tests due to refactor ([`4d37f56`](https://github.com/gsinghjay/mvp_qr_gen/commit/4d37f56d559e15eff436c5cf3d5547527d02f884))

### Features

* feat(dashboard): add path comparison panels for QR generation monitoring

- Add 4 new panels for old vs new path performance comparison
- Include request rate, success rate, duration comparison, and utilization overview
- Update dashboard status to reflect Phase 1 - Parallel Implementation progress
- Enable real-time A/B testing visualization and canary deployment monitoring ([`fad9a23`](https://github.com/gsinghjay/mvp_qr_gen/commit/fad9a232c884ed5a11688fbcdc93a7eddf1bcee8))

* feat(qr-service): implement comprehensive path-specific metrics instrumentation

- Add timing instrumentation for create_static_qr, create_dynamic_qr, and generate_qr methods
- Track performance metrics for both 'old' and 'new' service paths using time.perf_counter()
- Log success/failure status and duration for all QR generation operations
- Implement proper error handling with metrics collection in exception paths
- Support A/B testing and canary deployment monitoring through detailed path comparison ([`e34c2a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/e34c2a73730df4a930492b182acf33c9cc3b88ff))

* feat(metrics): update qr_generation_path_duration_seconds bucket configuration

- Update histogram buckets to match task specification: (0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.5, 5.0)
- Ensure consistency with Sub-Task 1.3.1 requirements for path-specific metrics ([`4c586fc`](https://github.com/gsinghjay/mvp_qr_gen/commit/4c586fca25447e9701694fe75d501b6517cf70f7))

### Unknown

* Merge pull request #56 from gsinghjay/task-1.3

Implement path-specific metrics instrumentation for QR generation ([`55f835a`](https://github.com/gsinghjay/mvp_qr_gen/commit/55f835a698db6c4d7f80fda0883a9f90c28f7936))


## v1.10.0 (2025-05-27)

### Features

* feat: add enhanced API testing script for circuit breaker validation ([`b236f6d`](https://github.com/gsinghjay/mvp_qr_gen/commit/b236f6d85e1d78d8656a803bc101b95b3afc8849))

* feat: integrate circuit breaker protection for all QR generation methods ([`b3f075c`](https://github.com/gsinghjay/mvp_qr_gen/commit/b3f075cc68207c260cd28fff0ecf6ec63cb5f835))

* feat: add synchronous wrapper for circuit breaker compatibility ([`a6f74ec`](https://github.com/gsinghjay/mvp_qr_gen/commit/a6f74ec3ceda9471189200ea7130a34a82d78835))

* feat: integrate circuit breaker into dependency injection system ([`4b2f74e`](https://github.com/gsinghjay/mvp_qr_gen/commit/4b2f74eb62a19b68968811e490db28bd69a8b000))

* feat: add circuit breaker metrics collection and logging ([`e085f42`](https://github.com/gsinghjay/mvp_qr_gen/commit/e085f4263fe0005eec038beaf85e5ea722385e6c))

* feat: implement circuit breaker with listener and dependency injection ([`5ddc275`](https://github.com/gsinghjay/mvp_qr_gen/commit/5ddc27524c783a7d61c21afb403e47841749f871))

* feat: add circuit breaker configuration settings ([`651b2dc`](https://github.com/gsinghjay/mvp_qr_gen/commit/651b2dcb716fa9c6f6540301777bed9f66d43717))

* feat: add pybreaker>=1.0.0 dependency for circuit breaker pattern ([`361bc40`](https://github.com/gsinghjay/mvp_qr_gen/commit/361bc40bd50e4c4e29734d38d7812fd33b54b1bc))

### Testing

* test: add QR test images for circuit breaker validation ([`3fa6bea`](https://github.com/gsinghjay/mvp_qr_gen/commit/3fa6bea7512358164a277aa6f6098e432bcc3371))

### Unknown

* Merge pull request #55 from gsinghjay/phase-1.2

Circuit Breaker Implementation ([`5e66c8a`](https://github.com/gsinghjay/mvp_qr_gen/commit/5e66c8a8378aa2da2268e0d923a8a1f45089d5f6))


## v1.9.1 (2025-05-27)

### Fixes

* fix: update traefik routing configuration to fix connection issues ([`0be55fb`](https://github.com/gsinghjay/mvp_qr_gen/commit/0be55fb3f9f88fb2982298f0cbe781d8749645bd))

* fix: use named volume for test_advanced_qr_images to resolve permission issues ([`fffa095`](https://github.com/gsinghjay/mvp_qr_gen/commit/fffa0956875899c5e42c5b110625208337abc671))

* fix: add test_advanced_qr_images directory with proper permissions ([`933a934`](https://github.com/gsinghjay/mvp_qr_gen/commit/933a9340a87ee1e2acee31864272e2672281bda1))


## v1.9.0 (2025-05-27)

### Chores

* chore(assets): update test QR images with new logo implementation ([`8a039e2`](https://github.com/gsinghjay/mvp_qr_gen/commit/8a039e2cca280264623baad0c3aa35d5cd510dea))

* chore(config): update default logo path to use hccc_logo_official.png ([`64ae2ae`](https://github.com/gsinghjay/mvp_qr_gen/commit/64ae2aee5f17bfa313a0043c69940c9a06715860))

### Features

* feat(assets): add official HCCC logo for QR codes ([`7908888`](https://github.com/gsinghjay/mvp_qr_gen/commit/790888869c28da8a9b7ac6967591a15ccea1b6a0))

* feat(docker): add volume mounts for test scripts and images

- Mount app/scripts to /app/app/scripts for Python imports
- Mount test_advanced_qr_images for immediate test access
- Update script mount comment to clarify init.sh inclusion ([`c6a4b35`](https://github.com/gsinghjay/mvp_qr_gen/commit/c6a4b35a4829924c292d0df9ef703f0f8cfacdca))

* feat(test): add comprehensive QR generation test suite

- Test SVG logo handling and error correction auto-upgrade
- Validate Segno best practices implementation
- Include physical dimensions and accessibility testing ([`912eb3e`](https://github.com/gsinghjay/mvp_qr_gen/commit/912eb3e396b951679da412ce8331b349eeec54d4))

* feat(qr): add automatic error correction upgrade for logos

- Auto-upgrade error correction to 'H' when include_logo=True
- Ensure QR codes with logos maintain scannability
- Implement service-layer validation for logo requirements ([`cbf273d`](https://github.com/gsinghjay/mvp_qr_gen/commit/cbf273d3a794d53fcce73665e93112042fa3b896))

* feat(qr): implement Segno best practices and SVG logo support

- Use Segno's recommended 33% logo scaling (was 25%)
- Add svg_inline() method using native Segno implementation
- Fix color defaults to prevent white QR codes
- Add adaptive SVG conversion with cairosvg integration
- Implement proper fallback handling for SVG logos ([`ddf2951`](https://github.com/gsinghjay/mvp_qr_gen/commit/ddf2951447d92d94b1c2adfb5a4f1282375555fa))

* feat(deps): add cairosvg for SVG logo conversion

- Add cairosvg>=2.8.2 for SVG to PNG conversion
- Enables proper SVG logo handling in QR codes ([`6b987a3`](https://github.com/gsinghjay/mvp_qr_gen/commit/6b987a30475e33d47aacf273eb2efe37ba50f6b1))

* feat(docker): add Cairo libraries for SVG logo support

- Add libcairo2-dev and libgirepository1.0-dev for cairosvg
- Enable SVG to PNG conversion for QR code logo embedding ([`74c90a4`](https://github.com/gsinghjay/mvp_qr_gen/commit/74c90a4ff6eaf6bd8ba4e704782a7024106eda1a))

### Fixes

* fix(qr): improve logo integration with QR background color matching ([`6dad531`](https://github.com/gsinghjay/mvp_qr_gen/commit/6dad531ff5d52eb6723aeeea77b7fe7107057ad6))

### Refactoring

* refactor(qr): update legacy QR imaging utilities for logo handling ([`ec5a4a9`](https://github.com/gsinghjay/mvp_qr_gen/commit/ec5a4a971efd6ee68204dae86e3d84dcdc69f768))

### Testing

* test(qr): remove SVG logo tests and update logo tests for PNG ([`ad5359f`](https://github.com/gsinghjay/mvp_qr_gen/commit/ad5359fa40e7982afb1ede08b3a598273fcd3f91))

* test: add generated QR test images for validation ([`675a9ba`](https://github.com/gsinghjay/mvp_qr_gen/commit/675a9ba3fe2ebe3a290d554c7f39cdc381b8ed29))

### Unknown

* Merge pull request #54 from gsinghjay/feat/segno

Implement Segno QR Code Best Practices and SVG Logo Support ([`80af5db`](https://github.com/gsinghjay/mvp_qr_gen/commit/80af5db7efeb0c25efe78532c261405f9fa5a295))


## v1.8.0 (2025-05-26)

### Chores

* chore: remove obsolete test and cleanup scripts ([`dc61033`](https://github.com/gsinghjay/mvp_qr_gen/commit/dc61033cdfee1c58e0e89412287c91025b7375ff))

### Features

* feat: add service-level input validation for QR generation ([`5471850`](https://github.com/gsinghjay/mvp_qr_gen/commit/54718504ac474f782e1b49c82a07dc9790bbf623))

* feat: enhance QRImageParameters with format validation and alias handling ([`a664bdd`](https://github.com/gsinghjay/mvp_qr_gen/commit/a664bdd02e509ab0305b093dbcb80ca1fda6205f))

* feat: add comprehensive format validation to Segno QR adapter ([`49372db`](https://github.com/gsinghjay/mvp_qr_gen/commit/49372db26b9cb0b3c9d248b5c18b6aa6d4150de2))

### Unknown

* Merge pull request #53 from gsinghjay/chore/house-cleaning

Enhanced Format Validation for QR Generation Pipeline ([`3fae1e5`](https://github.com/gsinghjay/mvp_qr_gen/commit/3fae1e53b8647ac63f7beacb2d06d21541804a5d))


## v1.7.0 (2025-05-26)

### Chores

* chore(debug): add SVG debugging utility script ([`e159a01`](https://github.com/gsinghjay/mvp_qr_gen/commit/e159a01d9149af145738404ba997fdb86fc0d6a8))

### Features

* feat(schemas): enhance QRImageParameters for advanced color support ([`c705a5f`](https://github.com/gsinghjay/mvp_qr_gen/commit/c705a5f770a15b01c4a188044a7391a6b392bb45))

* feat(adapters): implement data URI methods in PillowQRImageFormatter ([`c20bbcf`](https://github.com/gsinghjay/mvp_qr_gen/commit/c20bbcf02abbcc37df3b37eb99ba85b1f6f27207))

* feat(interfaces): add data URI methods to QRImageFormatter interface ([`9860ec6`](https://github.com/gsinghjay/mvp_qr_gen/commit/9860ec6d4a9543b5c54ff47850a81685ff5a6e1b))

* feat(services): add new validation service with provider interface ([`120c3ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/120c3ef804c4c97adb1f23987e7114b4fddc54dd))

* feat(services): add new QR generation service with interface-based architecture ([`0a754a2`](https://github.com/gsinghjay/mvp_qr_gen/commit/0a754a2c241aab6fa412df74410a8c5f3bdc00c3))

* feat(services): add new analytics service with MetricsLogger instrumentation ([`1d62f6d`](https://github.com/gsinghjay/mvp_qr_gen/commit/1d62f6d01fd1f2746d77c5153d3775033909ec5d))

* feat(interfaces): add core domain abstraction interfaces for Observatory-First architecture ([`1cea892`](https://github.com/gsinghjay/mvp_qr_gen/commit/1cea892fe7a53aa39656965d9fc1be74cc495030))

* feat(admin): add secured endpoints for service status and feature flags ([`1cc4c69`](https://github.com/gsinghjay/mvp_qr_gen/commit/1cc4c69eceb78cc0b0a6be3c216a4fbc492fba6d))

* feat(adapters): implement Segno QR generator with all optimizations ([`4420e82`](https://github.com/gsinghjay/mvp_qr_gen/commit/4420e8251c3105ec129bf5f904c5b71a63942cb9))

* feat(traefik): add secured admin endpoints with IP whitelist and basic auth ([`3b591f0`](https://github.com/gsinghjay/mvp_qr_gen/commit/3b591f0a29325ea4f38c102b27faaf1ec84ee84b))

* feat(health): implement dynamic health checks for new services ([`affa166`](https://github.com/gsinghjay/mvp_qr_gen/commit/affa166e48955b08fc87368ddedd013f5859c45e))

* feat(deps): add new service providers with interface-based injection ([`f7c7729`](https://github.com/gsinghjay/mvp_qr_gen/commit/f7c77297f8a6871af302521e9a8da50fdff0342c))

* feat(config): add Phase 0 feature flags and canary testing configuration ([`27b7c02`](https://github.com/gsinghjay/mvp_qr_gen/commit/27b7c0209c682253ba5d733ba8d1733648a4ee7f))

* feat(health): add dynamic service checks based on feature flags ([`cd23ecb`](https://github.com/gsinghjay/mvp_qr_gen/commit/cd23ecbc52ce8cb15ab0eab8bb9b1c4243f133aa))

* feat(api): export admin metrics endpoint for secured monitoring ([`c701455`](https://github.com/gsinghjay/mvp_qr_gen/commit/c70145575ee314f53d80dcfff007c289f53588fb))

### Testing

* test: add test script for Phase 0.2 features ([`8c9cb55`](https://github.com/gsinghjay/mvp_qr_gen/commit/8c9cb5578096e387ed26ca8e94bfdfa7c29455ca))

### Unknown

* Merge pull request #51 from gsinghjay/feat/phase-0

Phase 0: Pure Additions - Observatory-First Interface Architecture ([`b60dfa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/b60dfa0977fb5630635c39cdc72c3fca6cd39730))


## v1.6.0 (2025-05-26)

### Features

* feat(db): add nullable fields for refactoring preparation ([`5d72f61`](https://github.com/gsinghjay/mvp_qr_gen/commit/5d72f612d93553043d9da6824745791e8d219ede))

### Unknown

* Merge pull request #50 from gsinghjay/feat/nullable-db-columns

Complete Safety Phase Task S.5 - Database Schema Preparation ([`f05231e`](https://github.com/gsinghjay/mvp_qr_gen/commit/f05231e3272dfcfc38fa61040f04c57467a28c33))

* config(traefik): update dynamic configuration ([`6e7dc6e`](https://github.com/gsinghjay/mvp_qr_gen/commit/6e7dc6e805960790a9637e7d7e1ec185ab24bc41))


## v1.5.0 (2025-05-26)

### Documentation

* docs(grafana): add database monitoring dashboard and MCP integration documentation ([`23e3109`](https://github.com/gsinghjay/mvp_qr_gen/commit/23e31090cd4bd38f5edf7bfd55d51bd2fd7acfc7))

### Features

* feat(config): enable MCP Grafana integration and dashboard volume mounting ([`5f1d179`](https://github.com/gsinghjay/mvp_qr_gen/commit/5f1d1799fe223e4fb2ce1035301113b7e10a6e7a))

* feat(grafana): add comprehensive QR database monitoring dashboard ([`1653daa`](https://github.com/gsinghjay/mvp_qr_gen/commit/1653daae23cc1438686eaca1f78fdcb00266bde2))

* feat(grafana): add PostgreSQL datasources for production and test environments ([`83f0a6b`](https://github.com/gsinghjay/mvp_qr_gen/commit/83f0a6be50721bdd973f295a130495b62485bcb7))

* feat(utils): add timing decorator to QR image generation utility ([`e58a7dc`](https://github.com/gsinghjay/mvp_qr_gen/commit/e58a7dcb79ef4986fb2cbffe51989696d3aa6faa))

* feat(service): add comprehensive timing decorators to QRCodeService methods ([`9b7b793`](https://github.com/gsinghjay/mvp_qr_gen/commit/9b7b7934444a2951cf0bc9984e4b26023c8eef03))

* feat(repository): add timing decorators to ScanLogRepository methods ([`27f9bb0`](https://github.com/gsinghjay/mvp_qr_gen/commit/27f9bb0acc7a081f41493d244dc51b4ab32073fd))

* feat(repository): add timing decorators to QRCodeRepository methods ([`c5b9bb4`](https://github.com/gsinghjay/mvp_qr_gen/commit/c5b9bb406a42a0b500b68ac3c940fdc9af473171))

* feat(metrics): integrate feature flags with settings and enhance timing decorators ([`07d75e9`](https://github.com/gsinghjay/mvp_qr_gen/commit/07d75e948fcc300983ebf20e8ad4c1d286fd9079))

* feat(config): add feature flag settings for Observatory-First refactoring ([`91d9d6e`](https://github.com/gsinghjay/mvp_qr_gen/commit/91d9d6e544b6648b1c97b031a356f7d05ff4347c))

### Unknown

* Merge pull request #49 from gsinghjay/feature/enhanced-metrics-instrumentation

Enhanced Metrics Instrumentation for Observatory-First Refactoring ([`0f3750a`](https://github.com/gsinghjay/mvp_qr_gen/commit/0f3750ad986ec1f402b45036398f7d27bbe37678))

* security(docs): remove API key from GRAFANA.md documentation ([`cc37c9e`](https://github.com/gsinghjay/mvp_qr_gen/commit/cc37c9e064dd2133f2f0d889b483f4620c0543b8))


## v1.4.0 (2025-05-26)

### Documentation

* docs: add QR Application Custom Metrics dashboard to Grafana documentation ([`0d43792`](https://github.com/gsinghjay/mvp_qr_gen/commit/0d4379270e166beb93632dff92875704daedf05c))

* docs: add comment about Grafana restart requirement for changes ([`e227722`](https://github.com/gsinghjay/mvp_qr_gen/commit/e227722614dc2372cbe48c56bbf64df16ad2424f))

### Features

* feat: initialize feature flags during application startup ([`647d1dc`](https://github.com/gsinghjay/mvp_qr_gen/commit/647d1dc1a0db40d5ea1924d002db81893fdf9b84))

* feat: add redirect processing metrics with success/error tracking ([`cd5dcfa`](https://github.com/gsinghjay/mvp_qr_gen/commit/cd5dcfae8e2b32e05cd7a2ea886f0877288b1b4a))

* feat: integrate MetricsLogger in QR creation and image generation ([`0c2b841`](https://github.com/gsinghjay/mvp_qr_gen/commit/0c2b84172570d6dcacdf4df74be1cacb405ba407))

* feat: add QR Application Custom Metrics Grafana dashboard ([`4a9cb0b`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a9cb0b4d49470a01129a7019cf7367e2787be30))

* feat: add MetricsLogger with 5 custom Prometheus metrics ([`eb98af0`](https://github.com/gsinghjay/mvp_qr_gen/commit/eb98af050e734793fa87da85327dabec1f29bcc3))

### Fixes

* fix: import metrics_logger module to register custom metrics ([`e517c5e`](https://github.com/gsinghjay/mvp_qr_gen/commit/e517c5ec7fd2f9050bdd2d1f9d0056948ab2aabb))

### Unknown

* Merge pull request #48 from gsinghjay/feat/metrics-logger

MetricsLogger Implementation ([`850b288`](https://github.com/gsinghjay/mvp_qr_gen/commit/850b288abea5889966394dae1f2c596dc62d4680))


## v1.3.1 (2025-05-26)

### Fixes

* fix: remove conflicting paths-ignore from update-wiki.yml workflow

- GitHub Actions only allows paths OR paths-ignore, not both ([`27ab4f9`](https://github.com/gsinghjay/mvp_qr_gen/commit/27ab4f9267737e18ae1a9709317ac4b55a232960))


## v1.3.0 (2025-05-26)

### Documentation

* docs: update GRAFANA.md to reflect actual dashboard implementations

- fix refresh rates and replace non-existent Service Monitoring with Circuit Breaker dashboard ([`8754cfb`](https://github.com/gsinghjay/mvp_qr_gen/commit/8754cfb1c529e9c550a946432ad0d3758148f72b))

### Features

* feat: improve wiki workflow with proper semantic-release coordination ([`9cb9c7c`](https://github.com/gsinghjay/mvp_qr_gen/commit/9cb9c7cf54de794eca811daa04284ad1384ba4a9))


## v1.2.2 (2025-05-26)

### Fixes

* fix: remove invalid commit parser configuration causing semantic-release to fail ([`f459001`](https://github.com/gsinghjay/mvp_qr_gen/commit/f459001537d99784910145782e2f6d1fa58a097d))

* fix: configure GitHub Action to generate changelog properly ([`ac2b9c3`](https://github.com/gsinghjay/mvp_qr_gen/commit/ac2b9c3203300748e3714f005b3e73a4d3ecddc2))


## v1.2.1 (2025-05-26)

### Fixes

* fix: resolve workflow concurrency conflicts between semantic-release and wiki update ([`aacd755`](https://github.com/gsinghjay/mvp_qr_gen/commit/aacd7556d3bbd6e18a915e893696e38d81c91b82))


## v1.2.0 (2025-05-26)

### Features

* feat(rollback): add comprehensive timing improvements and build-based service support ([`2808a0a`](https://github.com/gsinghjay/mvp_qr_gen/commit/2808a0ade0719459b012c66f13e9d5d8d0bf04dd))

* feat: implement comprehensive rollback automation script (Task S.3) ([`164fdad`](https://github.com/gsinghjay/mvp_qr_gen/commit/164fdadb1a437cc5aec4ba6bc730693d3bef0e19))

* feat: complete Task S.2 enhanced smoke test with observatory integration ([`861144a`](https://github.com/gsinghjay/mvp_qr_gen/commit/861144ab42344eedd0cee27fa3da119d9f559814))

* feat: add QR database cleanup scripts - removed 366 test QR codes (79% reduction) ([`611ea47`](https://github.com/gsinghjay/mvp_qr_gen/commit/611ea47d803a6f5acf62e1037c9dbcc519dd00ef))

### Fixes

* fix(restore): remove timeout wrappers causing script hangs during restore ([`3bdce51`](https://github.com/gsinghjay/mvp_qr_gen/commit/3bdce516c5cd569aa4ee6b09ba231377e69bac55))

* fix(backup): handle build-based services and remove Docker-in-Docker deadlocks ([`947d326`](https://github.com/gsinghjay/mvp_qr_gen/commit/947d3260f6441927a2b21155622c8a3b818b495e))

* fix(backup): resolve --with-api-stop flag logic and improve restore output ([`bf59104`](https://github.com/gsinghjay/mvp_qr_gen/commit/bf591049767d185c7feca43926f59015841dbf6e))

### Unknown

* Merge pull request #47 from gsinghjay/feat/smoke-test

Implement Enhanced Smoke Test ([`ef971bc`](https://github.com/gsinghjay/mvp_qr_gen/commit/ef971bc88af733111fe9b07bd220863d08367eb8))


## v1.1.0 (2025-05-25)

### Features

* feat: add health monitoring alerts for system status tracking ([`53e4532`](https://github.com/gsinghjay/mvp_qr_gen/commit/53e453222b002a602a65f91cdcd0377ae738997f))


## v1.0.1 (2025-05-25)

### Fixes

* fix(config): ignore extra environment variables in Pydantic settings ([`13e35ab`](https://github.com/gsinghjay/mvp_qr_gen/commit/13e35ab8a4926ce28da1dbfbe850f4edf74a5dc9))

* fix(docker): mount .env file and remove obsolete version directive ([`b23912b`](https://github.com/gsinghjay/mvp_qr_gen/commit/b23912b772a4e0fb68fabfd9c2a7812d4b082272))

* fix(docker): remove docker group assignment in container build ([`73dc6cc`](https://github.com/gsinghjay/mvp_qr_gen/commit/73dc6cc27e01b6d86de6b2804fba5bbd9c558b6f))


## v1.0.0 (2025-05-25)

### Features

* feat: complete S.0 refactor of test_api_script.sh with DRY utility functions

- Add unified _api_request() function for all API calls
- Implement consistent error handling with _assert_* utilities
- Eliminate code duplication across all test functions
- Enhance debugging with detailed error reporting
- Maintain 100% test pass rate with improved maintainability ([`6d2d6f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d2d6f40c4e0376d5779556574effbd3e1ce4e73))


## v0.32.0 (2025-05-25)

### Chores

* chore: remove unused Node.js package files ([`10fdd76`](https://github.com/gsinghjay/mvp_qr_gen/commit/10fdd76ee9b930edc403fbf04c31b9e5f734d69a))

* chore: remove obsolete test_api_restructure.sh script ([`e3e647c`](https://github.com/gsinghjay/mvp_qr_gen/commit/e3e647c08316978b00e0a98e5294fc1891352355))

### Documentation

* docs: update BACKUP-RESTORE.md for public wiki with enhanced troubleshooting ([`0a75ccb`](https://github.com/gsinghjay/mvp_qr_gen/commit/0a75ccb0f59c221b0d65c16536f1c8257f816743))

* docs(backup): add comprehensive backup and restore operational procedures ([`a8a92cd`](https://github.com/gsinghjay/mvp_qr_gen/commit/a8a92cd2e551c8f476d594569d3ae66b66c22b45))

* docs(ci): update wiki workflow for S.1 refinement documentation ([`c4add23`](https://github.com/gsinghjay/mvp_qr_gen/commit/c4add2387949fa84cf96c46d50506ce4823e20c8))

* docs: enhance wiki maintenance guide and merge dashboard content into GRAFANA.md ([`6d9c42a`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d9c42af1e8a5e4f60a01a83bf054e3d6539eeb9))

* docs: add new developer pages to wiki maintenance guide ([`2e23006`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e23006749807cf7b7143cae4f9385a92c4b42a8))

* docs: add PromQL developer guide to main documentation links ([`7092ab4`](https://github.com/gsinghjay/mvp_qr_gen/commit/7092ab4ed3163f792945a9bae9cd905383fcf781))

### Features

* feat(restore): add standardized .env loading and required variable validation ([`521363d`](https://github.com/gsinghjay/mvp_qr_gen/commit/521363dfe4dbf7578beb6d1b27aba1abd4215734))

* feat(backup): add standardized .env loading and required variable validation ([`d4b3368`](https://github.com/gsinghjay/mvp_qr_gen/commit/d4b3368e59c945f2fbfe2146bddd62c32050bec5))

* feat(db): enhance database manager with fail-fast validation and application-level health checks ([`0518d75`](https://github.com/gsinghjay/mvp_qr_gen/commit/0518d75aaf569549fc11e79b5029c5fcd106b8f1))

* feat(init): add fail-fast environment variable validation and .env loading ([`e133f07`](https://github.com/gsinghjay/mvp_qr_gen/commit/e133f0761753306b00ca9cbd0bf2fbbc68aa844d))

* feat(test): implement comprehensive multi-stage backup/restore verification with env vars ([`0318853`](https://github.com/gsinghjay/mvp_qr_gen/commit/0318853d88d2d349659d368e26dd9c3a73c09048))

* feat(backup): centralize API service control with Docker integration and safety enhancements ([`172cbde`](https://github.com/gsinghjay/mvp_qr_gen/commit/172cbdeab4d8bc8591d6b29e594e462ceedfa3c6))

* feat(docker): mount Docker socket for API service container control during backups ([`3317109`](https://github.com/gsinghjay/mvp_qr_gen/commit/3317109f71599ac6415b1d89a41d907caa6c0eb0))

* feat(docker): add Docker CLI and container control capabilities for backup operations ([`40fb1a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/40fb1a739454eb47868fa29079bf153a607146c5))

* feat(test): add comprehensive multi-stage restore verification

- Implement create/delete QR code state management
- Add dual backup and restore verification workflow
- Include comprehensive cleanup and validation throughout ([`9a0cefb`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a0cefb258edd4ad120b5ced29b29ef7c7275f39))

* feat(backup): add automatic alembic stamping and enhanced console output

- Add automatic alembic version stamping after database restore
- Enhance validation with step-by-step console feedback
- Add API service control methods with --with-api-stop flag
- Improve error handling with detailed progress indicators ([`a953dfd`](https://github.com/gsinghjay/mvp_qr_gen/commit/a953dfd19a19f3cbcdd23609b65035c0df904440))

* feat(docker): mount scripts directory for immediate availability without rebuilds ([`ac5b9c5`](https://github.com/gsinghjay/mvp_qr_gen/commit/ac5b9c53fb7d21d1e97b17dd47c0c96380b29f9a))

* feat(restore): add production-safe restore script with service management ([`127af22`](https://github.com/gsinghjay/mvp_qr_gen/commit/127af222afd79709ddb0f93b8ed32d93899516b3))

* feat(database): enhance manage_db.py with progress indicators and error handling ([`46a5b94`](https://github.com/gsinghjay/mvp_qr_gen/commit/46a5b94f474f75ef5bb6d2df245114766a0599ab))

* feat(backup): add production-safe backup script with service lifecycle management ([`6079e87`](https://github.com/gsinghjay/mvp_qr_gen/commit/6079e877672e0757e920a3efc5e6766702dafb01))

### Fixes

* fix: resolve backup freezing and implement hybrid API/DB testing with Traefik auth ([`9fb3b26`](https://github.com/gsinghjay/mvp_qr_gen/commit/9fb3b26857ce3fc4322c2f6bed3d35bdc0ed6fdb))

* fix: implement hybrid API/DB testing with proper Traefik authentication ([`f3abc26`](https://github.com/gsinghjay/mvp_qr_gen/commit/f3abc2624ea8ca62ab5582bbd410869b08dd7f08))

* fix(docker): correct PostgreSQL health check database specification

- Add -d parameter to pg_isready commands for both postgres services
- Prevents 'database pguser does not exist' errors in health checks
- Ensures health checks connect to correct database names ([`ac0f4d0`](https://github.com/gsinghjay/mvp_qr_gen/commit/ac0f4d08d94ef49d034edd5c79d101f898f4d31a))

* fix(init): update script permissions handling for mounted volumes ([`9ba6eb4`](https://github.com/gsinghjay/mvp_qr_gen/commit/9ba6eb41bc8b35ef85b25977395baad011d60bc7))

### Refactoring

* refactor(restore): simplify to thin wrapper with enhanced verification and safety warnings ([`d7b08be`](https://github.com/gsinghjay/mvp_qr_gen/commit/d7b08bea3f583d435ebed04596e8ef746b636766))

* refactor(backup): simplify to thin wrapper around enhanced manage_db.py with improved UX ([`1f0110d`](https://github.com/gsinghjay/mvp_qr_gen/commit/1f0110d2dd1a84963874354e02bab7360265fbc7))

* refactor(restore): convert to thin wrapper calling manage_db.py

- Delegate core restore operations to manage_db.py
- Maintain host-level API service lifecycle management
- Preserve safety checks and verification reporting ([`277ba02`](https://github.com/gsinghjay/mvp_qr_gen/commit/277ba020310933c5e367f06fb7999b05c2fe955a))

* refactor(backup): convert to thin wrapper calling manage_db.py

- Delegate core backup operations to manage_db.py
- Maintain host-level API service lifecycle management
- Simplify script logic while preserving production safety ([`a56689b`](https://github.com/gsinghjay/mvp_qr_gen/commit/a56689b50ae3f483c7489c8c50da69504595ec31))

* refactor(docker): optimize script handling for mounted volumes ([`8fc64cf`](https://github.com/gsinghjay/mvp_qr_gen/commit/8fc64cf62e9865bb30b17c96713723fdec91d070))

### Testing

* test(s1): add comprehensive test suite for S1 fast-failing enhancements ([`6f00c59`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f00c59358ca2456c88c88ac382d59825d85807b))

* test(backup): add simple backup test for debugging connection issues ([`84dc616`](https://github.com/gsinghjay/mvp_qr_gen/commit/84dc6168bed3f825f438e649c348ebbdb7c06e3d))

* test(backup): add comprehensive backup and restore testing script ([`ae445c5`](https://github.com/gsinghjay/mvp_qr_gen/commit/ae445c54e2ea999ed5c8ae0c9b1c53dcecfd5b86))

### Unknown

* Merge pull request #46 from gsinghjay/refactor/safety-phase

🛡️ Task S.1: Comprehensive Backup and Restore Procedures ([`f26b566`](https://github.com/gsinghjay/mvp_qr_gen/commit/f26b566d28eff4ea56a88350b1444d5c51843ef3))

* remove(test): delete obsolete simple backup test replaced by enhanced test_restore.sh ([`a426166`](https://github.com/gsinghjay/mvp_qr_gen/commit/a426166b695ad86848e28d4a83b62aa55beaf0dc))


## v0.31.2 (2025-05-24)

### Documentation

* docs: remove memory-bank from public repository ([`1feb276`](https://github.com/gsinghjay/mvp_qr_gen/commit/1feb2764c92082d9fdf53cd57498146bc07a2b4e))

* docs: test auto-sync workflow trigger ([`b6da892`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6da892683910b3ac46c9633ced96f71ff2b318d))

### Fixes

* fix: remove docs/ references from wiki automation ([`00448ea`](https://github.com/gsinghjay/mvp_qr_gen/commit/00448ea6d9ef0ab1865c6016a172a614f4621a94))


## v0.31.1 (2025-05-24)

### Documentation

* docs: update memory bank with GitHub wiki integration and CORS fixes ([`781071e`](https://github.com/gsinghjay/mvp_qr_gen/commit/781071e54d8a489b3036e00d12eb4ac9787a8eeb))

### Fixes

* fix: update wiki workflow to use personal access token for wiki permissions ([`d47e7dc`](https://github.com/gsinghjay/mvp_qr_gen/commit/d47e7dc7d113b07ad2a84fb280b957ed13b02e42))


## v0.31.0 (2025-05-24)

### Chores

* chore: update gitignore to keep docs folder ignored while supporting wiki system ([`43ff926`](https://github.com/gsinghjay/mvp_qr_gen/commit/43ff9262f6d937eafb254ae535e3a12f8abdb83a))

### Continuous Integration

* ci: add automated wiki documentation sync workflow ([`87dd2fa`](https://github.com/gsinghjay/mvp_qr_gen/commit/87dd2fad51845c0f5c8f1b9447e2ae379a60ca58))

### Documentation

* docs: update README to reference GitHub wiki instead of ignored docs directory ([`241d587`](https://github.com/gsinghjay/mvp_qr_gen/commit/241d587a497984f3bb3843146d63e46e3e4fc9d3))

* docs: add comprehensive GitHub wiki maintenance guide ([`1a9722c`](https://github.com/gsinghjay/mvp_qr_gen/commit/1a9722cbf067c731e68772d218387c51409b19c5))

### Features

* feat: add wiki maintenance script for documentation sync ([`651d754`](https://github.com/gsinghjay/mvp_qr_gen/commit/651d754eb4aba0de6b23d0d9168c68be0fc49e62))

### Fixes

* fix: enhance CORS headers for Grafana RSS feeds and external resources ([`7e30a33`](https://github.com/gsinghjay/mvp_qr_gen/commit/7e30a33ab024dfeb11a28b99a7c52635bb6ae3fb))

### Unknown

* Merge pull request #45 from gsinghjay/feat/github-wiki-integration

Implement GitHub Wiki Integration With Automated Documentation Sync ([`53feb58`](https://github.com/gsinghjay/mvp_qr_gen/commit/53feb58f3bcf4c5ffcff8f6afa5547f33267bfeb))

* config: disable Grafana news feed and configure CORS settings ([`b9f9ce7`](https://github.com/gsinghjay/mvp_qr_gen/commit/b9f9ce7cd2c9b9bed8d51d354458575f7c79ccc4))


## v0.30.0 (2025-05-24)

### Chores

* chore: add cursor indexing ignore configuration ([`86b92b7`](https://github.com/gsinghjay/mvp_qr_gen/commit/86b92b7cd07d9c038ae511ad47940c624942fe93))

* chore: add monitoring service directories to gitignore ([`0b39eb7`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b39eb71772b2ac3c40b1cb58a2a4bc8ce0ba024))

### Documentation

* docs(memory-bank): update Observatory-First monitoring progress and CORS implementation ([`453c9e7`](https://github.com/gsinghjay/mvp_qr_gen/commit/453c9e71dafd783ac62688b9b38f8c86fd9d6b3a))

* docs: add comprehensive Grafana monitoring guide for college staff ([`99ebdf9`](https://github.com/gsinghjay/mvp_qr_gen/commit/99ebdf9231b51198f664a06c0b23a2e6f8fc6a84))

* docs: add Observatory-First monitoring features to README ([`d512caa`](https://github.com/gsinghjay/mvp_qr_gen/commit/d512caa4dcb0b0fdfd7b745941209520e1a9e705))

* docs: add memory bank documentation for project context ([`8226ae8`](https://github.com/gsinghjay/mvp_qr_gen/commit/8226ae866f3e19a6bf959cb68920a95047b17e63))

### Features

* feat(grafana): configure CORS support for cross-origin requests ([`c493413`](https://github.com/gsinghjay/mvp_qr_gen/commit/c493413c723983ba0a41474d03013354bfc2047a))

* feat(traefik): add CORS support for Grafana with dedicated middleware ([`40f87a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/40f87a7472186d479eda8dafb79cd885179d380e))

* feat(infrastructure): add Prometheus, Grafana, Loki monitoring stack to Docker Compose ([`8c290b2`](https://github.com/gsinghjay/mvp_qr_gen/commit/8c290b240f5059f6d699365e870333ce8c46e00e))

* feat(scripts): add alert testing and monitoring utility scripts ([`d27d8a4`](https://github.com/gsinghjay/mvp_qr_gen/commit/d27d8a415ccd8a79f7ec53448dea3333cee74a53))

* feat(monitoring): add Grafana alerting configuration for comprehensive monitoring ([`5ab0dbf`](https://github.com/gsinghjay/mvp_qr_gen/commit/5ab0dbf813ac56479dce86a1f77e5d999f875087))

* feat(monitoring): add Observatory-First alert system with 8 critical rules ([`89f98d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/89f98d285d9ea974596648599edb684d38934e30))

* feat: add alerting and SLA overview dashboard for compliance monitoring ([`164d71f`](https://github.com/gsinghjay/mvp_qr_gen/commit/164d71f9477f1f1be4834f81931765b6ae4ac1fd))

* feat: add user experience monitoring dashboard for UX tracking ([`25ed35f`](https://github.com/gsinghjay/mvp_qr_gen/commit/25ed35fbe9299cebd019ccacb2acaba2de2195cc))

* feat: add infrastructure deep dive dashboard for resource monitoring ([`dd57c1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd57c1e7b45d97f30ade685133b920d50aad90f6))

* feat: add circuit breaker and feature flag monitoring dashboard ([`05ca07a`](https://github.com/gsinghjay/mvp_qr_gen/commit/05ca07a955ee167d70c58f0423ae0bb1f9ad19ac))

* feat: add detailed refactoring analysis dashboard for technical monitoring ([`4855fb3`](https://github.com/gsinghjay/mvp_qr_gen/commit/4855fb3832f73d5066596c06cc52a59f0604009b))

* feat: add Promtail configuration for log shipping ([`3236b2e`](https://github.com/gsinghjay/mvp_qr_gen/commit/3236b2e9e5bfda8f20a733377b8a7d9f6a356d49))

* feat: add Loki configuration for log aggregation ([`dd286fa`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd286faf840f2a6553049eb2b6da59d06b565441))

* feat: add Grafana dashboards and datasource configurations ([`7be3f5b`](https://github.com/gsinghjay/mvp_qr_gen/commit/7be3f5b66d8c613102aa40083a7067e6905ed952))

* feat: add Prometheus configuration for metrics collection ([`7ddf6eb`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ddf6ebe6c75f1571728429caaed1b9b84ef5a5c))

* feat: add Grafana routing configuration to Traefik ([`6d21185`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d21185d699088474654a029f9db57e13778f2f9))

* feat: add Grafana, Loki, and Promtail services for monitoring ([`0ddcbed`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ddcbed492c1c22c0a51ff4aef76d72c7209b19a))

### Fixes

* fix: update analytics dashboard queries to prevent NaN values ([`308679b`](https://github.com/gsinghjay/mvp_qr_gen/commit/308679bae6562ff0590055090e56fda7e127738d))

* fix: update refactoring progress dashboard with extended time windows ([`721b3be`](https://github.com/gsinghjay/mvp_qr_gen/commit/721b3bedb02cde8ed1a61dd99a9c8491b35a5263))

* fix: update QR system health dashboard queries with proper fallbacks ([`d54fa08`](https://github.com/gsinghjay/mvp_qr_gen/commit/d54fa080263bcfe83a62d19dbf72b174179bbdec))

### Unknown

* Merge pull request #44 from gsinghjay/feat/monitoring

Implement comprehensive monitoring stack with Grafana, Loki, and Prometheus ([`3a28f8a`](https://github.com/gsinghjay/mvp_qr_gen/commit/3a28f8a5c9c2ff2d65824285cbec2a5f44932b43))


## v0.29.0 (2025-05-23)

### Documentation

* docs: update test API readme with production hardening and classroom-optimized rate limiting ([`38a73f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/38a73f70a1e1cd0bcd75c6ee2e5057eb6c0aadf1))

### Features

* feat(security): implement classroom-friendly rate limiting for QR redirects ([`4508517`](https://github.com/gsinghjay/mvp_qr_gen/commit/45085173a55f9f5f7cbbd243fccec39c591b63a1))

* feat(security): adjust rate limiting to 60/min average with 10 burst for better abuse prevention ([`9ae5592`](https://github.com/gsinghjay/mvp_qr_gen/commit/9ae55929c2f4967890adafd128e85d9961c57a3e))

* feat(security): add comprehensive input validation and error handling to redirect endpoint ([`2f21cad`](https://github.com/gsinghjay/mvp_qr_gen/commit/2f21cad962fcfae64cdd1d99ec8c33ea6de3087a))

* feat(security): implement URL safety validation and background task error handling ([`fa025a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/fa025a75cd27c276578d0b669bc7e118003998b2))

* feat(docker): add ALLOWED_REDIRECT_DOMAINS environment variable to api service ([`d960b09`](https://github.com/gsinghjay/mvp_qr_gen/commit/d960b09eeb50fbbf13ca1f7a63cf76f2f2719d2b))

* feat(config): add ALLOWED_REDIRECT_DOMAINS setting with environment variable parsing ([`63cfc05`](https://github.com/gsinghjay/mvp_qr_gen/commit/63cfc05659c8361ee0b36c740889f9a6d479f3be))

### Testing

* test: enhance rate limiting tests for differentiated QR vs API access patterns ([`8d36f1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/8d36f1e62d531bc55524d82d78299ecf3b096b71))

* test: add comprehensive security tests and fix domain validation in update test ([`cc78161`](https://github.com/gsinghjay/mvp_qr_gen/commit/cc781616c9577dde005e97f668ca192f0948ef2a))

### Unknown

* Merge pull request #43 from gsinghjay/fix/redirect-hardening

🔒 Production Hardening - Security & Reliability Enhancements ([`ed42d06`](https://github.com/gsinghjay/mvp_qr_gen/commit/ed42d0660f75e1125f5e521e5a9c7bff543fa352))


## v0.28.0 (2025-05-23)

### Documentation

* docs: update testing best practices in README.md ([`7211d95`](https://github.com/gsinghjay/mvp_qr_gen/commit/7211d95af5b94243951498d2f56adf832391cc54))

* docs: remove STORY.md in favor of README diagrams ([`69236c5`](https://github.com/gsinghjay/mvp_qr_gen/commit/69236c550c1f2fe608f8a9bf92598f7b55ead9e5))

* docs: remove INFRASTRUCTURE.md in favor of README diagrams ([`755f4e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/755f4e37c0eb2282b9f372b9edfae160dc2e0828))

* docs: enhance README with architecture and flow diagrams ([`c09999a`](https://github.com/gsinghjay/mvp_qr_gen/commit/c09999a88e8acc77820b954c604af5144f8a091f))

### Features

* feat: implement comprehensive QR code endpoint tests ([`360fbc0`](https://github.com/gsinghjay/mvp_qr_gen/commit/360fbc0adf9fbb6c8463a732325a0ca241027286))

* feat: add dedicated tests for HTMX fragment endpoints ([`cfef808`](https://github.com/gsinghjay/mvp_qr_gen/commit/cfef808fe1ed3ed9a984a88bd48556eb178df63e))

### Fixes

* fix: update QR service tests for repository pattern ([`eed680a`](https://github.com/gsinghjay/mvp_qr_gen/commit/eed680a9ef0e89b3b821951ec68507904963895e))

* fix: correct test_db fixture naming in conftest.py ([`1e784f8`](https://github.com/gsinghjay/mvp_qr_gen/commit/1e784f853ab1fb70a991918b5fe2b2208db985c1))

### Refactoring

* refactor: replace Font Awesome icons with Bootstrap Icons in device stats fragment ([`6f66af7`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f66af70c8103ea4cf8115eef475cac57fda6e4c))

* refactor: remove test factories examples after factory implementation ([`c0c79d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/c0c79d2474e4e9bc55c982863fcb5ee12ef0ce69))

* refactor: remove async example tests for proper async implementation ([`9f338d6`](https://github.com/gsinghjay/mvp_qr_gen/commit/9f338d6c10a5a6abe6b6e78f7b39a639bb0c12e8))

* refactor: remove placeholder repository integration tests ([`51ebdba`](https://github.com/gsinghjay/mvp_qr_gen/commit/51ebdbad59e480d2d710d09b43f9993fc73aa9d2))

* refactor: remove generic validation tests for endpoint-specific tests ([`dc61591`](https://github.com/gsinghjay/mvp_qr_gen/commit/dc61591cba178ec801f600d30f9e5688712eec29))

* refactor: remove router structure tests for endpoint-specific tests ([`d378a78`](https://github.com/gsinghjay/mvp_qr_gen/commit/d378a78c17ee8c632ec5c88390b6f0b00de04f8b))

* refactor: remove generic response model tests for endpoint-specific tests ([`ab17955`](https://github.com/gsinghjay/mvp_qr_gen/commit/ab1795527ded2bc20b4f7f427ae64a2f394fec0d))

* refactor: remove generic HTTP method tests for endpoint-specific tests ([`fddb5be`](https://github.com/gsinghjay/mvp_qr_gen/commit/fddb5bed707f5ec3517f16ff6b67dc62d004a784))

* refactor: remove general API tests for module-specific tests ([`3d94fcc`](https://github.com/gsinghjay/mvp_qr_gen/commit/3d94fcc34610fc4a2de2e7479660862fbfe4a4e7))

* refactor: remove generic exception tests for endpoint-specific tests ([`18fee7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/18fee7d3c8b726dd092f29129e7d28afa8b5f7fa))

* refactor: remove generic background tasks tests for endpoint-specific tests ([`5d99dea`](https://github.com/gsinghjay/mvp_qr_gen/commit/5d99dea6b40257061bcb39f352e7c2c04a48dae4))

* refactor: remove redundant API restructure tests ([`2dda5e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/2dda5e489547b79a34ceafa5efb0717a8db73313))

* refactor: update API test module imports ([`1259e3f`](https://github.com/gsinghjay/mvp_qr_gen/commit/1259e3f2c47403845fa624fcdbebdb9c056ea741))

* refactor: align dependency injection with test_db fixture ([`a551f88`](https://github.com/gsinghjay/mvp_qr_gen/commit/a551f8855ca6e705d41af6ed7c87d28febbbb4d3))

### Testing

* test: remove old QR service test file (replaced by test_qr.py) ([`bd38bc1`](https://github.com/gsinghjay/mvp_qr_gen/commit/bd38bc1b2370b7cf52c3405bcb57e49a002a2a2a))

* test: add unit tests for health API endpoint with mocking ([`6a44b35`](https://github.com/gsinghjay/mvp_qr_gen/commit/6a44b35e58fac51be0fe51d9e9f6983a6b7da7b2))

* test: add comprehensive unit tests for QR service with mock and real DB approaches ([`94d2dfc`](https://github.com/gsinghjay/mvp_qr_gen/commit/94d2dfc503630e3c698bc15e32fdf88ae68a2b08))

* test: add unit tests for health service with mocking ([`779c880`](https://github.com/gsinghjay/mvp_qr_gen/commit/779c8804a4cd8d963c8379c17f2158a22b437165))

* test: add integration tests for health check API endpoints ([`e610727`](https://github.com/gsinghjay/mvp_qr_gen/commit/e61072766384455714393b4d168056b266c4cbaa))

### Unknown

* Merge pull request #42 from gsinghjay/refactor/tests

Test Suite Refactoring: Module-Specific Test Organization ([`96d0589`](https://github.com/gsinghjay/mvp_qr_gen/commit/96d05894adf2f0af0563bd363fb6a6810b0ac4a5))


## v0.27.0 (2025-05-21)

### Chores

* chore: update .gitignore file ([`35bb6e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/35bb6e4d51793c3ea996dd73e68074678cc97eab))

### Features

* feat: implement service layer coordination between repositories ([`168d2f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/168d2f426169eca08e94f9f631e95183fca5c4e2))

* feat: implement ScanLogRepository for specialized scan log operations ([`0adb494`](https://github.com/gsinghjay/mvp_qr_gen/commit/0adb494fa092a73b233890181f49f0edbdcc52ba))

* feat: update repository exports to include ScanLogRepository ([`36e7fa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/36e7fa002e2b08fe7572d381979ee589d71eb70a))

* feat: implement QRCodeRepository in dedicated file per phase-1 plan ([`88a3458`](https://github.com/gsinghjay/mvp_qr_gen/commit/88a34584e93ba64dc0f089fdbc6c9fcb105f0aa5))

### Fixes

* fix: add missing model_class parameter to ScanLogRepository.__init__ ([`4249da3`](https://github.com/gsinghjay/mvp_qr_gen/commit/4249da376221d9e05be3a441370140ce2724d812))

* fix: update integration test package initialization ([`04467b5`](https://github.com/gsinghjay/mvp_qr_gen/commit/04467b57f22e51462f6a703e6afdb6b835b9c2cc))

### Refactoring

* refactor: consolidate security headers to Traefik ([`a043411`](https://github.com/gsinghjay/mvp_qr_gen/commit/a0434112620e7f59fd037b439bc3644fff10de41))

* refactor(api): update fragments endpoints to use specialized repositories ([`38ca2ee`](https://github.com/gsinghjay/mvp_qr_gen/commit/38ca2eef62a6567ab1bfbd2e58e9f7e19cef93ae))

* refactor(types): update type definitions to use specialized repositories ([`de22c7e`](https://github.com/gsinghjay/mvp_qr_gen/commit/de22c7ed8a53df296a613b3338f3c1ed094cf072))

* refactor(service): update QRCodeService to use specialized repositories ([`3c0573d`](https://github.com/gsinghjay/mvp_qr_gen/commit/3c0573df842442f4e40bb1e0cfb9ec06ed82ce9d))

* refactor(repos): remove deprecated qr_repository.py ([`b6bcf62`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6bcf6259850a99e34202ffb7e13126cf9d80a8d))

* refactor(repos): update __init__.py to export only specialized repositories ([`97fe612`](https://github.com/gsinghjay/mvp_qr_gen/commit/97fe612def15d160b9e5d9d72d6b9e258c651aa0))

* refactor(main): update imports to use specialized repositories ([`64ffef0`](https://github.com/gsinghjay/mvp_qr_gen/commit/64ffef07833f3fe491a7db6ac0a54ed7dc5f9170))

* refactor(deps): update dependencies to use specialized repositories ([`7ba3d01`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ba3d01a59069129f07a612dc342e8ea6ff525f0))

* refactor: update repository exports for clearer naming ([`a2b62af`](https://github.com/gsinghjay/mvp_qr_gen/commit/a2b62afd4566e5708727a817a427d29f59a4b490))

* refactor: update type aliases for new repository naming ([`d9b0b83`](https://github.com/gsinghjay/mvp_qr_gen/commit/d9b0b832dfac4d14be2ac8e354a6b6f12ae4f8bc))

* refactor: update dependencies to use new repository structure ([`96a1626`](https://github.com/gsinghjay/mvp_qr_gen/commit/96a1626c210c96e694e91f5143c92751e7726c1e))

* refactor: modify existing QRRepository for backward compatibility ([`56d2186`](https://github.com/gsinghjay/mvp_qr_gen/commit/56d218688ae98afdb93679772b2d0245c6f8e531))

* refactor: update repository exports to include new QRCodeRepository ([`9480e28`](https://github.com/gsinghjay/mvp_qr_gen/commit/9480e2884b7f3c157f451ec1d2b2af858205a222))

### Testing

* test: add integration test directory structure for repositories ([`be295de`](https://github.com/gsinghjay/mvp_qr_gen/commit/be295deb762203148a48d0419eb716c206f3b658))

* test: add unit tests for new QRCodeRepository implementation ([`a8c0835`](https://github.com/gsinghjay/mvp_qr_gen/commit/a8c0835946a20720c6c0836e89ffff57757a2f48))

### Unknown

* Merge pull request #41 from gsinghjay/refactor/repositories

Repository Refactoring ([`2090db2`](https://github.com/gsinghjay/mvp_qr_gen/commit/2090db231baba1359839652c080b4e4a8aba3edc))


## v0.26.2 (2025-05-21)

### Fixes

* fix: address 401 errors in test script by adding Host headers ([`8f7675b`](https://github.com/gsinghjay/mvp_qr_gen/commit/8f7675bf739f91cd0504491abff23f3cbba0987f))


## v0.26.1 (2025-05-21)

### Documentation

* docs: update README with performance testing findings and refactoring decision ([`3eefe1f`](https://github.com/gsinghjay/mvp_qr_gen/commit/3eefe1f08a6ca7c51e6e39d2e5dc77b1635b93a0))

* docs: update performance test results with comprehensive metrics ([`db13585`](https://github.com/gsinghjay/mvp_qr_gen/commit/db1358553e91a72ab57d605926fa6686fb8039dd))

### Fixes

* fix: improve error handling and reliability in performance test script ([`cd1e977`](https://github.com/gsinghjay/mvp_qr_gen/commit/cd1e97761be5b669c79c290dced72404c38acace))

### Unknown

* Merge pull request #40 from gsinghjay/refactor/performance-script

Performance testing and synchronous code refactoring decision ([`728bed7`](https://github.com/gsinghjay/mvp_qr_gen/commit/728bed7b4c14afb7a43239f0675e5fb247c11874))


## v0.26.0 (2025-05-21)

### Features

* feat: connect chart.js to real time series data from API endpoint ([`7c586de`](https://github.com/gsinghjay/mvp_qr_gen/commit/7c586de4ea6efd94d43ce4624c14973049c981f5))

* feat: add scan-timeseries endpoint for QR analytics chart data ([`a671b33`](https://github.com/gsinghjay/mvp_qr_gen/commit/a671b330db8ee8cb0453f981111f6ef4a029e4b9))

* feat: implement get_scan_timeseries repository method for chart data ([`9d2abea`](https://github.com/gsinghjay/mvp_qr_gen/commit/9d2abea671b2a7f27dafd3f41be6085a2e866134))

* feat: create dedicated edit form fragment for in-page editing ([`aedc92b`](https://github.com/gsinghjay/mvp_qr_gen/commit/aedc92bed7fc974e329776e3e64ec52737fd2e6b))

* feat: integrate edit button and form container in analytics page ([`7c96602`](https://github.com/gsinghjay/mvp_qr_gen/commit/7c96602dbd652879914ca05de11ec745acc43f85))

* feat: add in-page edit form endpoints for QR analytics page ([`e8d6ae4`](https://github.com/gsinghjay/mvp_qr_gen/commit/e8d6ae4e4ae992bb1d155816b25ae6620ba11835))

* feat: implement Alpine.js components for chart controls and fix container height ([`266a824`](https://github.com/gsinghjay/mvp_qr_gen/commit/266a82457a63168ecacd927753003824402480ef))

* feat: add Alpine.js v3 via CDN to enable reactive UI components ([`0b6770f`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b6770fac164a04f7859a16d960951f63d0eacaf))

* feat: replace modal view button with direct link to analytics page ([`3dbd45e`](https://github.com/gsinghjay/mvp_qr_gen/commit/3dbd45ef2360812671e82750c697432c9671bca4))

* feat: integrate download options fragment into analytics page ([`c6a127d`](https://github.com/gsinghjay/mvp_qr_gen/commit/c6a127d72133d91160fd3b7684b51b4a219ee637))

* feat: implement endpoint to serve QR download options fragment ([`63374ad`](https://github.com/gsinghjay/mvp_qr_gen/commit/63374adcc7b23588fa8e3852a4669e4d36042824))

* feat: create QR download options fragment template with customization notice ([`56a7234`](https://github.com/gsinghjay/mvp_qr_gen/commit/56a72347b7a1f97b67905b83c96de23457dd4ec8))

* feat(analytics): update toast message and implement redirect to analytics page ([`2131701`](https://github.com/gsinghjay/mvp_qr_gen/commit/2131701849c85cede117dd07a0887c34b155caef))

* feat(analytics): add QR ID in response headers to support post-creation redirect ([`021a84e`](https://github.com/gsinghjay/mvp_qr_gen/commit/021a84ea571c5b3c0d9f5368e4abbe44f56a5c1c))

* feat(ui): add Analytics button to QR list items for direct access to analytics page ([`18c9f3d`](https://github.com/gsinghjay/mvp_qr_gen/commit/18c9f3d9f6a7c46147482e468222f897fc27ef9f))

* feat(navigation): add redirect from /qr to /qr-list for consistent URL structure ([`7676a0d`](https://github.com/gsinghjay/mvp_qr_gen/commit/7676a0d4d0b17eb869be50b2f53a85322198323c))

* feat(analytics): create device/browser/OS stats fragment template with visualization components ([`717294f`](https://github.com/gsinghjay/mvp_qr_gen/commit/717294f327d4e8ab164846ba32926046e5eadeb4))

* feat(analytics): implement device/browser/OS stats endpoint for QR analytics ([`61c280f`](https://github.com/gsinghjay/mvp_qr_gen/commit/61c280fffe68cbcb56a96fe65d908eb75c45d8fb))

* feat(ui): update analytics page to load scan logs with proper HTMX integration ([`f796829`](https://github.com/gsinghjay/mvp_qr_gen/commit/f796829c21c24b734c072f9376570cda31f3a7df))

* feat(api): implement scan log fragment endpoint with filtering capabilities ([`08464bd`](https://github.com/gsinghjay/mvp_qr_gen/commit/08464bdac37529071751cb793642bec7345b9866))

* feat(analytics): add scan log table fragment template with filtering and pagination ([`c7c0d2d`](https://github.com/gsinghjay/mvp_qr_gen/commit/c7c0d2d42279769391c97a4ec0b2b86ad68043f8))

* feat(analytics): create QR analytics page template with chart placeholders ([`679a954`](https://github.com/gsinghjay/mvp_qr_gen/commit/679a954d12f9ed11b39281d0372c07406c906cba))

* feat(analytics): add QR analytics page endpoint ([`5021493`](https://github.com/gsinghjay/mvp_qr_gen/commit/5021493b69934f01cfc1fa6e75924efe148006a7))

### Fixes

* fix: update Content Security Policy to allow unsafe-eval for Alpine.js compatibility ([`aa84d4c`](https://github.com/gsinghjay/mvp_qr_gen/commit/aa84d4c060b7629d4dcfc3be7a4b51d8225b9b15))

* fix(analytics): update device stats container to remove unnecessary borders ([`ab3aa55`](https://github.com/gsinghjay/mvp_qr_gen/commit/ab3aa5523b0ec32933c4e9b0835f5d481cec4b9e))

### Refactoring

* refactor: remove QR detail modal HTML and related JavaScript ([`41442ab`](https://github.com/gsinghjay/mvp_qr_gen/commit/41442ab3c0f210f7c4a92353118a3886b19921fa))

* refactor: update fragment endpoints to redirect to analytics page ([`38fe942`](https://github.com/gsinghjay/mvp_qr_gen/commit/38fe9429936e3c921021262d190ed8019c2a877d))

* refactor(ui): rename Home to Dashboard in sidebar and consolidate navigation ([`574b617`](https://github.com/gsinghjay/mvp_qr_gen/commit/574b61785ad255ea0710212449bb13445180ceee))

* refactor(api): change QR analytics endpoint to follow RESTful convention ([`94fde88`](https://github.com/gsinghjay/mvp_qr_gen/commit/94fde8893072514c5222de574f49ed0a91666e82))

### Unknown

* Merge pull request #39 from gsinghjay/feature/detailed-analytics

Add QR Code Analytics Page ([`c8ade4d`](https://github.com/gsinghjay/mvp_qr_gen/commit/c8ade4d08c1d042af4f1ca3198a729c398b7a304))


## v0.25.0 (2025-05-21)

### Features

* feat(tests): add helper functions for validating scan log data ([`b7d459f`](https://github.com/gsinghjay/mvp_qr_gen/commit/b7d459fb3234589a394d48dc122562579da9eea4))

* feat(tests): add scan_log_factory fixtures and qr_with_scans fixtures ([`29c40d8`](https://github.com/gsinghjay/mvp_qr_gen/commit/29c40d809d62345133360c8a07111b61710ce3d8))

* feat(tests): add ScanLogFactory for test data generation ([`8b319e6`](https://github.com/gsinghjay/mvp_qr_gen/commit/8b319e68acd1673868a1d1b054301334749eaf28))

### Testing

* test(factories): add tests demonstrating factory pattern usage ([`3ed1830`](https://github.com/gsinghjay/mvp_qr_gen/commit/3ed18302edfd3add2c43e8ca7372b9498933465d))

### Unknown

* Merge pull request #38 from gsinghjay/refactor/test-1.4

Centralize Test Data Creation with Factory Pattern ([`6917199`](https://github.com/gsinghjay/mvp_qr_gen/commit/6917199672ad9d27b0e8adc35f41f7c4c0fe6ec6))


## v0.24.0 (2025-05-20)

### Documentation

* docs(tests): add dependencies.py to test directory structure ([`886e7f1`](https://github.com/gsinghjay/mvp_qr_gen/commit/886e7f188ac9c02e6662a5d782875d56cd064e4c))

* docs(tests): document standardized dependency override approach ([`4fa6ee2`](https://github.com/gsinghjay/mvp_qr_gen/commit/4fa6ee270a0283e62373a2b1396404b750867c40))

### Features

* feat(tests): create centralized test dependency injection functions ([`bab3a1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/bab3a1e3c92d6bfa1a83843d031d06f6ba72c756))

### Fixes

* fix(security): add font-src directive to CSP to allow Bootstrap icons ([`e905446`](https://github.com/gsinghjay/mvp_qr_gen/commit/e9054463043f3cd877b0b22f0c8f50ddd09847e6))

* fix(tests): update import paths in test_general_api.py ([`b848e1b`](https://github.com/gsinghjay/mvp_qr_gen/commit/b848e1b2fb7eb191861665d7cb215e95cd382048))

### Refactoring

* refactor(tests): standardize client fixture dependency overrides in conftest.py ([`dc4ac28`](https://github.com/gsinghjay/mvp_qr_gen/commit/dc4ac289cd40939ccac69d085b8fc2461c2e7f09))

### Unknown

* Merge pull request #37 from gsinghjay/refactor/test-1.3

Standardize test dependency injection and fix CSP for Bootstrap fonts ([`95d9041`](https://github.com/gsinghjay/mvp_qr_gen/commit/95d904103c26a674358c7a084b770e9192a74758))


## v0.23.0 (2025-05-20)

### Chores

* chore(config): improve Traefik static configuration with proper log paths and entrypoints ([`0843eaf`](https://github.com/gsinghjay/mvp_qr_gen/commit/0843eaf9ebfbc69345fa33fbf92a542155528efd))

### Features

* feat(routing): reorganize Traefik routers with proper priorities and domain isolation ([`508ea67`](https://github.com/gsinghjay/mvp_qr_gen/commit/508ea673cc9e88ddc208c0da1f9d2bb90dff0af6))

### Refactoring

* refactor(docker): streamline api service configuration and containerization ([`fd3fd88`](https://github.com/gsinghjay/mvp_qr_gen/commit/fd3fd88058ac1b9d3cbfd66445e2c99cf539be42))

### Unknown

* Merge pull request #36 from gsinghjay/feature/new-domain

Reorganize Traefik routing for improved security and Keycloak preparation ([`e2382b7`](https://github.com/gsinghjay/mvp_qr_gen/commit/e2382b700710868d95fa604533273b96794e803b))


## v0.22.1 (2025-05-19)

### Documentation

* docs: add directory structure documentation for test organization ([`4bd1333`](https://github.com/gsinghjay/mvp_qr_gen/commit/4bd13337503661aede9410096f1c5b21b6a2d744))

### Fixes

* fix(tests): add missing app import in QR service tests ([`63b4198`](https://github.com/gsinghjay/mvp_qr_gen/commit/63b41982a57a397e3c13be73772569d8ac439793))

* fix(tests): resolve duplicate table errors in test database setup ([`c1e16ce`](https://github.com/gsinghjay/mvp_qr_gen/commit/c1e16ce038b2d70625d582717a44002ff9602ef4))

### Refactoring

* refactor: remove test_validation_parameterized.py after reorganization ([`cfa7a88`](https://github.com/gsinghjay/mvp_qr_gen/commit/cfa7a8822fa5fa3e145926fbcd73f56713030c05))

* refactor: remove SQLite-specific tests after PostgreSQL migration ([`d194766`](https://github.com/gsinghjay/mvp_qr_gen/commit/d194766fdb81b90bd3c1e338c4d5b80e332f34c9))

* refactor: remove test_router_structure.py after reorganization ([`d539634`](https://github.com/gsinghjay/mvp_qr_gen/commit/d539634413a2775aebc9af727cea2ef07a8f75c4))

* refactor: remove test_response_models.py after reorganization ([`2e4b332`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e4b332ea14417bc151c07ceb98069d9aabd24f2))

* refactor: remove test_qr_service.py after reorganization ([`2e21e97`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e21e9761de4971022508baf32745caf2faf5fdf))

* refactor: remove test_models_schemas.py after reorganization ([`933371e`](https://github.com/gsinghjay/mvp_qr_gen/commit/933371e06433dc73b0033753460d528581eddd11))

* refactor: remove test_middleware.py after reorganization ([`80bd09f`](https://github.com/gsinghjay/mvp_qr_gen/commit/80bd09f1e4dccf3b9eac946872d42352a1606d08))

* refactor: remove test_main.py after reorganization ([`0062814`](https://github.com/gsinghjay/mvp_qr_gen/commit/0062814f7ccd69ff4f2a70cce804043f59a91c2f))

* refactor: remove test_lifecycle.py after reorganization ([`b2e093a`](https://github.com/gsinghjay/mvp_qr_gen/commit/b2e093a8695843f4b650b2ad1fccb12b50028bd5))

* refactor: remove test_integration.py after reorganization ([`1af2655`](https://github.com/gsinghjay/mvp_qr_gen/commit/1af2655a54a750a415a46dfdf2ec3ea1057266bd))

* refactor: remove test_http_methods.py after reorganization ([`eec0bd8`](https://github.com/gsinghjay/mvp_qr_gen/commit/eec0bd8ea99ea186a356ec60afe199b40c3e930e))

* refactor: remove test_factories.py after reorganization ([`65d1647`](https://github.com/gsinghjay/mvp_qr_gen/commit/65d16474a0ea964c0ce174bdf4732161286f246d))

* refactor: remove test_exceptions.py after reorganization ([`d5f1171`](https://github.com/gsinghjay/mvp_qr_gen/commit/d5f1171b33ace5d7311d3a7c5d67b686fb2b5cc8))

* refactor: remove test_dependency_overrides.py after reorganization ([`6cfaf83`](https://github.com/gsinghjay/mvp_qr_gen/commit/6cfaf832f7b0d76c5496581f49e08bcc02c8b6a5))

* refactor: remove test_database_connection.py after reorganization ([`40abe1b`](https://github.com/gsinghjay/mvp_qr_gen/commit/40abe1b7d73dd1a093028a9cd374ead9337c3090))

* refactor: remove test_background_tasks.py after reorganization ([`a44d04f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a44d04f08fd2a9e877f9105080b7b99089a1b883))

* refactor: remove test_async_example.py after reorganization ([`884ba79`](https://github.com/gsinghjay/mvp_qr_gen/commit/884ba79b66e032f94e5bf1433d6fb083f7fd41a4))

* refactor: remove test_api_restructure.py after reorganization ([`fa8583a`](https://github.com/gsinghjay/mvp_qr_gen/commit/fa8583a62ac600cfd2184c4d5b4f56b814f942aa))

* refactor: organize unit tests in dedicated directory ([`62c9e39`](https://github.com/gsinghjay/mvp_qr_gen/commit/62c9e397f279d84bb2e47bc495b7a88746844677))

* refactor: organize integration tests in dedicated directory ([`906e48c`](https://github.com/gsinghjay/mvp_qr_gen/commit/906e48cda5c8a77fda8f116de8a55564f88d3b44))

* refactor: organize end-to-end tests in dedicated directory ([`e00c0a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/e00c0a74f1edbc1f0c77012fc68f3dbbc03d9fce))

### Testing

* test(db): add specific tests to verify test database setup integrity ([`ea258ae`](https://github.com/gsinghjay/mvp_qr_gen/commit/ea258ae7a009cdc65d0faf63cf8cbe584e004f08))

### Unknown

* Merge pull request #35 from gsinghjay/refactor/test-1.2

Resolve "relation already exists" errors in test database setup (Task 1.2) ([`6483beb`](https://github.com/gsinghjay/mvp_qr_gen/commit/6483beb73d9a8eb6efa3392e02f0ffb1c54213ed))

* Merge pull request #34 from gsinghjay/refactor/test-1.1

Refactor test suite organization (Task 1.1) ([`a0e83a4`](https://github.com/gsinghjay/mvp_qr_gen/commit/a0e83a48edaeebb56aca842c1d2d130b0bcf887f))


## v0.22.0 (2025-05-19)

### Chores

* chore: remove unused image assets ([`fe1403c`](https://github.com/gsinghjay/mvp_qr_gen/commit/fe1403cd3466d688446ece3cd3069132ef5f13cc))

* chore: update gitignore patterns ([`6f19679`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f19679a94869620d2a926b1300a7ea13e30d661))

* chore: update project metadata and dependencies ([`9e46b91`](https://github.com/gsinghjay/mvp_qr_gen/commit/9e46b9149e8031557a9ea693fac5786c7027e742))

* chore: update QR logo image ([`1f7b255`](https://github.com/gsinghjay/mvp_qr_gen/commit/1f7b2552650f8e578929708df83e82df56f37bcc))

* chore: add backups directory to gitignore ([`d75d87d`](https://github.com/gsinghjay/mvp_qr_gen/commit/d75d87d6a65cec8e163d9a07ac3a8e263e1d7702))

* chore: remove SQLite-specific migration files ([`86b49ba`](https://github.com/gsinghjay/mvp_qr_gen/commit/86b49bac26f7c6428559d0ad160a297c7ee7dc38))

* chore: add alembic script template for migration generation ([`0c07b5c`](https://github.com/gsinghjay/mvp_qr_gen/commit/0c07b5ccdcbb60eb58fd10c2e9a0bb5af3b4df92))

* chore: update alembic.ini for PostgreSQL compatibility ([`517c50e`](https://github.com/gsinghjay/mvp_qr_gen/commit/517c50e60f9ca9fa339cb289966f05a912eaa621))

* chore(docker): replace SQLite with PostgreSQL client tools ([`5000d7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/5000d7d28f1c74e02faae26b3fe4ee109ce22e01))

### Documentation

* docs: add detailed documentation for database schema report script ([`15eb906`](https://github.com/gsinghjay/mvp_qr_gen/commit/15eb9060aa2159be5cd7a36ffc89e5e35b7d5800))

* docs: add README for database scripts directory ([`8fe08b1`](https://github.com/gsinghjay/mvp_qr_gen/commit/8fe08b1a3c5662beeb4e2f0bcc299e9461c98361))

* docs: update API test documentation and scripts for scan tracking ([`ec3ee30`](https://github.com/gsinghjay/mvp_qr_gen/commit/ec3ee30ef18fca5644b8ec3a4799d4db7a6ed3f7))

* docs: update test documentation for PostgreSQL test database ([`89371e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/89371e32d43fcb260f37662f6819107e34923ab0))

* docs: update project story to reflect PostgreSQL migration ([`39b85ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/39b85ef41aaf170133958383a3f81b73b48626b2))

* docs: remove STATUS.md in favor of consolidated documentation ([`093a482`](https://github.com/gsinghjay/mvp_qr_gen/commit/093a482660762e3379b839ecbdecc940c474a1c2))

* docs: update README to reflect PostgreSQL-only usage ([`9f18e32`](https://github.com/gsinghjay/mvp_qr_gen/commit/9f18e3250a2d4bc1c22d284c5f70194f2dad69ee))

* docs: update infrastructure documentation for PostgreSQL architecture ([`b8a766d`](https://github.com/gsinghjay/mvp_qr_gen/commit/b8a766d7d1be14947650900f0f4686ccfac45298))

### Features

* feat: add official HCCC logo in SVG format ([`372cc34`](https://github.com/gsinghjay/mvp_qr_gen/commit/372cc34b0613d02657a1c529bfdb27d1bd5718c2))

* feat: add PostgreSQL database schema report script ([`4591d1c`](https://github.com/gsinghjay/mvp_qr_gen/commit/4591d1cf1898a093c157c581d68ac99af7607126))

* feat: update fragment endpoints to support scan analytics display ([`8d0470c`](https://github.com/gsinghjay/mvp_qr_gen/commit/8d0470c33ad372bf7520ee7d0ce49ea7ebcb761f))

* feat: enhance QR detail template to display scan statistics ([`971fe34`](https://github.com/gsinghjay/mvp_qr_gen/commit/971fe340a7766e4da9343a092c2efa280739c85e))

* feat: update QR schemas with scan tracking information ([`386f44f`](https://github.com/gsinghjay/mvp_qr_gen/commit/386f44f0d7851ec1ee4bf1acc7dfb626bb8fbad2))

* feat: add scan_ref parameter handling for genuine scan detection ([`ecd8630`](https://github.com/gsinghjay/mvp_qr_gen/commit/ecd8630e062accb22689fa6adf2da784a345b8db))

* feat: implement user agent parsing and scan logging in QRService ([`7e6d5a1`](https://github.com/gsinghjay/mvp_qr_gen/commit/7e6d5a14b04188c0a9e387898b11e43dac026fb4))

* feat: add methods for scan statistics and analytics in QRRepository ([`31f07b2`](https://github.com/gsinghjay/mvp_qr_gen/commit/31f07b2f2f3e68678a5512b67d9d756c0e1a541c))

* feat: enhance QRCode model with genuine scan tracking fields ([`0ca376b`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ca376b2470fdd7a61694e596107c3c5f771a3d8))

* feat: include ScanLog model in models package ([`89510eb`](https://github.com/gsinghjay/mvp_qr_gen/commit/89510eb4c1552c3fa0ec03f6bea114c37dc2ff4f))

* feat: add ScanLog model for detailed scan tracking ([`7613638`](https://github.com/gsinghjay/mvp_qr_gen/commit/7613638b9beebdaf0a5014972fc0e4bb799da3fb))

* feat: add migration for scan_log table and QR code enhancements ([`4e7ad71`](https://github.com/gsinghjay/mvp_qr_gen/commit/4e7ad716d792f3b74b5114197493f5f9921623cb))

* feat: update Docker configuration for PostgreSQL services ([`0e2716d`](https://github.com/gsinghjay/mvp_qr_gen/commit/0e2716d3bd7a6a759cb603ea5fad104deec6b05a))

* feat: enhance QR imaging with physical dimension and DPI support ([`f42c32c`](https://github.com/gsinghjay/mvp_qr_gen/commit/f42c32c9e51a7cfcf0f3921187ef78fe3db020c6))

* feat: implement streamlined QR creation workflow ([`a9dcb35`](https://github.com/gsinghjay/mvp_qr_gen/commit/a9dcb35d024f50a1500ecd55a8b12c4d39db7dcc))

* feat: add physical dimension inputs to QR details modal ([`7654dba`](https://github.com/gsinghjay/mvp_qr_gen/commit/7654dbac493c3a5d07125a1fea46e20eba21227f))

* feat: enhance QR service with physical dimension support ([`42176a3`](https://github.com/gsinghjay/mvp_qr_gen/commit/42176a3b547a6ba183a98fed810b51b115dabdcb))

* feat: add physical dimension parameters to QR image schemas ([`ccfe0f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/ccfe0f45a8abf99b6e090596a872efd110a0a33d))

* feat: update QR schemas for PostgreSQL compatibility ([`4c1617c`](https://github.com/gsinghjay/mvp_qr_gen/commit/4c1617c29e148ec5f0074c1e5e5583ef258c3c4f))

* feat: enhance QR endpoints to support physical dimensions and DPI ([`30a71c5`](https://github.com/gsinghjay/mvp_qr_gen/commit/30a71c58a783a5e15706d96534f57c9259f72de8))

* feat: update fragments endpoint to handle physical dimension parameters ([`9a7466b`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a7466b4b0136add8239f4fc19dfe8c9dd5caba4))

* feat(security): add routing for new auth domain and IP 130.156.44.53 ([`425bb22`](https://github.com/gsinghjay/mvp_qr_gen/commit/425bb2255a6c935288c8d6ea710f8e68d16ffc7b))

* feat(ui): implement toast notification with QR details modal for better user experience ([`aba23d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/aba23d280230ff5a9bd9fde67355010b9caa6898))

* feat: add short_id field to QR code schemas for improved data validation and API responses ([`64606e7`](https://github.com/gsinghjay/mvp_qr_gen/commit/64606e7a46d660e5123d7d1885c21769be3dd2b6))

* feat: add migration for short_id column with data population ([`814b875`](https://github.com/gsinghjay/mvp_qr_gen/commit/814b875df1c9174720036205e17224822df34711))

* feat: update QRCodeService to utilize short_id for improved redirect performance ([`7ce41ff`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ce41ff1eaac8e5f5211afd6883aedae8c29400b))

* feat: implement get_by_short_id repository method for direct lookups ([`75494fc`](https://github.com/gsinghjay/mvp_qr_gen/commit/75494fcb6d2c0ef733f2be4ccd406cdfe2dec35a))

* feat: add short_id column to QRCode model for optimized lookups ([`b3c3450`](https://github.com/gsinghjay/mvp_qr_gen/commit/b3c34504847f519bee043782f80037420fd62c18))

* feat: add PostgreSQL backup capability to manage_db.py ([`f42027a`](https://github.com/gsinghjay/mvp_qr_gen/commit/f42027a203de3e9f97c099a4b7effd6d63e58cae))

* feat: update init.sh to support PostgreSQL backup on startup ([`d989a58`](https://github.com/gsinghjay/mvp_qr_gen/commit/d989a583e5c3e53f40e465198d9983061b52ed4d))

* feat: create initial PostgreSQL schema migration ([`2097dbd`](https://github.com/gsinghjay/mvp_qr_gen/commit/2097dbd45838a00423a09d39ab0dceb06e15cc98))

* feat: configure alembic env.py for PostgreSQL support ([`57019c6`](https://github.com/gsinghjay/mvp_qr_gen/commit/57019c68f4b3e9c7f62f75a485740011ee8a66c4))

* feat(scripts): update init.sh with PostgreSQL readiness checks ([`6d6642d`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d6642dd0e8e9f607b2fdf80f0ef215efbf8e725))

* feat(scripts): enhance manage_db.py with PostgreSQL validation and backup ([`0b3de97`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b3de973cb9e4d6649ee03111d6c84d8155c2d9e))

* feat(deps): add psycopg2-binary for PostgreSQL support ([`d964f1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/d964f1e6e4d92f7b01093dbd3b8986a11708a967))

* feat(docker): add PostgreSQL service to Docker Compose ([`9aab687`](https://github.com/gsinghjay/mvp_qr_gen/commit/9aab687f235a7f2b072bed002de0e6f290528823))

### Fixes

* fix: adjust QR code size calculation for pixel unit ([`0670682`](https://github.com/gsinghjay/mvp_qr_gen/commit/0670682626524d821978a1508104ca4ca4c3ec7e))

* fix: correct indentation and update test fixtures for PostgreSQL ([`2432d48`](https://github.com/gsinghjay/mvp_qr_gen/commit/2432d48c0886a1ed99c7cd4cea96b397603008d3))

* fix: improve QR list display and pagination ([`47a5993`](https://github.com/gsinghjay/mvp_qr_gen/commit/47a5993f58dc88600562611d3219a9e82442dcf9))

* fix: update QR model to use PostgreSQL-compatible timestamp defaults ([`df2bb96`](https://github.com/gsinghjay/mvp_qr_gen/commit/df2bb9635b9de1cbe3b8c83c462e997d9fad3669))

* fix(security): prevent redirect loop on auth domain by excluding access-restricted path ([`8bb672e`](https://github.com/gsinghjay/mvp_qr_gen/commit/8bb672e838c6d268929d8c1597b9a7cba3ed0553))

* fix(backend): remove restriction to allow editing any QR code type ([`039fba4`](https://github.com/gsinghjay/mvp_qr_gen/commit/039fba4216c64f0a2c0681d5e5cd2f57cbee8590))

* fix(frontend): correct form structure in QR edit modal to enable form submission ([`6493050`](https://github.com/gsinghjay/mvp_qr_gen/commit/6493050a8e5f469a733e6d3e59d3dcbecceca484))

### Refactoring

* refactor: update test helpers for PostgreSQL support ([`0c27d73`](https://github.com/gsinghjay/mvp_qr_gen/commit/0c27d7301541b895c94f4d51647e47c9d5e4c087))

* refactor: update test factories for PostgreSQL compatibility ([`2eb6199`](https://github.com/gsinghjay/mvp_qr_gen/commit/2eb619918c9e7b308a8d7c347a2086cf7ae8ea5b))

* refactor: remove physical dimension fields from QR creation form ([`7ab5803`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ab5803a4e33d0c4d75413539759c2afd3738dd5))

* refactor: update health service for PostgreSQL-exclusive metrics ([`a7ed95f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a7ed95fb802a2a678ca654a2d184d77282852abe))

* refactor: remove SQLite-specific code from database management script ([`a310a19`](https://github.com/gsinghjay/mvp_qr_gen/commit/a310a19dec8f49d8f55510e42e46e9b3d21f57db))

* refactor: update initialization script for PostgreSQL-only setup ([`1692475`](https://github.com/gsinghjay/mvp_qr_gen/commit/16924752f0412efa891f8b6249bcbd432a6af024))

* refactor: simplify database module for PostgreSQL-only operation ([`83b008e`](https://github.com/gsinghjay/mvp_qr_gen/commit/83b008ee44a4055fe790a43e9d8f5d67fff54bba))

* refactor: remove SQLite database URL from configuration ([`8d59e73`](https://github.com/gsinghjay/mvp_qr_gen/commit/8d59e73c65e691e99bd947b036d9228e1a35d3c3))

* refactor: update Alembic configuration for PostgreSQL exclusivity ([`f373c7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/f373c7d2c306bfa78601e2d87bd9ca2fe73b8baf))

* refactor(startup): simplify lifespan warmup logic for QR lookups ([`d3ca7f1`](https://github.com/gsinghjay/mvp_qr_gen/commit/d3ca7f11ef40e293e7caf946f99e45a233af0ee0))

* refactor(repo): remove unused find_by_pattern method ([`33357d5`](https://github.com/gsinghjay/mvp_qr_gen/commit/33357d5b29c474676e9b010e771565624401f9b3))

* refactor(service): remove fallback pattern matching in get_qr_by_short_id ([`35079e9`](https://github.com/gsinghjay/mvp_qr_gen/commit/35079e99a5cc11bca435106ad95e24575170cedf))

* refactor(database): implement dual database support for SQLite and PostgreSQL ([`cf3dd21`](https://github.com/gsinghjay/mvp_qr_gen/commit/cf3dd2100d7226c6629f90b1a26ba2bae7971e51))

### Testing

* test: implement database connection tests for PostgreSQL ([`481f101`](https://github.com/gsinghjay/mvp_qr_gen/commit/481f101c8ecfdf5c155678546266c9ea84bb1da9))

* test: add asynchronous test examples for PostgreSQL compatibility ([`2b13fba`](https://github.com/gsinghjay/mvp_qr_gen/commit/2b13fba63eb1088ca1ae26e8bfa1c883ca21689f))

* test: adapt SQLite-specific tests for PostgreSQL environment ([`684a7a6`](https://github.com/gsinghjay/mvp_qr_gen/commit/684a7a667dd1fa352c1c453ecc140680663c2253))

* test: refactor QR service tests for PostgreSQL test database ([`c279d04`](https://github.com/gsinghjay/mvp_qr_gen/commit/c279d041a1887850a2b18170f41a00fa12d17e66))

* test: update middleware tests for PostgreSQL compatibility ([`eecde35`](https://github.com/gsinghjay/mvp_qr_gen/commit/eecde359c5a0d15e1e792eb293dcd41cf3c608d3))

* test: convert main application tests to use PostgreSQL ([`350f1b3`](https://github.com/gsinghjay/mvp_qr_gen/commit/350f1b3e64d840d847c5d753cf480cbfe6639436))

* test: update lifecycle tests for PostgreSQL compatibility ([`0e8eed0`](https://github.com/gsinghjay/mvp_qr_gen/commit/0e8eed01c711addee3636944c3a92ae203d48bef))

* test: convert integration tests to use PostgreSQL ([`db28701`](https://github.com/gsinghjay/mvp_qr_gen/commit/db28701a8ebb71a242cb76dcf4b463714afe2b3b))

### Unknown

* Merge pull request #33 from gsinghjay/feat/postgresql

PostgreSQL Migration Phase ([`ef4d0a6`](https://github.com/gsinghjay/mvp_qr_gen/commit/ef4d0a6c1f5cb2ba5ca6ab6979c946dbf2983f25))

* deps: remove SQLite dependencies and add PostgreSQL drivers ([`7abd909`](https://github.com/gsinghjay/mvp_qr_gen/commit/7abd909225b1f3c40d9476a8908197ed9989bd28))

* config(docker): update docker-compose.yml with PostgreSQL environment variables ([`52fa438`](https://github.com/gsinghjay/mvp_qr_gen/commit/52fa438cfd18cf68a7482cd6f673f04a36a284e5))


## v0.21.0 (2025-05-06)

### Chores

* chore: removed legacy css/js from before HTMX migration ([`d321ee5`](https://github.com/gsinghjay/mvp_qr_gen/commit/d321ee588eff34144502c08dcd3815484b9d75c5))

### Features

* feat: add title and description fields to QR edit form ([`e9b594f`](https://github.com/gsinghjay/mvp_qr_gen/commit/e9b594ff58af1a75e76a0f06244819d71d2cf3f9))

* feat: display QR title in list items ([`f7453fd`](https://github.com/gsinghjay/mvp_qr_gen/commit/f7453fd952cbf9922dbff1a206d4ff20f4dc9252))

* feat: add title column to QR list view ([`8fdf533`](https://github.com/gsinghjay/mvp_qr_gen/commit/8fdf533e5945a133ec29a4f2e606501704e3230e))

* feat: display title and description in QR detail view ([`a80628e`](https://github.com/gsinghjay/mvp_qr_gen/commit/a80628eb20d96a4199d922e61f406ad7f384c652))

* feat: add title and description fields to QR creation form ([`1206681`](https://github.com/gsinghjay/mvp_qr_gen/commit/1206681856e72a357ab9cc745512686f9251588d))

* feat: update fragment endpoints to handle title and description fields ([`95c5d88`](https://github.com/gsinghjay/mvp_qr_gen/commit/95c5d887889ebef2bc5df31ec12806fa87860756))

* feat: update API endpoints to support title and description ([`af01edf`](https://github.com/gsinghjay/mvp_qr_gen/commit/af01edf56ac5c0ed9471d7d1a9f40a5951f6ad66))

* feat: update QR service to handle title and description fields ([`3a10c62`](https://github.com/gsinghjay/mvp_qr_gen/commit/3a10c62b220da354343d0e0cbcd0fbcc2956e3ba))

* feat: enhance search functionality to include title and description ([`23f104f`](https://github.com/gsinghjay/mvp_qr_gen/commit/23f104fa83c69aff6bfecfbbd373bed7a8257797))

* feat: add title and description to QR response models ([`71a2b1a`](https://github.com/gsinghjay/mvp_qr_gen/commit/71a2b1a5ab53f816840c168b5ea62176dd691f03))

* feat: update parameter schemas with title and description fields ([`20ddd28`](https://github.com/gsinghjay/mvp_qr_gen/commit/20ddd282c6f07d27b4f0bf79b8dcc0d24d86ac8d))

* feat: add title and description fields to QRCode model ([`d5f88d3`](https://github.com/gsinghjay/mvp_qr_gen/commit/d5f88d3d7d2111bbe34c6dbc2ae9a3fdbd72eb41))

* feat: add migration for title and description columns in qr_codes table ([`db1df6c`](https://github.com/gsinghjay/mvp_qr_gen/commit/db1df6c07363cc0330bbe0ad754176e4dc768370))

### Testing

* test: update test script to include title and description in API requests ([`dd5cc43`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd5cc433da9df7574e5d713bfe09ceb17a9dc8dc))

### Unknown

* Merge pull request #32 from gsinghjay/feat/title-desc

Add title and description fields to QR codes ([`dcbc5ba`](https://github.com/gsinghjay/mvp_qr_gen/commit/dcbc5bae9bd6637ae871275a7babc1cf2d2f247c))


## v0.20.0 (2025-05-06)

### Chores

* chore: backup original custom CSS file for reference ([`5f9259c`](https://github.com/gsinghjay/mvp_qr_gen/commit/5f9259c59efbb16d29cb3424e15c42030ca873d6))

### Features

* feat(ui): add HTML fragments for HTMX partial updates ([`01c950a`](https://github.com/gsinghjay/mvp_qr_gen/commit/01c950a1ddbf335671e520233365a6876fd851fd))

* feat(ui): add HTMX library to base template ([`8373e42`](https://github.com/gsinghjay/mvp_qr_gen/commit/8373e42dd68643cd3b5f11ac9ea1ce98862c5de6))

* feat(api): register fragments router in API initialization ([`7d84d81`](https://github.com/gsinghjay/mvp_qr_gen/commit/7d84d818770f4d00e76141e1804cb77a80eb399e))

* feat(api): add fragments endpoint for HTMX integration ([`20bf094`](https://github.com/gsinghjay/mvp_qr_gen/commit/20bf094f7afd80ce7509a02d460be67f1e47b951))

### Refactoring

* refactor(ui): remove templates moved to pages directory ([`2115884`](https://github.com/gsinghjay/mvp_qr_gen/commit/211588495bd649b3b64ad276b0624ea766cfbc71))

* refactor(js): remove JavaScript files replaced by HTMX ([`9006f7f`](https://github.com/gsinghjay/mvp_qr_gen/commit/9006f7fbf3164994b7f48e67e7b8eb1cf47be37f))

* refactor(css): remove custom CSS in favor of Bootstrap classes ([`a57fb7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/a57fb7d7ca3812edb4bf45b71a4b51fad5b84521))

* refactor(js): move unused JavaScript to depreciated-js directory ([`2632683`](https://github.com/gsinghjay/mvp_qr_gen/commit/26326833b1cf7098ae48d879227788c0b7a15bb5))

* refactor(ui): update QR list template for HTMX compatibility ([`4a2de54`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a2de54c6f46ca3a259b9c619bd241a493db3e19))

* refactor(ui): migrate templates to pages directory structure ([`25cd908`](https://github.com/gsinghjay/mvp_qr_gen/commit/25cd90883e4be6b9ad082d8f250e3886aae8d85f))

* refactor(api): update QR endpoints for HTMX compatibility ([`4418ff0`](https://github.com/gsinghjay/mvp_qr_gen/commit/4418ff02cb64b0a99922f3da88458939c1f593ae))

* refactor(pages): update page handlers to use new template structure ([`a6ee368`](https://github.com/gsinghjay/mvp_qr_gen/commit/a6ee368fce5090e2d766b51b75c4e49bd381c7b2))

### Unknown

* Merge pull request #31 from gsinghjay/feature/htmx

HTMX Frontend Integration ([`aa73bb3`](https://github.com/gsinghjay/mvp_qr_gen/commit/aa73bb3af0de9fb430c0c804b310e1bcd2d4a2c9))

* enhance(ui): redesign QR detail modal with card-based layout ([`2153e8c`](https://github.com/gsinghjay/mvp_qr_gen/commit/2153e8cb1bd0ae9846bc4be4e294be69141df1b0))

* enhance(ui): improve QR metadata formatting in fragment endpoints ([`e58ff49`](https://github.com/gsinghjay/mvp_qr_gen/commit/e58ff49b7be9c774550278216f507a32dd89dd67))


## v0.19.0 (2025-05-05)

### Chores

* chore: remove outdated performance results file ([`10689ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/10689ef9d3c2fe1ca15ae3c2041a96d9690b9938))

### Documentation

* docs: update development story with JS refactoring information ([`c76e2cb`](https://github.com/gsinghjay/mvp_qr_gen/commit/c76e2cb76949d2d0ab95120af9343baf96b43f7c))

* docs: update README with modular JS architecture details ([`8b1a95d`](https://github.com/gsinghjay/mvp_qr_gen/commit/8b1a95d59d8e0fe49ed2b7dc9a0ff12b2dc3c08d))

### Features

* feat(js): add event-initializer module for setup and binding ([`cf9f22d`](https://github.com/gsinghjay/mvp_qr_gen/commit/cf9f22d679bb0a555533061b82eb12a3addefbe1))

* feat(js): add list-manager module for pagination and filtering ([`601ca62`](https://github.com/gsinghjay/mvp_qr_gen/commit/601ca62daf4a08e82bf2f3f590d9e0e6feb8107b))

* feat(js): add qr-operations module for core QR code functionality ([`381a0cf`](https://github.com/gsinghjay/mvp_qr_gen/commit/381a0cf56874ffd39c21d077185bc122d8ba71f1))

* feat(js): add form-handler module for form submissions and validation ([`5db36dd`](https://github.com/gsinghjay/mvp_qr_gen/commit/5db36dd1038633462be95ac56018c6d40426da75))

* feat(js): add modal-handler module for dialog operations ([`2797d9e`](https://github.com/gsinghjay/mvp_qr_gen/commit/2797d9e75f2c796c28af8cdb0de9a21ddd068e1d))

### Fixes

* fix(performance): optimize redirect initialization for faster QR code scans ([`9827fa4`](https://github.com/gsinghjay/mvp_qr_gen/commit/9827fa4211575a8fa2a9c20ee0484597004a803a))

### Refactoring

* refactor(html): update QR list template for modular JS structure ([`97ce131`](https://github.com/gsinghjay/mvp_qr_gen/commit/97ce1315a7b6cb23a09b876cf47564b2bc2b9bf0))

* refactor(html): update QR creation template for modular JS ([`734ff9a`](https://github.com/gsinghjay/mvp_qr_gen/commit/734ff9aa7e48b5749d1306898818ae4130866064))

* refactor(html): update index template for modular JS structure ([`b6600c7`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6600c7b49243c68ee70b8dc6d5dd4433811eb65))

* refactor(html): update dashboard template for modular JS structure ([`e79cfa4`](https://github.com/gsinghjay/mvp_qr_gen/commit/e79cfa4214df3d4cd0431962aeaa13c38e6014f7))

* refactor(html): update base template for modular JS architecture ([`bf1e272`](https://github.com/gsinghjay/mvp_qr_gen/commit/bf1e272e04f3f475f829d296f5cbb5c55ae8c239))

* refactor(js): deprecate script.js with backward compatibility ([`b35d999`](https://github.com/gsinghjay/mvp_qr_gen/commit/b35d999a3cea7a7d4708b233286de6e050b6766e))

* refactor(js): update main.js as modular architecture entry point ([`6b64d00`](https://github.com/gsinghjay/mvp_qr_gen/commit/6b64d009e22d272b06d1359969004782f6e5737c))

* refactor: standardize schema validation placement by removing redundant color checks ([`2a6ed8b`](https://github.com/gsinghjay/mvp_qr_gen/commit/2a6ed8b38153d6d8c037915bf578aa257f92df06))

* refactor: simplify error handling in repository and service layers ([`e1a51f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/e1a51f7bca575c46a2126bb46cbf916d3a882765))

* refactor: move RequestIDMiddleware to middleware directory ([`09e593c`](https://github.com/gsinghjay/mvp_qr_gen/commit/09e593c4f2a46f3fa43981f3af7cc7296606092e))

### Testing

* test: add updated performance results for modular architecture ([`d02f1e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/d02f1e4918611ea9c30bd05d66b710fa124f093e))

### Unknown

* Merge pull request #30 from gsinghjay/refactor/javascript

JavaScript Refactor ([`b44ecd2`](https://github.com/gsinghjay/mvp_qr_gen/commit/b44ecd27fa49388e6e36dbb360423b046aeec355))

* Merge pull request #29 from gsinghjay/refactor/inconsistencies

Fix code inconsistencies - middleware organization and path handling ([`14c380f`](https://github.com/gsinghjay/mvp_qr_gen/commit/14c380f8ea16a09dd56f025faf7da3a29d43be7b))


## v0.18.0 (2025-05-05)

### Features

* feat: added auth to test scripts ([`657f4c3`](https://github.com/gsinghjay/mvp_qr_gen/commit/657f4c3ed09517e6d2a2c1ba6dc25b334603901c))

* feat(api): update endpoints to support error correction and SVG accessibility ([`7defd7b`](https://github.com/gsinghjay/mvp_qr_gen/commit/7defd7b5bb7c15ae6103b086014a7dc1367c115f))

* feat(utils): enhance QR generation with error levels and SVG accessibility ([`8106a54`](https://github.com/gsinghjay/mvp_qr_gen/commit/8106a54193e58b7761fb8eb4b2321dad724ed328))

* feat(services): implement error correction level in QR generation service ([`4a2fe45`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a2fe451b6e4f54be297a4b47c6b758703ce9342))

* feat(models): add error_level field to QRCode model ([`111ad77`](https://github.com/gsinghjay/mvp_qr_gen/commit/111ad77221c3a3d192f7b67b054d3da64fe256bb))

* feat(schemas): add error correction level and SVG accessibility parameters ([`0ce1381`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ce138161678427c5bf4971f667ecbfdedd0174d))

* feat(db): add error_level column to qr_codes table ([`64b6ed8`](https://github.com/gsinghjay/mvp_qr_gen/commit/64b6ed8f633b12c8d0a083d7c12ef506c5efd77a))

### Unknown

* Merge pull request #28 from gsinghjay/feat/enhance-qr-gen

QR Code Error Correction Level ([`816c639`](https://github.com/gsinghjay/mvp_qr_gen/commit/816c639f2143af11a6686d09389ab09afd24bcd3))


## v0.17.0 (2025-05-04)

### Chores

* chore: add users.htpasswd to .gitignore for security ([`d149f4c`](https://github.com/gsinghjay/mvp_qr_gen/commit/d149f4cb21d714130cdfea90b7f1b0a686d0ee6a))

### Documentation

* docs: update documentation with basic authentication implementation details ([`11ed736`](https://github.com/gsinghjay/mvp_qr_gen/commit/11ed736e3c83972046abd1eec32d7a9dab15bb7c))

### Features

* feat: configure Traefik to mount htpasswd file for basic authentication ([`c202e95`](https://github.com/gsinghjay/mvp_qr_gen/commit/c202e9536a5b943da93aa43e48329fb7c5aee4c7))

* feat: implement basic authentication middleware for dashboard access ([`416d213`](https://github.com/gsinghjay/mvp_qr_gen/commit/416d2131980ac6e8831a7e591706f457ad6e763f))

### Unknown

* Merge pull request #27 from gsinghjay/feature/basic-auth

Implement Basic Authentication for Dashboard Access ([`a0ce90a`](https://github.com/gsinghjay/mvp_qr_gen/commit/a0ce90a8a8ee52ab42c817a900f2f6303e19f649))


## v0.16.1 (2025-05-04)

### Chores

* chore: irrelevant task file ([`5e7128f`](https://github.com/gsinghjay/mvp_qr_gen/commit/5e7128fa4ed2eb80028cd9d7551236bb8bfd6877))

### Code Style

* style(css): remove login button styles from custom.css ([`9a1b709`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a1b7094750964c41b576ad732f1f0f83ce321ef))

### Fixes

* fix(auth): remove login endpoint functionality from pages.py router ([`40e948b`](https://github.com/gsinghjay/mvp_qr_gen/commit/40e948ba26713f9e46bc2fbbe54ee7393e194151))

* fix: standardize dependency injection and code structure patterns ([`992440d`](https://github.com/gsinghjay/mvp_qr_gen/commit/992440d782eb4cbed9b731f5ad817f81cefb34a0))

* fix(health): use settings.ENVIRONMENT in health endpoint response ([`f31c9bb`](https://github.com/gsinghjay/mvp_qr_gen/commit/f31c9bbe19aefcb3056d1820b8e42ceb58824607))

* fix(config): explicitly load ENVIRONMENT from env variables ([`07bdc49`](https://github.com/gsinghjay/mvp_qr_gen/commit/07bdc4987a7727cd3aecbbcd1b2d51ec3cc5822c))

### Performance Improvements

* perf: optimize first-request performance with FastAPI lifespan initialization ([`2a8769b`](https://github.com/gsinghjay/mvp_qr_gen/commit/2a8769b69dafd77e4bce4745ef4d3073688699da))

* perf: add route warmup to init.sh to improve first request performance ([`300a4ee`](https://github.com/gsinghjay/mvp_qr_gen/commit/300a4eef2b0d04f44ffad136ffc593b53a60b860))

### Refactoring

* refactor(auth): delete portal-login.html template as part of login removal ([`67f3fd2`](https://github.com/gsinghjay/mvp_qr_gen/commit/67f3fd2fc2cc5fef889eb98e5799a590ee9b3a89))

* refactor(ui): remove logout link from base.html template ([`01556f5`](https://github.com/gsinghjay/mvp_qr_gen/commit/01556f5e2ccfe53acff4d00b052529825a6f4b97))

* refactor(js): remove setupLoginButtons function from main.js ([`a55d31f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a55d31f55eaeb336b04006dd26e142760d6dfa89))

* refactor: move settings import to module level in qr_service.py for better initialization ([`8261c41`](https://github.com/gsinghjay/mvp_qr_gen/commit/8261c41a271c0b6d7c294ded523bf1a4ecda6394))

* refactor(api): migrate to modern FastAPI structure

- Move router endpoints to app/api/v1/endpoints
- Organize endpoints by resource rather than operation type
- Implement proper API versioning with nested routers
- Maintain backward compatibility for all endpoints
- Remove old router structure
- Update main.py to use new router imports
- Add test script to verify API restructuring
- Create documentation in app/api/README.md ([`131be20`](https://github.com/gsinghjay/mvp_qr_gen/commit/131be20d9f7cab7a90c25a43afbeb88a81e20712))

### Unknown

* Merge pull request #26 from gsinghjay/refactor/router

Refactor: Migrate to Modern FastAPI Structure with Versioned API ([`b6351f3`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6351f3cf1c0ec008d62042a0d47f4b03406b0d4))


## v0.16.0 (2025-04-30)

### Features

* feat: add type aliases for common dependencies

- Create DbSessionDep, QRRepositoryDep, and QRServiceDep
- Use Annotated syntax for modern FastAPI type annotations
- Prepare for future adoption in router endpoints ([`5dce8fd`](https://github.com/gsinghjay/mvp_qr_gen/commit/5dce8fd2906164120c1f66e0f607ec91f78063fd))

* feat: implement QRCodeRepository for QR code database operations

- Create QRCodeRepository extending BaseRepository
- Implement QR-specific methods like get_by_content
- Add custom update_qr method for attribute-based updates
- Implement scan tracking methods with proper error handling
- Move list_qr_codes functionality to repository layer ([`f82bd0c`](https://github.com/gsinghjay/mvp_qr_gen/commit/f82bd0cacfce1e0e4ad83a9926b8ec6367ac4af2))

* feat: implement BaseRepository with generic CRUD operations

- Create generic BaseRepository with type-safe operations
- Implement get_by_id, get_all, create, update, delete methods
- Add proper error handling and logging
- Use with_retry decorator for operations prone to locking ([`103e5f1`](https://github.com/gsinghjay/mvp_qr_gen/commit/103e5f1fe2530792b70e774e51f1976b4cdb9cbd))

### Refactoring

* refactor: update QRCodeService to use repository pattern

- Replace direct database access with repository calls
- Remove duplicate error handling now in repository layer
- Use repository.update_qr for dynamic QR updates
- Delegate scan statistics tracking to repository
- Keep business logic validation in service layer ([`31f9870`](https://github.com/gsinghjay/mvp_qr_gen/commit/31f98709a482addae461846cfb6857a9b9ede08f))

* refactor: update dependency injection to use repository pattern

- Update get_qr_service to accept repository dependency
- Create new get_qr_repository dependency
- Use Annotated syntax for modern FastAPI dependency injection
- Add get_db shorthand dependency for consistency ([`0321c46`](https://github.com/gsinghjay/mvp_qr_gen/commit/0321c46a5f578ab4a326b5839d65c60a67c5ec33))

### Unknown

* Merge pull request #25 from gsinghjay/refactor/repository

Implement Repository Pattern for Data Access ([`4e7ee5d`](https://github.com/gsinghjay/mvp_qr_gen/commit/4e7ee5d1a28bef58b01591a2958664eeb774d1df))


## v0.15.0 (2025-04-30)

### Build System

* build: remove Keycloak and authentication-related dependencies ([`f3e88aa`](https://github.com/gsinghjay/mvp_qr_gen/commit/f3e88aa256a768891627c5ae7f696aa8332d10b9))

### Chores

* chore: update gitignore to exclude project rules ([`ba97fa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/ba97fa041973a876671bf65af947d76c80223625))

* chore: updated gitignore to include sensitive data ([`02a404d`](https://github.com/gsinghjay/mvp_qr_gen/commit/02a404d9da51700397feae30a92b4c9ee07dcb78))

* chore: update gitignore patterns ([`3799bb4`](https://github.com/gsinghjay/mvp_qr_gen/commit/3799bb4a83cd2f83c634953e4cb4613dc227a976))

* chore: redundant file, no longer using Giga ([`9add430`](https://github.com/gsinghjay/mvp_qr_gen/commit/9add430bd05123e7f12226d66e4a2a9ef8a6bba3))

* chore: update gitignore with Keycloak-related patterns ([`2d674c2`](https://github.com/gsinghjay/mvp_qr_gen/commit/2d674c23e11685c91608dda9819667098a5763a7))

### Documentation

* docs: update project story to reflect security model evolution ([`3d3f70d`](https://github.com/gsinghjay/mvp_qr_gen/commit/3d3f70dc5e4d85f9e55428fbed6324696362a19a))

* docs: update infrastructure documentation for network-based security model ([`d6b055d`](https://github.com/gsinghjay/mvp_qr_gen/commit/d6b055da1fbc5dc4bd016c8b35cb92559eb75783))

* docs: update README to reflect simplified security architecture ([`bd338a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/bd338a7fdf7cf4da4eafb6a91392a1dab802b771))

* docs: update system documentation to include Keycloak migration ([`faa7b32`](https://github.com/gsinghjay/mvp_qr_gen/commit/faa7b32bed724c1f889630e8e98488d0e4b71490))

* docs(infra): update infrastructure documentation with Keycloak integration ([`f4725f2`](https://github.com/gsinghjay/mvp_qr_gen/commit/f4725f2b847b38193d461a0306190bc43ca27635))

### Features

* feat: add HCCC QR logo for branded QR codes ([`6f3080d`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f3080ddbc2e8d88e3e0fc0b45fa9d50ef802db0))

* feat: add access-restricted page for unauthorized navigation attempts ([`83215ba`](https://github.com/gsinghjay/mvp_qr_gen/commit/83215ba658b6133be02585cc552a12f4e9e59903))

* feat(infra): migrate from bind mounts to named volumes for improved permission handling ([`64b502e`](https://github.com/gsinghjay/mvp_qr_gen/commit/64b502ec727773de3615204980755a918777ec9b))

### Fixes

* fix(keycloak): configure traefik routing with explicit naming for keycloak service ([`55673c0`](https://github.com/gsinghjay/mvp_qr_gen/commit/55673c0f325097aee39fc1522e5bfca5acf07043))

* fix(db): improve database persistence by creating backups instead of removing database file ([`e155222`](https://github.com/gsinghjay/mvp_qr_gen/commit/e1552226f29d15961c7b46e5468288b88b6e8b54))

### Refactoring

* refactor: migrate from qrcode library to segno for improved QR generation ([`6732bad`](https://github.com/gsinghjay/mvp_qr_gen/commit/6732bad28aeaa6e8bd9c28e8f028c46cd2dfd9d5))

* refactor: simplify database session handling without auth considerations ([`e5e5091`](https://github.com/gsinghjay/mvp_qr_gen/commit/e5e5091b8c91873535592f0f112c0904975bbb61))

* refactor: update scripts to remove authentication dependencies ([`be4daae`](https://github.com/gsinghjay/mvp_qr_gen/commit/be4daae02b49b908e83eee4478cd39052d63de94))

* refactor: remove authentication UI elements from templates ([`4e4e575`](https://github.com/gsinghjay/mvp_qr_gen/commit/4e4e575f1b2d54a492ff2c96ee9e1aed3fcc2f11))

* refactor: remove authentication from frontend JavaScript ([`f057b8a`](https://github.com/gsinghjay/mvp_qr_gen/commit/f057b8abb419b3a6e13a3a20ee1de143cff41082))

* refactor: remove authentication dependencies from services and schemas ([`2a68b85`](https://github.com/gsinghjay/mvp_qr_gen/commit/2a68b85bc2076bd6a35f6442ff571516dce44f9d))

* refactor: simplify security middleware without authentication ([`3a6f9e2`](https://github.com/gsinghjay/mvp_qr_gen/commit/3a6f9e2b6bcda5d9da884cfd47d8612e69fc4c77))

* refactor: remove authentication middleware and setup from main application ([`0ac70ab`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ac70ab538c8dd963a4fd47420f748c3936844a9))

* refactor: remove authentication imports and dependencies from routers ([`d868f3e`](https://github.com/gsinghjay/mvp_qr_gen/commit/d868f3ef10da3442c444bbcc9b1b9a21e4515813))

* refactor: remove authentication router ([`6eba6d7`](https://github.com/gsinghjay/mvp_qr_gen/commit/6eba6d75ccf1b3ddb7ddd569cc5e27bf4388f2e9))

* refactor: remove authentication directory and related code ([`f02ca75`](https://github.com/gsinghjay/mvp_qr_gen/commit/f02ca750a60e0af5b06ff7fa1ad086e71257f98d))

* refactor: remove authentication environment variables from docker-compose ([`5940134`](https://github.com/gsinghjay/mvp_qr_gen/commit/59401345d55e9f6ea1d771c3f0e7083a61f32f8e))

* refactor: remove SESSION_SECRET_KEY and authentication config from settings ([`51ac389`](https://github.com/gsinghjay/mvp_qr_gen/commit/51ac38967fa9bcdbf7130230b9f9e8013eccd473))

### Testing

* test: remove authentication-related tests ([`848a45a`](https://github.com/gsinghjay/mvp_qr_gen/commit/848a45a1063e1f106e27e23572049dfbab43fc84))

### Unknown

* Merge pull request #24 from gsinghjay/feat/keycloak

Authentication Removal and Security Simplification ([`11a7e9f`](https://github.com/gsinghjay/mvp_qr_gen/commit/11a7e9f86c6f365fde5ba36ee372dbe0e3b5f9cb))

* config: update Traefik configuration for edge security model ([`a707e6f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a707e6f14c9cff65e0d8d2309e81cb2ded6f1bd4))


## v0.14.0 (2025-03-25)

### Features

* feat(js): update JavaScript modules to support new templates ([`29e8099`](https://github.com/gsinghjay/mvp_qr_gen/commit/29e809965d5af2cec60daca59647ad8f2c6c8e3d))

* feat(routes): implement server-side routes for template pages ([`0961578`](https://github.com/gsinghjay/mvp_qr_gen/commit/09615781f085be7633e6d3ea4e0e0df32deb7ff7))

* feat(ui): add QR code detail view with statistics and actions ([`9c0f60c`](https://github.com/gsinghjay/mvp_qr_gen/commit/9c0f60c1621a8f8847c55729c7472b660d3929f5))

* feat(ui): implement QR code creation page with tabs and preview ([`4a1a9d1`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a1a9d1894cf06f3f1bf4ea688129c94e396c4fa))

* feat(ui): add QR code listing page with sorting and filtering ([`5be7451`](https://github.com/gsinghjay/mvp_qr_gen/commit/5be74515c52bf1aac5c494484b154b89e0223ece))

* feat(ui): create dashboard template extending base layout ([`17c29a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/17c29a7f25f3ef8e8d0cae9cf1076383d665beef))

* feat(ui): implement base template with common elements ([`1071cd0`](https://github.com/gsinghjay/mvp_qr_gen/commit/1071cd09d883a25ea0cdf9ee69f7181ae504ddfb))

### Refactoring

* refactor(ui): remove redundant user info and notification elements from navbar ([`9b05246`](https://github.com/gsinghjay/mvp_qr_gen/commit/9b05246a85eb2e07bd16aac18f03bc2a2e8f4e6d))

### Unknown

* Merge pull request #23 from gsinghjay/refactor/fe_bs

Frontend Refactoring: Bootstrap-Based UI Templates (Tasks 1.1-1.5) ([`a768193`](https://github.com/gsinghjay/mvp_qr_gen/commit/a76819345ee4c5596fa9d80086dbc40d659b6410))


## v0.13.0 (2025-03-18)

### Chores

* chore: update Docker configuration with BASE_URL environment ([`70c8573`](https://github.com/gsinghjay/mvp_qr_gen/commit/70c857316e9b6d6c8c9c1f5d820960bef39d3608))

* chore: updated diagrams ([`48e0527`](https://github.com/gsinghjay/mvp_qr_gen/commit/48e052771e4297e374b7352e3f11d42d923bec47))

### Code Style

* style(portal): enhance styling for portal login page ([`cca70bd`](https://github.com/gsinghjay/mvp_qr_gen/commit/cca70bd8f0ad7340333ffe838ef2cded0eae53d4))

* style(ui): add styles for table rows and interaction states ([`c40e0d0`](https://github.com/gsinghjay/mvp_qr_gen/commit/c40e0d0b79d79e60ef00c9472fdd84c5c2269bf0))

### Documentation

* docs: remove obsolete task_msal.md file ([`0570c93`](https://github.com/gsinghjay/mvp_qr_gen/commit/0570c93a495f0a1450a59058117a56dba0ecce8a))

### Features

* feat: add QR content display to modal view for better user experience ([`82da8c4`](https://github.com/gsinghjay/mvp_qr_gen/commit/82da8c4f550a2e07d386f9ce1840ee749cd3701b))

* feat(js): add search and sort functionality to QR code dashboard ([`b73119d`](https://github.com/gsinghjay/mvp_qr_gen/commit/b73119d7fc3d413d224decd079118f1dd26cc73c))

* feat(ui): implement table header sorting with visual indicators ([`162040e`](https://github.com/gsinghjay/mvp_qr_gen/commit/162040e3797d7cb542bc4fe4a45cf7779cbd2663))

* feat(api): add search and sorting functionality to QR code listing ([`073415c`](https://github.com/gsinghjay/mvp_qr_gen/commit/073415c6e7165cbb3e973819c148d3204b4ab388))

* feat(portal): add client-side functionality for portal login ([`0d9e3dd`](https://github.com/gsinghjay/mvp_qr_gen/commit/0d9e3dd60204b4d08f2e16bb3c682fb80d9b1c1a))

* feat(portal): update portal login template for improved user experience ([`2b431f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/2b431f72f935d353e0cb5cf817996167d7d3c225))

* feat(auth): add group-based endpoints and authorization ([`8678671`](https://github.com/gsinghjay/mvp_qr_gen/commit/8678671739b8f4cf18661ac548bc7dd3e27f76e0))

* feat(auth): add group membership support to SSO implementation ([`74e40f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/74e40f77a6d78314838b761643d43d7a0e52081b))

* feat(ui): implement event delegation for table interactions ([`9a1dae3`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a1dae3973e2a0b1fed49d8013792b2450cba761))

* feat(ui): improve QR list rendering with better data formatting ([`26b4f6b`](https://github.com/gsinghjay/mvp_qr_gen/commit/26b4f6b9776499ea3783f21a4a3e46d1229da1a3))

* feat(ui): enhance QR code table with semantic HTML5 elements ([`761a585`](https://github.com/gsinghjay/mvp_qr_gen/commit/761a58564ef59aa76dd56918cf402fe7408b59fc))

* feat(templates): create portal-login.html template ([`0624d60`](https://github.com/gsinghjay/mvp_qr_gen/commit/0624d60848e4921a9e644ce05fbefcab8aeaedfa))

* feat(web): add portal login route in pages.py ([`78cba5a`](https://github.com/gsinghjay/mvp_qr_gen/commit/78cba5a8b15e46e4eb49ab218f10ca94ea59bd2c))

* feat(auth): add scope inspection endpoints for OAuth debugging and RBAC support ([`431fbd8`](https://github.com/gsinghjay/mvp_qr_gen/commit/431fbd8789ce456085a7d0a844f0598f88023bff))

### Fixes

* fix: update UI components and CSS styles for improved layout ([`f24039f`](https://github.com/gsinghjay/mvp_qr_gen/commit/f24039f783875c8222c31f50edb1297d30723f4c))

* fix: update test script to handle full URL format with BASE_URL ([`db47110`](https://github.com/gsinghjay/mvp_qr_gen/commit/db471104702920cb0c72a98c8c7565cbc24c6838))

* fix: update QR code redirection with proper BASE_URL handling ([`f84c2a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/f84c2a799fff834b553a2814b28440289514063e))

### Testing

* test(auth): add comprehensive tests for logout functionality ([`ee2a12d`](https://github.com/gsinghjay/mvp_qr_gen/commit/ee2a12dfba24ae1b41d22896e8aa40dfc846eb9e))

* test(auth): update auth endpoint tests for group support ([`41cb2db`](https://github.com/gsinghjay/mvp_qr_gen/commit/41cb2db59268c285c769b69aaa75afa11964b810))

* test(auth): add tests for group membership functionality ([`f9da740`](https://github.com/gsinghjay/mvp_qr_gen/commit/f9da7400ec4a59e80feed26a3e77e6d38f103aeb))

### Unknown

* Merge pull request #22 from gsinghjay/feat/portal-login

Add Portal Login Page Implementation (Task 1) ([`05029df`](https://github.com/gsinghjay/mvp_qr_gen/commit/05029df1cc0918d0bef50d0a9b6e4a1a89936418))


## v0.12.0 (2025-03-12)

### Chores

* chore: format with ruff and black ([`9d6c9f0`](https://github.com/gsinghjay/mvp_qr_gen/commit/9d6c9f09327a97fe4c5b64ad6fced96730db10ed))

### Documentation

* docs(tasks): update SSO implementation progress ([`8f0461a`](https://github.com/gsinghjay/mvp_qr_gen/commit/8f0461a33e532c4dd1da48e069dfcd07eb32ebe9))

### Features

* feat(router): integrate authentication router into application ([`ff07a3b`](https://github.com/gsinghjay/mvp_qr_gen/commit/ff07a3b4d00155d478f2a90d4ef79cce7bdac314))

* feat(auth): implement SSO login and callback endpoints ([`d27d7f8`](https://github.com/gsinghjay/mvp_qr_gen/commit/d27d7f8c9fb9e11254079d9ab0493d52606d72ef))

* feat(auth): implement SSO dependencies and configuration ([`db6cc74`](https://github.com/gsinghjay/mvp_qr_gen/commit/db6cc74a515673f8963ad4e783b5124dd2ea1be7))

### Fixes

* fix(tests): skip flaky middleware conditional activation test ([`5ecb61a`](https://github.com/gsinghjay/mvp_qr_gen/commit/5ecb61abf74bf1c6d0c8ed011a7ad2442988931e))

### Testing

* test(auth): add comprehensive tests for SSO endpoints ([`4d8646f`](https://github.com/gsinghjay/mvp_qr_gen/commit/4d8646f16eeb9508203a990379d3148151388c2e))

### Unknown

* Merge pull request #20 from gsinghjay/feat/sso

Add Microsoft SSO Integration ([`6178f5f`](https://github.com/gsinghjay/mvp_qr_gen/commit/6178f5f50c2e6022ba827b2392db447e959455f6))


## v0.11.0 (2025-03-12)

### Documentation

* docs(tests): enhance testing documentation with utility function examples ([`45b7645`](https://github.com/gsinghjay/mvp_qr_gen/commit/45b764596c2fc2aee3b6b21492fd80e22a3f0838))

### Features

* feat(tests): add validation utility functions for colors, URLs, and scan statistics ([`6f95507`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f9550721a5099cf676e38b8d2b201f9f6ee2b4b))

* feat(tests): add validation utility functions for colors, URLs, and scan statistics ([`c875961`](https://github.com/gsinghjay/mvp_qr_gen/commit/c875961d35efccf2e23f82998bf05f4a54291be7))

### Refactoring

* refactor(tests): update test files to use new validation utilities ([`a8e450a`](https://github.com/gsinghjay/mvp_qr_gen/commit/a8e450a805c59b88d0a0c4edde4e414aa42de109))

### Unknown

* Merge pull request #19 from gsinghjay/refactor/test-utils

Test Utilities Refactoring ([`81a740b`](https://github.com/gsinghjay/mvp_qr_gen/commit/81a740b4e194e3aaf460e9e976b7bf7c79a52b65))


## v0.10.0 (2025-03-12)

### Chores

* chore: remove obsolete optimization tasks file ([`807064b`](https://github.com/gsinghjay/mvp_qr_gen/commit/807064bfa8caa3afceb0e8a79eb65e6f6e739693))

* chore: updated docs ([`d06d707`](https://github.com/gsinghjay/mvp_qr_gen/commit/d06d707339b4f98a5c82c104a594f52be3b3cc7c))

### Documentation

* docs: update task tracking for completed test fixtures ([`f108ad5`](https://github.com/gsinghjay/mvp_qr_gen/commit/f108ad5fc04dcee276228d6405d3cc9672ce49ef))

* docs(tests): add comprehensive testing documentation ([`c99a1f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/c99a1f4b130c0d5389471139119700ca3ad308b6))

* docs: mark HTTP method decorator task as complete ([`388b56d`](https://github.com/gsinghjay/mvp_qr_gen/commit/388b56d5123d3f66ad8860d4b76b5dca59d3c06b))

### Features

* feat(tests): add reusable test utilities and assertions ([`7b01d4e`](https://github.com/gsinghjay/mvp_qr_gen/commit/7b01d4e8207f62c0cdbbfd227c2f9d9f8872b2c9))

* feat(tests): add comprehensive test fixtures for QR code testing ([`a99f12e`](https://github.com/gsinghjay/mvp_qr_gen/commit/a99f12eab8579215e0bfaf11eef04a9f7447bdb3))

### Refactoring

* refactor: update redirect endpoint with proper status code and response documentation ([`3cb20a9`](https://github.com/gsinghjay/mvp_qr_gen/commit/3cb20a90b2d572753ad6c67bf34eaa7ece81b942))

### Testing

* test: add HTTP method decorator tests ([`3008600`](https://github.com/gsinghjay/mvp_qr_gen/commit/3008600c453baa59c0ba8751adf5d571ec1349ac))

### Unknown

* Merge pull request #18 from gsinghjay/tests/fixtures

Test Infrastructure Enhancement ([`e153623`](https://github.com/gsinghjay/mvp_qr_gen/commit/e15362320fb2aa4cf34dc9c5a1ef3a768bdfa1f1))

* Merge pull request #15 from gsinghjay/refactor/http-decorators

HTTP Method Decorator Optimization ([`a77bf1b`](https://github.com/gsinghjay/mvp_qr_gen/commit/a77bf1b487c5315ebeb4ad6ec8548be0ae6e25ef))


## v0.9.0 (2025-03-10)

### Chores

* chore: following fastapi_optimization_tasks.md ([`ea3b248`](https://github.com/gsinghjay/mvp_qr_gen/commit/ea3b248a6d505013de66e4b5e1aa5db15a090874))

### Documentation

* docs(tasks): mark middleware simplification task as completed ([`5872a8e`](https://github.com/gsinghjay/mvp_qr_gen/commit/5872a8e2d589e741426b2e8ea7f7f38dee19169e))

### Features

* feat(app): implement modern lifespan approach for FastAPI lifecycle management ([`9a22572`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a2257218acd76bde99f42c97d78ce779b0de0df))

### Refactoring

* refactor(config): remove complex middleware configuration dictionary ([`1fc5b53`](https://github.com/gsinghjay/mvp_qr_gen/commit/1fc5b53e28a4158a956c893eddb8c14eb7991a87))

* refactor(app): replace custom middleware loader with direct FastAPI middleware calls ([`787e06b`](https://github.com/gsinghjay/mvp_qr_gen/commit/787e06b1b6f9eebd080ad4f23139d4968d030c2a))

### Testing

* test(middleware): add comprehensive tests for middleware functionality ([`00dd091`](https://github.com/gsinghjay/mvp_qr_gen/commit/00dd091912d66ae02b785acdf8948747cb19ae06))

### Unknown

* Merge pull request #14 from gsinghjay/feat/lifecycle-events

Implement Modern Lifespan Approach for FastAPI Lifecycle Management (Task 7) #5 ([`e965d1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/e965d1e124c111fac4cb9707863145bb0c681106))

* Merge pull request #13 from gsinghjay/refactor/middleware

Simplify Middleware Configuration ([`a6221b6`](https://github.com/gsinghjay/mvp_qr_gen/commit/a6221b6ac1de15526066a0a54b74fe41211a5c91))


## v0.8.0 (2025-03-10)

### Features

* feat(api): improve router tags and remove prefix duplication ([`de50cd4`](https://github.com/gsinghjay/mvp_qr_gen/commit/de50cd442e608142fac7f3d8026d8dfd35fdc082))

### Refactoring

* refactor(router): reorganize router initialization with proper parent routers ([`ca9af0f`](https://github.com/gsinghjay/mvp_qr_gen/commit/ca9af0f6bb5dac9601310c6b3a01c474c6d8538c))

### Testing

* test(router): add test_router_structure.py to verify API path accessibility ([`628be3d`](https://github.com/gsinghjay/mvp_qr_gen/commit/628be3d1d56e68e720a039bd25d5878417381adf))

### Unknown

* Merge pull request #12 from gsinghjay/refactor/router

Task 5: Restructure Router Hierarchy ([`ee2b5a2`](https://github.com/gsinghjay/mvp_qr_gen/commit/ee2b5a2b5deb8f5e319965e633ef5d5dffba6fff))


## v0.7.0 (2025-03-10)

### Build System

* build(deps): add aiosqlite dependency for async SQLite support ([`866c14f`](https://github.com/gsinghjay/mvp_qr_gen/commit/866c14f8f96611c463eaad99f22fb3ca54fad5eb))

### Documentation

* docs(refactor): mark dependency injection standardization task as completed ([`c033150`](https://github.com/gsinghjay/mvp_qr_gen/commit/c033150f728928ec181ac76d13467721825aa86f))

* docs: mark SQLite test refactoring tasks as completed ([`70c8b15`](https://github.com/gsinghjay/mvp_qr_gen/commit/70c8b15d5ded3d5d43b8c8e6c85014d53af2a7be))

* docs(scripts): update API test script documentation ([`67d3d5d`](https://github.com/gsinghjay/mvp_qr_gen/commit/67d3d5d0810a502cd17e42b6f439c199ff494dcf))

* docs: complete test refactoring plan ([`907c31e`](https://github.com/gsinghjay/mvp_qr_gen/commit/907c31ee297a7790d4f312ab2ce7ccd67f24f029))

### Features

* feat(core): add centralized exception handling system ([`1d59159`](https://github.com/gsinghjay/mvp_qr_gen/commit/1d5915998d5f311f86f504a5ad8f774cdff7eb0f))

* feat(schemas): update schema exports to include parameter models ([`a9c2f7e`](https://github.com/gsinghjay/mvp_qr_gen/commit/a9c2f7e6db72d760cc35589d336387eebbbd50c9))

* feat(validation): add parameter models with validation for QR code creation ([`989ae4d`](https://github.com/gsinghjay/mvp_qr_gen/commit/989ae4d974da4c22095541c4ece408f0d4e677f1))

* feat(tests): implement DependencyOverrideManager for standardized dependency injection ([`ca5011e`](https://github.com/gsinghjay/mvp_qr_gen/commit/ca5011e01d709c48ba1889b9bfd3c3b0709cc7eb))

* feat(tests): add helper functions for DRY test assertions ([`9fb6e87`](https://github.com/gsinghjay/mvp_qr_gen/commit/9fb6e87bbeb22991f28343635b2f0c9b17f3af1c))

* feat(tests): implement factory pattern for test data generation ([`86a93fe`](https://github.com/gsinghjay/mvp_qr_gen/commit/86a93fe9ecfe9afacce2d16612ba31540099f06f))

### Fixes

* fix(tasks): handle background task error states correctly ([`f79d1ed`](https://github.com/gsinghjay/mvp_qr_gen/commit/f79d1ed1e9a4b86785b73999a4173be42082c1f9))

* fix(api): update endpoint status codes to follow REST conventions ([`19b6246`](https://github.com/gsinghjay/mvp_qr_gen/commit/19b624678e684c96c0bbcce6177d756cd71ead8e))

* fix(services): convert HttpUrl to string before saving to database ([`ec2e4ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/ec2e4efa28cd475668e33d94b2ddab92891ed94d))

* fix(tests): improve concurrent reads test with session isolation ([`57aaf74`](https://github.com/gsinghjay/mvp_qr_gen/commit/57aaf74073bc2a869af06cdba0d686bdd9955b92))

* fix(qr): ensure dynamic QR codes always use redirect path as content ([`6e1398c`](https://github.com/gsinghjay/mvp_qr_gen/commit/6e1398cbcd316faea490e0565e9284638950f666))

* fix(tests): replace UTC import with timezone.utc for compatibility ([`dd5057a`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd5057ad9cc0591db8e6e15383390aa8cdfc17d6))

* fix(tests): resolve SQLite concurrency and WAL mode test failures ([`9d9e355`](https://github.com/gsinghjay/mvp_qr_gen/commit/9d9e355491d7b110b70016072b7605ed0d190871))

* fix(tests): update SQLite UTC functions to return consistent Z-suffix format ([`533028f`](https://github.com/gsinghjay/mvp_qr_gen/commit/533028fd3be0a9eac48ddb085507e835b7e1e34b))

* fix(health): adjust health service implementation for test compatibility ([`572262b`](https://github.com/gsinghjay/mvp_qr_gen/commit/572262b9666c445551f57880c2862511d4147fbf))

* fix(tests): update concurrent test assertion for dynamic test count ([`f6a243b`](https://github.com/gsinghjay/mvp_qr_gen/commit/f6a243bacb718c8ad4943de2c385bff74a7697ff))

* fix(tests): correct dependency injection and redirect status code in test_main.py ([`510cd23`](https://github.com/gsinghjay/mvp_qr_gen/commit/510cd239a27119fac8214c99003882687267b041))

### Refactoring

* refactor(routers): update QR routers to use parameter models ([`19ef336`](https://github.com/gsinghjay/mvp_qr_gen/commit/19ef3366795314f207897b5c555d3782c938a0f4))

* refactor(api): update API endpoints to use parameter models ([`18940cb`](https://github.com/gsinghjay/mvp_qr_gen/commit/18940cb7b98c29477518cbde9829de0da2a9d4c3))

* refactor(tests): parameterize QR service tests for better coverage ([`0e12eb4`](https://github.com/gsinghjay/mvp_qr_gen/commit/0e12eb4e59bf63e86d3dd9f233f1fa5df1f85e16))

* refactor(tests): parameterize validation tests to reduce duplication ([`3e19e04`](https://github.com/gsinghjay/mvp_qr_gen/commit/3e19e04e270392323c6f15266a3af96202ee5e07))

* refactor(tests): remove redundant real_db test files ([`618bb83`](https://github.com/gsinghjay/mvp_qr_gen/commit/618bb831779c318d8bcb5a619df9e37f911affca))

* refactor(tests): consolidate QR service tests from real_db variant ([`ed63efc`](https://github.com/gsinghjay/mvp_qr_gen/commit/ed63efcdf2975a6fe68a4efa04a290925e22778b))

* refactor(tests): enhance integration tests with consistent dependency handling ([`3c3b34e`](https://github.com/gsinghjay/mvp_qr_gen/commit/3c3b34e418140862664aef909ba68a8e65afc8fb))

* refactor(tests): improve background task testing with proper async handling ([`e56fdd4`](https://github.com/gsinghjay/mvp_qr_gen/commit/e56fdd45cb54255a6569c0f262d6fca0feaae29d))

* refactor(tests): improve database session management in conftest.py ([`abedc0b`](https://github.com/gsinghjay/mvp_qr_gen/commit/abedc0b430c68cc2a212eb80e8512910269225bf))

* refactor(tests): replace in-memory SQLite with file-based SQLite for integration tests ([`3ffb813`](https://github.com/gsinghjay/mvp_qr_gen/commit/3ffb8138ee4f5c3ea268c83812f0a30d625e4199))

### Testing

* test(framework): improve test fixtures and dependency overrides ([`c626f3e`](https://github.com/gsinghjay/mvp_qr_gen/commit/c626f3ef184533f8780aa5baa2cd8cc50a332340))

* test(integration): fix test assertions to expect correct status codes ([`5aa6b3d`](https://github.com/gsinghjay/mvp_qr_gen/commit/5aa6b3df1a15a335e2b3897808c7e491799ffd02))

* test(response): update response model tests for parameter validation ([`a7b342b`](https://github.com/gsinghjay/mvp_qr_gen/commit/a7b342b1c3698eefab1434ee1e212379f7a8531f))

* test(api): add comprehensive examples for dependency injection patterns ([`19d75fe`](https://github.com/gsinghjay/mvp_qr_gen/commit/19d75fe457fdc8116de9cf84112ea1e09d267467))

* test: implement response model validation tests ([`ad64279`](https://github.com/gsinghjay/mvp_qr_gen/commit/ad64279e2a3a772c85e988079de9e6ba9a3cd9c6))

* test: add unit tests for factory pattern implementation ([`59eb9e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/59eb9e392b6f48d2f476069009cd8fc533908f6e))

* test: add SQLite-specific functionality tests ([`0b41d74`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b41d748a1c49bcbe80a3819a6439b85514c7ea0))

* test: add real database tests for background tasks ([`2e5f81a`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e5f81a9219d46739f7789ced2b3991457753b83))

* test: add real database tests for QR service ([`59b792c`](https://github.com/gsinghjay/mvp_qr_gen/commit/59b792c9bb7253a992bada870594fc1d12d27854))

### Unknown

* Merge pull request #11 from gsinghjay/refactor/testing

Completed Tasks from refactor_testing.md ([`bda6331`](https://github.com/gsinghjay/mvp_qr_gen/commit/bda6331a06a1dc66271f631fc8752c53657bbeb2))

* Merge pull request #10 from gsinghjay/refactor/test-sqlite-file-based

Replace In-Memory SQLite with File-Based SQLite for Integration Tests ([`74c4ff9`](https://github.com/gsinghjay/mvp_qr_gen/commit/74c4ff9e95f8990fecf793d035a5c8fbd81d0e97))


## v0.6.0 (2025-03-05)

### Features

* feat(frontend): implement deleteQR function in API service ([`abe628c`](https://github.com/gsinghjay/mvp_qr_gen/commit/abe628cbfc049a47c02f8196fb0ce077c94ad727))

* feat(api): add DELETE endpoint for QR codes ([`675041f`](https://github.com/gsinghjay/mvp_qr_gen/commit/675041f63ecac96eadcfb90e500064d716aa6a06))

* feat(qr): add delete_qr method to QRCodeService ([`3b1f563`](https://github.com/gsinghjay/mvp_qr_gen/commit/3b1f56384cb705fe80f92f43e1188ce42d1131c7))

* feat(background-tasks): implement non-blocking scan statistics updates ([`e57f3c6`](https://github.com/gsinghjay/mvp_qr_gen/commit/e57f3c69d204445c95d7222aecb7fade4d3c85a4))

### Testing

* test(background-tasks): add comprehensive tests for background task functionality ([`126f058`](https://github.com/gsinghjay/mvp_qr_gen/commit/126f0588fdb7ab89b305e60430f24ab5509d85e1))

### Unknown

* Merge pull request #9 from gsinghjay/feat/bgtasks

FastAPI Optimization Tasks - Task 2 ([`32d2048`](https://github.com/gsinghjay/mvp_qr_gen/commit/32d204889b642a45c65003a9a797e4b52ca7b7d4))


## v0.5.1 (2025-03-03)

### Chores

* chore: added curl test workflow ([`2e8dca9`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e8dca9e8eea26aec9b9dc66c6b218870a9b719e))

### Fixes

* fix(api): improve test reliability for background tasks ([`e48a250`](https://github.com/gsinghjay/mvp_qr_gen/commit/e48a2500adc20db32af3e9b426d16fdd0e4e7bbe))

* fix(api): resolve dependency import issues and optimize database operations

- Fix import path for get_db dependency in redirect router
- Implement optimized database operations with retry functionality
- Enhance error handling for database operations
- Improve concurrency handling with SQLite ([`ad0c6d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/ad0c6d2c353a63bd691a85cfda299b105bea46b0))

### Refactoring

* refactor: reorganize models and schemas into modular directory structure ([`80ceae6`](https://github.com/gsinghjay/mvp_qr_gen/commit/80ceae651afb2a64d02db880500a08e8fe94054e))

### Testing

* test: add tests for refactored models and schemas ([`f5a6813`](https://github.com/gsinghjay/mvp_qr_gen/commit/f5a681318a9a9983dee13bbf64de8488687ed018))

### Unknown

* Merge pull request #8 from gsinghjay/refactor/models-schemas

Refactor Models and Schemas into Modular Directory Structure ([`189b03c`](https://github.com/gsinghjay/mvp_qr_gen/commit/189b03cd8a4857bf4d888a91487a2f00bd745baf))


## v0.5.0 (2025-03-03)

### Chores

* chore(deps): add psutil dependency for system metrics collection ([`e95135f`](https://github.com/gsinghjay/mvp_qr_gen/commit/e95135f35a518e8494f68f8e65478a8fc030d1ed))

* chore(services): update service module initialization ([`21af576`](https://github.com/gsinghjay/mvp_qr_gen/commit/21af576017e5b033af6dd56b0a2269c890599ab2))

### Features

* feat(app): configure health check endpoints and exception handling ([`3818fa7`](https://github.com/gsinghjay/mvp_qr_gen/commit/3818fa723169bfb91120d29703d16425d662a94b))

* feat(routers): register health check router in the application ([`0cfe182`](https://github.com/gsinghjay/mvp_qr_gen/commit/0cfe18210b3d18916d76b0761213c73fa1d50ede))

* feat(schemas): add health check response models and status enums ([`08f36e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/08f36e35c5e10c749394b2838697a741d3ecb35e))

* feat(health): implement synchronous health check service and endpoints ([`c42cf07`](https://github.com/gsinghjay/mvp_qr_gen/commit/c42cf07120dd1e62715dd615f1f8da15cf052013))

### Fixes

* fix(database): resolve dependency injection pattern for FastAPI compatibility ([`adc806c`](https://github.com/gsinghjay/mvp_qr_gen/commit/adc806c3d26d775c7521d4a30f3ea7ee0860a379))

### Testing

* test(health): add tests for health check endpoints ([`856e535`](https://github.com/gsinghjay/mvp_qr_gen/commit/856e5356b6b0a68b673bcc4c5dca26d6c03dd758))

### Unknown

* Merge pull request #6 from gsinghjay/feat/health

Enhance health check implementation and database dependency injection ([`3d4886d`](https://github.com/gsinghjay/mvp_qr_gen/commit/3d4886df4c1bab2ad3d5f99b778642fd98161921))


## v0.4.0 (2025-03-03)

### Chores

* chore: formatted more files with black ([`0cc520a`](https://github.com/gsinghjay/mvp_qr_gen/commit/0cc520a8bf59bd79c9b9217c9b287a7bcb419859))

* chore: added SPEC.md and formatted files with black ([`224f01a`](https://github.com/gsinghjay/mvp_qr_gen/commit/224f01ad3e0e17f767d705e14e617e3f7774f72e))

### Documentation

* docs(story): update story to reflect the status of the project ([`b453d98`](https://github.com/gsinghjay/mvp_qr_gen/commit/b453d9834aa81889dc804ccfadc2b37c7bac45c6))

* docs(infrastructure): update infrastructure documentation ([`a86cdf1`](https://github.com/gsinghjay/mvp_qr_gen/commit/a86cdf1016ad29a0aba50734033dadefad1cbf04))

* docs: add static folder documentation and update main README ([`65b9a0f`](https://github.com/gsinghjay/mvp_qr_gen/commit/65b9a0f9d00a36d21e7179d0a944b7b844675c8a))

* docs: update main README with project changes ([`0ff5630`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ff56304d459df90f3ee56487c7362762c8a2be8))

### Features

* feat(api): implement health check endpoint and improve error handling ([`3560143`](https://github.com/gsinghjay/mvp_qr_gen/commit/356014394e5a6b7d2ce9f86f8ccd30115f359c20))

* feat(api): implement QRCodeService for service-layer dependency injection ([`9a1e259`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a1e25951f7074138e67948a4429c542ab0499cb))

### Fixes

* fix(scripts): enhance database management script for reliability ([`ddea10e`](https://github.com/gsinghjay/mvp_qr_gen/commit/ddea10eb5cab91e901cc70fc4c00351c2bcc960d))

* fix(web): update web pages router to use new dependency injection pattern ([`1ba68d3`](https://github.com/gsinghjay/mvp_qr_gen/commit/1ba68d30e04bb591d9b2cfbc8d7efc7d5f8f9672))

* fix(database): resolve database initialization and connection issues ([`81d0aed`](https://github.com/gsinghjay/mvp_qr_gen/commit/81d0aed872a39427ce6619a09f683461dd1a9b47))

* fix(schemas): update QRCodeCreate schema to include qr_type field ([`c977c39`](https://github.com/gsinghjay/mvp_qr_gen/commit/c977c394f1b64afa93bb884a53cc66f47e33acc6))

### Refactoring

* refactor(service): remove deprecated service file in favor of new service layer ([`8717ec9`](https://github.com/gsinghjay/mvp_qr_gen/commit/8717ec9f5208c3c449efb0619b5ed800ed18b1f3))

* refactor(models): update database models for improved schema integrity ([`bb64fb2`](https://github.com/gsinghjay/mvp_qr_gen/commit/bb64fb2c231e5de970a94edf54537323949dca24))

* refactor(middleware): optimize middleware configuration and implementation ([`c2bb364`](https://github.com/gsinghjay/mvp_qr_gen/commit/c2bb364bd1fdb9d8155898cda1e11d25e8e4a086))

* refactor(api): update API endpoints to use QRCodeService ([`9569d11`](https://github.com/gsinghjay/mvp_qr_gen/commit/9569d1164bcc87abc21b559be4ae942f62a20ece))

* refactor(routers): update QR routers to use service layer ([`cbddae0`](https://github.com/gsinghjay/mvp_qr_gen/commit/cbddae03ab594311ea658d9425a4295f10265133))

* refactor(security): enforce HTTPS and improve code quality

- feat(security): enforce HTTPS for all routes and redirects
- refactor(schemas): update to Pydantic V2 style validators
- refactor(imports): fix incorrect database dependency imports
- style(formatting): apply Black code formatting
- style(lint): fix Ruff linting issues
- docs(comments): improve docstrings and comments ([`3e304ea`](https://github.com/gsinghjay/mvp_qr_gen/commit/3e304ea7d968e1e07adb25e49b8d064f7d263f79))

### Testing

* test(api): refactor API tests to use proper dependency injection ([`cb8ad76`](https://github.com/gsinghjay/mvp_qr_gen/commit/cb8ad764704eed63d809c662149f76ab5c832b57))

* test(integration): update integration tests to use test database session ([`eace9b9`](https://github.com/gsinghjay/mvp_qr_gen/commit/eace9b9cd9d4c989f24b4e18726697907a2a25f3))

* test(api): add service layer tests and integration tests ([`5d1ec4e`](https://github.com/gsinghjay/mvp_qr_gen/commit/5d1ec4e8da6a758d00cdc4b0defae0aa5db842f1))

### Unknown

* Merge pull request #4 from gsinghjay/refactor/deps

FastAPI Optimization Tasks - Task 1 ([`b912b63`](https://github.com/gsinghjay/mvp_qr_gen/commit/b912b6380cc743c839eece92e2c544f6b5fb3e34))


## v0.3.3 (2025-02-20)

### Chores

* chore: add development tools (black, ruff, mypy) with configurations ([`700ffc4`](https://github.com/gsinghjay/mvp_qr_gen/commit/700ffc48d764a68cb8838ae5b177a2d805dd54a6))

### Fixes

* fix(security): enforce HTTPS for static files and standardize code formatting ([`6c8237e`](https://github.com/gsinghjay/mvp_qr_gen/commit/6c8237e85e4397391230fd64767db9aaf7324536))


## v0.3.2 (2025-02-20)

### Chores

* chore: ignore certificates directory for local development ([`df07a97`](https://github.com/gsinghjay/mvp_qr_gen/commit/df07a97dc92e0894fecb4fc87e76835061457660))

### Fixes

* fix(frontend): update API calls and URL handling for HTTPS support ([`566c6ad`](https://github.com/gsinghjay/mvp_qr_gen/commit/566c6ad6b18786ead4ae968d110214ad60e64fbd))

* fix(backend): enforce HTTPS for static files and template URLs ([`d6279ea`](https://github.com/gsinghjay/mvp_qr_gen/commit/d6279ea5837b48fa300378e40373df4782ef19eb))

* fix(infra): configure traefik for HTTPS and CORS handling ([`a99faa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/a99faa0cab94e48089b3c4ea158c7f16d2cabe23))

### Unknown

* Merge pull request #3 from gsinghjay/fix/https-static-files

Fix HTTPS Support and Mixed Content Issues ([`00c5f2d`](https://github.com/gsinghjay/mvp_qr_gen/commit/00c5f2dc142d5a7da34ad908676c3f6b6963f2ea))


## v0.3.1 (2025-02-20)

### Fixes

* fix(db): ensure database initialization completes before app startup ([`c703557`](https://github.com/gsinghjay/mvp_qr_gen/commit/c703557e11c5c0e6219f8f8658f2646ca39f1f47))


## v0.3.0 (2025-02-20)

### Chores

* chore: updated project status ([`23f72d1`](https://github.com/gsinghjay/mvp_qr_gen/commit/23f72d1202a0c29f58c8bf8bd01265ec854699a0))

### Code Style

* style(ui): optimize CSS with better table styling and empty state improvements ([`4da8113`](https://github.com/gsinghjay/mvp_qr_gen/commit/4da8113479349dae22e395f8c9716d98c91c4867))

### Features

* feat(api): enhance API service with comprehensive TypeScript documentation and error handling ([`f79a141`](https://github.com/gsinghjay/mvp_qr_gen/commit/f79a141f0e3ddaab2d8447bd801d086bc07293bb))

### Refactoring

* refactor(ui): streamline QR list section with improved header and search functionality ([`5f037e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/5f037e438c304fad373324aa31df9ae3866d817e))

### Unknown

* Merge pull request #2 from gsinghjay/refactor/style

UI Improvements and API Service Enhancement ([`b174987`](https://github.com/gsinghjay/mvp_qr_gen/commit/b1749870336b5a061c4a9c557e041a01ae841441))


## v0.2.0 (2025-02-20)

### Features

* feat(routers): add modular router structure for API, web, and QR code operations ([`546a37b`](https://github.com/gsinghjay/mvp_qr_gen/commit/546a37b5e2dc8219e03722083766881a25030d3d))

### Refactoring

* refactor(main): migrate routes to dedicated router modules ([`4b528f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/4b528f42e0ab0b0a16ea857183984170e8658ce2))

* refactor(db): improve database session handling and error logging ([`db4e237`](https://github.com/gsinghjay/mvp_qr_gen/commit/db4e2370ee2cb41cb4bd49062111db7eb161cfc4))

### Testing

* test(config): update test configuration for router migration ([`bbfc084`](https://github.com/gsinghjay/mvp_qr_gen/commit/bbfc084fde71f1a0581b019cae0848395802d4b5))

### Unknown

* Merge pull request #1 from gsinghjay/refactor/routers

Router Migration and Code Organization Improvements ([`4fb1cf9`](https://github.com/gsinghjay/mvp_qr_gen/commit/4fb1cf941b11d0780a722bb150a8999451528796))

* Merge branch 'main' of github.com:gsinghjay/mvp_qr_gen ([`48d57ee`](https://github.com/gsinghjay/mvp_qr_gen/commit/48d57eef6fd69ad47f0d512cebc00db637e9707a))


## v0.1.0 (2025-02-19)

### Chores

* chore: update gitignore to exclude private development files ([`4b2aaf9`](https://github.com/gsinghjay/mvp_qr_gen/commit/4b2aaf9830d483ce3cd145d14d9be8461c5ce859))

* chore(config): add project dependencies and configuration files ([`52205ac`](https://github.com/gsinghjay/mvp_qr_gen/commit/52205aca5685a03a05589e9a7d735657ca977e8a))

* chore(infra): add docker and traefik configuration files ([`6d81d8a`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d81d8a9232c833199d1a1afba0101806270ddf9))

### Continuous Integration

* ci: add semantic release workflow ([`f621e30`](https://github.com/gsinghjay/mvp_qr_gen/commit/f621e30abcb1f79697b095b31f1d61a0d600b5a1))

### Documentation

* docs: update project documentation and status ([`67a4b13`](https://github.com/gsinghjay/mvp_qr_gen/commit/67a4b13c1c92e56562e9a56cea433670f9f75eb1))

* docs: add project documentation, research, and development tools configuration ([`d66da94`](https://github.com/gsinghjay/mvp_qr_gen/commit/d66da945f35f220a568948de0805071c5c4affff))

### Features

* feat(app): add initial application code and API tests ([`dd1104c`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd1104ca30251934093c7d3f1f7f924645d6eea7))

* feat(db): add alembic migration configuration and scripts ([`80d2be2`](https://github.com/gsinghjay/mvp_qr_gen/commit/80d2be2e0893b6bde2046c1adf06bc78a52d7bb6))

### Testing

* test: remove redundant test_api_endpoints.py ([`44b8941`](https://github.com/gsinghjay/mvp_qr_gen/commit/44b8941cfa3917ddd9c2645148544e1e059e2825))
