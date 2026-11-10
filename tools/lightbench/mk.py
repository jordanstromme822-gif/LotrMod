# Build a test harness from a Play Room page: the lighting code only, fed with game pictures.
import sys
s = open(sys.argv[1]).read(); L = s.split("\n")
def find(pfx, start=0):
    for i in range(start, len(L)):
        if L[i].startswith(pfx): return i
    raise SystemExit("missing " + pfx)
a = find("  const SCALEFX_PRESET"); b = find("  const LIGHT_LOOKS"); 
e_en = next(i for i in range(a + 2, len(L)) if L[i].rstrip().endswith("`;"))
c = find("  // Which look to use", b)
g = find("  const LIGHT_GLOW"); m = find("  function makeSharpHD", g)
end = find("  // Page side of the wide-view engine", m)
js = "\n".join(L[a:e_en + 1] + L[b:c] + L[g:end])
js += "\nwindow.makeSharpHD = makeSharpHD; window.LIGHT_LOOKS = LIGHT_LOOKS;\n"
open(sys.argv[2], "w").write("<!doctype html><html><body style='margin:0;background:#000'><canvas id=c></canvas><script>window.WideHost={front:0};\n" + js + "\n</script><script src=drive.js></script></body></html>")
print("ok", len(js))
