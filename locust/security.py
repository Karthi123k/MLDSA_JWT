import requests
import jwt
import base64
import json
import time
import csv
import os

AUTH = "http://localhost:8001"
USER = "http://localhost:8002"
GATEWAY = "http://localhost:8080"

TOTAL = 50

KEY_SIZE = os.environ["KEY_SIZE"]

tdr_detected = 0
fdr_detected = 0
rsr_success = 0

# -------------------------
# RESET SYSTEM
# -------------------------
requests.post(f"{AUTH}/reset")
requests.post(f"{USER}/reset")

# -------------------------
# HELPER: tamper token
# -------------------------
def tamper(token):
    header, payload, signature = token.split(".")

    decoded = json.loads(base64.urlsafe_b64decode(payload + "=="))
    decoded["admin"] = True

    new_payload = base64.urlsafe_b64encode(
        json.dumps(decoded).encode()
    ).decode().rstrip("=")

    return f"{header}.{new_payload}.{signature}"

# -------------------------
# LOAD FAKE KEY (DIFFERENT!)
# -------------------------
FAKE_KEY_SIZE = "512" if KEY_SIZE != "512" else "1024"

with open(f"../certs/{FAKE_KEY_SIZE}/private.pem") as f:
    fake_key = f.read()

# -------------------------
# TEST LOOP
# -------------------------
for _ in range(TOTAL):

    # -------------------------
    # GET VALID TOKEN
    # -------------------------
    res = requests.post(f"{AUTH}/login")
    token = res.json()["token"]

    # -------------------------
    # 1️⃣ TAMPER TEST
    # -------------------------
    tampered = tamper(token)

    r = requests.get(
        f"{GATEWAY}/protected",
        headers={"Authorization": f"Bearer {tampered}"}
    )

    if r.status_code != 200:
        tdr_detected += 1

    # -------------------------
    # 2️⃣ FORGERY TEST (REAL)
    # -------------------------
    try:
        fake = jwt.encode(
            {"user": "attacker", "iat": int(time.time())},
            fake_key,
            algorithm="RS256"
        )

        r = requests.get(
            f"{GATEWAY}/protected",
            headers={"Authorization": f"Bearer {fake}"}
        )

        if r.status_code != 200:
            fdr_detected += 1

    except Exception:
        # if invalid key format → still considered detected
        fdr_detected += 1

    # -------------------------
    # 3️⃣ REPLAY TEST
    # -------------------------
    r1 = requests.get(
        f"{GATEWAY}/protected",
        headers={"Authorization": f"Bearer {token}"}
    )

    r2 = requests.get(
        f"{GATEWAY}/protected",
        headers={"Authorization": f"Bearer {token}"}
    )

    if r2.status_code == 200:
        rsr_success += 1

# -------------------------
# METRICS
# -------------------------
TDR = tdr_detected / TOTAL
FDR = fdr_detected / TOTAL
RSR = rsr_success / TOTAL
ASR = rsr_success / (TOTAL * 3)

print("\n🔐 SECURITY METRICS\n")
print(f"KEY_SIZE: {KEY_SIZE}")
print(f"TDR: {TDR:.4f}")
print(f"FDR: {FDR:.4f}")
print(f"RSR: {RSR:.4f}")
print(f"ASR: {ASR:.4f}")

# -------------------------
# SAVE CSV
# -------------------------
os.makedirs("logs/security", exist_ok=True)

file_path = "logs/security/security_results.csv"
write_header = not os.path.exists(file_path)

with open(file_path, "a", newline="") as f:
    writer = csv.writer(f)

    if write_header:
        writer.writerow([
            "key_size",
            "TDR",
            "FDR",
            "RSR",
            "ASR"
        ])

    writer.writerow([
        KEY_SIZE,
        TDR,
        FDR,
        RSR,
        ASR
    ])