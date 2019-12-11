#include <stdio.h>
#include <stdlib.h>
#include <sys/random.h>
#include <wolfssl/options.h>
#include <wolfssl/wolfcrypt/ecc.h>
#include <wolfssl/wolfcrypt/hash.h>
#include <wolfssl/wolfcrypt/random.h>
#include <wolfssl/wolfcrypt/integer.h>
#define CLK_START clock_get
#define CLK_STOP clock_get
#include "common.c"

enum wc_HashType get_hash_algo(const char *hash) {
    if (!strcasecmp(hash, "SHA1")) {
        return WC_HASH_TYPE_SHA;
    } else if (!strcasecmp(hash, "SHA224")) {
        return WC_HASH_TYPE_SHA224;
    } else if (!strcasecmp(hash, "SHA256")) {
        return WC_HASH_TYPE_SHA256;
    } else if (!strcasecmp(hash, "SHA384")) {
        return WC_HASH_TYPE_SHA384;
    } else if (!strcasecmp(hash, "SHA512")) {
        return WC_HASH_TYPE_SHA512;
    } else if (!strcasecmp(hash, "NONE")) {
        return WC_HASH_TYPE_NONE;
    } else {
        fprintf(stderr, "Unknown hash type: %s\n", hash);
        exit(2);
    }
}

void print_mp(mp_int *val) {
    int hex_size;
    mp_radix_size(val, 16, &hex_size);
    char hex[hex_size + 1];
    hex[hex_size] = 0;
    mp_toradix(val, hex, 16);
    printf("%s", hex);
}

int main(int argc, char *argv[]) {
    args_t args = parse_args(argc, argv);
    enum wc_HashType hash_algo = get_hash_algo(args.hash);

    WC_RNG rng;
    wolfCrypt_Init();
    wc_InitRng(&rng);
    int curve_id = wc_ecc_get_curve_id_from_name(args.curve);
    if (curve_id == -1) {
        fprintf(stderr, "Unknown curve: %s\n", args.curve);
        exit(3);
    }
    ecc_key key;
    wc_ecc_init(&key);
    wc_ecc_make_key_ex(&rng, 0, &key, curve_id);
    unsigned int key_len = 0;
    wc_ecc_export_x963(&key, NULL, &key_len);
    byte key_out[key_len];
    wc_ecc_export_x963(&key, key_out, &key_len);
    print_buf(key_out, key_len);
    printf(" ");

    size_t data_len = 64;
    unsigned char data[data_len];
    getrandom(data, data_len, 0);
    print_buf(data, data_len);

#ifdef DEBUG
	printf(" ");
	print_mp(&key.k);
#endif //DEBUG

    printf("\n");

    int hash_len;
    if (hash_algo == WC_HASH_TYPE_NONE) {
        hash_len = data_len;
    } else {
        hash_len = wc_HashGetDigestSize(hash_algo);
    }
    byte hash[hash_len];
    if (hash_algo == WC_HASH_TYPE_NONE) {
        memcpy(hash, data, hash_len);
    } else {
        wc_Hash(hash_algo, data, data_len, hash, hash_len);
    }

    mp_int r, s;
    mp_init(&r);
    mp_init(&s);
    unsigned long long start, end;
    for (size_t i = 0; i < args.sig_count; ++i) {
        start = CLK_START();
        wc_ecc_sign_hash_ex(hash, hash_len, &rng, &key, &r, &s);
        end = CLK_STOP();

        unsigned long long diff = 0;
        if (end >= start) {
            diff = end - start;
        }
        print_mp(&r);
        printf(",");
        print_mp(&s);
        printf(",%llu\n", diff);
    }

    wc_FreeRng(&rng);
    wolfCrypt_Cleanup();
    return 0;
}