# Minerva

This package contains three tools for testing the presence of the vulnerability as well
as proof-of-concept code exploiting it.

## CPLC checker

The CPLC checker tests smartcard's CPLC data(identification data of a particular smart card model
from the GlobalPlatform standard) against a list of known or assumed vulnerable cards.

## PoC

The proof-of-concept performs the attack on a JavaCard with a custom target applet or on
target apps using the vulnerable libraries.

## Tester

The tester uses ECDH to test presence of bit-length timing leakage using a custom JavaCard applet.