# CHANGELOG


## v0.31.2 (2025-05-24)

### Bug Fixes

- Remove docs/ references from wiki automation
  ([`00448ea`](https://github.com/gsinghjay/mvp_qr_gen/commit/00448ea6d9ef0ab1865c6016a172a614f4621a94))

### Documentation

- Remove memory-bank from public repository
  ([`1feb276`](https://github.com/gsinghjay/mvp_qr_gen/commit/1feb2764c92082d9fdf53cd57498146bc07a2b4e))

- Test auto-sync workflow trigger
  ([`b6da892`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6da892683910b3ac46c9633ced96f71ff2b318d))


## v0.31.1 (2025-05-24)

### Bug Fixes

- Update wiki workflow to use personal access token for wiki permissions
  ([`d47e7dc`](https://github.com/gsinghjay/mvp_qr_gen/commit/d47e7dc7d113b07ad2a84fb280b957ed13b02e42))

### Documentation

- Update memory bank with GitHub wiki integration and CORS fixes
  ([`781071e`](https://github.com/gsinghjay/mvp_qr_gen/commit/781071e54d8a489b3036e00d12eb4ac9787a8eeb))


## v0.31.0 (2025-05-24)

### Bug Fixes

- Enhance CORS headers for Grafana RSS feeds and external resources
  ([`7e30a33`](https://github.com/gsinghjay/mvp_qr_gen/commit/7e30a33ab024dfeb11a28b99a7c52635bb6ae3fb))

### Chores

- Update gitignore to keep docs folder ignored while supporting wiki system
  ([`43ff926`](https://github.com/gsinghjay/mvp_qr_gen/commit/43ff9262f6d937eafb254ae535e3a12f8abdb83a))

### Continuous Integration

- Add automated wiki documentation sync workflow
  ([`87dd2fa`](https://github.com/gsinghjay/mvp_qr_gen/commit/87dd2fad51845c0f5c8f1b9447e2ae379a60ca58))

### Documentation

- Add comprehensive GitHub wiki maintenance guide
  ([`1a9722c`](https://github.com/gsinghjay/mvp_qr_gen/commit/1a9722cbf067c731e68772d218387c51409b19c5))

- Update README to reference GitHub wiki instead of ignored docs directory
  ([`241d587`](https://github.com/gsinghjay/mvp_qr_gen/commit/241d587a497984f3bb3843146d63e46e3e4fc9d3))

### Features

- Add wiki maintenance script for documentation sync
  ([`651d754`](https://github.com/gsinghjay/mvp_qr_gen/commit/651d754eb4aba0de6b23d0d9168c68be0fc49e62))


## v0.30.0 (2025-05-24)

### Bug Fixes

- Update analytics dashboard queries to prevent NaN values
  ([`308679b`](https://github.com/gsinghjay/mvp_qr_gen/commit/308679bae6562ff0590055090e56fda7e127738d))

- Update QR system health dashboard queries with proper fallbacks
  ([`d54fa08`](https://github.com/gsinghjay/mvp_qr_gen/commit/d54fa080263bcfe83a62d19dbf72b174179bbdec))

- Update refactoring progress dashboard with extended time windows
  ([`721b3be`](https://github.com/gsinghjay/mvp_qr_gen/commit/721b3bedb02cde8ed1a61dd99a9c8491b35a5263))

### Chores

- Add cursor indexing ignore configuration
  ([`86b92b7`](https://github.com/gsinghjay/mvp_qr_gen/commit/86b92b7cd07d9c038ae511ad47940c624942fe93))

- Add monitoring service directories to gitignore
  ([`0b39eb7`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b39eb71772b2ac3c40b1cb58a2a4bc8ce0ba024))

### Documentation

- Add comprehensive Grafana monitoring guide for college staff
  ([`99ebdf9`](https://github.com/gsinghjay/mvp_qr_gen/commit/99ebdf9231b51198f664a06c0b23a2e6f8fc6a84))

- Add memory bank documentation for project context
  ([`8226ae8`](https://github.com/gsinghjay/mvp_qr_gen/commit/8226ae866f3e19a6bf959cb68920a95047b17e63))

- Add Observatory-First monitoring features to README
  ([`d512caa`](https://github.com/gsinghjay/mvp_qr_gen/commit/d512caa4dcb0b0fdfd7b745941209520e1a9e705))

- **memory-bank**: Update Observatory-First monitoring progress and CORS implementation
  ([`453c9e7`](https://github.com/gsinghjay/mvp_qr_gen/commit/453c9e71dafd783ac62688b9b38f8c86fd9d6b3a))

### Features

- Add alerting and SLA overview dashboard for compliance monitoring
  ([`164d71f`](https://github.com/gsinghjay/mvp_qr_gen/commit/164d71f9477f1f1be4834f81931765b6ae4ac1fd))

- Add circuit breaker and feature flag monitoring dashboard
  ([`05ca07a`](https://github.com/gsinghjay/mvp_qr_gen/commit/05ca07a955ee167d70c58f0423ae0bb1f9ad19ac))

- Add detailed refactoring analysis dashboard for technical monitoring
  ([`4855fb3`](https://github.com/gsinghjay/mvp_qr_gen/commit/4855fb3832f73d5066596c06cc52a59f0604009b))

- Add Grafana dashboards and datasource configurations
  ([`7be3f5b`](https://github.com/gsinghjay/mvp_qr_gen/commit/7be3f5b66d8c613102aa40083a7067e6905ed952))

- Add Grafana routing configuration to Traefik
  ([`6d21185`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d21185d699088474654a029f9db57e13778f2f9))

- Add Grafana, Loki, and Promtail services for monitoring
  ([`0ddcbed`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ddcbed492c1c22c0a51ff4aef76d72c7209b19a))

- Add infrastructure deep dive dashboard for resource monitoring
  ([`dd57c1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd57c1e7b45d97f30ade685133b920d50aad90f6))

- Add Loki configuration for log aggregation
  ([`dd286fa`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd286faf840f2a6553049eb2b6da59d06b565441))

- Add Prometheus configuration for metrics collection
  ([`7ddf6eb`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ddf6ebe6c75f1571728429caaed1b9b84ef5a5c))

- Add Promtail configuration for log shipping
  ([`3236b2e`](https://github.com/gsinghjay/mvp_qr_gen/commit/3236b2e9e5bfda8f20a733377b8a7d9f6a356d49))

- Add user experience monitoring dashboard for UX tracking
  ([`25ed35f`](https://github.com/gsinghjay/mvp_qr_gen/commit/25ed35fbe9299cebd019ccacb2acaba2de2195cc))

- **grafana**: Configure CORS support for cross-origin requests
  ([`c493413`](https://github.com/gsinghjay/mvp_qr_gen/commit/c493413c723983ba0a41474d03013354bfc2047a))

- **infrastructure**: Add Prometheus, Grafana, Loki monitoring stack to Docker Compose
  ([`8c290b2`](https://github.com/gsinghjay/mvp_qr_gen/commit/8c290b240f5059f6d699365e870333ce8c46e00e))

- **monitoring**: Add Grafana alerting configuration for comprehensive monitoring
  ([`5ab0dbf`](https://github.com/gsinghjay/mvp_qr_gen/commit/5ab0dbf813ac56479dce86a1f77e5d999f875087))

- **monitoring**: Add Observatory-First alert system with 8 critical rules
  ([`89f98d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/89f98d285d9ea974596648599edb684d38934e30))

- **scripts**: Add alert testing and monitoring utility scripts
  ([`d27d8a4`](https://github.com/gsinghjay/mvp_qr_gen/commit/d27d8a415ccd8a79f7ec53448dea3333cee74a53))

- **traefik**: Add CORS support for Grafana with dedicated middleware
  ([`40f87a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/40f87a7472186d479eda8dafb79cd885179d380e))


## v0.29.0 (2025-05-23)

### Documentation

- Update test API readme with production hardening and classroom-optimized rate limiting
  ([`38a73f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/38a73f70a1e1cd0bcd75c6ee2e5057eb6c0aadf1))

### Features

- **config**: Add ALLOWED_REDIRECT_DOMAINS setting with environment variable parsing
  ([`63cfc05`](https://github.com/gsinghjay/mvp_qr_gen/commit/63cfc05659c8361ee0b36c740889f9a6d479f3be))

- **docker**: Add ALLOWED_REDIRECT_DOMAINS environment variable to api service
  ([`d960b09`](https://github.com/gsinghjay/mvp_qr_gen/commit/d960b09eeb50fbbf13ca1f7a63cf76f2f2719d2b))

- **security**: Add comprehensive input validation and error handling to redirect endpoint
  ([`2f21cad`](https://github.com/gsinghjay/mvp_qr_gen/commit/2f21cad962fcfae64cdd1d99ec8c33ea6de3087a))

- **security**: Adjust rate limiting to 60/min average with 10 burst for better abuse prevention
  ([`9ae5592`](https://github.com/gsinghjay/mvp_qr_gen/commit/9ae55929c2f4967890adafd128e85d9961c57a3e))

- **security**: Implement classroom-friendly rate limiting for QR redirects
  ([`4508517`](https://github.com/gsinghjay/mvp_qr_gen/commit/45085173a55f9f5f7cbbd243fccec39c591b63a1))

- **security**: Implement URL safety validation and background task error handling
  ([`fa025a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/fa025a75cd27c276578d0b669bc7e118003998b2))

### Testing

- Add comprehensive security tests and fix domain validation in update test
  ([`cc78161`](https://github.com/gsinghjay/mvp_qr_gen/commit/cc781616c9577dde005e97f668ca192f0948ef2a))

- Enhance rate limiting tests for differentiated QR vs API access patterns
  ([`8d36f1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/8d36f1e62d531bc55524d82d78299ecf3b096b71))


## v0.28.0 (2025-05-23)

### Bug Fixes

- Correct test_db fixture naming in conftest.py
  ([`1e784f8`](https://github.com/gsinghjay/mvp_qr_gen/commit/1e784f853ab1fb70a991918b5fe2b2208db985c1))

- Update QR service tests for repository pattern
  ([`eed680a`](https://github.com/gsinghjay/mvp_qr_gen/commit/eed680a9ef0e89b3b821951ec68507904963895e))

### Documentation

- Enhance README with architecture and flow diagrams
  ([`c09999a`](https://github.com/gsinghjay/mvp_qr_gen/commit/c09999a88e8acc77820b954c604af5144f8a091f))

- Remove INFRASTRUCTURE.md in favor of README diagrams
  ([`755f4e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/755f4e37c0eb2282b9f372b9edfae160dc2e0828))

- Remove STORY.md in favor of README diagrams
  ([`69236c5`](https://github.com/gsinghjay/mvp_qr_gen/commit/69236c550c1f2fe608f8a9bf92598f7b55ead9e5))

- Update testing best practices in README.md
  ([`7211d95`](https://github.com/gsinghjay/mvp_qr_gen/commit/7211d95af5b94243951498d2f56adf832391cc54))

### Features

- Add dedicated tests for HTMX fragment endpoints
  ([`cfef808`](https://github.com/gsinghjay/mvp_qr_gen/commit/cfef808fe1ed3ed9a984a88bd48556eb178df63e))

- Implement comprehensive QR code endpoint tests
  ([`360fbc0`](https://github.com/gsinghjay/mvp_qr_gen/commit/360fbc0adf9fbb6c8463a732325a0ca241027286))

### Refactoring

- Align dependency injection with test_db fixture
  ([`a551f88`](https://github.com/gsinghjay/mvp_qr_gen/commit/a551f8855ca6e705d41af6ed7c87d28febbbb4d3))

- Remove async example tests for proper async implementation
  ([`9f338d6`](https://github.com/gsinghjay/mvp_qr_gen/commit/9f338d6c10a5a6abe6b6e78f7b39a639bb0c12e8))

- Remove general API tests for module-specific tests
  ([`3d94fcc`](https://github.com/gsinghjay/mvp_qr_gen/commit/3d94fcc34610fc4a2de2e7479660862fbfe4a4e7))

- Remove generic background tasks tests for endpoint-specific tests
  ([`5d99dea`](https://github.com/gsinghjay/mvp_qr_gen/commit/5d99dea6b40257061bcb39f352e7c2c04a48dae4))

- Remove generic exception tests for endpoint-specific tests
  ([`18fee7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/18fee7d3c8b726dd092f29129e7d28afa8b5f7fa))

- Remove generic HTTP method tests for endpoint-specific tests
  ([`fddb5be`](https://github.com/gsinghjay/mvp_qr_gen/commit/fddb5bed707f5ec3517f16ff6b67dc62d004a784))

- Remove generic response model tests for endpoint-specific tests
  ([`ab17955`](https://github.com/gsinghjay/mvp_qr_gen/commit/ab1795527ded2bc20b4f7f427ae64a2f394fec0d))

- Remove generic validation tests for endpoint-specific tests
  ([`dc61591`](https://github.com/gsinghjay/mvp_qr_gen/commit/dc61591cba178ec801f600d30f9e5688712eec29))

- Remove placeholder repository integration tests
  ([`51ebdba`](https://github.com/gsinghjay/mvp_qr_gen/commit/51ebdbad59e480d2d710d09b43f9993fc73aa9d2))

- Remove redundant API restructure tests
  ([`2dda5e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/2dda5e489547b79a34ceafa5efb0717a8db73313))

- Remove router structure tests for endpoint-specific tests
  ([`d378a78`](https://github.com/gsinghjay/mvp_qr_gen/commit/d378a78c17ee8c632ec5c88390b6f0b00de04f8b))

- Remove test factories examples after factory implementation
  ([`c0c79d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/c0c79d2474e4e9bc55c982863fcb5ee12ef0ce69))

- Replace Font Awesome icons with Bootstrap Icons in device stats fragment
  ([`6f66af7`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f66af70c8103ea4cf8115eef475cac57fda6e4c))

- Update API test module imports
  ([`1259e3f`](https://github.com/gsinghjay/mvp_qr_gen/commit/1259e3f2c47403845fa624fcdbebdb9c056ea741))

### Testing

- Add comprehensive unit tests for QR service with mock and real DB approaches
  ([`94d2dfc`](https://github.com/gsinghjay/mvp_qr_gen/commit/94d2dfc503630e3c698bc15e32fdf88ae68a2b08))

- Add integration tests for health check API endpoints
  ([`e610727`](https://github.com/gsinghjay/mvp_qr_gen/commit/e61072766384455714393b4d168056b266c4cbaa))

- Add unit tests for health API endpoint with mocking
  ([`6a44b35`](https://github.com/gsinghjay/mvp_qr_gen/commit/6a44b35e58fac51be0fe51d9e9f6983a6b7da7b2))

- Add unit tests for health service with mocking
  ([`779c880`](https://github.com/gsinghjay/mvp_qr_gen/commit/779c8804a4cd8d963c8379c17f2158a22b437165))

- Remove old QR service test file (replaced by test_qr.py)
  ([`bd38bc1`](https://github.com/gsinghjay/mvp_qr_gen/commit/bd38bc1b2370b7cf52c3405bcb57e49a002a2a2a))


## v0.27.0 (2025-05-21)

### Bug Fixes

- Add missing model_class parameter to ScanLogRepository.__init__
  ([`4249da3`](https://github.com/gsinghjay/mvp_qr_gen/commit/4249da376221d9e05be3a441370140ce2724d812))

- Update integration test package initialization
  ([`04467b5`](https://github.com/gsinghjay/mvp_qr_gen/commit/04467b57f22e51462f6a703e6afdb6b835b9c2cc))

### Chores

- Update .gitignore file
  ([`35bb6e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/35bb6e4d51793c3ea996dd73e68074678cc97eab))

### Features

- Implement QRCodeRepository in dedicated file per phase-1 plan
  ([`88a3458`](https://github.com/gsinghjay/mvp_qr_gen/commit/88a34584e93ba64dc0f089fdbc6c9fcb105f0aa5))

- Implement ScanLogRepository for specialized scan log operations
  ([`0adb494`](https://github.com/gsinghjay/mvp_qr_gen/commit/0adb494fa092a73b233890181f49f0edbdcc52ba))

- Implement service layer coordination between repositories
  ([`168d2f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/168d2f426169eca08e94f9f631e95183fca5c4e2))

- Update repository exports to include ScanLogRepository
  ([`36e7fa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/36e7fa002e2b08fe7572d381979ee589d71eb70a))

### Refactoring

- Consolidate security headers to Traefik
  ([`a043411`](https://github.com/gsinghjay/mvp_qr_gen/commit/a0434112620e7f59fd037b439bc3644fff10de41))

- Modify existing QRRepository for backward compatibility
  ([`56d2186`](https://github.com/gsinghjay/mvp_qr_gen/commit/56d218688ae98afdb93679772b2d0245c6f8e531))

- Update dependencies to use new repository structure
  ([`96a1626`](https://github.com/gsinghjay/mvp_qr_gen/commit/96a1626c210c96e694e91f5143c92751e7726c1e))

- Update repository exports for clearer naming
  ([`a2b62af`](https://github.com/gsinghjay/mvp_qr_gen/commit/a2b62afd4566e5708727a817a427d29f59a4b490))

- Update repository exports to include new QRCodeRepository
  ([`9480e28`](https://github.com/gsinghjay/mvp_qr_gen/commit/9480e2884b7f3c157f451ec1d2b2af858205a222))

- Update type aliases for new repository naming
  ([`d9b0b83`](https://github.com/gsinghjay/mvp_qr_gen/commit/d9b0b832dfac4d14be2ac8e354a6b6f12ae4f8bc))

- **api**: Update fragments endpoints to use specialized repositories
  ([`38ca2ee`](https://github.com/gsinghjay/mvp_qr_gen/commit/38ca2eef62a6567ab1bfbd2e58e9f7e19cef93ae))

- **deps**: Update dependencies to use specialized repositories
  ([`7ba3d01`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ba3d01a59069129f07a612dc342e8ea6ff525f0))

- **main**: Update imports to use specialized repositories
  ([`64ffef0`](https://github.com/gsinghjay/mvp_qr_gen/commit/64ffef07833f3fe491a7db6ac0a54ed7dc5f9170))

- **repos**: Remove deprecated qr_repository.py
  ([`b6bcf62`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6bcf6259850a99e34202ffb7e13126cf9d80a8d))

- **repos**: Update __init__.py to export only specialized repositories
  ([`97fe612`](https://github.com/gsinghjay/mvp_qr_gen/commit/97fe612def15d160b9e5d9d72d6b9e258c651aa0))

- **service**: Update QRCodeService to use specialized repositories
  ([`3c0573d`](https://github.com/gsinghjay/mvp_qr_gen/commit/3c0573df842442f4e40bb1e0cfb9ec06ed82ce9d))

- **types**: Update type definitions to use specialized repositories
  ([`de22c7e`](https://github.com/gsinghjay/mvp_qr_gen/commit/de22c7ed8a53df296a613b3338f3c1ed094cf072))

### Testing

- Add integration test directory structure for repositories
  ([`be295de`](https://github.com/gsinghjay/mvp_qr_gen/commit/be295deb762203148a48d0419eb716c206f3b658))

- Add unit tests for new QRCodeRepository implementation
  ([`a8c0835`](https://github.com/gsinghjay/mvp_qr_gen/commit/a8c0835946a20720c6c0836e89ffff57757a2f48))


## v0.26.2 (2025-05-21)

### Bug Fixes

- Address 401 errors in test script by adding Host headers
  ([`8f7675b`](https://github.com/gsinghjay/mvp_qr_gen/commit/8f7675bf739f91cd0504491abff23f3cbba0987f))


## v0.26.1 (2025-05-21)

### Bug Fixes

- Improve error handling and reliability in performance test script
  ([`cd1e977`](https://github.com/gsinghjay/mvp_qr_gen/commit/cd1e97761be5b669c79c290dced72404c38acace))

### Documentation

- Update performance test results with comprehensive metrics
  ([`db13585`](https://github.com/gsinghjay/mvp_qr_gen/commit/db1358553e91a72ab57d605926fa6686fb8039dd))

- Update README with performance testing findings and refactoring decision
  ([`3eefe1f`](https://github.com/gsinghjay/mvp_qr_gen/commit/3eefe1f08a6ca7c51e6e39d2e5dc77b1635b93a0))


## v0.26.0 (2025-05-21)

### Bug Fixes

- Update Content Security Policy to allow unsafe-eval for Alpine.js compatibility
  ([`aa84d4c`](https://github.com/gsinghjay/mvp_qr_gen/commit/aa84d4c060b7629d4dcfc3be7a4b51d8225b9b15))

- **analytics**: Update device stats container to remove unnecessary borders
  ([`ab3aa55`](https://github.com/gsinghjay/mvp_qr_gen/commit/ab3aa5523b0ec32933c4e9b0835f5d481cec4b9e))

### Features

- Add Alpine.js v3 via CDN to enable reactive UI components
  ([`0b6770f`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b6770fac164a04f7859a16d960951f63d0eacaf))

- Add in-page edit form endpoints for QR analytics page
  ([`e8d6ae4`](https://github.com/gsinghjay/mvp_qr_gen/commit/e8d6ae4e4ae992bb1d155816b25ae6620ba11835))

- Add scan-timeseries endpoint for QR analytics chart data
  ([`a671b33`](https://github.com/gsinghjay/mvp_qr_gen/commit/a671b330db8ee8cb0453f981111f6ef4a029e4b9))

- Connect chart.js to real time series data from API endpoint
  ([`7c586de`](https://github.com/gsinghjay/mvp_qr_gen/commit/7c586de4ea6efd94d43ce4624c14973049c981f5))

- Create dedicated edit form fragment for in-page editing
  ([`aedc92b`](https://github.com/gsinghjay/mvp_qr_gen/commit/aedc92bed7fc974e329776e3e64ec52737fd2e6b))

- Create QR download options fragment template with customization notice
  ([`56a7234`](https://github.com/gsinghjay/mvp_qr_gen/commit/56a72347b7a1f97b67905b83c96de23457dd4ec8))

- Implement Alpine.js components for chart controls and fix container height
  ([`266a824`](https://github.com/gsinghjay/mvp_qr_gen/commit/266a82457a63168ecacd927753003824402480ef))

- Implement endpoint to serve QR download options fragment
  ([`63374ad`](https://github.com/gsinghjay/mvp_qr_gen/commit/63374adcc7b23588fa8e3852a4669e4d36042824))

- Implement get_scan_timeseries repository method for chart data
  ([`9d2abea`](https://github.com/gsinghjay/mvp_qr_gen/commit/9d2abea671b2a7f27dafd3f41be6085a2e866134))

- Integrate download options fragment into analytics page
  ([`c6a127d`](https://github.com/gsinghjay/mvp_qr_gen/commit/c6a127d72133d91160fd3b7684b51b4a219ee637))

- Integrate edit button and form container in analytics page
  ([`7c96602`](https://github.com/gsinghjay/mvp_qr_gen/commit/7c96602dbd652879914ca05de11ec745acc43f85))

- Replace modal view button with direct link to analytics page
  ([`3dbd45e`](https://github.com/gsinghjay/mvp_qr_gen/commit/3dbd45ef2360812671e82750c697432c9671bca4))

- **analytics**: Add QR analytics page endpoint
  ([`5021493`](https://github.com/gsinghjay/mvp_qr_gen/commit/5021493b69934f01cfc1fa6e75924efe148006a7))

- **analytics**: Add QR ID in response headers to support post-creation redirect
  ([`021a84e`](https://github.com/gsinghjay/mvp_qr_gen/commit/021a84ea571c5b3c0d9f5368e4abbe44f56a5c1c))

- **analytics**: Add scan log table fragment template with filtering and pagination
  ([`c7c0d2d`](https://github.com/gsinghjay/mvp_qr_gen/commit/c7c0d2d42279769391c97a4ec0b2b86ad68043f8))

- **analytics**: Create device/browser/OS stats fragment template with visualization components
  ([`717294f`](https://github.com/gsinghjay/mvp_qr_gen/commit/717294f327d4e8ab164846ba32926046e5eadeb4))

- **analytics**: Create QR analytics page template with chart placeholders
  ([`679a954`](https://github.com/gsinghjay/mvp_qr_gen/commit/679a954d12f9ed11b39281d0372c07406c906cba))

- **analytics**: Implement device/browser/OS stats endpoint for QR analytics
  ([`61c280f`](https://github.com/gsinghjay/mvp_qr_gen/commit/61c280fffe68cbcb56a96fe65d908eb75c45d8fb))

- **analytics**: Update toast message and implement redirect to analytics page
  ([`2131701`](https://github.com/gsinghjay/mvp_qr_gen/commit/2131701849c85cede117dd07a0887c34b155caef))

- **api**: Implement scan log fragment endpoint with filtering capabilities
  ([`08464bd`](https://github.com/gsinghjay/mvp_qr_gen/commit/08464bdac37529071751cb793642bec7345b9866))

- **navigation**: Add redirect from /qr to /qr-list for consistent URL structure
  ([`7676a0d`](https://github.com/gsinghjay/mvp_qr_gen/commit/7676a0d4d0b17eb869be50b2f53a85322198323c))

- **ui**: Add Analytics button to QR list items for direct access to analytics page
  ([`18c9f3d`](https://github.com/gsinghjay/mvp_qr_gen/commit/18c9f3d9f6a7c46147482e468222f897fc27ef9f))

- **ui**: Update analytics page to load scan logs with proper HTMX integration
  ([`f796829`](https://github.com/gsinghjay/mvp_qr_gen/commit/f796829c21c24b734c072f9376570cda31f3a7df))

### Refactoring

- Remove QR detail modal HTML and related JavaScript
  ([`41442ab`](https://github.com/gsinghjay/mvp_qr_gen/commit/41442ab3c0f210f7c4a92353118a3886b19921fa))

- Update fragment endpoints to redirect to analytics page
  ([`38fe942`](https://github.com/gsinghjay/mvp_qr_gen/commit/38fe9429936e3c921021262d190ed8019c2a877d))

- **api**: Change QR analytics endpoint to follow RESTful convention
  ([`94fde88`](https://github.com/gsinghjay/mvp_qr_gen/commit/94fde8893072514c5222de574f49ed0a91666e82))

- **ui**: Rename Home to Dashboard in sidebar and consolidate navigation
  ([`574b617`](https://github.com/gsinghjay/mvp_qr_gen/commit/574b61785ad255ea0710212449bb13445180ceee))


## v0.25.0 (2025-05-21)

### Features

- **tests**: Add helper functions for validating scan log data
  ([`b7d459f`](https://github.com/gsinghjay/mvp_qr_gen/commit/b7d459fb3234589a394d48dc122562579da9eea4))

- **tests**: Add scan_log_factory fixtures and qr_with_scans fixtures
  ([`29c40d8`](https://github.com/gsinghjay/mvp_qr_gen/commit/29c40d809d62345133360c8a07111b61710ce3d8))

- **tests**: Add ScanLogFactory for test data generation
  ([`8b319e6`](https://github.com/gsinghjay/mvp_qr_gen/commit/8b319e68acd1673868a1d1b054301334749eaf28))

### Testing

- **factories**: Add tests demonstrating factory pattern usage
  ([`3ed1830`](https://github.com/gsinghjay/mvp_qr_gen/commit/3ed18302edfd3add2c43e8ca7372b9498933465d))


## v0.24.0 (2025-05-20)

### Bug Fixes

- **security**: Add font-src directive to CSP to allow Bootstrap icons
  ([`e905446`](https://github.com/gsinghjay/mvp_qr_gen/commit/e9054463043f3cd877b0b22f0c8f50ddd09847e6))

- **tests**: Update import paths in test_general_api.py
  ([`b848e1b`](https://github.com/gsinghjay/mvp_qr_gen/commit/b848e1b2fb7eb191861665d7cb215e95cd382048))

### Documentation

- **tests**: Add dependencies.py to test directory structure
  ([`886e7f1`](https://github.com/gsinghjay/mvp_qr_gen/commit/886e7f188ac9c02e6662a5d782875d56cd064e4c))

- **tests**: Document standardized dependency override approach
  ([`4fa6ee2`](https://github.com/gsinghjay/mvp_qr_gen/commit/4fa6ee270a0283e62373a2b1396404b750867c40))

### Features

- **tests**: Create centralized test dependency injection functions
  ([`bab3a1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/bab3a1e3c92d6bfa1a83843d031d06f6ba72c756))

### Refactoring

- **tests**: Standardize client fixture dependency overrides in conftest.py
  ([`dc4ac28`](https://github.com/gsinghjay/mvp_qr_gen/commit/dc4ac289cd40939ccac69d085b8fc2461c2e7f09))


## v0.23.0 (2025-05-20)

### Chores

- **config**: Improve Traefik static configuration with proper log paths and entrypoints
  ([`0843eaf`](https://github.com/gsinghjay/mvp_qr_gen/commit/0843eaf9ebfbc69345fa33fbf92a542155528efd))

### Features

- **routing**: Reorganize Traefik routers with proper priorities and domain isolation
  ([`508ea67`](https://github.com/gsinghjay/mvp_qr_gen/commit/508ea673cc9e88ddc208c0da1f9d2bb90dff0af6))

### Refactoring

- **docker**: Streamline api service configuration and containerization
  ([`fd3fd88`](https://github.com/gsinghjay/mvp_qr_gen/commit/fd3fd88058ac1b9d3cbfd66445e2c99cf539be42))


## v0.22.1 (2025-05-19)

### Bug Fixes

- **tests**: Add missing app import in QR service tests
  ([`63b4198`](https://github.com/gsinghjay/mvp_qr_gen/commit/63b41982a57a397e3c13be73772569d8ac439793))

- **tests**: Resolve duplicate table errors in test database setup
  ([`c1e16ce`](https://github.com/gsinghjay/mvp_qr_gen/commit/c1e16ce038b2d70625d582717a44002ff9602ef4))

### Documentation

- Add directory structure documentation for test organization
  ([`4bd1333`](https://github.com/gsinghjay/mvp_qr_gen/commit/4bd13337503661aede9410096f1c5b21b6a2d744))

### Refactoring

- Organize end-to-end tests in dedicated directory
  ([`e00c0a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/e00c0a74f1edbc1f0c77012fc68f3dbbc03d9fce))

- Organize integration tests in dedicated directory
  ([`906e48c`](https://github.com/gsinghjay/mvp_qr_gen/commit/906e48cda5c8a77fda8f116de8a55564f88d3b44))

- Organize unit tests in dedicated directory
  ([`62c9e39`](https://github.com/gsinghjay/mvp_qr_gen/commit/62c9e397f279d84bb2e47bc495b7a88746844677))

- Remove SQLite-specific tests after PostgreSQL migration
  ([`d194766`](https://github.com/gsinghjay/mvp_qr_gen/commit/d194766fdb81b90bd3c1e338c4d5b80e332f34c9))

- Remove test_api_restructure.py after reorganization
  ([`fa8583a`](https://github.com/gsinghjay/mvp_qr_gen/commit/fa8583a62ac600cfd2184c4d5b4f56b814f942aa))

- Remove test_async_example.py after reorganization
  ([`884ba79`](https://github.com/gsinghjay/mvp_qr_gen/commit/884ba79b66e032f94e5bf1433d6fb083f7fd41a4))

- Remove test_background_tasks.py after reorganization
  ([`a44d04f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a44d04f08fd2a9e877f9105080b7b99089a1b883))

- Remove test_database_connection.py after reorganization
  ([`40abe1b`](https://github.com/gsinghjay/mvp_qr_gen/commit/40abe1b7d73dd1a093028a9cd374ead9337c3090))

- Remove test_dependency_overrides.py after reorganization
  ([`6cfaf83`](https://github.com/gsinghjay/mvp_qr_gen/commit/6cfaf832f7b0d76c5496581f49e08bcc02c8b6a5))

- Remove test_exceptions.py after reorganization
  ([`d5f1171`](https://github.com/gsinghjay/mvp_qr_gen/commit/d5f1171b33ace5d7311d3a7c5d67b686fb2b5cc8))

- Remove test_factories.py after reorganization
  ([`65d1647`](https://github.com/gsinghjay/mvp_qr_gen/commit/65d16474a0ea964c0ce174bdf4732161286f246d))

- Remove test_http_methods.py after reorganization
  ([`eec0bd8`](https://github.com/gsinghjay/mvp_qr_gen/commit/eec0bd8ea99ea186a356ec60afe199b40c3e930e))

- Remove test_integration.py after reorganization
  ([`1af2655`](https://github.com/gsinghjay/mvp_qr_gen/commit/1af2655a54a750a415a46dfdf2ec3ea1057266bd))

- Remove test_lifecycle.py after reorganization
  ([`b2e093a`](https://github.com/gsinghjay/mvp_qr_gen/commit/b2e093a8695843f4b650b2ad1fccb12b50028bd5))

- Remove test_main.py after reorganization
  ([`0062814`](https://github.com/gsinghjay/mvp_qr_gen/commit/0062814f7ccd69ff4f2a70cce804043f59a91c2f))

- Remove test_middleware.py after reorganization
  ([`80bd09f`](https://github.com/gsinghjay/mvp_qr_gen/commit/80bd09f1e4dccf3b9eac946872d42352a1606d08))

- Remove test_models_schemas.py after reorganization
  ([`933371e`](https://github.com/gsinghjay/mvp_qr_gen/commit/933371e06433dc73b0033753460d528581eddd11))

- Remove test_qr_service.py after reorganization
  ([`2e21e97`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e21e9761de4971022508baf32745caf2faf5fdf))

- Remove test_response_models.py after reorganization
  ([`2e4b332`](https://github.com/gsinghjay/mvp_qr_gen/commit/2e4b332ea14417bc151c07ceb98069d9aabd24f2))

- Remove test_router_structure.py after reorganization
  ([`d539634`](https://github.com/gsinghjay/mvp_qr_gen/commit/d539634413a2775aebc9af727cea2ef07a8f75c4))

- Remove test_validation_parameterized.py after reorganization
  ([`cfa7a88`](https://github.com/gsinghjay/mvp_qr_gen/commit/cfa7a8822fa5fa3e145926fbcd73f56713030c05))

### Testing

- **db**: Add specific tests to verify test database setup integrity
  ([`ea258ae`](https://github.com/gsinghjay/mvp_qr_gen/commit/ea258ae7a009cdc65d0faf63cf8cbe584e004f08))


## v0.22.0 (2025-05-19)

### Bug Fixes

- Adjust QR code size calculation for pixel unit
  ([`0670682`](https://github.com/gsinghjay/mvp_qr_gen/commit/0670682626524d821978a1508104ca4ca4c3ec7e))

- Correct indentation and update test fixtures for PostgreSQL
  ([`2432d48`](https://github.com/gsinghjay/mvp_qr_gen/commit/2432d48c0886a1ed99c7cd4cea96b397603008d3))

- Improve QR list display and pagination
  ([`47a5993`](https://github.com/gsinghjay/mvp_qr_gen/commit/47a5993f58dc88600562611d3219a9e82442dcf9))

- Update QR model to use PostgreSQL-compatible timestamp defaults
  ([`df2bb96`](https://github.com/gsinghjay/mvp_qr_gen/commit/df2bb9635b9de1cbe3b8c83c462e997d9fad3669))

- **backend**: Remove restriction to allow editing any QR code type
  ([`039fba4`](https://github.com/gsinghjay/mvp_qr_gen/commit/039fba4216c64f0a2c0681d5e5cd2f57cbee8590))

- **frontend**: Correct form structure in QR edit modal to enable form submission
  ([`6493050`](https://github.com/gsinghjay/mvp_qr_gen/commit/6493050a8e5f469a733e6d3e59d3dcbecceca484))

- **security**: Prevent redirect loop on auth domain by excluding access-restricted path
  ([`8bb672e`](https://github.com/gsinghjay/mvp_qr_gen/commit/8bb672e838c6d268929d8c1597b9a7cba3ed0553))

### Chores

- Add alembic script template for migration generation
  ([`0c07b5c`](https://github.com/gsinghjay/mvp_qr_gen/commit/0c07b5ccdcbb60eb58fd10c2e9a0bb5af3b4df92))

- Add backups directory to gitignore
  ([`d75d87d`](https://github.com/gsinghjay/mvp_qr_gen/commit/d75d87d6a65cec8e163d9a07ac3a8e263e1d7702))

- Remove SQLite-specific migration files
  ([`86b49ba`](https://github.com/gsinghjay/mvp_qr_gen/commit/86b49bac26f7c6428559d0ad160a297c7ee7dc38))

- Remove unused image assets
  ([`fe1403c`](https://github.com/gsinghjay/mvp_qr_gen/commit/fe1403cd3466d688446ece3cd3069132ef5f13cc))

- Update alembic.ini for PostgreSQL compatibility
  ([`517c50e`](https://github.com/gsinghjay/mvp_qr_gen/commit/517c50e60f9ca9fa339cb289966f05a912eaa621))

- Update gitignore patterns
  ([`6f19679`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f19679a94869620d2a926b1300a7ea13e30d661))

- Update project metadata and dependencies
  ([`9e46b91`](https://github.com/gsinghjay/mvp_qr_gen/commit/9e46b9149e8031557a9ea693fac5786c7027e742))

- Update QR logo image
  ([`1f7b255`](https://github.com/gsinghjay/mvp_qr_gen/commit/1f7b2552650f8e578929708df83e82df56f37bcc))

- **docker**: Replace SQLite with PostgreSQL client tools
  ([`5000d7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/5000d7d28f1c74e02faae26b3fe4ee109ce22e01))

### Documentation

- Add detailed documentation for database schema report script
  ([`15eb906`](https://github.com/gsinghjay/mvp_qr_gen/commit/15eb9060aa2159be5cd7a36ffc89e5e35b7d5800))

- Add README for database scripts directory
  ([`8fe08b1`](https://github.com/gsinghjay/mvp_qr_gen/commit/8fe08b1a3c5662beeb4e2f0bcc299e9461c98361))

- Remove STATUS.md in favor of consolidated documentation
  ([`093a482`](https://github.com/gsinghjay/mvp_qr_gen/commit/093a482660762e3379b839ecbdecc940c474a1c2))

- Update API test documentation and scripts for scan tracking
  ([`ec3ee30`](https://github.com/gsinghjay/mvp_qr_gen/commit/ec3ee30ef18fca5644b8ec3a4799d4db7a6ed3f7))

- Update infrastructure documentation for PostgreSQL architecture
  ([`b8a766d`](https://github.com/gsinghjay/mvp_qr_gen/commit/b8a766d7d1be14947650900f0f4686ccfac45298))

- Update project story to reflect PostgreSQL migration
  ([`39b85ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/39b85ef41aaf170133958383a3f81b73b48626b2))

- Update README to reflect PostgreSQL-only usage
  ([`9f18e32`](https://github.com/gsinghjay/mvp_qr_gen/commit/9f18e3250a2d4bc1c22d284c5f70194f2dad69ee))

- Update test documentation for PostgreSQL test database
  ([`89371e3`](https://github.com/gsinghjay/mvp_qr_gen/commit/89371e32d43fcb260f37662f6819107e34923ab0))

### Features

- Add methods for scan statistics and analytics in QRRepository
  ([`31f07b2`](https://github.com/gsinghjay/mvp_qr_gen/commit/31f07b2f2f3e68678a5512b67d9d756c0e1a541c))

- Add migration for scan_log table and QR code enhancements
  ([`4e7ad71`](https://github.com/gsinghjay/mvp_qr_gen/commit/4e7ad716d792f3b74b5114197493f5f9921623cb))

- Add migration for short_id column with data population
  ([`814b875`](https://github.com/gsinghjay/mvp_qr_gen/commit/814b875df1c9174720036205e17224822df34711))

- Add official HCCC logo in SVG format
  ([`372cc34`](https://github.com/gsinghjay/mvp_qr_gen/commit/372cc34b0613d02657a1c529bfdb27d1bd5718c2))

- Add physical dimension inputs to QR details modal
  ([`7654dba`](https://github.com/gsinghjay/mvp_qr_gen/commit/7654dbac493c3a5d07125a1fea46e20eba21227f))

- Add physical dimension parameters to QR image schemas
  ([`ccfe0f4`](https://github.com/gsinghjay/mvp_qr_gen/commit/ccfe0f45a8abf99b6e090596a872efd110a0a33d))

- Add PostgreSQL backup capability to manage_db.py
  ([`f42027a`](https://github.com/gsinghjay/mvp_qr_gen/commit/f42027a203de3e9f97c099a4b7effd6d63e58cae))

- Add PostgreSQL database schema report script
  ([`4591d1c`](https://github.com/gsinghjay/mvp_qr_gen/commit/4591d1cf1898a093c157c581d68ac99af7607126))

- Add scan_ref parameter handling for genuine scan detection
  ([`ecd8630`](https://github.com/gsinghjay/mvp_qr_gen/commit/ecd8630e062accb22689fa6adf2da784a345b8db))

- Add ScanLog model for detailed scan tracking
  ([`7613638`](https://github.com/gsinghjay/mvp_qr_gen/commit/7613638b9beebdaf0a5014972fc0e4bb799da3fb))

- Add short_id column to QRCode model for optimized lookups
  ([`b3c3450`](https://github.com/gsinghjay/mvp_qr_gen/commit/b3c34504847f519bee043782f80037420fd62c18))

- Add short_id field to QR code schemas for improved data validation and API responses
  ([`64606e7`](https://github.com/gsinghjay/mvp_qr_gen/commit/64606e7a46d660e5123d7d1885c21769be3dd2b6))

- Configure alembic env.py for PostgreSQL support
  ([`57019c6`](https://github.com/gsinghjay/mvp_qr_gen/commit/57019c68f4b3e9c7f62f75a485740011ee8a66c4))

- Create initial PostgreSQL schema migration
  ([`2097dbd`](https://github.com/gsinghjay/mvp_qr_gen/commit/2097dbd45838a00423a09d39ab0dceb06e15cc98))

- Enhance QR detail template to display scan statistics
  ([`971fe34`](https://github.com/gsinghjay/mvp_qr_gen/commit/971fe340a7766e4da9343a092c2efa280739c85e))

- Enhance QR endpoints to support physical dimensions and DPI
  ([`30a71c5`](https://github.com/gsinghjay/mvp_qr_gen/commit/30a71c58a783a5e15706d96534f57c9259f72de8))

- Enhance QR imaging with physical dimension and DPI support
  ([`f42c32c`](https://github.com/gsinghjay/mvp_qr_gen/commit/f42c32c9e51a7cfcf0f3921187ef78fe3db020c6))

- Enhance QR service with physical dimension support
  ([`42176a3`](https://github.com/gsinghjay/mvp_qr_gen/commit/42176a3b547a6ba183a98fed810b51b115dabdcb))

- Enhance QRCode model with genuine scan tracking fields
  ([`0ca376b`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ca376b2470fdd7a61694e596107c3c5f771a3d8))

- Implement get_by_short_id repository method for direct lookups
  ([`75494fc`](https://github.com/gsinghjay/mvp_qr_gen/commit/75494fcb6d2c0ef733f2be4ccd406cdfe2dec35a))

- Implement streamlined QR creation workflow
  ([`a9dcb35`](https://github.com/gsinghjay/mvp_qr_gen/commit/a9dcb35d024f50a1500ecd55a8b12c4d39db7dcc))

- Implement user agent parsing and scan logging in QRService
  ([`7e6d5a1`](https://github.com/gsinghjay/mvp_qr_gen/commit/7e6d5a14b04188c0a9e387898b11e43dac026fb4))

- Include ScanLog model in models package
  ([`89510eb`](https://github.com/gsinghjay/mvp_qr_gen/commit/89510eb4c1552c3fa0ec03f6bea114c37dc2ff4f))

- Update Docker configuration for PostgreSQL services
  ([`0e2716d`](https://github.com/gsinghjay/mvp_qr_gen/commit/0e2716d3bd7a6a759cb603ea5fad104deec6b05a))

- Update fragment endpoints to support scan analytics display
  ([`8d0470c`](https://github.com/gsinghjay/mvp_qr_gen/commit/8d0470c33ad372bf7520ee7d0ce49ea7ebcb761f))

- Update fragments endpoint to handle physical dimension parameters
  ([`9a7466b`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a7466b4b0136add8239f4fc19dfe8c9dd5caba4))

- Update init.sh to support PostgreSQL backup on startup
  ([`d989a58`](https://github.com/gsinghjay/mvp_qr_gen/commit/d989a583e5c3e53f40e465198d9983061b52ed4d))

- Update QR schemas for PostgreSQL compatibility
  ([`4c1617c`](https://github.com/gsinghjay/mvp_qr_gen/commit/4c1617c29e148ec5f0074c1e5e5583ef258c3c4f))

- Update QR schemas with scan tracking information
  ([`386f44f`](https://github.com/gsinghjay/mvp_qr_gen/commit/386f44f0d7851ec1ee4bf1acc7dfb626bb8fbad2))

- Update QRCodeService to utilize short_id for improved redirect performance
  ([`7ce41ff`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ce41ff1eaac8e5f5211afd6883aedae8c29400b))

- **deps**: Add psycopg2-binary for PostgreSQL support
  ([`d964f1e`](https://github.com/gsinghjay/mvp_qr_gen/commit/d964f1e6e4d92f7b01093dbd3b8986a11708a967))

- **docker**: Add PostgreSQL service to Docker Compose
  ([`9aab687`](https://github.com/gsinghjay/mvp_qr_gen/commit/9aab687f235a7f2b072bed002de0e6f290528823))

- **scripts**: Enhance manage_db.py with PostgreSQL validation and backup
  ([`0b3de97`](https://github.com/gsinghjay/mvp_qr_gen/commit/0b3de973cb9e4d6649ee03111d6c84d8155c2d9e))

- **scripts**: Update init.sh with PostgreSQL readiness checks
  ([`6d6642d`](https://github.com/gsinghjay/mvp_qr_gen/commit/6d6642dd0e8e9f607b2fdf80f0ef215efbf8e725))

- **security**: Add routing for new auth domain and IP 130.156.44.53
  ([`425bb22`](https://github.com/gsinghjay/mvp_qr_gen/commit/425bb2255a6c935288c8d6ea710f8e68d16ffc7b))

- **ui**: Implement toast notification with QR details modal for better user experience
  ([`aba23d2`](https://github.com/gsinghjay/mvp_qr_gen/commit/aba23d280230ff5a9bd9fde67355010b9caa6898))

### Refactoring

- Remove physical dimension fields from QR creation form
  ([`7ab5803`](https://github.com/gsinghjay/mvp_qr_gen/commit/7ab5803a4e33d0c4d75413539759c2afd3738dd5))

- Remove SQLite database URL from configuration
  ([`8d59e73`](https://github.com/gsinghjay/mvp_qr_gen/commit/8d59e73c65e691e99bd947b036d9228e1a35d3c3))

- Remove SQLite-specific code from database management script
  ([`a310a19`](https://github.com/gsinghjay/mvp_qr_gen/commit/a310a19dec8f49d8f55510e42e46e9b3d21f57db))

- Simplify database module for PostgreSQL-only operation
  ([`83b008e`](https://github.com/gsinghjay/mvp_qr_gen/commit/83b008ee44a4055fe790a43e9d8f5d67fff54bba))

- Update Alembic configuration for PostgreSQL exclusivity
  ([`f373c7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/f373c7d2c306bfa78601e2d87bd9ca2fe73b8baf))

- Update health service for PostgreSQL-exclusive metrics
  ([`a7ed95f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a7ed95fb802a2a678ca654a2d184d77282852abe))

- Update initialization script for PostgreSQL-only setup
  ([`1692475`](https://github.com/gsinghjay/mvp_qr_gen/commit/16924752f0412efa891f8b6249bcbd432a6af024))

- Update test factories for PostgreSQL compatibility
  ([`2eb6199`](https://github.com/gsinghjay/mvp_qr_gen/commit/2eb619918c9e7b308a8d7c347a2086cf7ae8ea5b))

- Update test helpers for PostgreSQL support
  ([`0c27d73`](https://github.com/gsinghjay/mvp_qr_gen/commit/0c27d7301541b895c94f4d51647e47c9d5e4c087))

- **database**: Implement dual database support for SQLite and PostgreSQL
  ([`cf3dd21`](https://github.com/gsinghjay/mvp_qr_gen/commit/cf3dd2100d7226c6629f90b1a26ba2bae7971e51))

- **repo**: Remove unused find_by_pattern method
  ([`33357d5`](https://github.com/gsinghjay/mvp_qr_gen/commit/33357d5b29c474676e9b010e771565624401f9b3))

- **service**: Remove fallback pattern matching in get_qr_by_short_id
  ([`35079e9`](https://github.com/gsinghjay/mvp_qr_gen/commit/35079e99a5cc11bca435106ad95e24575170cedf))

- **startup**: Simplify lifespan warmup logic for QR lookups
  ([`d3ca7f1`](https://github.com/gsinghjay/mvp_qr_gen/commit/d3ca7f11ef40e293e7caf946f99e45a233af0ee0))

### Testing

- Adapt SQLite-specific tests for PostgreSQL environment
  ([`684a7a6`](https://github.com/gsinghjay/mvp_qr_gen/commit/684a7a667dd1fa352c1c453ecc140680663c2253))

- Add asynchronous test examples for PostgreSQL compatibility
  ([`2b13fba`](https://github.com/gsinghjay/mvp_qr_gen/commit/2b13fba63eb1088ca1ae26e8bfa1c883ca21689f))

- Convert integration tests to use PostgreSQL
  ([`db28701`](https://github.com/gsinghjay/mvp_qr_gen/commit/db28701a8ebb71a242cb76dcf4b463714afe2b3b))

- Convert main application tests to use PostgreSQL
  ([`350f1b3`](https://github.com/gsinghjay/mvp_qr_gen/commit/350f1b3e64d840d847c5d753cf480cbfe6639436))

- Implement database connection tests for PostgreSQL
  ([`481f101`](https://github.com/gsinghjay/mvp_qr_gen/commit/481f101c8ecfdf5c155678546266c9ea84bb1da9))

- Refactor QR service tests for PostgreSQL test database
  ([`c279d04`](https://github.com/gsinghjay/mvp_qr_gen/commit/c279d041a1887850a2b18170f41a00fa12d17e66))

- Update lifecycle tests for PostgreSQL compatibility
  ([`0e8eed0`](https://github.com/gsinghjay/mvp_qr_gen/commit/0e8eed01c711addee3636944c3a92ae203d48bef))

- Update middleware tests for PostgreSQL compatibility
  ([`eecde35`](https://github.com/gsinghjay/mvp_qr_gen/commit/eecde359c5a0d15e1e792eb293dcd41cf3c608d3))


## v0.21.0 (2025-05-06)

### Chores

- Removed legacy css/js from before HTMX migration
  ([`d321ee5`](https://github.com/gsinghjay/mvp_qr_gen/commit/d321ee588eff34144502c08dcd3815484b9d75c5))

### Features

- Add migration for title and description columns in qr_codes table
  ([`db1df6c`](https://github.com/gsinghjay/mvp_qr_gen/commit/db1df6c07363cc0330bbe0ad754176e4dc768370))

- Add title and description fields to QR creation form
  ([`1206681`](https://github.com/gsinghjay/mvp_qr_gen/commit/1206681856e72a357ab9cc745512686f9251588d))

- Add title and description fields to QR edit form
  ([`e9b594f`](https://github.com/gsinghjay/mvp_qr_gen/commit/e9b594ff58af1a75e76a0f06244819d71d2cf3f9))

- Add title and description fields to QRCode model
  ([`d5f88d3`](https://github.com/gsinghjay/mvp_qr_gen/commit/d5f88d3d7d2111bbe34c6dbc2ae9a3fdbd72eb41))

- Add title and description to QR response models
  ([`71a2b1a`](https://github.com/gsinghjay/mvp_qr_gen/commit/71a2b1a5ab53f816840c168b5ea62176dd691f03))

- Add title column to QR list view
  ([`8fdf533`](https://github.com/gsinghjay/mvp_qr_gen/commit/8fdf533e5945a133ec29a4f2e606501704e3230e))

- Display QR title in list items
  ([`f7453fd`](https://github.com/gsinghjay/mvp_qr_gen/commit/f7453fd952cbf9922dbff1a206d4ff20f4dc9252))

- Display title and description in QR detail view
  ([`a80628e`](https://github.com/gsinghjay/mvp_qr_gen/commit/a80628eb20d96a4199d922e61f406ad7f384c652))

- Enhance search functionality to include title and description
  ([`23f104f`](https://github.com/gsinghjay/mvp_qr_gen/commit/23f104fa83c69aff6bfecfbbd373bed7a8257797))

- Update API endpoints to support title and description
  ([`af01edf`](https://github.com/gsinghjay/mvp_qr_gen/commit/af01edf56ac5c0ed9471d7d1a9f40a5951f6ad66))

- Update fragment endpoints to handle title and description fields
  ([`95c5d88`](https://github.com/gsinghjay/mvp_qr_gen/commit/95c5d887889ebef2bc5df31ec12806fa87860756))

- Update parameter schemas with title and description fields
  ([`20ddd28`](https://github.com/gsinghjay/mvp_qr_gen/commit/20ddd282c6f07d27b4f0bf79b8dcc0d24d86ac8d))

- Update QR service to handle title and description fields
  ([`3a10c62`](https://github.com/gsinghjay/mvp_qr_gen/commit/3a10c62b220da354343d0e0cbcd0fbcc2956e3ba))

### Testing

- Update test script to include title and description in API requests
  ([`dd5cc43`](https://github.com/gsinghjay/mvp_qr_gen/commit/dd5cc433da9df7574e5d713bfe09ceb17a9dc8dc))


## v0.20.0 (2025-05-06)

### Chores

- Backup original custom CSS file for reference
  ([`5f9259c`](https://github.com/gsinghjay/mvp_qr_gen/commit/5f9259c59efbb16d29cb3424e15c42030ca873d6))

### Features

- **api**: Add fragments endpoint for HTMX integration
  ([`20bf094`](https://github.com/gsinghjay/mvp_qr_gen/commit/20bf094f7afd80ce7509a02d460be67f1e47b951))

- **api**: Register fragments router in API initialization
  ([`7d84d81`](https://github.com/gsinghjay/mvp_qr_gen/commit/7d84d818770f4d00e76141e1804cb77a80eb399e))

- **ui**: Add HTML fragments for HTMX partial updates
  ([`01c950a`](https://github.com/gsinghjay/mvp_qr_gen/commit/01c950a1ddbf335671e520233365a6876fd851fd))

- **ui**: Add HTMX library to base template
  ([`8373e42`](https://github.com/gsinghjay/mvp_qr_gen/commit/8373e42dd68643cd3b5f11ac9ea1ce98862c5de6))

### Refactoring

- **api**: Update QR endpoints for HTMX compatibility
  ([`4418ff0`](https://github.com/gsinghjay/mvp_qr_gen/commit/4418ff02cb64b0a99922f3da88458939c1f593ae))

- **css**: Remove custom CSS in favor of Bootstrap classes
  ([`a57fb7d`](https://github.com/gsinghjay/mvp_qr_gen/commit/a57fb7d7ca3812edb4bf45b71a4b51fad5b84521))

- **js**: Move unused JavaScript to depreciated-js directory
  ([`2632683`](https://github.com/gsinghjay/mvp_qr_gen/commit/26326833b1cf7098ae48d879227788c0b7a15bb5))

- **js**: Remove JavaScript files replaced by HTMX
  ([`9006f7f`](https://github.com/gsinghjay/mvp_qr_gen/commit/9006f7fbf3164994b7f48e67e7b8eb1cf47be37f))

- **pages**: Update page handlers to use new template structure
  ([`a6ee368`](https://github.com/gsinghjay/mvp_qr_gen/commit/a6ee368fce5090e2d766b51b75c4e49bd381c7b2))

- **ui**: Migrate templates to pages directory structure
  ([`25cd908`](https://github.com/gsinghjay/mvp_qr_gen/commit/25cd90883e4be6b9ad082d8f250e3886aae8d85f))

- **ui**: Remove templates moved to pages directory
  ([`2115884`](https://github.com/gsinghjay/mvp_qr_gen/commit/211588495bd649b3b64ad276b0624ea766cfbc71))

- **ui**: Update QR list template for HTMX compatibility
  ([`4a2de54`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a2de54c6f46ca3a259b9c619bd241a493db3e19))


## v0.19.0 (2025-05-05)

### Bug Fixes

- **performance**: Optimize redirect initialization for faster QR code scans
  ([`9827fa4`](https://github.com/gsinghjay/mvp_qr_gen/commit/9827fa4211575a8fa2a9c20ee0484597004a803a))

### Chores

- Remove outdated performance results file
  ([`10689ef`](https://github.com/gsinghjay/mvp_qr_gen/commit/10689ef9d3c2fe1ca15ae3c2041a96d9690b9938))

### Documentation

- Update development story with JS refactoring information
  ([`c76e2cb`](https://github.com/gsinghjay/mvp_qr_gen/commit/c76e2cb76949d2d0ab95120af9343baf96b43f7c))

- Update README with modular JS architecture details
  ([`8b1a95d`](https://github.com/gsinghjay/mvp_qr_gen/commit/8b1a95d59d8e0fe49ed2b7dc9a0ff12b2dc3c08d))

### Features

- **js**: Add event-initializer module for setup and binding
  ([`cf9f22d`](https://github.com/gsinghjay/mvp_qr_gen/commit/cf9f22d679bb0a555533061b82eb12a3addefbe1))

- **js**: Add form-handler module for form submissions and validation
  ([`5db36dd`](https://github.com/gsinghjay/mvp_qr_gen/commit/5db36dd1038633462be95ac56018c6d40426da75))

- **js**: Add list-manager module for pagination and filtering
  ([`601ca62`](https://github.com/gsinghjay/mvp_qr_gen/commit/601ca62daf4a08e82bf2f3f590d9e0e6feb8107b))

- **js**: Add modal-handler module for dialog operations
  ([`2797d9e`](https://github.com/gsinghjay/mvp_qr_gen/commit/2797d9e75f2c796c28af8cdb0de9a21ddd068e1d))

- **js**: Add qr-operations module for core QR code functionality
  ([`381a0cf`](https://github.com/gsinghjay/mvp_qr_gen/commit/381a0cf56874ffd39c21d077185bc122d8ba71f1))

### Refactoring

- Move RequestIDMiddleware to middleware directory
  ([`09e593c`](https://github.com/gsinghjay/mvp_qr_gen/commit/09e593c4f2a46f3fa43981f3af7cc7296606092e))

- Simplify error handling in repository and service layers
  ([`e1a51f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/e1a51f7bca575c46a2126bb46cbf916d3a882765))

- Standardize schema validation placement by removing redundant color checks
  ([`2a6ed8b`](https://github.com/gsinghjay/mvp_qr_gen/commit/2a6ed8b38153d6d8c037915bf578aa257f92df06))

- **html**: Update base template for modular JS architecture
  ([`bf1e272`](https://github.com/gsinghjay/mvp_qr_gen/commit/bf1e272e04f3f475f829d296f5cbb5c55ae8c239))

- **html**: Update dashboard template for modular JS structure
  ([`e79cfa4`](https://github.com/gsinghjay/mvp_qr_gen/commit/e79cfa4214df3d4cd0431962aeaa13c38e6014f7))

- **html**: Update index template for modular JS structure
  ([`b6600c7`](https://github.com/gsinghjay/mvp_qr_gen/commit/b6600c7b49243c68ee70b8dc6d5dd4433811eb65))

- **html**: Update QR creation template for modular JS
  ([`734ff9a`](https://github.com/gsinghjay/mvp_qr_gen/commit/734ff9aa7e48b5749d1306898818ae4130866064))

- **html**: Update QR list template for modular JS structure
  ([`97ce131`](https://github.com/gsinghjay/mvp_qr_gen/commit/97ce1315a7b6cb23a09b876cf47564b2bc2b9bf0))

- **js**: Deprecate script.js with backward compatibility
  ([`b35d999`](https://github.com/gsinghjay/mvp_qr_gen/commit/b35d999a3cea7a7d4708b233286de6e050b6766e))

- **js**: Update main.js as modular architecture entry point
  ([`6b64d00`](https://github.com/gsinghjay/mvp_qr_gen/commit/6b64d009e22d272b06d1359969004782f6e5737c))

### Testing

- Add updated performance results for modular architecture
  ([`d02f1e4`](https://github.com/gsinghjay/mvp_qr_gen/commit/d02f1e4918611ea9c30bd05d66b710fa124f093e))


## v0.18.0 (2025-05-05)

### Features

- Added auth to test scripts
  ([`657f4c3`](https://github.com/gsinghjay/mvp_qr_gen/commit/657f4c3ed09517e6d2a2c1ba6dc25b334603901c))

- **api**: Update endpoints to support error correction and SVG accessibility
  ([`7defd7b`](https://github.com/gsinghjay/mvp_qr_gen/commit/7defd7b5bb7c15ae6103b086014a7dc1367c115f))

- **db**: Add error_level column to qr_codes table
  ([`64b6ed8`](https://github.com/gsinghjay/mvp_qr_gen/commit/64b6ed8f633b12c8d0a083d7c12ef506c5efd77a))

- **models**: Add error_level field to QRCode model
  ([`111ad77`](https://github.com/gsinghjay/mvp_qr_gen/commit/111ad77221c3a3d192f7b67b054d3da64fe256bb))

- **schemas**: Add error correction level and SVG accessibility parameters
  ([`0ce1381`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ce138161678427c5bf4971f667ecbfdedd0174d))

- **services**: Implement error correction level in QR generation service
  ([`4a2fe45`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a2fe451b6e4f54be297a4b47c6b758703ce9342))

- **utils**: Enhance QR generation with error levels and SVG accessibility
  ([`8106a54`](https://github.com/gsinghjay/mvp_qr_gen/commit/8106a54193e58b7761fb8eb4b2321dad724ed328))


## v0.17.0 (2025-05-04)

### Chores

- Add users.htpasswd to .gitignore for security
  ([`d149f4c`](https://github.com/gsinghjay/mvp_qr_gen/commit/d149f4cb21d714130cdfea90b7f1b0a686d0ee6a))

### Documentation

- Update documentation with basic authentication implementation details
  ([`11ed736`](https://github.com/gsinghjay/mvp_qr_gen/commit/11ed736e3c83972046abd1eec32d7a9dab15bb7c))

### Features

- Configure Traefik to mount htpasswd file for basic authentication
  ([`c202e95`](https://github.com/gsinghjay/mvp_qr_gen/commit/c202e9536a5b943da93aa43e48329fb7c5aee4c7))

- Implement basic authentication middleware for dashboard access
  ([`416d213`](https://github.com/gsinghjay/mvp_qr_gen/commit/416d2131980ac6e8831a7e591706f457ad6e763f))


## v0.16.1 (2025-05-04)

### Bug Fixes

- Standardize dependency injection and code structure patterns
  ([`992440d`](https://github.com/gsinghjay/mvp_qr_gen/commit/992440d782eb4cbed9b731f5ad817f81cefb34a0))

- **auth**: Remove login endpoint functionality from pages.py router
  ([`40e948b`](https://github.com/gsinghjay/mvp_qr_gen/commit/40e948ba26713f9e46bc2fbbe54ee7393e194151))

- **config**: Explicitly load ENVIRONMENT from env variables
  ([`07bdc49`](https://github.com/gsinghjay/mvp_qr_gen/commit/07bdc4987a7727cd3aecbbcd1b2d51ec3cc5822c))

- **health**: Use settings.ENVIRONMENT in health endpoint response
  ([`f31c9bb`](https://github.com/gsinghjay/mvp_qr_gen/commit/f31c9bbe19aefcb3056d1820b8e42ceb58824607))

### Chores

- Irrelevant task file
  ([`5e7128f`](https://github.com/gsinghjay/mvp_qr_gen/commit/5e7128fa4ed2eb80028cd9d7551236bb8bfd6877))

### Code Style

- **css**: Remove login button styles from custom.css
  ([`9a1b709`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a1b7094750964c41b576ad732f1f0f83ce321ef))

### Performance Improvements

- Add route warmup to init.sh to improve first request performance
  ([`300a4ee`](https://github.com/gsinghjay/mvp_qr_gen/commit/300a4eef2b0d04f44ffad136ffc593b53a60b860))

- Optimize first-request performance with FastAPI lifespan initialization
  ([`2a8769b`](https://github.com/gsinghjay/mvp_qr_gen/commit/2a8769b69dafd77e4bce4745ef4d3073688699da))

### Refactoring

- Move settings import to module level in qr_service.py for better initialization
  ([`8261c41`](https://github.com/gsinghjay/mvp_qr_gen/commit/8261c41a271c0b6d7c294ded523bf1a4ecda6394))

- **api**: Migrate to modern FastAPI structure
  ([`131be20`](https://github.com/gsinghjay/mvp_qr_gen/commit/131be20d9f7cab7a90c25a43afbeb88a81e20712))

- Move router endpoints to app/api/v1/endpoints - Organize endpoints by resource rather than
  operation type - Implement proper API versioning with nested routers - Maintain backward
  compatibility for all endpoints - Remove old router structure - Update main.py to use new router
  imports - Add test script to verify API restructuring - Create documentation in app/api/README.md

- **auth**: Delete portal-login.html template as part of login removal
  ([`67f3fd2`](https://github.com/gsinghjay/mvp_qr_gen/commit/67f3fd2fc2cc5fef889eb98e5799a590ee9b3a89))

- **js**: Remove setupLoginButtons function from main.js
  ([`a55d31f`](https://github.com/gsinghjay/mvp_qr_gen/commit/a55d31f55eaeb336b04006dd26e142760d6dfa89))

- **ui**: Remove logout link from base.html template
  ([`01556f5`](https://github.com/gsinghjay/mvp_qr_gen/commit/01556f5e2ccfe53acff4d00b052529825a6f4b97))


## v0.16.0 (2025-04-30)

### Features

- Add type aliases for common dependencies
  ([`5dce8fd`](https://github.com/gsinghjay/mvp_qr_gen/commit/5dce8fd2906164120c1f66e0f607ec91f78063fd))

- Create DbSessionDep, QRRepositoryDep, and QRServiceDep - Use Annotated syntax for modern FastAPI
  type annotations - Prepare for future adoption in router endpoints

- Implement BaseRepository with generic CRUD operations
  ([`103e5f1`](https://github.com/gsinghjay/mvp_qr_gen/commit/103e5f1fe2530792b70e774e51f1976b4cdb9cbd))

- Create generic BaseRepository with type-safe operations - Implement get_by_id, get_all, create,
  update, delete methods - Add proper error handling and logging - Use with_retry decorator for
  operations prone to locking

- Implement QRCodeRepository for QR code database operations
  ([`f82bd0c`](https://github.com/gsinghjay/mvp_qr_gen/commit/f82bd0cacfce1e0e4ad83a9926b8ec6367ac4af2))

- Create QRCodeRepository extending BaseRepository - Implement QR-specific methods like
  get_by_content - Add custom update_qr method for attribute-based updates - Implement scan tracking
  methods with proper error handling - Move list_qr_codes functionality to repository layer

### Refactoring

- Update dependency injection to use repository pattern
  ([`0321c46`](https://github.com/gsinghjay/mvp_qr_gen/commit/0321c46a5f578ab4a326b5839d65c60a67c5ec33))

- Update get_qr_service to accept repository dependency - Create new get_qr_repository dependency -
  Use Annotated syntax for modern FastAPI dependency injection - Add get_db shorthand dependency for
  consistency

- Update QRCodeService to use repository pattern
  ([`31f9870`](https://github.com/gsinghjay/mvp_qr_gen/commit/31f98709a482addae461846cfb6857a9b9ede08f))

- Replace direct database access with repository calls - Remove duplicate error handling now in
  repository layer - Use repository.update_qr for dynamic QR updates - Delegate scan statistics
  tracking to repository - Keep business logic validation in service layer


## v0.15.0 (2025-04-30)

### Bug Fixes

- **db**: Improve database persistence by creating backups instead of removing database file
  ([`e155222`](https://github.com/gsinghjay/mvp_qr_gen/commit/e1552226f29d15961c7b46e5468288b88b6e8b54))

- **keycloak**: Configure traefik routing with explicit naming for keycloak service
  ([`55673c0`](https://github.com/gsinghjay/mvp_qr_gen/commit/55673c0f325097aee39fc1522e5bfca5acf07043))

### Build System

- Remove Keycloak and authentication-related dependencies
  ([`f3e88aa`](https://github.com/gsinghjay/mvp_qr_gen/commit/f3e88aa256a768891627c5ae7f696aa8332d10b9))

### Chores

- Redundant file, no longer using Giga
  ([`9add430`](https://github.com/gsinghjay/mvp_qr_gen/commit/9add430bd05123e7f12226d66e4a2a9ef8a6bba3))

- Update gitignore patterns
  ([`3799bb4`](https://github.com/gsinghjay/mvp_qr_gen/commit/3799bb4a83cd2f83c634953e4cb4613dc227a976))

- Update gitignore to exclude project rules
  ([`ba97fa0`](https://github.com/gsinghjay/mvp_qr_gen/commit/ba97fa041973a876671bf65af947d76c80223625))

- Update gitignore with Keycloak-related patterns
  ([`2d674c2`](https://github.com/gsinghjay/mvp_qr_gen/commit/2d674c23e11685c91608dda9819667098a5763a7))

- Updated gitignore to include sensitive data
  ([`02a404d`](https://github.com/gsinghjay/mvp_qr_gen/commit/02a404d9da51700397feae30a92b4c9ee07dcb78))

### Documentation

- Update infrastructure documentation for network-based security model
  ([`d6b055d`](https://github.com/gsinghjay/mvp_qr_gen/commit/d6b055da1fbc5dc4bd016c8b35cb92559eb75783))

- Update project story to reflect security model evolution
  ([`3d3f70d`](https://github.com/gsinghjay/mvp_qr_gen/commit/3d3f70dc5e4d85f9e55428fbed6324696362a19a))

- Update README to reflect simplified security architecture
  ([`bd338a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/bd338a7fdf7cf4da4eafb6a91392a1dab802b771))

- Update system documentation to include Keycloak migration
  ([`faa7b32`](https://github.com/gsinghjay/mvp_qr_gen/commit/faa7b32bed724c1f889630e8e98488d0e4b71490))

- **infra**: Update infrastructure documentation with Keycloak integration
  ([`f4725f2`](https://github.com/gsinghjay/mvp_qr_gen/commit/f4725f2b847b38193d461a0306190bc43ca27635))

### Features

- Add access-restricted page for unauthorized navigation attempts
  ([`83215ba`](https://github.com/gsinghjay/mvp_qr_gen/commit/83215ba658b6133be02585cc552a12f4e9e59903))

- Add HCCC QR logo for branded QR codes
  ([`6f3080d`](https://github.com/gsinghjay/mvp_qr_gen/commit/6f3080ddbc2e8d88e3e0fc0b45fa9d50ef802db0))

- **infra**: Migrate from bind mounts to named volumes for improved permission handling
  ([`64b502e`](https://github.com/gsinghjay/mvp_qr_gen/commit/64b502ec727773de3615204980755a918777ec9b))

### Refactoring

- Migrate from qrcode library to segno for improved QR generation
  ([`6732bad`](https://github.com/gsinghjay/mvp_qr_gen/commit/6732bad28aeaa6e8bd9c28e8f028c46cd2dfd9d5))

- Remove authentication dependencies from services and schemas
  ([`2a68b85`](https://github.com/gsinghjay/mvp_qr_gen/commit/2a68b85bc2076bd6a35f6442ff571516dce44f9d))

- Remove authentication directory and related code
  ([`f02ca75`](https://github.com/gsinghjay/mvp_qr_gen/commit/f02ca750a60e0af5b06ff7fa1ad086e71257f98d))

- Remove authentication environment variables from docker-compose
  ([`5940134`](https://github.com/gsinghjay/mvp_qr_gen/commit/59401345d55e9f6ea1d771c3f0e7083a61f32f8e))

- Remove authentication from frontend JavaScript
  ([`f057b8a`](https://github.com/gsinghjay/mvp_qr_gen/commit/f057b8abb419b3a6e13a3a20ee1de143cff41082))

- Remove authentication imports and dependencies from routers
  ([`d868f3e`](https://github.com/gsinghjay/mvp_qr_gen/commit/d868f3ef10da3442c444bbcc9b1b9a21e4515813))

- Remove authentication middleware and setup from main application
  ([`0ac70ab`](https://github.com/gsinghjay/mvp_qr_gen/commit/0ac70ab538c8dd963a4fd47420f748c3936844a9))

- Remove authentication router
  ([`6eba6d7`](https://github.com/gsinghjay/mvp_qr_gen/commit/6eba6d75ccf1b3ddb7ddd569cc5e27bf4388f2e9))

- Remove authentication UI elements from templates
  ([`4e4e575`](https://github.com/gsinghjay/mvp_qr_gen/commit/4e4e575f1b2d54a492ff2c96ee9e1aed3fcc2f11))

- Remove SESSION_SECRET_KEY and authentication config from settings
  ([`51ac389`](https://github.com/gsinghjay/mvp_qr_gen/commit/51ac38967fa9bcdbf7130230b9f9e8013eccd473))

- Simplify database session handling without auth considerations
  ([`e5e5091`](https://github.com/gsinghjay/mvp_qr_gen/commit/e5e5091b8c91873535592f0f112c0904975bbb61))

- Simplify security middleware without authentication
  ([`3a6f9e2`](https://github.com/gsinghjay/mvp_qr_gen/commit/3a6f9e2b6bcda5d9da884cfd47d8612e69fc4c77))

- Update scripts to remove authentication dependencies
  ([`be4daae`](https://github.com/gsinghjay/mvp_qr_gen/commit/be4daae02b49b908e83eee4478cd39052d63de94))

### Testing

- Remove authentication-related tests
  ([`848a45a`](https://github.com/gsinghjay/mvp_qr_gen/commit/848a45a1063e1f106e27e23572049dfbab43fc84))


## v0.14.0 (2025-03-25)

### Features

- **js**: Update JavaScript modules to support new templates
  ([`29e8099`](https://github.com/gsinghjay/mvp_qr_gen/commit/29e809965d5af2cec60daca59647ad8f2c6c8e3d))

- **routes**: Implement server-side routes for template pages
  ([`0961578`](https://github.com/gsinghjay/mvp_qr_gen/commit/09615781f085be7633e6d3ea4e0e0df32deb7ff7))

- **ui**: Add QR code detail view with statistics and actions
  ([`9c0f60c`](https://github.com/gsinghjay/mvp_qr_gen/commit/9c0f60c1621a8f8847c55729c7472b660d3929f5))

- **ui**: Add QR code listing page with sorting and filtering
  ([`5be7451`](https://github.com/gsinghjay/mvp_qr_gen/commit/5be74515c52bf1aac5c494484b154b89e0223ece))

- **ui**: Create dashboard template extending base layout
  ([`17c29a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/17c29a7f25f3ef8e8d0cae9cf1076383d665beef))

- **ui**: Implement base template with common elements
  ([`1071cd0`](https://github.com/gsinghjay/mvp_qr_gen/commit/1071cd09d883a25ea0cdf9ee69f7181ae504ddfb))

- **ui**: Implement QR code creation page with tabs and preview
  ([`4a1a9d1`](https://github.com/gsinghjay/mvp_qr_gen/commit/4a1a9d1894cf06f3f1bf4ea688129c94e396c4fa))

### Refactoring

- **ui**: Remove redundant user info and notification elements from navbar
  ([`9b05246`](https://github.com/gsinghjay/mvp_qr_gen/commit/9b05246a85eb2e07bd16aac18f03bc2a2e8f4e6d))


## v0.13.0 (2025-03-18)

### Bug Fixes

- Update QR code redirection with proper BASE_URL handling
  ([`f84c2a7`](https://github.com/gsinghjay/mvp_qr_gen/commit/f84c2a799fff834b553a2814b28440289514063e))

- Update test script to handle full URL format with BASE_URL
  ([`db47110`](https://github.com/gsinghjay/mvp_qr_gen/commit/db471104702920cb0c72a98c8c7565cbc24c6838))

- Update UI components and CSS styles for improved layout
  ([`f24039f`](https://github.com/gsinghjay/mvp_qr_gen/commit/f24039f783875c8222c31f50edb1297d30723f4c))

### Chores

- Update Docker configuration with BASE_URL environment
  ([`70c8573`](https://github.com/gsinghjay/mvp_qr_gen/commit/70c857316e9b6d6c8c9c1f5d820960bef39d3608))

- Updated diagrams
  ([`48e0527`](https://github.com/gsinghjay/mvp_qr_gen/commit/48e052771e4297e374b7352e3f11d42d923bec47))

### Code Style

- **portal**: Enhance styling for portal login page
  ([`cca70bd`](https://github.com/gsinghjay/mvp_qr_gen/commit/cca70bd8f0ad7340333ffe838ef2cded0eae53d4))

- **ui**: Add styles for table rows and interaction states
  ([`c40e0d0`](https://github.com/gsinghjay/mvp_qr_gen/commit/c40e0d0b79d79e60ef00c9472fdd84c5c2269bf0))

### Documentation

- Remove obsolete task_msal.md file
  ([`0570c93`](https://github.com/gsinghjay/mvp_qr_gen/commit/0570c93a495f0a1450a59058117a56dba0ecce8a))

### Features

- Add QR content display to modal view for better user experience
  ([`82da8c4`](https://github.com/gsinghjay/mvp_qr_gen/commit/82da8c4f550a2e07d386f9ce1840ee749cd3701b))

- **api**: Add search and sorting functionality to QR code listing
  ([`073415c`](https://github.com/gsinghjay/mvp_qr_gen/commit/073415c6e7165cbb3e973819c148d3204b4ab388))

- **auth**: Add group membership support to SSO implementation
  ([`74e40f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/74e40f77a6d78314838b761643d43d7a0e52081b))

- **auth**: Add group-based endpoints and authorization
  ([`8678671`](https://github.com/gsinghjay/mvp_qr_gen/commit/8678671739b8f4cf18661ac548bc7dd3e27f76e0))

- **auth**: Add scope inspection endpoints for OAuth debugging and RBAC support
  ([`431fbd8`](https://github.com/gsinghjay/mvp_qr_gen/commit/431fbd8789ce456085a7d0a844f0598f88023bff))

- **js**: Add search and sort functionality to QR code dashboard
  ([`b73119d`](https://github.com/gsinghjay/mvp_qr_gen/commit/b73119d7fc3d413d224decd079118f1dd26cc73c))

- **portal**: Add client-side functionality for portal login
  ([`0d9e3dd`](https://github.com/gsinghjay/mvp_qr_gen/commit/0d9e3dd60204b4d08f2e16bb3c682fb80d9b1c1a))

- **portal**: Update portal login template for improved user experience
  ([`2b431f7`](https://github.com/gsinghjay/mvp_qr_gen/commit/2b431f72f935d353e0cb5cf817996167d7d3c225))

- **templates**: Create portal-login.html template
  ([`0624d60`](https://github.com/gsinghjay/mvp_qr_gen/commit/0624d60848e4921a9e644ce05fbefcab8aeaedfa))

- **ui**: Enhance QR code table with semantic HTML5 elements
  ([`761a585`](https://github.com/gsinghjay/mvp_qr_gen/commit/761a58564ef59aa76dd56918cf402fe7408b59fc))

- **ui**: Implement event delegation for table interactions
  ([`9a1dae3`](https://github.com/gsinghjay/mvp_qr_gen/commit/9a1dae3973e2a0b1fed49d8013792b2450cba761))

- **ui**: Implement table header sorting with visual indicators
  ([`162040e`](https://github.com/gsinghjay/mvp_qr_gen/commit/162040e3797d7cb542bc4fe4a45cf7779cbd2663))

- **ui**: Improve QR list rendering with better data formatting
  ([`26b4f6b`](https://github.com/gsinghjay/mvp_qr_gen/commit/26b4f6b9776499ea3783f21a4a3e46d1229da1a3))

- **web**: Add portal login route in pages.py
  ([`78cba5a`](https://github.com/gsinghjay/mvp_qr_gen/commit/78cba5a8b15e46e4eb49ab218f10ca94ea59bd2c))

### Testing

- **auth**: Add comprehensive tests for logout functionality
  ([`ee2a12d`](https://github.com/gsinghjay/mvp_qr_gen/commit/ee2a12dfba24ae1b41d22896e8aa40dfc846eb9e))

- **auth**: Add tests for group membership functionality
  ([`f9da740`](https://github.com/gsinghjay/mvp_qr_gen/commit/f9da7400ec4a59e80feed26a3e77e6d38f103aeb))

- **auth**: Update auth endpoint tests for group support
  ([`41cb2db`](https://github.com/gsinghjay/mvp_qr_gen/commit/41cb2db59268c285c769b69aaa75afa11964b810))


## v0.12.0 (2025-03-12)

### Bug Fixes

- **tests**: Skip flaky middleware conditional activation test
  ([`5ecb61a`](https://github.com/gsinghjay/mvp_qr_gen/commit/5ecb61abf74bf1c6d0c8ed011a7ad2442988931e))

### Chores

- Format with ruff and black
  ([`9d6c9f0`](https://github.com/gsinghjay/mvp_qr_gen/commit/9d6c9f09327a97fe4c5b64ad6fced96730db10ed))

### Documentation

- **tasks**: Update SSO implementation progress
  ([`8f0461a`](https://github.com/gsinghjay/mvp_qr_gen/commit/8f0461a33e532c4dd1da48e069dfcd07eb32ebe9))

### Features

- **auth**: Implement SSO dependencies and configuration
  ([`db6cc74`](https://github.com/gsinghjay/mvp_qr_gen/commit/db6cc74a515673f8963ad4e783b5124dd2ea1be7))

- **auth**: Implement SSO login and callback endpoints
  ([`d27d7f8`](https://github.com/gsinghjay/mvp_qr_gen/commit/d27d7f8c9fb9e11254079d9ab0493d52606d72ef))

- **router**: Integrate authentication router into application
  ([`ff07a3b`](https://github.com/gsinghjay/mvp_qr_gen/commit/ff07a3b4d00155d478f2a90d4ef79cce7bdac314))

### Testing

- **auth**: Add comprehensive tests for SSO endpoints
  ([`4d8646f`](https://github.com/gsinghjay/mvp_qr_gen/commit/4d8646f16eeb9508203a990379d3148151388c2e))


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
