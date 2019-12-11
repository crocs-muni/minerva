# Minerva - Tester

The Minerva tester is a testing tool for JavaCards which uses ECDH to assess the presence
of timing leakage of bit-length in scalar-multiplication. Since it has to use ECDH to control
the scalar (the ECDSA API in JavaCard does not allow to choose the random nonce = the scalar) the presence
of leakage in ECDH cannot be used to prove the presence of leakage in ECDSA, as the two might
be implemented differently and have different side-channel protections. We have observed both
cards which leaked in ECDH but not in ECDSA and those that leaked in ECDH and ECDSA.

## Contents

`applet/` contains code of a target applet. The applet creates an ECC keypair and sets the `secp256r1`
curve parameters. In the `PREPARE` command, the applet prepares a private key for ECDH, with bit-length
set in the command, the private key simply has the form `1 << (bit_length - 1)`. In the `KEX` command
the applet performs ECDH with the prepared private key. See `build.xml` for the ant build script.

`build/` is a directory created by the ant build which contains the CAP file with the
built JavaCard applet.

`reader/` contains code of the tester. It is written in Python 3 and uses the
`pyscard` library for communication.

`ext/` contains some third party content, such as the ant-javacard extension
(`ant-javacard.jar`) for the ant build system, which is used to build the
applet as well as a version of the JavaCard SDK 2.2.2 (`jckit_222`).

## Usage

 1. Build the applet via `ant build`.
 2. Install the applet (`build/applet.cap`) on the card. For example
 using [GlobalPlatformPro](https://github.com/martinpaljak/GlobalPlatformPro), so
 doing `gp --install build/applet.cap`.
 3. Install Python packages from `requirements.txt` (into a virtualenv).
 4. Run `reader/test.py`.
 5. Observe ECDH being performed, with private keys of varying bit-length, after
 all of the measurements are done a plot will display, showing the dependency
 of ECDH duration on bit-length (if any), and the correlation of the two. This
 dependency cannot be directly connected to ECDSA, since a different algorithm
 might be used for scalar multiplication there (as we observed with one card), but
 can be taken as guidance that if ECDH leaks, ECDSA might as well (as is the case with
 another card).