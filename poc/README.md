# Minerva - Proof of Concept

The Minerva proof-of-concept contains code that exploits the vulnerability against a JavaCard
with a target applet, or against targets using several vulnerable libraries.

## Contents

`applet/` contains code of the two target JavaCard applets, the `CollectApplet` and the `POCApplet`.
The applets are very similar, the only difference is that the `POCApplet` will never export its private
key, so it can be used for full verification of the attack (if the private key is recovered and the device
never exported it). It generates an ECC keypair on the
`secp256r1` curve in the `PREPARE` command and exports the public key in the response as well as the data
that will be signed. Then, in the `SIGN` command it signs the data using ECDSA with SHA256 and responds
with the signature. See `build.xml` for the ant build script.

`attack/` contains two attack scripts. An online one against a JavaCard target in `poc.py` and
an offline one in `attack.py`. Both are written in Python 3 and use the
`pyscard` library for communication and `fpylll` library for lattice reduction
and CVP solving required for the attack. Both take parameters in the form of a JSON
file, which specified what kind of attack is to be performed, see the description in `attack.py`.
The offline attack takes as input a csv file produced by one of the targets or the collection
script in `collect/` for the target JavaCard applet. The `params.json` file can be used as a template
to change some parameters internal to the attack or the PoC.

`build/` is a directory created by the ant build which contains the CAP file with the
built JavaCard applet.

`collect/` contains a Python script which collects signatures from the target JavaCard applet
and outputs it in a format ready for the offline attack script `attack/attack.py`.

`ext/` contains some third party content, such as the ant-javacard extension
(`ant-javacard.jar`) for the ant build system, which is used to build the
applet as well as a version of the JavaCard SDK 2.2.2 (`jckit_222`).

`target/` contains target apps which perform ECDSA signatures using the vulnerable libraries
and export the signatures with timing information in format ready for the offline attack script
`attack/attack.py`. See the Makefile for information on building.

## Usage

All of the attacks need some python packages.

Install Python packages from `requirements.txt` (into a virtualenv).
Starting with `pip install Cython` first, as it is a build dependency of 
`fpylll`. `fpylll` has a somewhat more involved install process, see
<https://github.com/fplll/fpylll>, you will need the current master version
 of `fpylll`.

### JavaCard (PoC)
This PoC attacks the `POCApplet`, which never exports it private key.

 1. Build the applet via `ant build`.
 2. Install the applet (`build/poc_applet.cap`) on the card. For example
 using [GlobalPlatformPro](https://github.com/martinpaljak/GlobalPlatformPro), so
 doing `gp --install build/poc_applet.cap`.
 3. Run `attack/poc.py`. If a USB reader is used, not using other
 USB devices during the attack makes it more reliable. Also, not using the machine
 for other computations during the attack limits the noise and makes it more reliable.
 4. Observe a new keypair being generated (the public key is exported from
 the card and printed) and the attack starting. Observe the reconstructed
 private key after around 10k-25k signatures. If the attack did not succeed
 after this time, it is likely that that particular run of the attack will
 not succeed at all, likely due to noise during the timing measurement.
 
### JavaCard (Collect)
This example first exports a bunch of signatures from the applet and then
attacks them.

 1. Build the applet via `ant build`.
 2. Install the applet (`build/collect_applet.cap`) on the card. For example
 using [GlobalPlatformPro](https://github.com/martinpaljak/GlobalPlatformPro), so
 doing `gp --install build/collect_applet.cap`.
 3. Run `collect/collect.py`. If a USB reader is used, not using other
 USB devices during the attack makes it more reliable. Also, not using the machine
 for other computations during the attack limits the noise and makes it more reliable.
 4. Observe a new keypair being generated and signatures being performed (the public key is exported from
 the card and printed, the private key is also exported in this mode). Save the
 output of the `collect.py` script somewhere, it is in csv, as per [data/README](../data/README.md).
 5. Run `attack/attack.py` passing the arguments `secp256r1 sha256` and a path to the collected file.
 Observe the reconstructed private key.

### Libraries

 1. Build the particular target app using the Makefile in the `target/` directory.
 2. Run the target, possibly with frequency scaling off (`echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo`),
 passing the arguments: the chosen curve, hash algorithm and amount of signatures requested. Save the 
 output to a file.
 3. Run `attack/attack.py`, again passing the arguments: chosen curve, hash algorithm and filename
 containing the signatures from the target. Observe the reconstructed private key.
 
### Simulation

 1. Run `attack/simulate.py <curve> <hash> <count>` with optional parameters specifying the leakage
 properties of the simulated target (`base`, `iter-time` and `sdev`) as modelled in the paper.
 2. Run `attack/attack.py`, again passing the arguments: chosen curve, hash algorithm and filename
 containing the signatures from the target. Observe the reconstructed private key.

