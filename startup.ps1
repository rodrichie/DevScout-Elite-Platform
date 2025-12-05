# DevScout Elite Platform - Complete Startup Script
# ===================================================
# This script starts all services and runs end-to-end tests

param(
    [switch]$SkipTests,
    [switch]$QuickStart
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "DevScout Elite Platform - Startup" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

# Step 1: Check Docker
Write-Host "[1/6] Checking Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "  $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Step 2: Check if .env exists
Write-Host "`n[2/6] Checking environment configuration..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "  Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  .env file created. You can customize it if needed." -ForegroundColor Green
} else {
    Write-Host "  .env file exists" -ForegroundColor Green
}

# Step 3: Start services
Write-Host "`n[3/6] Starting Docker services..." -ForegroundColor Cyan
Write-Host "  This will take 2-3 minutes for first-time startup..." -ForegroundColor Yellow

docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to start services!" -ForegroundColor Red
    exit 1
}

Write-Host "  All services started successfully!" -ForegroundColor Green

# Step 4: Wait for services
if (-not $QuickStart) {
    Write-Host "`n[4/6] Waiting for services to initialize..." -ForegroundColor Cyan
    Write-Host "  Progress: " -NoNewline
    
    for ($i = 1; $i -le 60; $i++) {
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline -ForegroundColor Yellow
        if ($i % 10 -eq 0) {
            Write-Host " $i/60s" -NoNewline -ForegroundColor Gray
        }
    }
    Write-Host "`n  Services should now be ready!" -ForegroundColor Green
} else {
    Write-Host "`n[4/6] Quick start mode - skipping wait" -ForegroundColor Yellow
}

# Step 5: Display access points
Write-Host "`n[5/6] Service Access Points:" -ForegroundColor Cyan
Write-Host "  Airflow UI:     http://localhost:8080 (airflow/airflow)" -ForegroundColor White
Write-Host "  FastAPI:        http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Streamlit:      http://localhost:8501" -ForegroundColor White
Write-Host "  MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor White
Write-Host "  Grafana:        http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host "  Spark Master:   http://localhost:8089" -ForegroundColor White
Write-Host "  Jupyter:        http://localhost:8888 (token: devscout)" -ForegroundColor White

# Step 6: Run tests
if (-not $SkipTests) {
    Write-Host "`n[6/6] Running end-to-end tests..." -ForegroundColor Cyan
    Write-Host "  Waiting 10 more seconds for API to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    try {
        python tests/e2e_test.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n  All tests passed!" -ForegroundColor Green
        } else {
            Write-Host "`n  Some tests failed. Check logs above." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Could not run tests: $_" -ForegroundColor Yellow
        Write-Host "  Run manually: python tests/e2e_test.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[6/6] Tests skipped (-SkipTests flag)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "Startup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Blue

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open Airflow UI: http://localhost:8080" -ForegroundColor White
Write-Host "  2. Trigger DAG: 'resume_etl_v1' or 'github_ingestion_v1'" -ForegroundColor White
Write-Host "  3. View Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "  4. Test API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n  To view logs: docker-compose logs -f [service-name]" -ForegroundColor Gray
Write-Host "  To stop: docker-compose down" -ForegroundColor Gray
Write-Host ""
