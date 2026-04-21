from pqcrypto.sign import ml_dsa_44, ml_dsa_65, ml_dsa_87
import os

BASE_DIR = "certs"

def generate_and_save(name, algo):
    path = f"{BASE_DIR}/{name}"
    os.makedirs(path, exist_ok=True)

    pk, sk = algo.generate_keypair()

    with open(f"{path}/public_key.bin", "wb") as f:
        f.write(pk)

    with open(f"{path}/private_key.bin", "wb") as f:
        f.write(sk)

    print(f"✅ {name} generated")
    print(f"   Public key size:  {len(pk)} bytes")
    print(f"   Private key size: {len(sk)} bytes\n")


# Generate all variants
generate_and_save("mldsa44", ml_dsa_44)
generate_and_save("mldsa65", ml_dsa_65)
generate_and_save("mldsa87", ml_dsa_87)