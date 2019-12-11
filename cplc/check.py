#!/usr/bin/env python3
"""
Vulnerability check based on CPLC data of known vulnerable cards.
"""

import csv

from smartcard.System import readers

SELECT_CM = [0x00, 0xA4, 0x04, 0x00, 0x00]
FETCH_GP_CPLC = [0x80, 0xCA, 0x9F, 0x7F, 0x00]
FETCH_ISO_CPLC = [0x00, 0xCA, 0x9F, 0x7F, 0x00]


class Ident(object):
    def __init__(self, ic_type, release_date, release_level, atr=None, name=None):
        self.ic_type = ic_type
        self.release_date = release_date
        self.release_level = release_level
        self.atr = atr
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, Ident):
            return False
        return (
                self.ic_type == other.ic_type
                and self.release_date == other.release_date
                and self.release_level == other.release_level
        )

    def __str__(self):
        return "{}({:04x}, {:04x}, {:04x})".format(
                self.name if self.name is not None else "",
                self.ic_type,
                self.release_date,
                self.release_level,
        )


VULNERABLE_TESTED = [
    Ident(
            0x010B,
            0x0352,
            0x0005,
            atr="3bd518ff8191fe1fc38073c8211309",
            name="Athena IDProtect",
    )
]

VULNERABLE_ASSUMED = [
    Ident(0x010E, 0x1245, 0x0002, name="Athena IDProtect"),
    Ident(0x0106, 0x0130, 0x0401, name="Athena IDProtect"),
    Ident(0x010E, 0x1245, 0x0002, name="Athena IDProtect"),
    Ident(0x010B, 0x0352, 0x0005, name="Valid S/A IDflex V"),
    Ident(0x010E, 0x1245, 0x0002, name="SafeNet eToken 4300"),
    Ident(0x010E, 0x0264, 0x0001, name="TecSec Armored Card"),
    Ident(0x0108, 0x0264, 0x0001, name="TecSec Armored Card"),
]


def load_list(fname, default):
    try:
        with open(fname, newline="") as f:
            reader = csv.reader(f)
            return [Ident(int(ic, 16), int(rel_date, 16), int(rel_level, 16), name)
                    for ic, rel_date, rel_level, name in reader]
    except:
        return default


def connect():
    """Connect to and select the Card Manager on the card in the first reader."""
    try:
        reader = readers()[0]
    except Exception as e:
        print("[x] Couldn't initialize a reader: {}".format(e))
        return None
    connection = reader.createConnection()
    connection.connect()
    print(
            "[*] Connected to card: {:x} in {}".format(
                    int.from_bytes(bytes(connection.getATR()), byteorder="big"), str(reader)
            )
    )
    resp, sw1, sw2 = connection.transmit(SELECT_CM)
    if sw1 == 0x90 and sw2 == 0:
        print("[*] Selected Card Manager.")
        return connection
    else:
        print("[x] Couldn't select applet: {:02x}{:02x}".format(sw1, sw2))
        return None


def fetch_cplc(connection):
    """Fetch CPLC data from the card."""
    print("[*] Requesting GP CPLC data.")
    resp, sw1, sw2 = connection.transmit(FETCH_GP_CPLC)
    if sw1 == 0x6E and sw2 == 0x00:
        print("[*] Requesting ISO CPLC data.")
        resp, sw1, sw2 = connection.transmit(FETCH_ISO_CPLC)

    if sw1 == 0x90 and sw2 == 00:
        print("[*] Got CPLC data.")
        return resp
    print("[x] Couldn't get CPLC data.")
    return None


def parse_cplc(data, atr, tested, assumed):
    """Parse CPLC data to get relevant identifiers."""
    ic_type = data[5] << 8 | data[6]
    release_date = data[9] << 8 | data[10]
    release_level = data[11] << 8 | data[12]
    card = Ident(ic_type, release_date, release_level, atr)
    print("[*] Card has CPLC data: {}.".format(card))

    vuln = False
    for other in tested:
        if other == card:
            print("[X] ! Card is vulnerable, matched {}!".format(other))
            vuln = True

    for other in assumed:
        if other == card:
            print("[X] ! Card is probably vulnerable, matched {}!".format(other))
            vuln = True

    if not vuln:
        print("[*] Card is not known to be vulnerable.")


if __name__ == "__main__":
    tested = load_list("tested.csv", VULNERABLE_TESTED)
    assumed = load_list("assumed.csv", VULNERABLE_ASSUMED)

    connection = connect()
    if connection is None:
        exit(1)

    atr = bytes(connection.getATR()).hex()
    data = fetch_cplc(connection)
    connection.disconnect()
    if data is None:
        exit(1)

    parse_cplc(data, atr, tested, assumed)
