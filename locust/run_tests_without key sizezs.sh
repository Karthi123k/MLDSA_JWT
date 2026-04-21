#!/bin/bash

set -e
mkdir -p logs

RUN_TIME="1m"
CONCURRENCY=(1 10 50)

echo "🚀 JWT FULL BENCHMARK START"

for USERS in "${CONCURRENCY[@]}"
do
    echo "=============================="
    echo "USERS = $USERS"
    echo "=============================="

    RESULT_PREFIX="logs/results_${USERS}"
    RESOURCE_FILE="logs/resource_${USERS}.csv"

    # =========================
    # START RESOURCE MONITOR
    # =========================
    echo "Container,CPU%,Memory,NetIO,BlockIO" > "$RESOURCE_FILE"

    docker stats --no-stream=false \
      --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" \
      > "$RESOURCE_FILE" &
    STATS_PID=$!

    # =========================
    # RUN LOCUST
    # =========================
    locust -H http://localhost:8080 \
      --headless \
      -u $USERS \
      -r 10 \
      -t $RUN_TIME \
      --csv="$RESULT_PREFIX"

    # =========================
    # STOP RESOURCE MONITOR
    # =========================
    kill $STATS_PID 2>/dev/null || true

    # =========================
    # FETCH JSON METRICS
    # =========================
    AUTH_JSON=$(curl -s http://localhost:8001/metrics/crypto)
    USER_JSON=$(curl -s http://localhost:8002/metrics/verify)

    # =========================
    # PARSE AUTH (SIGN) METRICS
    # =========================
    SIGN_MIN=$(echo $AUTH_JSON | jq -r '.sign_min')
    SIGN_AVG=$(echo $AUTH_JSON | jq -r '.sign_avg')
    SIGN_MAX=$(echo $AUTH_JSON | jq -r '.sign_max')
    SIGN_STD=$(echo $AUTH_JSON | jq -r '.sign_std')
    TOKEN_SIZE=$(echo $AUTH_JSON | jq -r '.token_size')
    SIG_SIZE=$(echo $AUTH_JSON | jq -r '.signature_size')

    # =========================
    # PARSE USER (VERIFY) METRICS
    # =========================
    VERIFY_MIN=$(echo $USER_JSON | jq -r '.verify_min')
    VERIFY_AVG=$(echo $USER_JSON | jq -r '.verify_avg')
    VERIFY_MAX=$(echo $USER_JSON | jq -r '.verify_max')
    VERIFY_STD=$(echo $USER_JSON | jq -r '.verify_std')

    # =========================
    # SAVE SEPARATE FILES (IMPORTANT)
    # =========================

    # 🔐 AUTH (SIGN METRICS FILE)
    echo "users,sign_min,sign_avg,sign_max,sign_std,token_size,signature_size" > logs/auth_sign_${USERS}.csv
    echo "$USERS,$SIGN_MIN,$SIGN_AVG,$SIGN_MAX,$SIGN_STD,$TOKEN_SIZE,$SIG_SIZE" >> logs/auth_sign_${USERS}.csv

    # 🔓 USER (VERIFY METRICS FILE)
    echo "users,verify_min,verify_avg,verify_max,verify_std" > logs/user_verify_${USERS}.csv
    echo "$USERS,$VERIFY_MIN,$VERIFY_AVG,$VERIFY_MAX,$VERIFY_STD" >> logs/user_verify_${USERS}.csv

    echo "✅ DONE USERS=$USERS"
    echo "----------------------------------"
done

echo "🚀 ALL BENCHMARKS COMPLETED"