"""
Locust load testing for DevScout Elite API
Run: locust -f locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import random


class DevScoutUser(HttpUser):
    """Simulate user behavior on DevScout API."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token."""
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin",
            "password": "secret"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(5)
    def get_candidates(self):
        """Get list of candidates (most common)."""
        skip = random.randint(0, 100)
        self.client.get(
            f"/api/v1/candidates?skip={skip}&limit=20",
            headers=self.headers,
            name="/api/v1/candidates"
        )
    
    @task(3)
    def search_candidates(self):
        """Search candidates."""
        queries = [
            "python developer",
            "senior engineer",
            "machine learning",
            "full stack",
            "devops"
        ]
        query = random.choice(queries)
        self.client.post(
            "/api/v1/candidates/search",
            json={"query": query, "max_results": 10},
            headers=self.headers,
            name="/api/v1/candidates/search"
        )
    
    @task(2)
    def get_candidate_details(self):
        """Get individual candidate details."""
        candidate_id = random.randint(1, 100)
        self.client.get(
            f"/api/v1/candidates/{candidate_id}",
            headers=self.headers,
            name="/api/v1/candidates/{id}"
        )
    
    @task(2)
    def get_skills(self):
        """Get skills list."""
        self.client.get(
            "/api/v1/skills?limit=50",
            headers=self.headers,
            name="/api/v1/skills"
        )
    
    @task(1)
    def get_analytics(self):
        """Get analytics summary."""
        self.client.get(
            "/api/v1/analytics/summary",
            headers=self.headers,
            name="/api/v1/analytics/summary"
        )
    
    @task(1)
    def get_github_stats(self):
        """Get GitHub top contributors."""
        self.client.get(
            "/api/v1/github/stats/top-contributors?limit=20",
            headers=self.headers,
            name="/api/v1/github/stats/top-contributors"
        )
    
    @task(1)
    def semantic_search(self):
        """Semantic search (if Weaviate is available)."""
        queries = [
            "experienced backend engineer with cloud expertise",
            "data scientist with python and tensorflow",
            "frontend developer react vue"
        ]
        query = random.choice(queries)
        self.client.get(
            f"/api/v1/semantic/search?query={query}&limit=10",
            headers=self.headers,
            name="/api/v1/semantic/search"
        )
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="/health")


class AdminUser(HttpUser):
    """Simulate admin user with heavier operations."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Admin login."""
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin",
            "password": "secret"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(3)
    def get_pipeline_health(self):
        """Check pipeline health."""
        self.client.get(
            "/api/v1/analytics/pipeline-health",
            headers=self.headers,
            name="/api/v1/analytics/pipeline-health"
        )
    
    @task(2)
    def get_hiring_trends(self):
        """Get hiring trends."""
        self.client.get(
            "/api/v1/analytics/trends/hiring",
            headers=self.headers,
            name="/api/v1/analytics/trends/hiring"
        )
    
    @task(1)
    def get_all_skills_with_candidates(self):
        """Heavy query - all skills."""
        self.client.get(
            "/api/v1/skills?limit=200&min_candidates=1",
            headers=self.headers,
            name="/api/v1/skills?limit=200"
        )
