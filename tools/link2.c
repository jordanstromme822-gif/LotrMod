// Two GBAs joined by a link cable, in one process: ./link2 romA romB script outdir
// Both cores run in turns of one scanline, so they stay within ~1200 cycles of each other.
// Multiplayer-mode (SIO_MULTI) transfers are done by our own small driver: when the master
// starts a transfer, both GBAs' SIOMLT_SEND words are latched and each GBA gets SIOMULTI0-3,
// its ID and the SIO interrupt after the transfer time.
// SAVE=1 loads romA.sav / romB.sav next to each ROM.
// script lines: "<frames> <keysA> <keysB>", "shot <name>" (writes outdir/name_a.ppm and _b.ppm),
//   "peek <addr>" (both GBAs), "poke <a|b> <addr> <u32>", "log on|off" (print every transfer)
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <mgba/core/timing.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/io.h>
#include <mgba/internal/gba/sio.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void nolog(struct mLogger* l, int c, enum mLogLevel lv, const char* f, va_list a) { (void) l; (void) c; (void) lv; (void) f; (void) a; }
static struct mLogger L = { .log = nolog };

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

static int keymask(const char* s) {
	int m = 0; char buf[128]; strncpy(buf, s, 127); buf[127] = 0;
	for (char* t = strtok(buf, "+"); t; t = strtok(NULL, "+")) {
		if (!strcmp(t, "A")) m |= 1; else if (!strcmp(t, "B")) m |= 2; else if (!strcmp(t, "SEL")) m |= 4; else if (!strcmp(t, "START")) m |= 8;
		else if (!strcmp(t, "RT")) m |= 16; else if (!strcmp(t, "LT")) m |= 32; else if (!strcmp(t, "U")) m |= 64; else if (!strcmp(t, "D")) m |= 128;
		else if (!strcmp(t, "R")) m |= 256; else if (!strcmp(t, "L")) m |= 512;
	}
	return m;
}

static struct mCore* cores[2];
static color_t* bufs[2];

static void runFrame(void) {
	uint32_t f0 = cores[0]->frameCounter(cores[0]), f1 = cores[1]->frameCounter(cores[1]);
	// Alternate by scanline until both have finished a frame.
	while (cores[0]->frameCounter(cores[0]) == f0 || cores[1]->frameCounter(cores[1]) == f1) {
		for (int i = 0; i < 2; ++i) {
			uint32_t fs = i ? f1 : f0;
			if (cores[i]->frameCounter(cores[i]) != fs) continue;
			uint16_t vc = gbas[i]->memory.io[REG_VCOUNT >> 1];
			while (gbas[i]->memory.io[REG_VCOUNT >> 1] == vc && cores[i]->frameCounter(cores[i]) == fs) cores[i]->runLoop(cores[i]);
		}
	}
}

static void shot(const char* dir, const char* name, int i) {
	char p[512]; snprintf(p, sizeof(p), "%s/%s_%c.ppm", dir, name, 'a' + i);
	FILE* f = fopen(p, "wb"); fprintf(f, "P6 240 160 255\n");
	for (int k = 0; k < 240 * 160; ++k) { color_t c = bufs[i][k]; unsigned char px[3] = { c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF }; fwrite(px, 1, 3, f); }
	fclose(f);
}

int main(int argc, char** argv) {
	if (argc < 5) { puts("usage: link2 romA romB script outdir"); return 1; }
	if (!getenv("MLOG")) mLogSetDefaultLogger(&L);
	for (int i = 0; i < 2; ++i) {
		struct mCore* c = mCoreFind(argv[1 + i]); if (!c) { puts("no core"); return 1; }
		c->init(c); mCoreInitConfig(c, NULL);
		bufs[i] = malloc(240 * 160 * sizeof(color_t)); c->setVideoBuffer(c, bufs[i], 240);
		if (!mCoreLoadFile(c, argv[1 + i])) { puts("load fail"); return 1; }
		if (getenv("SAVE")) mCoreAutoloadSave(c);
		cores[i] = c; gbas[i] = c->board;
		struct Node* n = &nodes[i];
		memset(n, 0, sizeof(*n)); n->id = i;
		n->d.load = nodeLoad; n->d.unload = nodeUnload; n->d.writeRegister = writeRegMaster;
		n->done.context = n; n->done.callback = finish; n->done.name = "Link transfer"; n->done.priority = 0x80;
		c->reset(c);
		GBASIOSetDriver(&gbas[i]->sio, &n->d, SIO_MULTI);
	}
	FILE* sc = fopen(argv[3], "r"); if (!sc) { puts("no script"); return 1; }
	char line[256]; long frame = 0;
	while (fgets(line, sizeof(line), sc)) {
		char a[64] = "", b[64] = "", c3[64] = "";
		int n = sscanf(line, "%63s %63s %63s", a, b, c3);
		if (n < 1) continue;
		if (!strcmp(a, "shot")) { shot(argv[4], b, 0); shot(argv[4], b, 1); continue; }
		if (!strcmp(a, "log")) { logXfer = !strcmp(b, "on"); continue; }
		if (!strcmp(a, "peek")) {
			uint32_t ad = strtoul(b, 0, 16);
			for (int i = 0; i < 2; ++i) { printf("PEEK%c %08x:", 'a' + i, ad); for (int k = 0; k < 8; ++k) printf(" %04x", cores[i]->busRead16(cores[i], ad + 2 * k)); printf("\n"); }
			continue;
		}
		if (!strcmp(a, "poke")) { uint32_t ad, v; sscanf(line, "%*s %*s %x %x", &ad, &v); int i = b[0] == 'b'; cores[i]->busWrite32(cores[i], ad, v); continue; }
		long fr = atol(a);
		int ka = keymask(n > 1 ? b : "-"), kb = keymask(n > 2 ? c3 : "-");
		cores[0]->setKeys(cores[0], ka); cores[1]->setKeys(cores[1], kb);
		for (long k = 0; k < fr; ++k) { runFrame(); ++frame; }
	}
	printf("ran %ld frames, %ld transfers\n", frame, xfers);
	return 0;
}
