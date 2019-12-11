#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const char *curve;
    const char *hash;
    size_t sig_count;
} args_t;

void print_buf(const unsigned char *buf, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        printf("%02x", (unsigned char) buf[i]);
    }
}

unsigned long long rdtsc_start(void) {
    unsigned long long high, low;
    __asm__ volatile ("cpuid\n"
                      "rdtsc\n"
                      "mov %%rdx, %0\n"
                      "mov %%rax, %1\n": "=r" (high), "=r" (low) :: "%rax", "%rbx", "%rcx", "%rdx");
    return high << 32 | low;
}

unsigned long long clock_get(void) {
	struct timespec start;
	clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &start);
	return start.tv_sec * 1000000000 + start.tv_nsec;
}

unsigned long long rdtsc_stop(void) {
    unsigned long long high, low;
    __asm__ volatile ("rdtscp\n"
                      "mov %%rdx, %0\n"
                      "mov %%rax, %1\n"
                      "cpuid": "=r" (high), "=r" (low) :: "%rax", "%rbx", "%rcx", "%rdx");
    return high << 32 | low;
}

args_t parse_args(int argc, char *argv[]) {
    args_t result = {0};
    if (argc != 4) {
        fprintf(stderr, "usage: %s <curve> <hash> <signature count>\n", argv[0]);
        exit(1);
    }
    result.curve = argv[1];
    result.hash = argv[2];
    result.sig_count = atoll(argv[3]);
    return result;
}

unsigned char *asn1_der_encode(const unsigned char *r, size_t r_len, const unsigned char *s, size_t s_len) {
    const unsigned char *rtmp = r;
    while (*rtmp++ == 0) {
        r++;
        r_len--;
    }
    const unsigned char *stmp = s;
    while (*stmp++ == 0) {
        s++;
        s_len--;
    }

    unsigned char r_length = (unsigned char) r_len + (r[0] & 0x80 ? 1 : 0);
    unsigned char s_length = (unsigned char) s_len + (s[0] & 0x80 ? 1 : 0);

    // R and S are < 128 bytes, so 1 byte tag + 1 byte len + len bytes value
    size_t seq_value_len = 2 + r_length + 2 + s_length;
    size_t whole_len = seq_value_len;

    // The SEQUENCE length might be >= 128, so more bytes of length
    size_t seq_len_len = 0;
    if (seq_value_len >= 128) {
        size_t s = seq_value_len;
        do {
            seq_len_len++;
        } while ((s = s >> 8));
    }
    // seq_len_len bytes for length and one for length of length
    whole_len += seq_len_len + 1;

    // 1 byte tag for SEQUENCE
    whole_len += 1;

    unsigned char *data = (unsigned char *) malloc(whole_len);
    size_t i = 0;
    data[i++] = 0x30; // SEQUENCE
    if (seq_value_len < 128) {
        data[i++] = (unsigned char) seq_value_len;
    } else {
        data[i++] = (unsigned char) (seq_len_len | (1 << 7));
        for (size_t j = 0; j < seq_len_len; ++j) {
            data[i++] = (unsigned char) (seq_value_len & (0xff << (8 * (seq_len_len - j - 1))));
        }
    }
    data[i++] = 0x02; //INTEGER
    data[i++] = r_length;
    if (r[0] & 0x80) {
        data[i++] = 0;
    }
    memcpy(data + i, r, r_len);
    i += r_len;
    data[i++] = 0x02; //INTEGER
    data[i++] = s_length;
    if (s[0] & 0x80) {
        data[i++] = 0;
    }
    memcpy(data + i, s, s_len);
    i += s_len;

    return data;
}

bool asn1_der_decode(unsigned char *sig, size_t sig_len, unsigned char **r_data, size_t *r_len, unsigned char **s_data, size_t *s_len) {
    size_t i = 0;
    if (sig[i++] != 0x30) {//SEQUENCE
        return false;
    }
    size_t seq_value_len = 0;
    if (!(sig[i] & 0x80)) {
        seq_value_len = sig[i++];
    } else {
        size_t seq_len_len = sig[i++] & 0x7f;
        while (seq_len_len > 0) {
            seq_value_len |= (sig[i++] << (seq_len_len - 1));
            seq_len_len--;
        }
    }

    if (sig[i++] != 0x02) {//INTEGER
        return false;
    }
    size_t r_length = sig[i++];
    unsigned char *r_out = (unsigned char *) malloc(r_length);
    memcpy(r_out, sig + i, r_length);
    i += r_length;

    if (sig[i++] != 0x02) {//INTEGER
        free(r_out);
        return false;
    }
    size_t s_length = sig[i++];
    unsigned char *s_out = (unsigned char *) malloc(s_length);
    memcpy(s_out, sig + i, s_length);
    i += s_length;

    if (i != sig_len) {
        free(r_out);
        free(s_out);
        return false;
    }

    *r_len = r_length;
    *r_data = r_out;
    *s_len = s_length;
    *s_data = s_out;
    return true;
}

#ifdef __cplusplus
}
#endif
