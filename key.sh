#!/bin/bash

set -e

echo "========================================"
echo " ML-DSA (Dilithium) Key Generation Script"
echo "========================================"

# Algorithms list
ALGORITHMS=("mldsa44" "mldsa65" "mldsa87")

# Output directory
OUT_DIR="mldsa_keys"
mkdir -p $OUT_DIR

echo "[+] Output directory: $OUT_DIR"
echo

# Check if oqsprovider is loaded
echo "[*] Checking oqsprovider..."
if ! openssl list -providers | grep -q oqsprovider; then
    echo "[ERROR] oqsprovider not loaded!"
    exit 1
fi
echo "[OK] oqsprovider is active"
echo

# Generate keys
for algo in "${ALGORITHMS[@]}"
do
    echo "----------------------------------------"
    echo "[*] Generating keys for: $algo"
    
    PRIV_KEY="$OUT_DIR/${algo}_private.pem"
    PUB_KEY="$OUT_DIR/${algo}_public.pem"

    # Generate private key
    openssl genpkey -algorithm $algo -out $PRIV_KEY

    # Extract public key
    openssl pkey -in $PRIV_KEY -pubout -out $PUB_KEY

    echo "[OK] Generated:"
    echo "     Private: $PRIV_KEY"
    echo "     Public : $PUB_KEY"

    # Quick validation
    echo "[*] Validating key..."
    openssl pkey -in $PRIV_KEY -noout > /dev/null
    echo "[OK] Validation passed"

    echo
done

echo "========================================"
echo " Key Generation Completed Successfully!"
echo "========================================"

# Show file sizes (important for research)
echo
echo "[*] Key Sizes:"
ls -lh $OUT_DIR