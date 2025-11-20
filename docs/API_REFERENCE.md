# API Reference Documentation

## Overview

The DevScout Elite Platform provides a comprehensive RESTful API for accessing candidate data, performing semantic searches, and retrieving analytics. All endpoints require OAuth2 authentication except for health checks.

## Base URL

```
http://localhost:8000
```

Production: Replace with your deployed URL

---

## Authentication

### Get Access Token

**Endpoint**: `POST /api/v1/auth/token`

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "username": "admin",
    "email": "admin@devscout.com",
    "role": "admin"
  }
}
```

**Default Users**:
- **Admin**: username=`admin`, password=`secret`
- **Recruiter**: username=`recruiter`, password=`secret`

### Using the Token

Include the token in all subsequent requests:

```bash
curl -H "Authorization: Bearer <your_token>" \
  "http://localhost:8000/api/v1/candidates"
```

### Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Response**:
```json
{
  "username": "admin",
  "email": "admin@devscout.com",
  "role": "admin"
}
```

---

## Candidates API

### List Candidates

**Endpoint**: `GET /api/v1/candidates`

**Query Parameters**:
- `skip` (integer, default=0): Number of records to skip
- `limit` (integer, default=20, max=100): Maximum records to return
- `min_score` (float, optional): Minimum overall score filter

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/candidates?skip=0&limit=20&min_score=70"
```

**Response**:
```json
[
  {
    "candidate_id": 1,
    "candidate_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "years_experience": 5,
    "education_level": "Bachelor",
    "skill_count": 15,
    "github_username": "johndoe",
    "github_score": 85.5,
    "overall_score": 88.3,
    "rank": 1,
    "created_at": "2025-11-20T10:00:00Z"
  }
]
```

### Get Candidate by ID

**Endpoint**: `GET /api/v1/candidates/{candidate_id}`

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/candidates/1"
```

**Response**: Same structure as list item above

### Get Candidate Skills

**Endpoint**: `GET /api/v1/candidates/{candidate_id}/skills`

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/candidates/1/skills"
```

**Response**:
```json
[
  {
    "skill_name": "Python",
    "skill_category": "Programming Languages",
    "proficiency_level": "Expert"
  },
  {
    "skill_name": "PostgreSQL",
    "skill_category": "Databases",
    "proficiency_level": "Advanced"
  }
]
```

### Search Candidates

**Endpoint**: `POST /api/v1/candidates/search`

**Request Body**:
```json
{
  "query": "python developer",
  "max_results": 10,
  "min_score": 70.0,
  "required_skills": ["Python", "SQL"]
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/candidates/search" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "senior python developer",
    "max_results": 10,
    "min_score": 75
  }'
```

**Response**:
```json
{
  "query": "senior python developer",
  "results_count": 5,
  "candidates": [
    {
      "candidate_id": 1,
      "candidate_name": "John Doe",
      "email": "john.doe@example.com",
      "years_experience": 5,
      "education_level": "Bachelor",
      "skill_count": 15,
      "overall_score": 88.3,
      "rank": 1
    }
  ]
}
```

---

## Skills API

### List Skills

**Endpoint**: `GET /api/v1/skills`

**Query Parameters**:
- `skip` (integer, default=0)
- `limit` (integer, default=50, max=200)
- `category` (string, optional): Filter by skill category
- `min_candidates` (integer, default=1): Minimum number of candidates with skill

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/skills?category=Programming%20Languages&limit=20"
```

**Response**:
```json
[
  {
    "skill_name": "Python",
    "skill_category": "Programming Languages",
    "candidate_count": 45,
    "total_occurrences": 67,
    "proficiency_level": "Various"
  }
]
```

### Get Skill Categories

**Endpoint**: `GET /api/v1/skills/categories`

**Response**:
```json
[
  {
    "category": "Programming Languages",
    "skill_count": 25,
    "candidate_count": 150
  },
  {
    "category": "Databases",
    "skill_count": 15,
    "candidate_count": 120
  }
]
```

### Get Trending Skills

**Endpoint**: `GET /api/v1/skills/trending`

**Query Parameters**:
- `limit` (integer, default=20, max=50)

**Response**:
```json
[
  {
    "skill_name": "Kubernetes",
    "skill_category": "DevOps",
    "candidate_count": 35,
    "last_seen": "2025-11-20"
  }
]
```

---

## GitHub API

### Get GitHub Profile

**Endpoint**: `GET /api/v1/github/{username}`

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/github/johndoe"
```

