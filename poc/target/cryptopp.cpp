#include <cstdlib>
using std::exit;

#include <cryptopp/osrng.h>
using CryptoPP::AutoSeededRandomPool;

#include <cryptopp/sha.h>
using CryptoPP::SHA1;
using CryptoPP::SHA224;
using CryptoPP::SHA256;
using CryptoPP::SHA384;
using CryptoPP::SHA512;

#include <cryptopp/eccrypto.h>
using CryptoPP::ECP;
using CryptoPP::EC2N;
using CryptoPP::DL_PrivateKey_EC;
using CryptoPP::DL_PublicKey_EC;
using CryptoPP::DL_GroupParameters_EC;
using CryptoPP::ECDSA;

#include <cryptopp/oids.h>
using CryptoPP::OID;

#include <cryptopp/asn.h>

using CryptoPP::byte;
using CryptoPP::Integer;

#include <iostream>
#include <sys/random.h>

#define CLK_START clock_get
#define CLK_STOP clock_get
#include "common.c"

#define SET_CURVE(out, in, curve) \
    if (!strcasecmp(in, #curve)) { \
        out = CryptoPP::ASN1::curve(); \
    }

template<class EC, class HASH> void perform(args_t args) {
    AutoSeededRandomPool rng;
    typename ECDSA<EC, HASH>::Signer signer;
    OID curve;
    SET_CURVE(curve, args.curve, secp160r1)
    SET_CURVE(curve, args.curve, secp192r1)
    SET_CURVE(curve, args.curve, secp224r1)
    SET_CURVE(curve, args.curve, secp256r1)
    SET_CURVE(curve, args.curve, secp384r1)
    SET_CURVE(curve, args.curve, secp521r1)

    SET_CURVE(curve, args.curve, sect163r1)
    SET_CURVE(curve, args.curve, sect233r1)
    SET_CURVE(curve, args.curve, sect283r1)
    SET_CURVE(curve, args.curve, sect409r1)
    SET_CURVE(curve, args.curve, sect571r1)
    if (curve.Empty()) {
        fprintf(stderr, "Unsupported curve: %s\n", args.curve);
        exit(3);
    }

    signer.AccessKey().Initialize(rng, curve);
    typename ECDSA<EC, HASH>::PublicKey pkey;
    signer.AccessKey().MakePublicKey(pkey);
    const typename EC::Point& q = pkey.GetPublicElement();
    unsigned int len = pkey.GetGroupParameters().GetEncodedElementSize(true);
    byte pt[len];
    pkey.GetGroupParameters().EncodeElement(true, q, pt);
    print_buf(pt, len);
    printf(" ");

    size_t data_len = 64;
    unsigned char data[data_len];
    getrandom(data, data_len, 0);
    print_buf(data, data_len);

#ifdef DEBUG
	printf(" ");
	const Integer& x = signer.AccessKey().GetPrivateExponent();
	size_t xlen = x.MinEncodedSize();
	byte xdata[len];
	x.Encode(xdata, xlen);
	print_buf(xdata, xlen);
#endif //DEBUG

    printf("\n");

    std::string signature(signer.MaxSignatureLength(), 0);
    size_t sig_len;
    unsigned long long start, end;
    for (size_t i = 0; i < args.sig_count; ++i) {
        start = CLK_START();
        sig_len = signer.SignMessage(rng, (byte *)data, data_len, (byte *)signature.c_str());
        end = CLK_STOP();
        unsigned long long diff = 0;
        if (end >= start) {
            diff = end - start;
        }

        print_buf((const unsigned char *) signature.c_str(), sig_len / 2);
        printf(",");
        print_buf((const unsigned char *) signature.c_str() + (sig_len / 2), sig_len / 2);
        printf(",%llu\n", diff);
    }
}

int main(int argc, char *argv[]) {
    args_t args = parse_args(argc, argv);
    std::string curve = args.curve;
    if (curve.rfind("secp", 0) == 0) {
        if (!strcasecmp(args.hash, "SHA1")) {
            perform<ECP, SHA1>(args);
        } else if (!strcasecmp(args.hash, "SHA224")) {
            perform<ECP, SHA224>(args);
        } else if (!strcasecmp(args.hash, "SHA256")) {
            perform<ECP, SHA256>(args);
        } else if (!strcasecmp(args.hash, "SHA384")) {
            perform<ECP, SHA384>(args);
        } else if (!strcasecmp(args.hash, "SHA512")) {
            perform<ECP, SHA512>(args);
        } else {
            fprintf(stderr, "Unknown hash type: %s\n", args.hash);
            return 2;
        }
    } else if (curve.rfind("sect", 0) == 0) {
        if (!strcasecmp(args.hash, "SHA1")) {
            perform<EC2N, SHA1>(args);
        } else if (!strcasecmp(args.hash, "SHA224")) {
            perform<EC2N, SHA224>(args);
        } else if (!strcasecmp(args.hash, "SHA256")) {
            perform<EC2N, SHA256>(args);
        } else if (!strcasecmp(args.hash, "SHA384")) {
            perform<EC2N, SHA384>(args);
        } else if (!strcasecmp(args.hash, "SHA512")) {
            perform<EC2N, SHA512>(args);
        } else {
            fprintf(stderr, "Unknown hash type: %s\n", args.hash);
            return 2;
        }
    } else {
        fprintf(stderr, "Unknown curve type: %s\n", curve.c_str());
        return 3;
    }
    return 0;
}