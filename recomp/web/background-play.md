# Background play (Play Room v93, 2026-11-08)

Browsers stop requestAnimationFrame while a page is hidden, which stopped the Wide engine's
emscripten main loop. The runtime now exports `rotk_bg_tick()` (runtime.cpp, web build: runs
`web_single_tick()` once) and `link.sh` exports `_rotk_bg_tick`. The page starts a tiny worker
(`setInterval(postMessage, 16)`) and, only while `document.visibilityState === "hidden"`, calls
`M._rotk_bg_tick()` and the Auto bot's `window.__autoTick()` on each message. Visible pages keep
using animation frames. If workers are unavailable the page pauses on hide as before.
Phones (iOS) suspend background pages entirely, so this only helps on PC.
Tested headless by queueing rAF callbacks and faking `visibilityState`: 10 s hidden = ~620 game frames.
