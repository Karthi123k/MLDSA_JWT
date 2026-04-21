from locust import HttpUser, task, between, events
import os
import threading

MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", 1000))

counter_lock = threading.Lock()
request_count = 0

class User(HttpUser):
    wait_time = between(0.001, 0.01)

    @task
    def full_flow(self):
        global request_count

        with counter_lock:
            if request_count >= MAX_REQUESTS:
                return   # ✅ DO NOT quit here
            request_count += 1

        # 🔐 SIGN
        res = self.client.post("/login")
        if res.status_code != 200:
            return

        token = res.json().get("token")
        if not token:
            return

        # 🔐 VERIFY
        self.client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )


# ✅ GLOBAL STOP HANDLER (CRITICAL FIX)
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("✅ Test finished cleanly, stats will be saved")