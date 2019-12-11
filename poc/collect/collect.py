#!/usr/bin/env python3
"""
Collection module, allows for collection of signatures and
precise timing.
"""

import argparse
import csv
import time
import sys
from binascii import hexlify

from smartcard.System import readers
from smartcard.pcsc.PCSCCardConnection import translateprotocolheader
from smartcard.scard import SCardTransmit
from asn1crypto.core import Sequence


SELECT = [0x00, 0xa4, 0x04, 0x00, 0x0f, 0x4d, 0x69, 0x6e, 0x65, 0x72, 0x76, 0x61, 0x2d, 0x70, 0x6f, 0x63, 0x2e, 0x63, 0x61, 0x70]
PREPARE = [0xb0, 0x5a, 0x00, 0x00]
SIGN = [0xb0, 0x5b, 0x00, 0x00]


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
		print("[x] Couldn't initialize a reader: {}".format(e), file=sys.stderr)
		return None
	connection = reader.createConnection()
	connection.connect()
	print("[*] Connected to card: {:x} in {}.".format(int.from_bytes(bytes(connection.getATR()), byteorder="big"), str(reader)), file=sys.stderr)
	resp, sw1, sw2 = connection.transmit(SELECT)
	if sw1 == 0x90 and sw2 == 0:
		print("[*] Selected applet.", file=sys.stderr)
		return connection
	else:
		print("[x] Couldn't select applet: {:02x}{:02x}".format(sw1, sw2), file=sys.stderr)
		return None


def prepare(connection):
	"""Prepare for signature collection by generating a new keypair."""
	resp, sw1, sw2 = connection.transmit(PREPARE)
	x = int.from_bytes(bytes(resp[1:33]), byteorder="big")
	y = int.from_bytes(bytes(resp[33:65]), byteorder="big")
	raw = bytes(resp[:65])
	pubkey = (x, y)
	data = bytes(resp[65:97])
	private = None
	if len(resp) == 129:
		private = bytes(resp[97:])
	print("[*] Generated ECDSA keypair, public key:", pubkey, ", data:", hexlify(data).decode(), file=sys.stderr)
	return raw, pubkey, data, private


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("signatures", help="Number of signatures to collect.", type=int)
	args = parser.parse_args()
	
	connection = connect()
	if connection is None:
		exit(1)
	raw, pub, data, private = prepare(connection)

	if private is not None:
		print(hexlify(raw), hexlify(data), hexlify(private))
	else:
		print(hexlify(raw), hexlify(data))

	writer = csv.DictWriter(sys.stdout, ("r", "s", "elapsed"))
	def out(i, elapsed, resp):
		try:
			r, s = Sequence.load(resp).native.values()
		except ValueError:
			print("[x] Failed to parse signature:", hexlify(resp), file=sys.stderr)
			return
		writer.writerow({"elapsed": elapsed,
						 "r": hexlify(r.to_bytes(byteorder="big")),
						 "s": hexlify(s.to_bytes(byteorder="big"))})
		if i % 50 == 0:
			print("[ ] Collected {} signatures.".format(i), file=sys.stderr)
	finish = lambda i: args.signatures != 0 and i >= args.signatures
	print("[ ] Starting collection.", file=sys.stderr)
	try:
		collect_signatures(connection, out, finish)
	except KeyboardInterrupt:
		pass
	print("[*] Finished collection.", file=sys.stderr)
