#include <stdio.h>
#include <stdlib.h>
#include <gcrypt.h>
#include <sys/random.h>
#define CLK_START clock_get
#define CLK_STOP clock_get
#include "common.c"

int get_hash_algo(const char *hash) {
    if (!strcasecmp(hash, "SHA1")) {
        return GCRY_MD_SHA1;
    } else if (!strcasecmp(hash, "SHA224")) {
        return GCRY_MD_SHA224;
    } else if (!strcasecmp(hash, "SHA256")) {
        return GCRY_MD_SHA256;
    } else if (!strcasecmp(hash, "SHA384")) {
        return GCRY_MD_SHA384;
    } else if (!strcasecmp(hash, "SHA512")) {
        return GCRY_MD_SHA512;
    } else if (!strcasecmp(hash, "NONE")) {
        return GCRY_MD_NONE;
    } else {
        fprintf(stderr, "Unknown hash type: %s\n", hash);
        exit(2);
    }
}

int main(int argc, char *argv[]) {
    args_t args = parse_args(argc, argv);
    int hash_algo = get_hash_algo(args.hash);
    gcry_sexp_t gen_sexp, key_sexp, priv_sexp;

    gcry_sexp_build(&gen_sexp, NULL, "(genkey (ecc (flags param) (curve %s)))", args.curve);
    gcry_pk_genkey(&key_sexp, gen_sexp);

    priv_sexp = gcry_sexp_find_token(key_sexp, "private-key", 0);

    gcry_buffer_t q = {0};
    gcry_mpi_t d;
    gcry_sexp_extract_param(priv_sexp, "ecc", "&q+d", &q, &d, NULL);
    print_buf((unsigned char *) q.data, q.size);
    printf(" ");

    size_t data_len = 64;
    unsigned char data[data_len];
    getrandom(data, data_len, 0);
    print_buf(data, data_len);

#ifdef DEBUG
	printf(" ");
	size_t dlen = 0;
	gcry_mpi_print(GCRYMPI_FMT_USG, NULL, 0, &dlen, d);
	unsigned char ddata[dlen];
	gcry_mpi_print(GCRYMPI_FMT_USG, ddata, dlen, &dlen, d);
	print_buf(ddata, dlen);
#endif //DEBUG
    
    printf("\n");

    unsigned int hash_len;
    if (hash_algo == GCRY_MD_NONE) {
        hash_len = data_len;
    } else {
        hash_len = gcry_md_get_algo_dlen(hash_algo);
    }
    unsigned char hash[hash_len];
    if (hash_algo == GCRY_MD_NONE) {
        memcpy(hash, data, data_len);
    } else {
        gcry_md_hash_buffer(hash_algo, hash, data, data_len);
    }

    gcry_mpi_t hash_mpi;
    gcry_mpi_scan(&hash_mpi, GCRYMPI_FMT_USG, hash, hash_len, NULL);
    gcry_sexp_t data_sexp;
    gcry_sexp_build(&data_sexp, NULL, "(data (flags raw param) (value %M))", hash_mpi);

    gcry_sexp_t sig_sexp;
    gcry_buffer_t r_buf = {0};
    gcry_buffer_t s_buf = {0};
    unsigned long long start, end;
    for (size_t i = 0; i < args.sig_count; ++i) {
        start = CLK_START();
        gcry_pk_sign(&sig_sexp, data_sexp, priv_sexp);
        end = CLK_STOP();
        unsigned long long diff = 0;
        if (end >= start) {
            diff = end - start;
        }
        gcry_sexp_extract_param(sig_sexp, "ecdsa", "&rs", &r_buf, &s_buf, NULL);

        gcry_sexp_release(sig_sexp);
        print_buf(r_buf.data, r_buf.size);
        printf(",");
        print_buf(s_buf.data, s_buf.size);
        printf(",%llu\n", diff);
        gcry_free(r_buf.data);
        memset(&r_buf, 0, sizeof(r_buf));
        gcry_free(s_buf.data);
        memset(&s_buf, 0, sizeof(s_buf));
    }

    gcry_sexp_release(gen_sexp);
    gcry_sexp_release(key_sexp);
    gcry_sexp_release(priv_sexp);
    gcry_mpi_release(d);
    gcry_free(q.data);
    gcry_mpi_release(hash_mpi);
    gcry_sexp_release(data_sexp);
    return 0;
}