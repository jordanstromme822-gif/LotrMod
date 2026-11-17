#!/usr/bin/env python3
"""Play Room v184: smooth sound, no clicks or pops (2026-11-17).

  python3 audio-stream-v184.py in.html out.html

Jordan: "Audio is clicky and poppy". The page played each game frame's sound as its own little buffer, scheduled
back to back. Each one restarted its resampling (a tiny step at every join, 60 a second), and whenever the engine fell
a little behind (phones, 2-player) the queue ran dry: a hard cut to silence, then a restart 80 ms later (a pop).
Now the sound is one continuous stream: an AudioWorklet plays from a queue, resampling carries on across frames, a
dry queue fades out over a few ms instead of cutting, and it fades back in after 60 ms of sound is ready. Falls back to
the old way if the phone has no AudioWorklet. The log gets "gaps" (times the queue ran dry).
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)

WORKLET = r'''class GbrStream extends AudioWorkletProcessor {
  constructor() { super(); this.q = []; this.off = 0; this.n = 0; this.on = false; this.last = 0; this.fade = 0; this.k = 0; this.gaps = 0;
    this.port.onmessage = (e) => { if (e.data === "reset") { this.q = []; this.n = 0; this.off = 0; this.on = false; return; } this.q.push(e.data); this.n += e.data.length;
      if (this.n > sampleRate * 0.4) { while (this.n > sampleRate * 0.15 && this.q.length > 1) { const b = this.q.shift(); this.n -= b.length - this.off; this.off = 0; } } }; }
  process(inputs, outputs) {
    const out = outputs[0], o = out[0], N = o.length;
    if (!this.on && this.n >= sampleRate * 0.06) { this.on = true; this.fade = 0; }
    for (let i = 0; i < N; i++) {
      if (this.on && this.n > 0) {
        const b = this.q[0]; let v = b[this.off++]; this.n--; if (this.off >= b.length) { this.q.shift(); this.off = 0; }
        if (this.fade < 1) { this.fade = Math.min(1, this.fade + 1 / 256); v = this.last + (v - this.last) * this.fade; }
        o[i] = this.last = v;
      } else {
        if (this.on) { this.on = false; this.gaps++; }
        this.last *= 0.985; o[i] = this.last;
      }
    }
    for (let c = 1; c < out.length; c++) out[c].set(o);
    if (++this.k % 8 === 0) this.port.postMessage({ q: this.n, gaps: this.gaps });
    return true;
  }
}
registerProcessor("gbr-stream", GbrStream);'''

rep('''    pumpAudio() {
      const d = this.d; let r = this.ld("audioRead"); const w = this.ld("audioWrite");
      if (this.ld("resetRequest") !== this.ld("resetAck")) { this.st("audioRead", w); this.st("resetAck", this.ld("resetRequest")); return; }
      const ac = this.audio;
      if (!ac || ac.state !== "running") { if (r !== w) this.aDrop = (this.aDrop || 0) + 1; this.st("audioRead", w); return; }
      while (r !== w) {''',
'''    // v184 (Jordan: "Audio is clicky and poppy"): one continuous stream through an AudioWorklet (gbr-stream): resampling
    // carries on from frame to frame, a dry queue fades out instead of cutting off, and sound fades back in once 60 ms
    // is ready. Until the worklet is loaded (or with no AudioWorklet) the old buffer-per-frame way plays.
    streamFor(ac) {
      if (this.sAc === ac) return this.sNode;
      this.sAc = ac; this.sNode = null; this.sPh = 0; this.sLast = 0; this.sQ = 0;
      try {
        if (!ac.audioWorklet || typeof AudioWorkletNode === "undefined") return null;
        const url = URL.createObjectURL(new Blob([__GBR_WORKLET__], { type: "text/javascript" }));
        ac.audioWorklet.addModule(url).then(() => {
          if (this.sAc !== ac) return;
          const node = new AudioWorkletNode(ac, "gbr-stream", { numberOfInputs: 0, numberOfOutputs: 1, outputChannelCount: [1] });
          node.port.onmessage = (e) => { this.sQ = e.data.q; this.aGaps = e.data.gaps; };
          node.connect(this.out || ac.destination); this.sNode = node;
        }).catch((e) => { (window.__wideLog || (window.__wideLog = [])).push("sound stream: " + e); });
      } catch (e) {}
      return null;
    },
    pumpAudio() {
      const d = this.d; let r = this.ld("audioRead"); const w = this.ld("audioWrite");
      if (this.ld("resetRequest") !== this.ld("resetAck")) { this.st("audioRead", w); this.st("resetAck", this.ld("resetRequest")); try { if (this.sNode) this.sNode.port.postMessage("reset"); } catch (e) {} return; }
      const ac = this.audio;
      if (!ac || ac.state !== "running") { if (r !== w) this.aDrop = (this.aDrop || 0) + 1; this.st("audioRead", w); return; }
      const sn = this.streamFor(ac);
      if (sn) {
        while (r !== w) {
          this.aPlay = (this.aPlay || 0) + 1;
          const p = this.ptr + d.audio + (r & (d.audioSlots - 1)) * d.audioStride, u = this.u32(), n = u[p >> 2], rate = u[(p >> 2) + 1]; r = (r + 1) >>> 0;
          if (n < 1 || n > d.audioSamples || !rate) continue;
          const pcm = this._i16.subarray((p + 12) >> 1, ((p + 12) >> 1) + n);
          if (!(this.aPlay & 63)) { let pk = this.aPeak || 0; for (let i = 0; i < n; i += 8) { const v = pcm[i] < 0 ? -pcm[i] : pcm[i]; if (v > pk) pk = v; } this.aPeak = pk; }
          // Same catch-up as before: 1% faster while more than 0.14 s waits. Resampling runs across frames: position x
          // counts from the previous frame's last sample (0) through this frame's samples (1..n).
          const step = rate / ac.sampleRate * (this.sQ > ac.sampleRate * 0.14 ? 1.01 : 1);
          const out = new Float32Array(Math.ceil((n - this.sPh) / step) + 1); let k = 0, x = this.sPh;
          for (; x < n; x += step) { const j = x | 0, f = x - j, a = j ? pcm[j - 1] : this.sLast, b = pcm[j]; out[k++] = (a + (b - a) * f) / 32768; }
          this.sPh = x - n; this.sLast = pcm[n - 1];
          if (k) { const blk = k === out.length ? out : out.slice(0, k); sn.port.postMessage(blk, [blk.buffer]); this.sQ += k; }
        }
        this.audioT = ac.currentTime + this.sQ / ac.sampleRate;
        this.st("audioRead", r); return;
      }
      while (r !== w) {''')

rep('''  window.GbrHost = WideHost;''', '''  const __GBR_WORKLET__ = %s;
  window.GbrHost = WideHost;''' % repr(WORKLET).replace("\\n", "\\n"))
rep('''", dropped " + (H.aDrop || 0) + ", ahead "''', '''", dropped " + (H.aDrop || 0) + ", gaps " + (H.aGaps || 0) + (H.sNode ? " (stream)" : "") + ", ahead "''')
open(dst, "w", encoding="utf-8").write(s)
print("ok")
