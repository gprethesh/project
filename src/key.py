from ecdsa import SigningKey, SECP256k1
import binascii

private_key_sender1 = "e265786c34e8dfa1a5801d51dfc3c26024b4651e35f5f834f5e00a8b25cce50d"
private_key_sender2 = "f63795f1f00944217faa57bf6965eec798e1f7a3261c7542424ca7526d3f7af2"

# Convert the private key from hexadecimal to bytes
private_key_bytes = binascii.unhexlify(private_key_sender1)

# Create a SigningKey object from the private key
sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)

# Get the VerifyingKey (public key) from the SigningKey
vk = sk.get_verifying_key()

# Convert the public key to bytes
public_key_bytes = vk.to_string()

# Convert the public key bytes to hexadecimal
# public_key_hex = '04' + binascii.hexlify(public_key_bytes).decode()
public_key_hex = binascii.hexlify(public_key_bytes).decode()

# Now you can compare public_key_hex with your known public key
print("Public key:", public_key_hex)