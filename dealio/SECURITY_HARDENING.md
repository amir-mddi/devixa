# Dealio security hardening

This package contains a source-level security audit and hardening pass for the
Django application. The existing controller → logic → repository → adapter
boundaries were preserved; security behavior was added at the relevant
boundary instead of being duplicated in controllers.

## Main fixes

### Authentication and authorization

- The global DRF default permission is authenticated access.
- Public endpoints explicitly opt in to `AllowAny`.
- JWT authentication rejects inactive and soft-deleted users.
- Authorization reads the current role from the database instead of trusting a
  potentially stale role claim from a token.
- Refresh-token rotation and the Simple JWT blacklist application are enabled.
- Password changes and resets revoke outstanding refresh tokens.
- The user directory is read-only: staff can list users, while a normal user can
  retrieve only their own account.
- Swagger, Redoc, and schema endpoints require an authenticated administrator.

### Account and verification security

- Email, phone verification, password recovery, and bot account-link codes use
  cryptographically secure six-digit generation.
- Verification values are stored as keyed HMAC digests rather than plaintext.
- `cache.add()` prevents replacing an unexpired code and prevents duplicate
  delivery while the previous code remains active.
- Failed verification attempts are counted and locked after the configured
  limit.
- Cache keys are purpose- and identifier-bound.
- Successful verification consumes the code.
- Phone and email changes automatically reset their verification status.
- Email and username uniqueness is enforced case-insensitively at database
  level.
- Soft-deleted users are deactivated.
- New/current passwords use Django password validation and current-password
  verification.
- Temporary passwords use `secrets` and have a twelve-character minimum with
  mixed character classes.

### Settings and deployment defaults

- Production refuses to start with an unsafe/missing `APP_SECRET_KEY` or empty
  `ALLOWED_HOSTS`.
- Debug Toolbar is installed only when `DEBUG` is enabled.
- CORS is deny-by-default outside local environments.
- Secure cookie, CSRF, HSTS, frame, referrer, MIME-sniffing, and SSL redirect
  settings are environment controlled with secure production defaults.
- Forwarded client IP and proxy SSL headers are trusted only when explicitly
  enabled and restricted to configured proxy addresses.
- Metrics are hidden outside debug mode unless protected by a metrics token.
- Request/file counts and sizes are bounded.

### Webhooks and bot integrations

- Telegram, Bale, and Rubika webhooks fail closed when a webhook secret is not
  configured.
- Webhook secrets use constant-time comparison.
- Webhook payload shape, update IDs, collection sizes, and string sizes are
  validated.
- All webhook responses are marked `no-store`/`no-cache`.
- Processing failures return a retryable 503 response instead of acknowledging
  failed updates.
- Bot HTTP adapters share one HTTPS-only, no-redirect, bounded-response
  transport that does not expose tokenized URLs or provider response bodies.
- Telegram file paths are checked before download and downloads are bounded.
- Update logs store only an event summary, not raw messages, OTPs, contacts, or
  phone numbers.
- Bot update-log retention is bounded and cleaned by a scheduled task.
- Runtime bot secrets are encrypted and no hard-coded encryption fallback is
  used.

### Payment security

- Payment gateway endpoints and redirects must use public HTTPS URLs and can be
  restricted by host allowlists.
- Provider redirects are rejected and provider responses are size-bounded.
- Provider response secrets are recursively redacted before persistence.
- Callback fields are allowlisted, normalized, length-limited, and control
  characters are rejected.
- Callback processing uses a database transaction and row lock for idempotent
  concurrent processing.
- Public callback responses expose only the success result and are marked
  `no-store`.
- Frontend callback redirects are validated and query parameters are encoded.
- Payment callbacks have a dedicated trusted-client-IP throttle.
- Public receipt serialization no longer exposes internal moderation notes or
  reviewer identities.

### Upload and outbound-request validation

- Receipt and course-thumbnail uploads validate extension, content type, magic
  bytes, actual image decoding, dimensions, pixel count, and file size.
