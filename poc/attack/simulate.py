#!/usr/bin/env python
"""
Simulates bit-length leakage, with no noise, and exports (private key as well for debug).
"""

from ec import get_curve, Mod

import hashlib
import secrets
from scipy.stats import norm
from binascii import hexlify

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("curve", type=str)
    parser.add_argument("hash", type=str)
    parser.add_argument("count", type=int)
    parser.add_argument("--base", type=int, default=0)
    parser.add_argument("--t-time", type=int, default=1)
    parser.add_argument("--sdev", type=float, default=None)
    args = parser.parse_args()

    curve = get_curve(args.curve)
    hash = hashlib.new(args.hash)
    private = secrets.randbelow(curve.group.n)
    public = private * curve.g

    data = secrets.token_bytes(64)
    print(hexlify(curve.encode_point(public)).decode(), hexlify(data).decode(), hex(private)[2:])
    hash.update(data)
    hashed = int(hash.hexdigest(), 16)
    if hash.digest_size * 8 > curve.group.n.bit_length():
        hashed >>= hash.digest_size * 8 - curve.group.n.bit_length()
    hashed = Mod(hashed, curve.group.n)

    if args.sdev is None or args.sdev == 0:
        noise_f = lambda: 0
    else:
        noise = norm(0, args.sdev)
        noise_f = lambda: noise.rvs()

    for i in range(args.count):
        k = secrets.randbelow(curve.group.n)
        pt = k * curve.g
        r = int(pt.x)
        s = int(Mod(k, curve.group.n).inverse() * (hashed + r * private))
        elapsed = args.base + args.t_time * k.bit_length() + int(noise_f())
        print(hex(r)[2:] + "," + hex(s)[2:] + "," + str(elapsed))
