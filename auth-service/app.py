from fastapi import FastAPI
import time
import statistics
import os
import csv
import uuid
import json
import base64

from pqcrypto.sign import ml_dsa_44, ml_dsa_65, ml_dsa_87

app = FastAPI()

KEY_SIZE = os.environ["KEY_SIZE"]

# 🔥 Select algorithm
if KEY_SIZE == "mldsa44":
    ALGO = ml_dsa_44
elif KEY_SIZE == "mldsa65":
    ALGO = ml_dsa_65
elif KEY_SIZE == "mldsa87":
    ALGO = ml_dsa_87
else:
    raise Exception("Invalid KEY_SIZE")

PRIVATE_KEY_PATH = f"/app/certs/{KEY_SIZE}/private_key.bin"

# ✅ MUST be binary
with open(PRIVATE_KEY_PATH, "rb") as f:
    PRIVATE_KEY = f.read()

sign_times = []
token_sizes = []
signature_sizes = []

os.makedirs("logs", exist_ok=True)

@app.post("/reset")
def reset():
    global sign_times, token_sizes, signature_sizes
    sign_times = []
    token_sizes = []
    signature_sizes = []
    return {"status": "auth reset done"}

@app.post("/login")
def login():

    payload = {
        "sub": "user",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "jti": str(uuid.uuid4())
    }

    message = json.dumps(payload).encode()

    start = time.perf_counter()
    signature = ALGO.sign(PRIVATE_KEY, message)
    sign_time = (time.perf_counter() - start) * 1000

    token = (
        base64.urlsafe_b64encode(message).decode() + "." +
        base64.urlsafe_b64encode(signature).decode()
    )

    sign_times.append(sign_time)

    token_sizes.append(len(token))
    signature_sizes.append(len(signature))

    return {
        "token": token,
        "sign_time": sign_time,
        "token_size": len(token),
        "signature_size": len(signature)
    }

@app.get("/metrics/crypto")
def crypto_metrics():
    return {
        "sign_min": min(sign_times) if sign_times else 0,
        "sign_avg": statistics.mean(sign_times) if sign_times else 0,
        "sign_max": max(sign_times) if sign_times else 0,
        "sign_std": statistics.stdev(sign_times) if len(sign_times) > 1 else 0,
        "token_size": token_sizes[-1] if token_sizes else 0,
        "signature_size": signature_sizes[-1] if signature_sizes else 0
    }