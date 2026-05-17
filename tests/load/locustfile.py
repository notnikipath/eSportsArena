from locust import HttpUser, between, task


class GatewayUser(HttpUser):
    wait_time = between(1, 2)

    @task(4)
    def health(self):
        self.client.get("/health")

    @task(3)
    def dashboard(self):
        self.client.get("/dashboard/ARENA-DEMO/USR-ORG-1")

    @task(1)
    def start_match_workflow(self):
        self.client.post(
            "/workflow/start-match",
            json={
                "match_id": "MCH-OPEN-001",
                "user_id": "USR-ORG-1",
                "arena_id": "ARENA-DEMO",
                "actor_role": "organizer",
                "provider": "hls",
            },
        )
