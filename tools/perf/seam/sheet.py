import sys,glob
from PIL import Image
d=sys.argv[1]; fs=sorted(glob.glob(d+'/*.png')); fs=[f for f in fs if 'sheet' not in f]
ims=[Image.open(f).resize((422,195)) for f in fs]
cols=3; rows=(len(ims)+cols-1)//cols
S=Image.new('RGB',(422*cols,195*rows))
for i,im in enumerate(ims): S.paste(im,((i%cols)*422,(i//cols)*195))
S.save(d+'/sheet.png')