- Pillow decompression-bomb warnings/errors are rejected.
- User-provided outbound URLs require public HTTPS destinations and reject
  loopback, private, link-local, and unsafe targets.
- Project social/bot links and initial environment configuration are sanitized.
- OAuth redirects use an exact allowlist, OAuth responses are bounded, inactive
  users cannot authenticate, and raw provider profiles are reduced before
  persistence.

### Logging, secrets, backups, and messaging

- Sensitive request fields and tokenized URLs are redacted from request logs.
- Base-model audit logging redacts secret/password/token/API-key fields.
- API keys are write-only through the API and masked in list/admin views; the
  admin change page never renders the stored raw value.
- Database backup and transfer commands use argument arrays, bounded timeouts,
  restricted paths, and never use `shell=True`.
- RabbitMQ and Kafka no longer use hard-coded credentials and do not log message
  bodies.
- Messaging adapters are instantiated lazily so unrelated application paths do
  not require those external services.

## New migrations

Apply these migrations before starting the updated application:

- `accounts/0012_security_hardening.py`
- `accounts/0013_alter_customuser_options.py`
- `billing/0005_alter_discountcode_minimum_order_amount_and_more.py`
- `courses/0003_alter_course_price.py`

`accounts/0012_security_hardening.py` deliberately stops if existing usernames
or non-empty emails collide case-insensitively. Resolve those duplicates before
running the migration.

```bash
python -m dealio.project.manage migrate --noinput
```

## Important production configuration

Use strong, environment-specific values and do not commit them:

```env
ENV=production
IS_DEBUG=false
APP_SECRET_KEY=<long-random-secret>
ENCRYPTION_KEY=<separate-long-random-encryption-key>
ALLOWED_HOSTS=api.example.com
CORS_ORIGIN_ALLOW_ALL=false
CROSS_ORIGIN_DOMAIN=https://app.example.com

SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true

TRUST_PROXY_SSL_HEADER=true
TRUST_X_FORWARDED_FOR=true
TRUSTED_PROXY_IPS=<only-your-reverse-proxy-address-or-cidr>

PROMETHEUS_METRICS_TOKEN=<long-random-token>
TELEGRAM_WEBHOOK_SECRET=<long-random-secret>
BALE_WEBHOOK_SECRET=<long-random-secret>
RUBIKA_WEBHOOK_SECRET=<long-random-secret>

OAUTH_ALLOWED_REDIRECT_URIS=https://app.example.com/oauth/callback

PARDAKHTYAR_ALLOWED_HOSTS=gateway.example
PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS=pay.example
PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS=api.example.com
PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS=app.example.com
```

Only enable forwarded-header trust when the application is reachable solely
through the listed trusted proxy. Do not enable HSTS preload until every current
and future subdomain is HTTPS-ready.

## Secret rotation after deployment

Rotate credentials that may previously have existed in source, logs, database
exports, or deployment history:

- Django secret and encryption keys where operationally possible
- Kavenegar key
- Bot tokens and webhook secrets
- OAuth client secrets
- Payment merchant credentials
- Database, Redis, RabbitMQ, and Kafka credentials
- Metrics token

Changing `APP_SECRET_KEY` invalidates existing signed sessions/tokens. Changing
`ENCRYPTION_KEY` requires a planned migration of encrypted bot runtime values.

## Verification performed

```text
206 Django tests passed
System check identified no issues in test settings
No model changes were left without migrations
Python compilation completed successfully
```

Security regression coverage includes verification-code reuse and lockout,
permissions, inactive-token rejection, webhook authentication/payload limits,
payment callback privacy, SSRF prevention, provider-response bounds, secret
redaction, image-content validation, and bot update-log privacy.

## Audit boundary

This was a source-code and configuration audit of the uploaded Django project.
A package CVE/SBOM audit should also be run against the exact production lock or
requirements files in CI, for example with `pip-audit`, because dependency
versions and container/base-image vulnerabilities are a separate supply-chain
scope.
