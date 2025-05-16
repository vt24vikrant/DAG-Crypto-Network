import json
import os

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from config import PRIVATE_KEY_FILE


# -- Signing Keys --
def load_or_generate_signing_key():
    if os.path.exists(PRIVATE_KEY_FILE):
        with open(PRIVATE_KEY_FILE, "rb") as f:
            return SigningKey(f.read())
    key = SigningKey.generate()
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(key.encode())
    return key

def sign_data(data, signing_key):
    # Serialize data with sorted keys for consistent signing
    serialized_data = json.dumps(data, sort_keys=True).encode()
    return signing_key.sign(serialized_data).signature

def verify_signature(data, signature_hex: str, public_key_hex: str):
    data_copy = dict(data)
    data_copy.pop("signature", None)

    public_key = bytes.fromhex(public_key_hex)
    signature = bytes.fromhex(signature_hex)

    verify_key = VerifyKey(public_key)
    try:
        serialized = json.dumps(data_copy, sort_keys=True).encode()
        verify_key.verify(serialized, signature)
        return True
    except BadSignatureError:
        return False



# -- Encryption --
def generate_rsa_keys(bits=2048):
    key = RSA.generate(bits)
    return key, key.publickey()

def rsa_encrypt(public_key, session_key):
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(session_key)

def rsa_decrypt(private_key, ciphertext):
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(ciphertext)

def aes_encrypt(key, plaintext):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return {
        "ciphertext": ciphertext.hex(),
        "tag": tag.hex(),
        "nonce": cipher.nonce.hex()
    }

def aes_decrypt(key, data):
    cipher = AES.new(key, AES.MODE_GCM, bytes.fromhex(data["nonce"]))
    plaintext = cipher.decrypt_and_verify(bytes.fromhex(data["ciphertext"]), bytes.fromhex(data["tag"]))
    return plaintext.decode()
