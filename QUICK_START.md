# DevScout Elite Platform - Quick Reference

## Start Platform (One Command)

```powershell
.\startup.ps1
```

This will:
1. Check Docker is running
2. Create .env file
3. Start all 20 services
4. Wait 60 seconds
5. Run end-to-end tests
6. Display access URLs

---

## Service Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow** | http://localhost:8080 | airflow / airflow |
| **FastAPI** | http://localhost:8000/docs | admin / secret |
| **Streamlit Dashboard** | http://localhost:8501 | No login |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Spark Master** | http://localhost:8089 | No login |
| **Prometheus** | http://localhost:9090 | No login |
| **Jupyter** | http://localhost:8888 | token: devscout |

---

## Quick Commands

### Start/Stop
```powershell
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose restart        # Restart services
docker-compose ps             # Check status
```

### Testing
```powershell
python tests/e2e_test.py            # End-to-end tests
python tests/upload_sample_data.py  # Upload sample resumes
make quick-test                     # Quick health check
```

### Data Pipeline
```powershell
# Via Airflow UI: http://localhost:8080
# 1. Click on "resume_etl_v1" DAG
# 2. Click "Play" button → "Trigger DAG"
# 3. Watch execution in Graph view
```

### Database Access
```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U devscout -d devscout_dw

# Check data
SELECT COUNT(*) FROM silver.candidates;
SELECT COUNT(*) FROM silver.resume_skills;
SELECT * FROM gold.agg_candidate_rankings LIMIT 5;
```

### Logs
```powershell
docker-compose logs -f                # All logs
docker-compose logs -f fastapi        # API logs
docker-compose logs -f airflow-scheduler  # Airflow logs
```

---

## Testing Workflow (5 Minutes)

```powershell
# 1. Start services
.\startup.ps1

# 2. Upload sample data (if not done automatically)
python tests/upload_sample_data.py

# 3. Trigger pipeline in Airflow UI
# http://localhost:8080 → resume_etl_v1 → Play

# 4. Wait 5-7 minutes for completion

# 5. Check results
# - Dashboard: http://localhost:8501
# - API: http://localhost:8000/docs
```

---

## API Quick Test

```powershell
# 1. Get auth token
$response = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/token" `
  -Body @{username="admin"; password="secret"}

$token = $response.access_token

# 2. Test endpoints
$headers = @{Authorization="Bearer $token"}

# List candidates
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/candidates" -Headers $headers

# Get analytics
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analytics/summary" -Headers $headers
```

---

## Troubleshooting

### Docker not running
```powershell
# Start Docker Desktop manually
# Then run: .\startup.ps1
```

### Services won't start
```powershell
# Check resources
docker system df

# Clean up
docker system prune -a

# Restart
docker-compose down
docker-compose up -d
```

### No data in database
```powershell
# Upload sample data
python tests/upload_sample_data.py

# Trigger pipeline in Airflow UI
# http://localhost:8080

# Check logs
docker-compose logs airflow-scheduler
```

### API not responding
```powershell
# Check status
docker-compose ps fastapi

# Restart API
docker-compose restart fastapi

# Check logs
docker-compose logs fastapi
```

---

## Files to Review

| File | Purpose |
|------|---------|
| `README.md` | Main documentation |
| `COMPLETION_SUMMARY.md` | Project status |
| `docs/TESTING_GUIDE.md` | Complete testing workflow |
| `docs/API_REFERENCE.md` | API documentation |
| `docs/ARCHITECTURE.md` | System design |
| `docs/SECURITY.md` | Security guidelines |

---

## Next Steps

1. **Review Documentation**: Start with `README.md`
2. **Run Tests**: Execute `.\startup.ps1`
3. **Explore Dashboard**: http://localhost:8501
4. **Test API**: http://localhost:8000/docs
5. **View Monitoring**: http://localhost:3001

---

## Performance Expectations

- **Startup Time**: 60-90 seconds
- **Pipeline Execution**: 5-7 minutes (6 resumes)
- **API Response**: 50-200ms
- **Resource Usage**: 8-12GB RAM

---

## Production Checklist

- [ ] Generate secure JWT secret
- [ ] Change all default passwords
- [ ] Enable HTTPS/TLS
- [ ] Set up secrets management
- [ ] Configure monitoring alerts
- [ ] Deploy to Kubernetes
- [ ] Set up backups

See: `docs/SECURITY.md` for complete checklist

---

**Need Help?** Check `docs/TESTING_GUIDE.md` for detailed instructions
