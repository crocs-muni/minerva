# [![Minerva](logo.png)](https://minerva.crocs.fi.muni.cz/ "Minerva")

This package contains the tools for testing the presence of the Minerva vulnerability as well
as proof-of-concept code exploiting it. It also contains datasets and code for experiments
performed in the paper.

See [our website](https://minerva.crocs.fi.muni.cz/) for more info.

## CPLC checker

The CPLC checker tests smartcard's CPLC data(identification data of a particular smart card model
from the GlobalPlatform standard) against a list of known or assumed vulnerable cards.

## PoC

The proof-of-concept performs the attack on a JavaCard with a custom target applet or on
target apps using the vulnerable libraries.

## Tester

The tester uses ECDH to test presence of bit-length timing leakage using a custom JavaCard applet.

## Data & Experiments

The `data` directory contains the datasets collected for the paper. The experiments directory
contains experiments run on the [Metacentrum](https://metacentrum.cz/en/) grid computing network.