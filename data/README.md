# Timing data

This directory contains timing data collected from leaking implementations.
The data is in CSV-like format (only the first line is not CSV):
```
<public key> <data> <private key>
<r1>,<s1>,<time1>
<r2>,<s2>,<time2>
...
<r>,<s>,<time>
``` 
Time is in nanoseconds. All of the datasets contain 50 000 signatures.

## Datasets

 - **Athena IDProtect**: [data_athena.csv](data_athena.csv) ECDSA on secp256r1 using SHA-256. Was 
 measured using a Python script, with a USB card reader, on Linux. Exhibits clear bit-length only leakage.
 - **libgcrypt**: [data_gcrypt.csv](data_gcrypt.csv) ECDSA on secp256r1 using SHA-1. Was measured 
 on Linux. Exhibits clear bit-length only leakage.
 - **SunEC/OpenJDK/OracleJDK**: [data_sunec.csv](data_sunec.csv) ECDSA on sect233r1 using SHA-1. Was 
 measured on Linux. Exhibits clear bit-length only leakage.
 - **Crypto++**: [data_cryptopp.csv](data_cryptopp.csv) ECDSA on sect233r1 using SHA-1. Was measured
 on Linux. Exhibits bit-length leakage along with more leakage from the MSB.
 - **MatrixSSL**: [data_matrixssl.csv](data_matrixssl.csv) ECDSA on secp256r1 using SHA-1. Was measured
 on Linux. Exhibits bit-length leakage as well as Hamming weight leakage.
 - **WolfCrypt**: [data_wolfcrypt.csv](data_wolfcrypt.csv) ECDSA on secp256r1 using SHA-1. Was measured
 on Linux. Exhibits very small bit-length-like leakage.
 - **Simulated**: [data_sim.csv](data_sim.csv) ECDSA on secp256r1 using SHA-1. Was simulated with no noise.
 Exhibits exact bit-length leakage.
