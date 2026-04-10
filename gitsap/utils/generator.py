import time
import os

CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def encode_base32(value: int, length: int) -> str:
    result = []
    for _ in range(length):
        result.append(CROCKFORD_BASE32[value & 31])
        value >>= 5
    return "".join(reversed(result))


def generate_ulid() -> str:
    # 48-bit timestamp (milliseconds)
    timestamp = int(time.time() * 1000)

    # 80-bit randomness
    randomness = int.from_bytes(os.urandom(10), "big")

    # Encode parts
    time_str = encode_base32(timestamp, 10)
    rand_str = encode_base32(randomness, 16)

    return time_str + rand_str
