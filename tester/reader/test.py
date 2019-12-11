#!/usr/bin/env python3
"""
Tester using chosen private key in ECDH to check leakage.
"""

import argparse
import random
import time

import matplotlib.pyplot as plt
import numpy as np
from smartcard.System import readers

SELECT = [0x00, 0xa4, 0x04, 0x00, 0x10, 0x4d, 0x69, 0x6e, 0x65, 0x72, 0x76, 0x61, 0x2d, 0x74, 0x65,
          0x73, 0x74, 0x2e, 0x63, 0x61, 0x70]
PREPARE = [0xb0, 0x5a]
KEX = [0xb0, 0x5b, 0x00, 0x00]


def connect():
    """Connect to and select the applet on the card in the first reader."""
    try:
        reader = readers()[0]
    except Exception as e:
        print("[x] Couldn't initialize a reader: {}".format(e))
        return None
    connection = reader.createConnection()
    connection.connect()
    print(
            "[*] Connected to card: {:x} in {}.".format(
                    int.from_bytes(bytes(connection.getATR()), byteorder="big"), str(reader)
            )
    )
    resp, sw1, sw2 = connection.transmit(SELECT)
    if sw1 == 0x90 and sw2 == 0:
        print("[*] Selected Tester applet.")
        return connection
    else:
        print("[x] Couldn't select applet: {:02x}{:02x}".format(sw1, sw2))
        return None


def measure(connection, repeats, full):
    """Measure ECDH duration, on scalars with bit-length in range [1, full), doing repeats tries."""
    x = range(1, full)

    blens = list(x)
    random.shuffle(blens)

    scatter_x = []
    scatter_y = []

    print("[ ] Start collecting data.")
    for bitlen in blens:
        prep_cmd = PREPARE + [bitlen, 0x00]
        connection.transmit(prep_cmd)
        print("{: 3}: ".format(bitlen), end="", flush=True)
        total = 0
        for i in range(repeats + 1):
            elapsed = -time.perf_counter_ns()
            connection.transmit(KEX)
            elapsed += time.perf_counter_ns()
            if i == 0:
                continue
            total += elapsed
            scatter_x.append(bitlen + 1)
            scatter_y.append(elapsed)
            print(".", end="", flush=True)
        avg = total / repeats
        print(" {:.2f}".format(avg))
    print("[*] Finished collecting data.")
    return scatter_x, scatter_y


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repeats", type=int, dest="repeats", default=8,
                        help="Amount of repeats per one bit-length, to smooth out noise.")
    parser.add_argument("-n", "--range", type=int, dest="range", default=0xff,
                        help="Upper bound of the tested bit-length. Must be in (1, 256].")

    args = parser.parse_args()
    if 256 < args.range <= 1:
        print("[x] Range needs to be in (1, 256].")
        exit(1)
    if args.repeats == 0:
        print("[x] Repeats must be non-zero.")
        exit(1)

    connection = connect()
    if connection is None:
        exit(1)
    scatter_x, scatter_y = measure(connection, args.repeats, args.range)

    corr = np.corrcoef(scatter_x, scatter_y)
    correlation = corr[0][1]
    print("[*] Correlation: {:.2f}".format(correlation))
    line = np.poly1d(np.polyfit(scatter_x, scatter_y, 1))
    print("[*] Linear fit: {}".format(str(line)[2:]))

    plt.suptitle("Correlation: {:.2f}".format(correlation))
    plt.scatter(scatter_x, scatter_y)
    plt.plot(range(args.range), line(range(args.range)), label=str(line))
    plt.xlabel("bit-length")
    plt.ylabel("duration [ns]")
    plt.legend()
    plt.tight_layout(2)
    plt.show()
