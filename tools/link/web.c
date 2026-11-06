// Browser build: two linked GBAs for online 2-player. Every player's device runs BOTH GBAs from the
// same game file and saves, and feeds them the same buttons on the same frame, so the two copies stay
// identical; each device shows (and plays the sound of) its own player's GBA.
//
// Build (see tools/link/build.sh): emcc web.c libmgba.a -> link.js + link.wasm
#include <emscripten.h>
#include <mgba/core/core.h>
#include <mgba/core/blip_buf.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
#include <stdarg.h>
#include <stdlib.h>
#include "linkdrv.h"

static void nolog(struct mLogger* l, int c, enum mLogLevel lv, const char* f, va_list a) { (void) l; (void) c; (void) lv; (void) f; (void) a; }
static struct mLogger L = { .log = nolog };

static struct mCore* cores[2];
static color_t* video[2];
static int16_t audioOut[4096];
static int started;

static void runFrame(void) {
	uint32_t f0 = cores[0]->frameCounter(cores[0]), f1 = cores[1]->frameCounter(cores[1]);
	while (cores[0]->frameCounter(cores[0]) == f0 || cores[1]->frameCounter(cores[1]) == f1) {
		for (int i = 0; i < 2; ++i) {
			uint32_t fs = i ? f1 : f0;
			if (cores[i]->frameCounter(cores[i]) != fs) continue;
			uint16_t vc = gbas[i]->memory.io[REG_VCOUNT >> 1];
			while (gbas[i]->memory.io[REG_VCOUNT >> 1] == vc && cores[i]->frameCounter(cores[i]) == fs) cores[i]->runLoop(cores[i]);
		}
	}
}

// rom: the built game; sav0/sav1: player 1's and player 2's save files (may be empty).
// rate: the page's audio sample rate.
EMSCRIPTEN_KEEPALIVE int lk_init(const uint8_t* rom, int romLen, const uint8_t* sav0, int sav0Len, const uint8_t* sav1, int sav1Len, int rate) {
	mLogSetDefaultLogger(&L);
	const uint8_t* savs[2] = { sav0, sav1 };
	int savLens[2] = { sav0Len, sav1Len };
	for (int i = 0; i < 2; ++i) {
		void* copy = malloc(romLen); memcpy(copy, rom, romLen);
		struct VFile* vf = VFileFromMemory(copy, romLen);
		struct mCore* c = mCoreFindVF(vf);
		if (!c) return -1;
		c->init(c);
		mCoreInitConfig(c, NULL);
		video[i] = calloc(240 * 160, sizeof(color_t));
		c->setVideoBuffer(c, video[i], 240);
		if (!c->loadROM(c, vf)) return -2;
		struct VFile* sv = VFileMemChunk(savLens[i] ? savs[i] : NULL, savLens[i]);
		c->loadSave(c, sv);
		c->setAudioBufferSize(c, 2048);
		blip_set_rates(c->getAudioChannel(c, 0), c->frequency(c), rate);
		blip_set_rates(c->getAudioChannel(c, 1), c->frequency(c), rate);
		c->reset(c);
		cores[i] = c;
		linkAttach(c->board, i);
	}
	started = 1;
	return 0;
}

// Runs one frame on both GBAs with these buttons (GBA KEYINPUT bits, 1 = pressed).
EMSCRIPTEN_KEEPALIVE void lk_frame(int keys0, int keys1) {
	if (!started) return;
	cores[0]->setKeys(cores[0], keys0);
	cores[1]->setKeys(cores[1], keys1);
	runFrame();
}

EMSCRIPTEN_KEEPALIVE color_t* lk_video(int i) { return video[i & 1]; }

// Interleaved stereo samples of GBA i since the last call; returns the number of stereo frames.
EMSCRIPTEN_KEEPALIVE int16_t* lk_audio_buf(void) { return audioOut; }
EMSCRIPTEN_KEEPALIVE int lk_audio(int i, int other) {
	struct mCore* c = cores[i & 1];
	blip_t* l = c->getAudioChannel(c, 0); blip_t* r = c->getAudioChannel(c, 1);
	int n = blip_samples_avail(l); if (n > 2048) n = 2048;
	blip_read_samples(l, audioOut, n, 1);
	blip_read_samples(r, audioOut + 1, n, 1);
	// The other GBA's sound is thrown away so its buffer doesn't fill up.
	struct mCore* o = cores[other & 1];
	if (o != c) {
		blip_t* ol = o->getAudioChannel(o, 0); blip_t* orr = o->getAudioChannel(o, 1);
		int m = blip_samples_avail(ol);
		while (m > 0) { int k = m > 1024 ? 1024 : m; static int16_t junk[2048]; blip_read_samples(ol, junk, k, 1); blip_read_samples(orr, junk + 1, k, 1); m -= k; }
	}
	return n;
}

// The current save file of GBA i (copied into a buffer the page frees with lk_free).
static int saveLen;
EMSCRIPTEN_KEEPALIVE void* lk_save(int i) { void* p = NULL; saveLen = (int) cores[i & 1]->savedataClone(cores[i & 1], &p); return p; }
EMSCRIPTEN_KEEPALIVE int lk_save_len(void) { return saveLen; }
EMSCRIPTEN_KEEPALIVE void lk_free(void* p) { free(p); }

// A cheap fingerprint of both GBAs' work RAM, so the two devices can check they are still in step.
EMSCRIPTEN_KEEPALIVE uint32_t lk_hash(void) {
	uint32_t h = 2166136261u;
	for (int i = 0; i < 2; ++i) {
		const uint8_t* m = (const uint8_t*) gbas[i]->memory.iwram;
		for (int k = 0; k < 0x8000; k += 4) { h ^= *(const uint32_t*) (m + k); h *= 16777619u; }
	}
	return h;
}

EMSCRIPTEN_KEEPALIVE uint8_t* lk_iwram(int i) { return (uint8_t*) gbas[i & 1]->memory.iwram; }
EMSCRIPTEN_KEEPALIVE uint8_t* lk_ewram(int i) { return (uint8_t*) gbas[i & 1]->memory.wram; }
EMSCRIPTEN_KEEPALIVE uint8_t* lk_alloc(int n) { return malloc(n); }
