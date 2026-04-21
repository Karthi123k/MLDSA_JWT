from fastapi import FastAPI, Request, HTTPException
import time
import statistics
import os
import csv
import base64
import json

from pqcrypto.sign import ml_dsa_44, ml_dsa_65, ml_dsa_87

app = FastAPI()

KEY_SIZE = os.environ["KEY_SIZE"]
REPLAY_PROTECTION = os.getenv("REPLAY_PROTECTION", "OFF")

# 🔥 Select algorithm
if KEY_SIZE == "mldsa44":
    ALGO = ml_dsa_44
elif KEY_SIZE == "mldsa65":
    ALGO = ml_dsa_65
elif KEY_SIZE == "mldsa87":
    ALGO = ml_dsa_87
else:
    raise Exception("Invalid KEY_SIZE")

PUBLIC_KEY_PATH = f"/app/certs/{KEY_SIZE}/public_key.bin"

# ✅ MUST be binary
with open(PUBLIC_KEY_PATH, "rb") as f:
    PUBLIC_KEY = f.read()

verify_times = []
used_jti = set()

os.makedirs("logs", exist_ok=True)

@app.post("/reset")
def reset():
    global verify_times, used_jti
    verify_times = []
    used_jti = set()
    return {"status": "user reset done"}

@app.get("/protected")
def protected(request: Request):

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth_header.split()[1]

    try:
        start = time.perf_counter()

        msg_b64, sig_b64 = token.split(".")

        message = base64.urlsafe_b64decode(msg_b64)
        signature = base64.urlsafe_b64decode(sig_b64)

        ALGO.verify(PUBLIC_KEY, message, signature)

        decoded = json.loads(message)

        verify_time = (time.perf_counter() - start) * 1000
        verify_times.append(verify_time)

        # Replay protection
        jti = decoded.get("jti")

        if REPLAY_PROTECTION == "ON":
            if jti in used_jti:
                raise HTTPException(status_code=401, detail="Replay attack")
            used_jti.add(jti)

        return {"verify_time": verify_time}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/metrics/verify")
def verify_metrics():
    return {
        "verify_min": min(verify_times) if verify_times else 0,
        "verify_avg": statistics.mean(verify_times) if verify_times else 0,
        "verify_max": max(verify_times) if verify_times else 0,
        "verify_std": statistics.stdev(verify_times) if len(verify_times) > 1 else 0
    }