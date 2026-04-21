# we can chnage the reuese and fullflow  -> each sign and each veirfy resue means one sign and multiple verify

#!/bin/bash

set -e

# =========================
# CONFIG
# =========================

MODE="reuse"   # reuse / fullflow

ITERATIONS=(10)        # total requests
CONCURRENCY=(1 )         # users
KEY_SIZES=(mldsa44 mldsa65 mldsa 87)

BASE_LOG_DIR="logs/${MODE}"

echo "🚀 JWT BENCHMARK START (MODE=$MODE)"

mkdir -p "$BASE_LOG_DIR"

# =========================
# LOOP START
# =========================

for KEY_SIZE in "${KEY_SIZES[@]}"
do
    echo "======================================"
    echo "🔐 KEY SIZE = $KEY_SIZE"
    echo "======================================"

    # 📁 per-key folder
    KEY_DIR="${BASE_LOG_DIR}/${KEY_SIZE}"
    mkdir -p "$KEY_DIR"

    # start services
    KEY_SIZE=$KEY_SIZE docker compose up -d --build
    sleep 5

    for USERS in "${CONCURRENCY[@]}"
    do
        for ITER in "${ITERATIONS[@]}"
        do
            echo "------------------------------"
            echo "KEY=$KEY_SIZE | USERS=$USERS | ITER=$ITER"
            echo "------------------------------"

            export MAX_REQUESTS=$ITER

            RESULT_PREFIX="${KEY_DIR}/locust_u${USERS}_i${ITER}"
            RESOURCE_FILE="${KEY_DIR}/resource_u${USERS}_i${ITER}.csv"

            # =========================
            # RESET METRICS
            # =========================
            curl -s -X POST http://localhost:8001/reset > /dev/null
            curl -s -X POST http://localhost:8002/reset > /dev/null

            # =========================
            # START RESOURCE MONITOR (continuous)
            # =========================
            echo "Container,CPU%,Memory,NetIO,BlockIO" > "$RESOURCE_FILE"

            docker stats \
              --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" \
              >> "$RESOURCE_FILE" &
            STATS_PID=$!

            # =========================
            # SELECT LOCUST FILE
            # =========================
            if [ "$MODE" = "reuse" ]; then
                LOCUST_FILE="locust_reuse.py"
            else
                LOCUST_FILE="locust_fullflow.py"
            fi

            # =========================
            # RUN LOCUST (FIXED)
            # =========================
            locust -f $LOCUST_FILE \
              -H http://localhost:8080 \
              --headless \
              -u $USERS \
              -r $USERS \
              --run-time 30s \
              --stop-timeout 5 \
              --csv="$RESULT_PREFIX"

            # =========================
            # STOP RESOURCE MONITOR
            # =========================
            kill $STATS_PID 2>/dev/null || true

            # =========================
            # FETCH METRICS
            # =========================
            AUTH_JSON=$(curl -s http://localhost:8001/metrics/crypto)
            USER_JSON=$(curl -s http://localhost:8002/metrics/verify)

            SIGN_MIN=$(echo $AUTH_JSON | jq -r '.sign_min')
            SIGN_AVG=$(echo $AUTH_JSON | jq -r '.sign_avg')
            SIGN_MAX=$(echo $AUTH_JSON | jq -r '.sign_max')
            SIGN_STD=$(echo $AUTH_JSON | jq -r '.sign_std')
            TOKEN_SIZE=$(echo $AUTH_JSON | jq -r '.token_size')
            SIG_SIZE=$(echo $AUTH_JSON | jq -r '.signature_size')

            VERIFY_MIN=$(echo $USER_JSON | jq -r '.verify_min')
            VERIFY_AVG=$(echo $USER_JSON | jq -r '.verify_avg')
            VERIFY_MAX=$(echo $USER_JSON | jq -r '.verify_max')
            VERIFY_STD=$(echo $USER_JSON | jq -r '.verify_std')

            # =========================
            # SAVE AUTH METRICS
            # =========================
            AUTH_FILE="${KEY_DIR}/auth_u${USERS}_i${ITER}.csv"

            echo "key_size,users,iterations,sign_min,sign_avg,sign_max,sign_std,token_size,signature_size" > "$AUTH_FILE"
            echo "$KEY_SIZE,$USERS,$ITER,$SIGN_MIN,$SIGN_AVG,$SIGN_MAX,$SIGN_STD,$TOKEN_SIZE,$SIG_SIZE" >> "$AUTH_FILE"

            # =========================
            # SAVE VERIFY METRICS
            # =========================
            VERIFY_FILE="${KEY_DIR}/verify_u${USERS}_i${ITER}.csv"

            echo "key_size,users,iterations,verify_min,verify_avg,verify_max,verify_std" > "$VERIFY_FILE"
            echo "$KEY_SIZE,$USERS,$ITER,$VERIFY_MIN,$VERIFY_AVG,$VERIFY_MAX,$VERIFY_STD" >> "$VERIFY_FILE"

            echo "✅ DONE KEY=$KEY_SIZE USERS=$USERS ITER=$ITER"
        done
    done

    docker compose down
done

echo "🚀 ALL BENCHMARKS COMPLETED"