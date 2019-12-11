
CFLAGS=-O2 -Wall

all: gcrypt_target matrixssl_target cryptopp_target wolfcrypt_target sunec_target

# Use libgcrypt-config to locate the libs.
gcrypt_target: gcrypt.c
	$(CC) $(shell libgcrypt-config --cflags) $(CFLAGS) -o $@ -I. $(shell libgcrypt-config --libs) $<

# This assumes matrixssl is in the matrixssl dicertory and its two static libs are in the current dir.
# It also requires a particular MatrixSSL crypto config.
matrixssl_target: matrixssl.c
	$(CC) $(CFLAGS) -o $@ -I. -Imatrixssl/ -L. $< libcrypt_s.a libcore_s.a

cryptopp_target: cryptopp.cpp
	$(CXX) $(shell pkg-config libcryptopp --cflags) $(CXXFLAGS) -o $@ -I. $(shell pkg-config libcryptopp --libs) $<

sunec_target: sunec.java
	javac -d . sunec.java

wolfcrypt_target: wolfcrypt.c
	$(CC) $(shell pkg-config wolfssl --cflags) $(CFLAGS) -o $@ -I. $(shell pkg-config wolfssl --libs) $<

strip:
	strip *_target

clean:
	rm -f gcrypt_target
	rm -f matrixssl_target
	rm -f cryptopp_target
	rm -f sunec_target.class
	rm -f wolfcrypt_target

.PHONY: all clean strip