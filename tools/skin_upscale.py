import sys, torch, numpy as np
from PIL import Image
from spandrel import ModelLoader
m = ModelLoader().load_from_file(sys.argv[1]).eval()
for f in sys.argv[2:]:
    im = np.asarray(Image.open(f).convert('RGB')).astype(np.float32) / 255
    t = torch.from_numpy(im).permute(2, 0, 1)[None]
    with torch.no_grad(): o = m(t)[0].clamp(0, 1).permute(1, 2, 0).numpy()
    Image.fromarray((o * 255).round().astype(np.uint8)).save(f.replace('.png', '_x4.png'))
    print(f, o.shape)
