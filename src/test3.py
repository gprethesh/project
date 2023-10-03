from ecdsa import SigningKey, VerifyingKey, SECP256k1
import binascii

# Provided private key and public key
private_key_hex = "e7b1b7229a1f0e0560acb37ad0a7359cd3b26478c5877ad03fb34e30791d23b0"
public_key_hex = "3a4e0472a912a37c9d67af2c3de58859d9eba20300b024d32bfbce30648a6575ff4a9dcf5f8ea6528d2fcfe765d2b532a7b8b2c592881e1db3fd0333dabc295b"

# Convert hex to bytes
private_key_bytes = binascii.unhexlify(private_key_hex)
public_key_bytes = binascii.unhexlify(public_key_hex)

# Create SigningKey and VerifyingKey
private_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
public_key = VerifyingKey.from_string(public_key_bytes, curve=SECP256k1)

# Sign a message
message = b'This is a test message'
signature = private_key.sign(message)

print(f"Signature: {signature.hex()}")
print("private_key", private_key)
print("public_key", public_key)

# Verify the signature
try:
    assert public_key.verify(signature, message)
    print("The signature is valid.")
except:
    print("The signature is invalid.")
