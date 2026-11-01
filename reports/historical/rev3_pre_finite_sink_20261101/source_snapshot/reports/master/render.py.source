"""Pixel checks and two-page review spreads, separate from scientific figures."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw

def inspect(out):
    render=out/'renders';files=sorted(render.glob('page-*.png'));stats=[]
    for path in files:
        a=np.asarray(Image.open(path).convert('RGB'));ink=np.min(a,axis=2)<235
        border=np.r_[ink[:4].ravel(),ink[-4:].ravel(),ink[:,:4].ravel(),ink[:,-4:].ravel()]
        if ink.mean()<.005 or border.any():raise ValueError('Blank or edge-clipped page: '+path.name)
        stats.append({'page':path.name,'ink_fraction':float(ink.mean()),'edge_ink':bool(border.any())})
    if not stats:raise ValueError('No rendered pages')
    for old in render.glob('spread-*.png'):old.unlink()
    for i in range(0,len(files),2):
        sheet=Image.new('RGB',(1840,1330),'#dddddd');draw=ImageDraw.Draw(sheet)
        for j,p in enumerate(files[i:i+2]):
            im=ImageOps.contain(Image.open(p).convert('RGB'),(910,1290))
            sheet.paste(im,(j*920+5,5));draw.text((j*920+15,1310),p.stem,fill='black')
        sheet.save(render/f'spread-{i//2+1:02d}.png')
    (out/'render_pixel_checks.json').write_text(json.dumps(stats,indent=2)+'\n')
    return stats

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();inspect(a.out)