**Response**:
```json
{
  "candidate_id": 1,
  "github_username": "johndoe",
  "total_repos": 25,
  "total_stars": 150,
  "total_forks": 45,
  "followers_count": 75,
  "contributions_90_days": 320,
  "top_language": "Python",
  "code_quality_score": 85.5,
  "contribution_score": 88.0,
  "impact_score": 82.3,
  "overall_github_score": 85.6
}
```

### Get Top Contributors

**Endpoint**: `GET /api/v1/github/stats/top-contributors`

**Query Parameters**:
- `limit` (integer, default=20, max=100)
- `metric` (string, default="overall"): One of `overall`, `stars`, `repos`, `contributions`

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/github/stats/top-contributors?metric=stars&limit=10"
```

**Response**:
```json
[
  {
    "username": "johndoe",
    "total_repos": 25,
    "total_stars": 150,
    "contributions_90_days": 320,
    "top_language": "Python",
    "overall_score": 85.6
  }
]
```

### Get Language Distribution

**Endpoint**: `GET /api/v1/github/stats/languages`

**Response**:
```json
[
  {
    "language": "Python",
    "user_count": 45,
    "avg_repos": 18.5,
    "avg_stars": 125.3
  },
  {
    "language": "JavaScript",
    "user_count": 38,
    "avg_repos": 22.1,
    "avg_stars": 95.7
  }
]
```

---

## Semantic Search API

### Semantic Candidate Search

**Endpoint**: `GET /api/v1/semantic/search`

**Query Parameters**:
- `query` (string, required): Natural language search query
- `limit` (integer, default=10, max=50)
- `min_certainty` (float, default=0.7): Minimum similarity score (0-1)

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/semantic/search?query=experienced%20backend%20engineer%20with%20cloud%20expertise&limit=10"
```

**Response**:
```json
{
  "query": "experienced backend engineer with cloud expertise",
  "results_count": 5,
  "candidates": [
    {
      "candidateId": 1,
      "candidateName": "John Doe",
      "email": "john.doe@example.com",
      "skills": ["Python", "AWS", "Docker", "PostgreSQL"],
      "yearsExperience": 5,
      "educationLevel": "Bachelor",
      "githubUsername": "johndoe",
      "overallScore": 88.3,
      "similarity_score": 0.92
    }
  ]
}
```

### Find Similar Candidates

**Endpoint**: `GET /api/v1/semantic/similar/{candidate_id}`

**Query Parameters**:
- `limit` (integer, default=5, max=20)

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/semantic/similar/1?limit=5"
```

**Response**:
```json
{
  "reference_candidate_id": 1,
  "similar_count": 5,
  "similar_candidates": [
    {
      "candidateId": 15,
      "candidateName": "Jane Smith",
      "email": "jane.smith@example.com",
      "skills": ["Python", "AWS", "Kubernetes"],
      "yearsExperience": 6,
      "educationLevel": "Master",
      "overallScore": 87.5,
      "similarity_score": 0.89
    }
  ]
}
```

### Semantic Skill Search

**Endpoint**: `GET /api/v1/semantic/skills/semantic`

**Query Parameters**:
- `query` (string, required)
- `limit` (integer, default=10, max=30)

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/semantic/skills/semantic?query=machine%20learning%20frameworks"
```

**Response**:
```json
{
  "query": "machine learning frameworks",
  "results_count": 5,
  "skills": [
    {
      "skillName": "TensorFlow",
      "skillCategory": "Machine Learning",
      "description": "TensorFlow is a Machine Learning skill...",
      "candidateCount": 25,
      "relevance_score": 0.94
    }
  ]
}
```

### Vector Database Stats

**Endpoint**: `GET /api/v1/semantic/stats`

