import os
import hmac
import hashlib
import base64
import click

HASH_KEY = bytes(
    [
        (b + 256) % 256
        for b in [
            -82,
            -124,
            -92,
            29,
            41,
            -60,
            51,
            39,
            -112,
            52,
            85,
            -56,
            118,
            76,
            4,
            82,
        ]
    ]
)
SERIAL_NO_RANGES = [
    ("902795HP52A000001", "902795HP52A001000"),
    ("PG010000000001", "PG010000010000"),
    ("NPG010100000001", "NPG010100010000"),
    ("NPG010200000001", "NPG010200000250"),
]


# Find common prefix of two strings
def common_prefix(str1, str2):
    return os.path.commonprefix([str1, str2])


# Compute the SHA-512 hash of a string and encode it in base64
def compute_base64_sha512_hash(string):
    hash_object = hmac.new(HASH_KEY, string.encode(), hashlib.sha512)
    base64_encoded_hash = base64.b64encode(hash_object.digest()[:20]).decode()
    return base64_encoded_hash


# Find a string with a SHA-512 hash that matches the given prefix within a range
def find_matching_hash(range_start, range_end, search_prefix, progress):
    prefix = common_prefix(range_start, range_end)
    prefix_len = len(prefix)
    suffix_len = len(range_start) - prefix_len
    start_num = int(range_start[prefix_len:])
    end_num = int(range_end[prefix_len:])
    for i in range(start_num, end_num + 1):
        string = f"{{prefix}}{{:0{suffix_len}d}}".format(i, prefix=prefix)
        base64_hash = compute_base64_sha512_hash(string)
        progress.update(1)
        if base64_hash.startswith(search_prefix):
            return string, base64_hash
    return None


@click.command()
@click.argument("id_prefix")
def serialno(id_prefix: str):
    """Reverse lookup a device serial number from a device tracking ID."""

    # Calculate the total number of items across all ranges
    total_items = 0
    for start_str, end_str in SERIAL_NO_RANGES:
        prefix_len = len(common_prefix(start_str, end_str))
        total_items += int(end_str[prefix_len:]) - int(start_str[prefix_len:]) + 1

    # Iterate each range and find a matching result
    result = None
    with click.progressbar(length=total_items) as progress:
        for range_start, range_end in SERIAL_NO_RANGES:
            result = find_matching_hash(range_start, range_end, id_prefix, progress)
            if result:
                break

    if result:
        matching_serial_no, matching_hash = result
        print(f"Serial No.: {matching_serial_no}")
        print(f"Device Tracking ID: {matching_hash}")
    else:
        print("No matches.")


@click.command()
@click.argument("serialno")
def trackingid(serialno: str):
    """Lookup a device tracking ID from a device serial number."""
    base64_hash = compute_base64_sha512_hash(serialno)
    print(f"Device Tracking ID: {base64_hash}")
