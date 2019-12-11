#include <stdio.h>
#include <stdlib.h>
#include <cryptoApi.h>
#include <coreApi.h>
#include <sys/random.h>
#define CLK_START clock_get
#define CLK_STOP clock_get
#include "common.c"

typedef void (*hash_ptr)(unsigned char *data, size_t data_len , unsigned char *out);

#define HASH_FUNC(name, ctx_name, fname) \
    void name##_func(unsigned char *data, size_t data_len, unsigned char *out) { \
        ps##ctx_name##_t ctx; \
        ps##fname##Init(&ctx); \
        ps##fname##Update(&ctx, data, data_len); \
        ps##fname##Final(&ctx, out); \
    }

HASH_FUNC(sha1, Sha1, Sha1)
HASH_FUNC(sha224, Sha256, Sha224)
HASH_FUNC(sha256, Sha256, Sha256)
HASH_FUNC(sha384, Sha384, Sha384)
HASH_FUNC(sha512, Sha512, Sha512)

hash_ptr get_hash_algo(const char *hash) {
    if (!strcasecmp(hash, "SHA1")) {
        return sha1_func;
    } else if (!strcasecmp(hash, "SHA224")) {
        return sha224_func;
    } else if (!strcasecmp(hash, "SHA256")) {
        return sha256_func;
    } else if (!strcasecmp(hash, "SHA384")) {
        return sha384_func;
    } else if (!strcasecmp(hash, "SHA512")) {
        return sha512_func;
    } else if (!strcasecmp(hash, "NONE")) {
        return NULL;
    } else {
        fprintf(stderr, "Unknown hash type: %s\n", hash);
        exit(2);
    }
}

int get_hash_len(const char *hash) {
    if (!strcasecmp(hash, "SHA1")) {
        return SHA1_HASH_SIZE;
    } else if (!strcasecmp(hash, "SHA224")) {
        return SHA224_HASH_SIZE;
    } else if (!strcasecmp(hash, "SHA256")) {
        return SHA256_HASH_SIZE;
    } else if (!strcasecmp(hash, "SHA384")) {
        return SHA384_HASH_SIZE;
    } else if (!strcasecmp(hash, "SHA512")) {
        return SHA512_HASH_SIZE;
    } else if (!strcasecmp(hash, "NONE")) {
        return 0;
    } else {
        fprintf(stderr, "Unknown hash type: %s\n", hash);
        exit(2);
    }
}

int main(int argc, char *argv[]) {
    args_t args = parse_args(argc, argv);
    hash_ptr hash_algo = get_hash_algo(args.hash);
    int hash_len = get_hash_len(args.hash);

    psCoreOpen(PSCORE_CONFIG);
    psOpenPrng();

    size_t i = 0;
    while (eccCurves[i].size > 0) {
        if (strcmp(eccCurves[i].name, args.curve) == 0) {
            break;
        }
        i++;
    }
    if (eccCurves[i].size <= 0) {
        fprintf(stderr, "Unknown curve: %s\n", args.curve);
        exit(3);
    }

    const psEccCurve_t *curve = &eccCurves[i];
    psEccKey_t *key;
    psEccNewKey(NULL, &key, curve);
    psEccInitKey(NULL, key, curve);
    psEccGenKey(NULL, key, curve, NULL);

    int xlen = pstm_unsigned_bin_size(&key->pubkey.x);
    int ylen = pstm_unsigned_bin_size(&key->pubkey.y);
    int felem_size = (strlen(curve->prime) + 1) / 2;
    int pubkey_size = 1 + felem_size * 2;
    unsigned char pubkey[pubkey_size];
    memset(pubkey, 0, pubkey_size);
    pstm_to_unsigned_bin(NULL, &key->pubkey.x, pubkey + 1 + (felem_size - xlen));
    pubkey[0] = 0x04;
    pstm_to_unsigned_bin(NULL, &key->pubkey.y, pubkey + 1 + felem_size + (felem_size - ylen));
    print_buf(pubkey, pubkey_size);
    printf(" ");

    size_t data_len = 64;
    unsigned char data[data_len];
    getrandom(data, data_len, 0);
    print_buf(data, data_len);

#ifdef DEBUG
	printf(" ");
	int dlen = pstm_unsigned_bin_size(&key->k);
	unsigned char ddata[dlen];
	pstm_to_unsigned_bin(NULL, &key->k, ddata);
	print_buf(ddata, dlen);
#endif //DEBUG

    printf("\n");

    if (hash_algo == NULL) {
        hash_len = data_len;
    }
    unsigned char hash[hash_len];
    if (hash_algo != NULL) {
        hash_algo(data, data_len, hash);
    } else {
        memcpy(hash, data, data_len);
    }

    psSize_t sig_len = 512;
    unsigned char sig[sig_len];
    unsigned long long start, end;
    for (size_t i = 0; i < args.sig_count; ++i) {
        start = CLK_START();
        psEccDsaSign(NULL, key, hash, hash_len, sig, &sig_len, 0, NULL);
        end = CLK_STOP();

        unsigned long long diff = 0;
        if (end >= start) {
            diff = end - start;
        }
        unsigned char *r = NULL, *s = NULL;
        size_t rlen = 0, slen = 0;
        asn1_der_decode(sig, sig_len, &r, &rlen, &s, &slen);
        print_buf(r, rlen);
        printf(",");
        print_buf(s, slen);
        printf(",%llu\n", diff);
        free(r);
        free(s);
        sig_len = 512;
    }

    psEccDeleteKey(&key);
    return 0;
}