"""Z-buffered source-CAD solid figure; fixes Matplotlib 3D translucent-occlusion artifact.
This view is strictly rendering-only: no coordinates, bodies or physics modified.
"""
from pathlib import Path
import sys,subprocess,struct,hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).parent))
from solid_tec_render import face_geometry
SRC=Path(__file__).resolve().parents[2]/'data/synthetic_v3_assembly_20261102/source_final/design.json'
HERE=Path(__file__).resolve().parent
OUT=HERE/'figures'
BIN='/tmp/tec_zbuffer_raster_20261108'
W,H=1250,1100
faces,colors,counts=face_geometry()
print('Triangles:',2*len(faces),'bodies:',counts,flush=True)
def vnorm(a):return a/np.linalg.norm(a)
def project(azimuth,elevation):
    # Fixed orthographic views; true source model dimensions preserved.
    a=np.deg2rad(azimuth);e=np.deg2rad(elevation)
    view=vnorm(np.array([np.cos(a)*np.cos(e),np.sin(a)*np.cos(e),np.sin(e)]))
    right=vnorm(np.cross(view,[0.,0.,1.]))
    up=vnorm(np.cross(right,view))
    allp=np.concatenate(faces).reshape(-1,3)
    center=np.array([0.,0.,3.74])
    u=(allp-center)@right
    v=(allp-center)@up
    lo_u,hi_u=np.min(u),np.max(u)
    lo_v,hi_v=np.min(v),np.max(v)
    margin=.115
    scale=min((W*(1-2*margin))/(hi_u-lo_u),(H*(1-2*margin))/(hi_v-lo_v))
    center_u=(hi_u+lo_u)/2
    center_v=(hi_v+lo_v)/2
    recs=[]
    for poly,col in zip(faces,colors):
        p=np.asarray(poly)
        xyz=np.column_stack([W/2+(((p-center)@right)-center_u)*scale,
                             H/2-(((p-center)@up)-center_v)*scale,
                             ((p-center)@view).astype(float)])
        # Triangulate quad or general (mostly quads).
        for idx in range(1,len(xyz)-1):
            tri=np.vstack([xyz[0],xyz[idx],xyz[idx+1]]).astype('<f4')
            # C++ reads [x,y,depth] *3, then 3 RGB bytes.
            c=(np.clip(np.array(col),0,1)*255+.5).astype(np.uint8)
            recs.append((tri,c))
    return recs
def render(az,e,name):
    records=project(az,e)
    path=HERE/f'_raster_{name}.bin'
    with path.open('wb') as f:
        f.write(struct.pack('<I',len(records)))
        for points,color in records:
            f.write(points.tobytes())
            f.write(color.tobytes())
    result=HERE/f'_raster_{name}.ppm'
    subprocess.run([BIN,str(path),str(result),str(W),str(H)],check=True)
    im=Image.open(result).convert('RGB')
    im=im.resize((890,784),Image.Resampling.LANCZOS)
    path.unlink(missing_ok=True)
    result.unlink(missing_ok=True)
    return im
a=render(115,28,'positive_y')
b=render(-60,28,'negative_y')
# Clean figure plate with no misleading perspective overlays.
base=Image.new('RGB',(1880,1120),(250,251,252))
draw=ImageDraw.Draw(base)
def font(sz,bold=False):
    candidates=('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    return ImageFont.truetype(candidates[0 if bold else 1],sz)
draw.text((50,32),'REPLACEMENT TEC  |  SOLID CAD INSPECTION',fill='#203752',font=font(38,True))
draw.text((51,92),'Fixed orthographic cameras   •   exact source body coordinates   •   pixel-correct hidden-surface removal',
          fill='#536679',font=font(20))
base.paste(a,(38,148));base.paste(b,(955,148))
draw.text((54,948),'VIEW A   Positive-Y face',fill='#233e56',font=font(23,True))
draw.text((967,948),'VIEW B   Opposite face',fill='#233e56',font=font(23,True))
legend=[('Ceramic plates','#dbe5e9'),('P legs','#d97376'),('N legs','#467eaa'),
        ('Metal contacts','#c49a58'),('Formed copper','#e86b25'),('HgCdTe die','#684a70')]
for i,(label,color) in enumerate(legend):
    xx=48+i*305
    draw.rounded_rectangle((xx,997,xx+28,1025),5,fill=color,outline='#999999',width=1)
    draw.text((xx+40,999),label,fill='#3e5268',font=font(17))
draw.text((48,1068),
          'Verified source: 824-body V3 R1 CAD  |  Outer case, bond wires and sub-micron film layers hidden for inspection.',
          fill='#586b7f',font=font(17))
path=OUT/'tec_solid_inspection.png'
base.save(path,optimize=True)
print('Saved',path,path.stat().st_size,'bytes',flush=True)
manifest_path=OUT/'tec_render_source.json'
m=json.loads(manifest_path.read_text())
m.update({'renderer':'Per-pixel software Z-buffer rasterizer (no painter polygon sorting)',
          'camera_type':'two fixed orthographic 28-degree elevation cameras, 115 and -60 degrees azimuth',
          'render_code':'reports/current/zbuffer_raster.cpp and reports/current/solid_tec_zbuffer.py',
          'new_image_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
manifest_path.write_text(json.dumps(m,indent=2)+'\n')
