// Two-GBA multiplayer-mode link cable driver, shared by tools/link2.c (native test runner)
// and tools/link/web.c (browser build). Both GBAs live in one process and take turns.
#pragma once
#include <mgba/core/timing.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/io.h>
#include <mgba/internal/gba/sio.h>
#include <stdio.h>
#include <string.h>

struct Node { struct GBASIODriver d; int id; struct mTimingEvent done; uint16_t recv[4]; int busy; };
static struct Node nodes[2];
static struct GBA* gbas[2];
static int logXfer;
static long xfers;

static int bothMulti(void) { return gbas[0]->sio.mode == SIO_MULTI && gbas[1]->sio.mode == SIO_MULTI; }

static void finish(struct mTiming* t, void* ctx, uint32_t late) {
	(void) t; (void) late;
	struct Node* n = ctx; struct GBA* g = gbas[n->id];
	for (int i = 0; i < 4; ++i) g->memory.io[(REG_SIOMULTI0 >> 1) + i] = n->recv[i];
	g->sio.siocnt = (g->sio.siocnt & ~0x0030 & ~0x0080) | (n->id << 4);
	n->busy = 0;
	if (g->sio.siocnt & 0x4000) GBARaiseIRQ(g, GBA_IRQ_SIO, 0);
}

static uint16_t ready(int id, uint16_t v) {
	v &= ~0x000C;
	if (id) v |= 0x0004;            // SI: slave
	if (bothMulti()) v |= 0x0008;   // SD: everyone is connected
	return v;
}

static uint16_t writeReg(struct GBASIODriver* drv, uint32_t address, uint16_t value) {
	struct Node* n = (struct Node*) drv;
	if (address != REG_SIOCNT) return value;
	uint16_t keep = drv->p->siocnt & 0x00B0; // ID bits and busy stay as they are
	(void) n;
	return ready(n->id, (value & 0xFF03 & ~0x0080) | keep);
}

static uint16_t writeRegMaster(struct GBASIODriver* drv, uint32_t address, uint16_t value) {
	struct Node* n = (struct Node*) drv;
	uint16_t start = value & 0x0080;
	uint16_t out = writeReg(drv, address, value);
	if (address != REG_SIOCNT || n->id != 0 || !start || n->busy || !bothMulti()) return out;
	uint16_t data[4] = { gbas[0]->memory.io[REG_SIOMLT_SEND >> 1], gbas[1]->memory.io[REG_SIOMLT_SEND >> 1], 0xFFFF, 0xFFFF };
	int cycles = GBASIOCyclesPerTransfer[out & 3][1];
	if (logXfer) printf("XFER %ld %04x %04x\n", xfers, data[0], data[1]);
	++xfers;
	for (int i = 0; i < 2; ++i) {
		struct Node* m = &nodes[i]; struct GBA* g = gbas[i];
		memcpy(m->recv, data, sizeof(data));
		m->busy = 1;
		for (int k = 0; k < 4; ++k) g->memory.io[(REG_SIOMULTI0 >> 1) + k] = 0xFFFF;
		if (i) g->sio.siocnt |= 0x0080;
		if (mTimingIsScheduled(&g->timing, &m->done)) mTimingDeschedule(&g->timing, &m->done);
		mTimingSchedule(&g->timing, &m->done, cycles);
	}
	return out | 0x0080;
}

static bool nodeLoad(struct GBASIODriver* drv) {
	struct Node* n = (struct Node*) drv;
	drv->p->siocnt = ready(n->id, drv->p->siocnt);
	return true;
}
static bool nodeUnload(struct GBASIODriver* drv) {
	struct Node* n = (struct Node*) drv;
	struct GBA* g = gbas[n->id];
	if (mTimingIsScheduled(&g->timing, &n->done)) mTimingDeschedule(&g->timing, &n->done);
	n->busy = 0;
	return true;
}


static void linkAttach(struct GBA* g, int i) {
	struct Node* n = &nodes[i];
	memset(n, 0, sizeof(*n)); n->id = i; gbas[i] = g;
	n->d.load = nodeLoad; n->d.unload = nodeUnload; n->d.writeRegister = writeRegMaster;
	n->done.context = n; n->done.callback = finish; n->done.name = "Link transfer"; n->done.priority = 0x80;
	GBASIOSetDriver(&g->sio, &n->d, SIO_MULTI);
}
