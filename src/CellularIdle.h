#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

// The original eight-byte periodic ping is unchanged for legacy hosts.
// Sunshine accepts an optional MSI1 extension; stale classification disables it.
static inline int buildCellularIdlePing(char payload[13], bool sunshine,
                                       bool cellular, uint64_t updatedMs, uint64_t nowMs) {
    memset(payload, 0, 13);
    payload[0] = 4;
    if (!sunshine) return 8;
    memcpy(payload + 8, "MSI1", 4);
    payload[12] = cellular && nowMs >= updatedMs && nowMs - updatedMs < 1500;
    return 13;
}
