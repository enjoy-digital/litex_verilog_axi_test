#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <libbase/uart.h>
#include <libbase/console.h>
#include <generated/csr.h>
#include <generated/mem.h>

#include "axi_mmap.h"

/* Test RAM */
void test_ram(char * name, uint32_t base) {
	volatile uint32_t *axi_ram = (uint32_t *) base;

	int errors = 0;

	printf("\nTesting %s at @0x%08x...\n", name, base);

	/* Very simple test */
	axi_ram[0] = 0x5aa55aa5;
	axi_ram[1] = 0x12345678;
	if (axi_ram[0] != 0x5aa55aa5)
		errors++;
	if (axi_ram[1] != 0x12345678)
		errors++;

	/* Result */
	printf("errors: %d\n", errors);
}
