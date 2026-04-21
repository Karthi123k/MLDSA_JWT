from locust import HttpUser, task, between
import os

MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", 100))

class User(HttpUser):
    wait_time = between(0.001, 0.005)

    def on_start(self):
        # 🔐 Login once
        res = self.client.post("/login")
        if res.status_code == 200:
            self.token = res.json().get("token")
        else:
            self.token = None

        self.request_count = 0

    @task
    def verify_only(self):
        if not self.token:
            return

        if self.request_count >= MAX_REQUESTS:
            self.stop(True)   # ✅ graceful stop
            return

        self.client.get(
            "/protected",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        self.request_count += 1