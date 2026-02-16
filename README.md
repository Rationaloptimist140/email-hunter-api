# Email Hunter & Text Tools API

A FastAPI-based REST API that provides text processing utilities including email extraction, phone number formatting, and case conversion tools.

## Features

- **Email Extraction**: Extract and validate email addresses from text
- **Phone Number Formatting**: Clean and format phone numbers
- **Case Conversion**: Convert text between different cases (camel, snake, kebab, title)
- **API Key Authentication**: Secure endpoints with API key validation
- **Rate Limiting**: 10 requests per minute per IP for free tier
- **API Key Generation**: Generate demo keys for testing

## API Endpoints

### Public Endpoints (No Auth Required)

#### Health Check
```bash
GET /
GET /health
```

Returns API status and available endpoints.

#### Generate Demo API Key
```bash
POST /api/generate-key
```

Generates a test API key valid for 24 hours.

**Example:**
```bash
curl -X POST https://your-api.railway.app/api/generate-key
```

**Response:**
```json
{
  "api_key": "demo_abc123...",
  "valid_until": "2026-02-17T09:30:00Z",
  "note": "This is a demo key valid for 24 hours"
}
```

---

### Protected Endpoints (Require API Key)

All protected endpoints require the `X-API-Key` header:

```bash
-H "X-API-Key: your_api_key_here"
```

#### Extract Emails
```bash
POST /api/extract-emails
```

Extract email addresses from text input.

**Request Body:**
```json
{
  "text": "Contact us at support@example.com or sales@company.org"
}
```

**Example:**
```bash
curl -X POST https://your-api.railway.app/api/extract-emails \
  -H "X-API-Key: demo_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"text": "Email me at john@example.com or jane@test.org"}'
```

**Response:**
```json
{
  "emails": ["john@example.com", "jane@test.org"],
  "count": 2
}
```

#### Format Phone Number
```bash
POST /api/format-phone
```

Clean and format phone numbers.

**Request Body:**
```json
{
  "phone": "+1 (555) 123-4567",
  "country_code": "US"
}
```

**Example:**
```bash
curl -X POST https://your-api.railway.app/api/format-phone \
  -H "X-API-Key: demo_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1-555-123-4567", "country_code": "US"}'
```

#### Convert Case
```bash
POST /api/convert-case
```

Convert text between different cases.

**Request Body:**
```json
{
  "text": "hello world example",
  "case_type": "camel"
}
```

**Case Types:**
- `camel`: helloWorldExample
- `snake`: hello_world_example
- `kebab`: hello-world-example
- `title`: Hello World Example
- `upper`: HELLO WORLD EXAMPLE
- `lower`: hello world example

**Example:**
```bash
curl -X POST https://your-api.railway.app/api/convert-case \
  -H "X-API-Key: demo_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world", "case_type": "camel"}'
```

---

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd code/api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from example:
```bash
cp env.example .env
```

5. Edit `.env` and add your API keys:
```bash
API_KEYS=your_secure_master_key_here
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Run Locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the API at: `http://localhost:8000`

Access interactive docs at: `http://localhost:8000/docs`

---

## Railway Deployment

### Deploy to Railway

1. **Create a new Railway project:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" > "Deploy from GitHub repo"
   - Select your repository

2. **Configure environment variables:**
   - Go to your project settings
   - Add variable: `API_KEYS` with your master key(s)
   - Railway will auto-set `PORT`

3. **Deploy:**
   - Railway will automatically detect the Procfile
   - Build and deployment will start automatically

### Environment Variables

Required variables in Railway:
- `API_KEYS`: Comma-separated list of valid API keys
- `PORT`: Automatically set by Railway

### Configuration Files

- `Procfile`: Defines the web process command
- `railway.json`: Railway-specific configuration
- `requirements.txt`: Python dependencies
- `env.example`: Example environment variables

---

## API Authentication

### Using API Keys

Include the API key in the request header:

```bash
X-API-Key: your_api_key_here
```

### Master Keys

Set master keys in the `API_KEYS` environment variable (comma-separated):

```bash
API_KEYS=master_key_1,master_key_2,master_key_3
```

### Demo Keys

Generate temporary demo keys for testing:

```bash
curl -X POST https://your-api.railway.app/api/generate-key
```

Demo keys are valid for 24 hours and prefixed with `demo_`.

---

## Rate Limiting

- **Free tier**: 10 requests per minute per IP address
- Rate limit applies to all protected endpoints
- Returns HTTP 429 when limit exceeded

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Missing API key"
}
```

### 403 Forbidden
```json
{
  "detail": "Invalid API key"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Testing

### Test Health Check
```bash
curl https://your-api.railway.app/health
```

### Test Email Extraction (with demo key)
```bash
# 1. Generate demo key
DEMO_KEY=$(curl -s -X POST https://your-api.railway.app/api/generate-key | jq -r '.api_key')

# 2. Test email extraction
curl -X POST https://your-api.railway.app/api/extract-emails \
  -H "X-API-Key: $DEMO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact john@example.com for more info"}'
```

---

## Project Structure

```
code/api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Procfile            # Railway startup command
├── railway.json        # Railway configuration
├── env.example         # Environment variables template
└── README.md           # This file
```

---

## Tech Stack

- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **SlowAPI**: Rate limiting
- **Railway**: Hosting platform

---

## Support

For issues or questions:
- Check the interactive API docs at `/docs`
- Review error messages in API responses
- Verify API key is valid and included in headers

---

## License

[Your License Here]

---

## Quick Start Checklist

- [ ] Clone repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with `API_KEYS`
- [ ] Run locally: `uvicorn main:app --reload`
- [ ] Test at `http://localhost:8000/docs`
- [ ] Deploy to Railway
- [ ] Set `API_KEYS` environment variable in Railway
- [ ] Test live API at your Railway URL

---

Built with FastAPI | Deployed on Railway
