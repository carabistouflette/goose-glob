#include <stdint.h>
#include <stdio.h>
#include <inttypes.h>
static uint64_t profile_parts, profile_spans, profile_part_bytes, profile_span_bytes;
static uint64_t profile_current, profile_max;
static void allocation_reset(void) {
    profile_parts = profile_spans = profile_part_bytes = profile_span_bytes = profile_current = profile_max = 0;
}
static void allocation_begin(void) { profile_current = 0; }
static void allocation_end(void) { if (profile_current > profile_max) profile_max = profile_current; }
static void allocation_report(int64_t calls) {
    fprintf(stderr, "records\t%" PRId64 "\t%" PRIu64 "\t%" PRIu64 "\t%" PRIu64 "\t%" PRIu64 "\t%" PRIu64 "\n", calls, profile_parts, profile_part_bytes, profile_spans, profile_span_bytes, profile_max);
}
