from colorama import Fore
from loguru import logger
import argparse
import hashlib
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from random import SystemRandom

# Constants
PATTERN_FOUR_ZEROS = r"^0x[0-9a-fA-F]{4}0000[0-9a-fA-F]{36}$"
PATTERN_TRIPLE_DIGITS = r"^0x[0-9a-fA-F]*[0-9]{3}[0-9a-fA-F]*$"
PATTERN_ASCENDING = r"^0x[0-9a-fA-F]*(1234|2345|3456|4567|5678|6789)[0-9a-fA-F]*$"
PATTERN_DESCENDING = r"^0x[0-9a-fA-F]*(9876|8765|7654|6543|5432|4321|3210)[0-9a-fA-F]*$"
PATTERN_PALINDROME = r"^0x[0-9a-fA-F]*([0-9a-fA-F]{6})([0-9a-fA-F]{6})[0-9a-fA-F]*$"
PATTERN_REPEATED_BYTE = r"^0x[0-9a-fA-F]*([0-9a-fA-F]{2})/1{3}[0-9a-fA-F]*$"
PATTERN_BINARY = r"^0x[0-9a-fA-F]*(10){4}[0-9a-fA-F]*$"
PATTERN_HEXSPEAK = r"^0x[0-9a-fA-F]*(DEADBEEF|BADDCAFE|1337BEEF)[0-9a-fA-F]*$"

START_PATTERN = "6969"
END_PATTERN = "6969"


def parse_args():
    parser = argparse.ArgumentParser(description="Ethereum Address Generator")
    parser.add_argument(
        "-p", "--start-pattern", default="", help="Prefix of the eth address"
    )
    parser.add_argument(
        "-e", "--end-pattern", default="", help="Suffix of the eth address"
    )
    parser.add_argument(
        "-c", "--checksum", action="store_true", help="Enable EIP-55 checksum"
    )
    parser.add_argument(
        "-s",
        "--step",
        type=int,
        default=50000,
        help="# of attempts between progress logs",
    )
    parser.add_argument(
        "-m",
        "--max-tries",
        type=int,
        default=5000000000000000,
        help="Max # of attempts",
    )
    parser.add_argument(
        "-i", "--log-interval", type=int, default=5000, help="Logging interval in ms"
    )
    return parser.parse_args()


def calculate_rarity_score(address):
    char_counts = defaultdict(int)
    for c in address:
        char_counts[c] += 1

    unique_chars = len(char_counts)
    max_count = max(char_counts.values(), default=0)
    repetition_factor = max_count / len(address)

    # calculate rarity score (lower is rarer)
    rarity_score = (unique_chars / 16.0) * (1.0 + repetition_factor)
    return rarity_score


def is_palindrome(s):
    return s == s[::-1]


def to_checksum_address(address):
    address = address.lower().replace("0x", "")
    hash_bytes = hashlib.sha3_256(address.encode("utf-8")).hexdigest()
    checksum_address = "0x"

    for i, c in enumerate(address):
        if c.isdigit() or int(hash_bytes[i], 16) < 8:
            checksum_address += c
        else:
            checksum_address += c.upper()

    return checksum_address


# verify address
def verify_address(address, private_key):
    # this function would require a library like ecdsa to implement properly
    # for now, it will just return True as a placeholder
    return True


def main():
    args = parse_args()

    start_pattern = args.start_pattern.lower()
    end_pattern = args.end_pattern.lower()
    use_checksum = args.checksum
    step = args.step
    max_tries = args.max_tries
    log_interval = args.log_interval

    logger.info("Starting Vanity Address Generator 🚀")
    logger.info(f"Prefix: {START_PATTERN}")
    logger.info(f"Suffix: {END_PATTERN}")
    logger.info(f"Checksum: {'✅' if use_checksum else '❌'}")
    logger.info(f"Step: {step}")
    logger.info(f"Max Tries: {max_tries}")
    logger.info(f"Log Interval (ms): {log_interval}")

    found = threading.Event()
    total_attempts = 0

    def log_progress():
        while not found.is_set():
            time.sleep(log_interval / 1000)
            logger.info(f"Total checked addresses: {total_attempts} 🔍")

    threading.Thread(target=log_progress, daemon=True).start()

    patterns = [
        (PATTERN_FOUR_ZEROS, "red"),
        (PATTERN_TRIPLE_DIGITS, "green"),
        (PATTERN_ASCENDING, "yellow"),
        (PATTERN_DESCENDING, "blue"),
        (PATTERN_PALINDROME, "magenta"),
        (PATTERN_REPEATED_BYTE, "cyan"),
        (PATTERN_BINARY, "white"),
        (PATTERN_HEXSPEAK, "black"),
    ]

    compiled_patterns = [(re.compile(p), color) for p, color in patterns]

    def generate_address():
        nonlocal total_attempts
        rng = SystemRandom()

        while not found.is_set() and total_attempts < max_tries:
            # simulate key generation
            secret_key = rng.getrandbits(256)
            public_key = rng.getrandbits(512)  # placeholder for actual public key
            address = hashlib.sha3_256(str(public_key).encode("utf-8")).hexdigest()[
                -40:
            ]

            if use_checksum:
                final_address = to_checksum_address(address)
            else:
                final_address = address

            for pattern, color in compiled_patterns:
                if pattern.match(final_address):
                    logger.opt(colors=True).info(
                        f"<{color}>Pattern matched: {final_address}</{color}>"
                    )
                    break

            matches_custom = final_address.startswith(
                start_pattern
            ) and final_address.endswith(end_pattern)

            if matches_custom or is_palindrome(final_address[:12]):
                priv_key_hex = hex(secret_key)[2:]
                rarity_score = calculate_rarity_score(final_address)
                logger.success("\n🎉 New wallet found!")
                logger.success(f"Address: {final_address}")
                logger.success(f"Private Key: {priv_key_hex}")
                logger.success(f"Attempts: {total_attempts}")
                logger.success(f"Rarity Score: {rarity_score:.4f} (lower is rarer)")
                found.set()
                break

            total_attempts += 1

    with ThreadPoolExecutor() as executor:
        for _ in range(4):  # adjust the number of threads as needed
            executor.submit(generate_address)


if __name__ == "__main__":
    main()
