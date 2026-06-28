# Social OAuth local testing

This project exposes API endpoints for Google and GitHub OAuth code exchange:

```http
POST /api/v1/account/oauth/google/
POST /api/v1/account/oauth/github/
```

Request body:

```json
{
  "code": "AUTHORIZATION_CODE_FROM_PROVIDER",
  "redirectUri": "http://localhost:3000/oauth/callback"
}
```

## Local environment

Copy these values into your real `deployment/env/local.env` file:

```env
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret

OAUTH_ALLOWED_REDIRECT_URIS=http://localhost:3000/oauth/callback
OAUTH_DEFAULT_USER_ROLE_SYMBOL=user
OAUTH_HTTP_TIMEOUT_SECONDS=10
```

Do not commit real client secrets.

## Run backend

Terminal 1:

```bash
python dealio/project/manage.py migrate
python dealio/project/manage.py runserver 8000
```

## Test Google

Terminal 2:

```bash
python dealio/project/manage.py test_social_oauth google
```

## Test GitHub

Terminal 2:

```bash
python dealio/project/manage.py test_social_oauth github
```

The command opens the provider login page, receives the temporary OAuth `code` on `http://localhost:3000/oauth/callback`, validates `state`, then sends the code to your Django backend.

Google/GitHub redirect only a temporary `code`, `state`, and scope metadata to the callback URL. Your backend exchanges the code with the provider using the client ID and client secret, then receives the verified user profile and returns your JWT response.