**Response**:
```json
{
  "status": "healthy",
  "candidates_indexed": 150,
  "skills_indexed": 245
}
```

---

## Analytics API

### Platform Summary

**Endpoint**: `GET /api/v1/analytics/summary`

**Example**:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/analytics/summary"
```

**Response**:
```json
{
  "total_candidates": 150,
  "avg_experience": 4.5,
  "total_skills": 245,
  "avg_score": 75.3,
  "top_skills": [
    {"skill": "Python", "count": 45},
    {"skill": "JavaScript", "count": 38}
  ],
  "score_distribution": {
    "Elite": 15,
    "Strong": 35,
    "Good": 60,
    "Average": 30,
    "Below Average": 10
  }
}
```

### Pipeline Health

**Endpoint**: `GET /api/v1/analytics/pipeline-health`

**Response**:
```json
[
  {
    "pipeline": "resume_etl_v1",
    "total_runs": 50,
    "successful_runs": 48,
    "success_rate": 96.0,
    "avg_execution_time": 180.5,
    "last_run": "2025-11-20T10:30:00Z"
  },
  {
    "pipeline": "github_ingestion_v1",
    "total_runs": 30,
    "successful_runs": 29,
    "success_rate": 96.67,
    "avg_execution_time": 450.2,
    "last_run": "2025-11-20T11:00:00Z"
  }
]
```

### Hiring Trends

**Endpoint**: `GET /api/v1/analytics/trends/hiring`

**Response**:
```json
{
  "experience_distribution": [
    {
      "range": "0-2 years",
      "count": 25,
      "avg_github_score": 70.5
    },
    {
      "range": "2-5 years",
      "count": 50,
      "avg_github_score": 78.2
    }
  ],
  "education_distribution": [
    {
      "level": "Master",
      "count": 45,
      "avg_score": 82.5
    },
    {
      "level": "Bachelor",
      "count": 85,
      "avg_score": 76.3
    }
  ]
}
```

---

## Health & Status

### Health Check

**Endpoint**: `GET /health`

**No authentication required**

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-20T12:00:00Z"
}
```

### API Status

**Endpoint**: `GET /api/v1/status`

**Response**:
```json
{
  "api_version": "1.0.0",
  "environment": "development",
  "features": {
    "candidate_search": true,
    "skill_matching": true,
    "github_integration": true,
    "analytics": true,
    "vector_search": true
  }
}
```

### Root Endpoint

**Endpoint**: `GET /`

**Response**:
```json
{
  "name": "DevScout Elite API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "endpoints": {
    "candidates": "/api/v1/candidates",
    "skills": "/api/v1/skills",
    "github": "/api/v1/github",
    "analytics": "/api/v1/analytics"
  }
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Request body validation failed |
| 500 | Internal Server Error |
| 503 | Service Unavailable - External service down |

### Example Error Response

```json
{
  "detail": "Candidate not found"
}
```

---

## Rate Limiting

- **Default**: No rate limiting in development
- **Production**: Implement rate limiting per token/IP

---

## Interactive Documentation

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

Both provide interactive API testing and comprehensive schema documentation.

---

## SDK & Client Libraries

### Python Client Example

```python
import requests

# Authenticate
response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    data={"username": "admin", "password": "secret"}
)
token = response.json()["access_token"]

# Make authenticated request
headers = {"Authorization": f"Bearer {token}"}
candidates = requests.get(
    "http://localhost:8000/api/v1/candidates",
    headers=headers,
    params={"limit": 10, "min_score": 75}
)

print(candidates.json())
```

### JavaScript Client Example

```javascript
// Authenticate
const authResponse = await fetch('http://localhost:8000/api/v1/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=admin&password=secret'
});
const { access_token } = await authResponse.json();

// Make authenticated request
const candidatesResponse = await fetch(
  'http://localhost:8000/api/v1/candidates?limit=10',
  {
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);
const candidates = await candidatesResponse.json();
console.log(candidates);
```

---

## Support

For issues or questions:
- GitHub Issues: <https://github.com/rodrichie/DevScout-Elite-Platform/issues>
- Documentation: `/docs` directory
- API Docs: <http://localhost:8000/docs>
