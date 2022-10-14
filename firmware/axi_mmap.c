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

void dump_buf(const char *bufname, const uint32_t *buf, size_t size)
{
	printf("%s dump:\n", bufname);
	for(uint32_t *end = buf+size/sizeof(*buf); buf != end; ++buf)
	{
	  printf("Address %p = 0x%08x\n", buf, *buf);
	}
}

void test_dma(char * name) {
	int errors = 0;
	typedef struct
	{
		volatile uint32_t src[4], dst[4];
	} dma_data;
	dma_data *cdma = (dma_data *) AXI_DP_RAM_1A_BASE;
	dma_data *dma = (dma_data *) AXI_DP_RAM_2A_BASE;

	printf("\nTesting %s...\n", name);
	
	/* Set abitrary values */
	memset(cdma, 0xFF, sizeof(*cdma));
	memset(dma, 0xFF, sizeof(*dma));
	cdma->src[1] = 0x12345678;
	dma->src[2] = 0xAABBCCDD;

	/*Make sure buffers are initially different*/
	errors += (memcmp(dma->src, cdma->dst, sizeof(dma->src)) == 0);
	errors += (memcmp(cdma->src, dma->dst, sizeof(cdma->src)) == 0);
	
	/* Dump "before" state */
	printf("\nBEFORE state:\n");
	dump_buf("src_cdma", cdma->src, sizeof(cdma->src));
	dump_buf("dst_cdma", cdma->dst, sizeof(cdma->dst));
	dump_buf("src_dma", dma->src, sizeof(dma->src));
	dump_buf("dst_dma", dma->dst, sizeof(dma->dst));
	
	/*Configure CDMA*/
	axi_cdma_read_addr_write(cdma->src);
	axi_cdma_write_addr_write(cdma->dst);
	axi_cdma_len_write(sizeof(cdma->dst));
	axi_cdma_valid_write(1);
	axi_cdma_valid_write(0);

	/*Configure DMA*/
	axi_dma_read_addr_write(dma->src);
	axi_dma_write_addr_write(dma->dst);
	axi_dma_len_write(sizeof(dma->dst));
	axi_dma_valid_write(1);
	axi_dma_valid_write(0);

	/* Dump "after" state */
	printf("\AFTER state:\n");
	dump_buf("src_cdma", cdma->src, sizeof(cdma->src));
	dump_buf("dst_cdma", cdma->dst, sizeof(cdma->dst));
	dump_buf("src_dma", dma->src, sizeof(dma->src));
	dump_buf("dst_dma", dma->dst, sizeof(dma->dst));

	/* Compare results */
	errors += (memcmp(dma->src, cdma->dst, sizeof(dma->src)) != 0);
	errors += (memcmp(cdma->src, dma->dst, sizeof(cdma->src)) != 0);

	/* Result */
	printf("\nDMA errors: %d\n", errors);
}
