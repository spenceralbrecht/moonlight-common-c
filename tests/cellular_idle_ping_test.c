#include "CellularIdle.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    char payload[13];
    assert(buildCellularIdlePing(payload, false, true, 100, 101) == 8);
    assert(payload[0] == 4 && payload[8] == 0);
    assert(buildCellularIdlePing(payload, true, true, 100, 1599) == 13);
    assert(memcmp(payload + 8, "MSI1", 4) == 0 && payload[12] == 1);
    assert(buildCellularIdlePing(payload, true, true, 100, 1600) == 13 && payload[12] == 0);
    assert(buildCellularIdlePing(payload, true, false, 100, 101) == 13 && payload[12] == 0);
    assert(buildCellularIdlePing(payload, true, true, 100, 99) == 13 && payload[12] == 0);
    puts("cellular idle ping: legacy, cellular, Wi-Fi, expiry and clock checks passed");
    return 0;
}
