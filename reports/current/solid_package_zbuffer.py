"""Source-based shaded package rendering for Figure 1.
Two fixed orthographic views: cap/window installed, and cap/window hidden.
All geometry is tessellated from frozen 824-body V3 design.json; exterior long
pin tails are visually cropped at header underside z=0. No geometry is edited.
Per-pixel depth test uses the same small C++ renderer as figure 3.
"""
from pathlib import Path
from collections import Counter
from math import pi,cos,sin,atan2,acos,sqrt
import hashlib,json,sys,struct,subprocess
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.path import Path as MplPath
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
from solid_tec_render import D,B,box_polys,foil_polys,visible,shade
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE/'figures'
BIN='/tmp/tec_zbuffer_raster_20261108'
W,H=1120,1120
BY={a['name']:a for a in B}
HEADER=BY['VIGO_reference_header']
BASE_COLOR={
  'Kovar':'#8491a0','Kovar_pin':'#8b8c93','Glass':'#739e9e',
  'Steel':'#9caab7','ZnSe_candidate':'#77b8b9',
  'Au':'#dfb657','Cu':'#c39356','Ni':'#b4bac2',
  'In52Sn48':'#ada49b','SnBi57_43':'#ba9d8b','Polyimide_candidate':'#647da2'
}
def circle_points(cx,cy,r,n=48):
    ts=np.linspace(0,2*pi,n+1)[:-1]
    return np.stack([cx+r*np.cos(ts),cy+r*np.sin(ts)],axis=1)
def arc_points(a,b,c,n):
    aa=np.array(a)-c;bb=np.array(b)-c
    t0=atan2(aa[1],aa[0]);t1=atan2(bb[1],bb[0])
    dt=(t1-t0+pi)%(2*pi)-pi
    th=t0+np.linspace(0,dt,n+1)
    rad=np.linalg.norm(aa)
    return np.column_stack([c[0]+rad*np.cos(th),c[1]+rad*np.sin(th)])
def header_outline():
    reg=HEADER['registry']['dimensions']
    r=lambda k:reg[k]['simulated']
    R0,rr=r('central_radius'),r('ear_radius')
    d=r('hole_pitch')/2
    aa=(R0-rr)/d;bb=sqrt(1-aa*aa)
    p=[(d+aa*rr,-bb*rr),(d+aa*rr,bb*rr),
       (aa*R0,bb*R0),(-aa*R0,bb*R0),
       (-d-aa*rr,bb*rr),(-d-aa*rr,-bb*rr),
       (-aa*R0,-bb*R0),(aa*R0,-bb*R0)]
    curves=[]
    for j in range(8):
        if j in (0,2,4,6):
            center={0:np.array([d,0]),2:np.zeros(2),4:np.array([-d,0]),6:np.zeros(2)}[j]
            seg=arc_points(p[j],p[(j+1)%8],center,16)
        else: seg=np.array([p[j],p[(j+1)%8]])
        curves.extend(seg[:-1])
    return np.array(curves)
def holes():
    registry=HEADER['registry']['dimensions']
    r=lambda k:registry[k]['simulated']
    d=r('hole_pitch')/2
    h=[(-d,0,r('hole_diameter')/2),(d,0,r('hole_diameter')/2)]
    for b in B:
        if b['name'].startswith('glass') and b['name'][5:].isdigit():
            h.append((b['base'][0],b['base'][1],b['radius']))
    assert len(h)==11
    return h
def triangulated_header():
    outer=header_outline()
    holespec=holes()
    # Native source cap/header contour, computational surface sampling only.
    xx,yy=np.meshgrid(np.arange(-15.76,15.77,.34),np.arange(-8.76,8.77,.34))
    grid=np.column_stack([xx.ravel(),yy.ravel()])
    test=MplPath(outer).contains_points(grid,radius=-1e-8)
    for cx,cy,r in holespec:
        test &= (grid[:,0]-cx)**2+(grid[:,1]-cy)**2>(r+.03)**2
    grid=grid[test]
    circles=[circle_points(x,y,r,40) for x,y,r in holespec]
    points=np.vstack([grid,outer,*circles])
    dt=Delaunay(points)
    trip=points[dt.simplices]
    ctr=trip.mean(axis=1)
    ok=MplPath(outer).contains_points(ctr,radius=-1e-8)
    # Mid-edge and vertex tests reject boundary-crossing facets.
    for i in range(3):
        midpoint=(trip[:,i]+trip[:,(i+1)%3])/2
        ok &= MplPath(outer).contains_points(midpoint,radius=1e-7)
        for cx,cy,r in holespec:
            ok &= (ctr[:,0]-cx)**2+(ctr[:,1]-cy)**2 >= (r-.001)**2
            ok &= (midpoint[:,0]-cx)**2+(midpoint[:,1]-cy)**2 >= (r-.001)**2
    trip=trip[ok]
    faces=[]
    for z in (0,1.5):
        faces.extend(np.column_stack([t,np.full(3,z)]) for t in trip)
    # Contour and eleven hole wall surfaces preserve their actual 1.5mm depth.
    for contour in [outer,*circles]:
        for i in range(len(contour)):
            a=contour[i];b=contour[(i+1)%len(contour)]
            faces.append(np.array([[*a,0],[*b,0],[*b,1.5],[*a,1.5]]))
    return faces
def cylinder(body,section=False):
    z0=float(body['base'][2]);z1=z0+float(body['height'])
    if section and body['name'].startswith('pin') and body['material']=='Kovar_pin':
        z0=max(z0,0.) # inspection crop; unchanged original rod saved in CAD.
    c=np.asarray(body['base'][:2],float)
    r=float(body['radius']);rin=float(body.get('inner_radius',0.))
    n=28 if r<1 else 72
    outer=circle_points(*c,r,n)
    o=[]
    for i in range(n):
        j=(i+1)%n
        o.append(np.array([[*outer[i],z0],[*outer[j],z0],[*outer[j],z1],[*outer[i],z1]]))
        if rin>0:
            inner=circle_points(*c,rin,n)
            o.extend([
                np.array([[*inner[i],z0],[*outer[i],z0],[*outer[j],z0],[*inner[j],z0]]),
                np.array([[*inner[i],z1],[*inner[j],z1],[*outer[j],z1],[*outer[i],z1]]),
                np.array([[*inner[i],z0],[*inner[i],z1],[*inner[j],z1],[*inner[j],z0]])
            ])
        else:
            cent0=np.array([*c,z0]);cent1=np.array([*c,z1])
            o.extend([np.array([cent0,[*outer[j],z0],[*outer[i],z0]]),
                      np.array([cent1,[*outer[i],z1],[*outer[j],z1]])])
    return o
def path3d(parts):
    pts=[]
    for p in parts:
        a=np.asarray(p['a'],float);b=np.asarray(p['b'],float)
        if p['type']=='line':
            seq=[a,b]
        else:
            c=np.asarray(p['c'],float)
            v0=a-c;v1=b-c;r=np.linalg.norm(v0)
            q0=v0/r;q1=v1/np.linalg.norm(v1)
            theta=np.arccos(np.clip(np.dot(q0,q1),-1,1))
            if theta<1e-8:seq=[a,b]
            else:
                seq=[c+r*(np.sin((1-t)*theta)*q0+np.sin(t*theta)*q1)/np.sin(theta)
                     for t in np.linspace(0,1,7)]
        if pts:seq=seq[1:]
        pts.extend(seq)
    return np.array(pts)
def wire_polys(body):
    points=path3d(body['parts'])
    r=float(body['radius'])
    sides=10
    out=[]
    t=np.gradient(points,axis=0)
    t=t/(np.linalg.norm(t,axis=1)[:,None])
    rings=[]
    for p,tg in zip(points,t):
        ref=np.array([0,0,1.])
        if abs(np.dot(ref,tg))>.95:ref=np.array([1,0,0.])
        v=np.cross(tg,ref);v=v/np.linalg.norm(v);w=np.cross(tg,v)
        rings.append(np.array([p+r*(v*np.cos(k*2*pi/sides)+w*np.sin(k*2*pi/sides)) for k in range(sides)]))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(sides):
            jj=(j+1)%sides
            out.append(np.array([a[j],a[jj],b[jj],b[j]]))
    return out
def append_faces(faces,colors,polygons,col):
    for p in polygons:
        faces.append(p);colors.append(shade(p,col))
def geometries(with_cap):
    faces=[];colors=[];count=Counter()
    header=triangulated_header()
    append_faces(faces,colors,header,'#a3aebb')
    count['header']=1
    if with_cap:
        names=['cap_shell','cap_roof','window']
        # Show cap and window opaque: the glass source is a separate solid.
    else:
        names=[b['name'] for b in B if visible(b)]+[
            'header_finish_Ni','header_finish_Au','hot_mount_In52Sn48',
            'underside_Au','underside_Ni','underside_Cu',
            'lead1_land_joint','lead9_land_joint','lead1_pin_joint','lead9_pin_joint',
            'TEC_lead1','TEC_lead9','detector_bond7','detector_bond8',
            'det7_Au','det8_Au','pin7_wedge_foot','pin8_wedge_foot',
            'pin1_Au','pin9_Au','pin7_Au','pin8_Au']
    # Actual feedthrough glass seals and full header pin location; exterior tails cropped only for illustration.
    names += [b['name'] for b in B if b['name'].startswith('glass') and b['name'][5:].isdigit()]
    names += [b['name'] for b in B if b['name'].startswith('pin') and b['material']=='Kovar_pin']
    seen=set()
    for name in names:
        if name in seen:continue
        seen.add(name);b=BY.get(name)
        if not b:continue
        if b['shape']=='boxes':
            polys=[face for v in b['boxes_mm'] for face in box_polys(v)]
        elif b['shape']=='tab':polys=foil_polys(b)
        elif b['shape'] in ('cylinder','annulus'):polys=cylinder(b,section=True)
        elif b['shape']=='wire':polys=wire_polys(b)
        else:continue
        col=BASE_COLOR.get(b['material'])
        if not col:
            if b['name'].startswith('formed_tab'):col='#de7b32'
            elif b['material']=='Al2O3':col='#dae2e9'
            elif b['material']=='P':col='#d87a7c'
            elif b['material']=='N':col='#477eac'
            elif b['material']=='pHgCdTe_PC':col='#715077'
            elif b['material']=='Sapphire':col='#72b9bb'
            elif b['material']=='SnSb':col='#bcc2c8'
            else:col='#c7cdd4'
        append_faces(faces,colors,polys,col)
        count[b['material']]+=1
    return faces,colors,count
def raster(faces,colors,az=110,elev=37,name='open',center_zoom=False):
    az=np.deg2rad(az);el=np.deg2rad(elev)
    eye=np.array([np.cos(az)*np.cos(el),np.sin(az)*np.cos(el),np.sin(el)])
    right=np.cross(eye,[0.,0.,1.]);right/=np.linalg.norm(right)
    up=np.cross(right,eye)
    coords=np.concatenate(faces).reshape(-1,3)
    # Inspection zoom changes the viewing frame only; no source geometry moves.
    # The full package silhouette is retained in the cap-fitted left view.
    if center_zoom:
        coords=np.array([[x,y,z] for x in (-7.2,7.2)
                         for y in (-6.7,6.7) for z in (0.0,7.25)])
    center=np.array([0.,0.,4.9])
    u=(coords-center)@right;v=(coords-center)@up
    u0,u1=np.min(u),np.max(u)
    v0,v1=np.min(v),np.max(v)
    # Slight less margin for larger useful package.
    scale=min(W*.87/(u1-u0),H*.85/(v1-v0))
    ub=.5*(u0+u1);vb=.5*(v0+v1)
    records=[]
    for p,c in zip(faces,colors):
        xyz=np.column_stack([W/2+(((p-center)@right)-ub)*scale,
                             H/2-(((p-center)@up)-vb)*scale,
                             ((p-center)@eye).astype(float)])
        for i in range(1,len(xyz)-1):
            triangle=np.array([xyz[0],xyz[i],xyz[i+1]],dtype='<f4')
            rgb=np.array(np.clip(np.array(c)*255+.5,0,255),dtype=np.uint8)
            records.append((triangle,rgb))
    f=HERE/f'_package_{name}.bin';ppm=HERE/f'_package_{name}.ppm'
    with f.open('wb') as z:
        z.write(struct.pack('<I',len(records)))
        for tri,rgb in records:
            z.write(tri.tobytes());z.write(rgb.tobytes())
    subprocess.run([BIN,str(f),str(ppm),str(W),str(H)],check=True)
    im=Image.open(ppm).convert('RGB').resize((920,920),Image.Resampling.LANCZOS)
    f.unlink();ppm.unlink()
    print(name,'faces',len(faces),'triangles',len(records),'bodies',count,flush=True)
    return im
def fnt(s,bold=False):
    base='/usr/share/fonts/truetype/dejavu/DejaVuSans'
    return ImageFont.truetype(base+('-Bold' if bold else '')+'.ttf',s)
if __name__=='__main__':
    closed,cols,count=geometries(True)
    left=raster(closed,cols,name='cap')
    opened,cols,count=geometries(False)
    right=raster(opened,cols,name='opened',center_zoom=False)
    detail=raster(opened,cols,name='detail',center_zoom=True)
    im=Image.new('RGB',(2040,1180),'#fafbfd')
    d=ImageDraw.Draw(im)
    d.text((60,35),'SOURCE CAD   |   PACKAGE & ELECTRICAL INTERCONNECTIONS',font=fnt(38,True),fill='#243c54')
    d.text((60,92),'True shaded surfaces   •   solid header and pin feeds   •   two orthographic views   •   cover removed at right',font=fnt(19),fill='#657588')
    im.paste(left,(55,143)); im.paste(right,(1050,143))
    d.text((65,1067),'CAP AND WINDOW FITTED',font=fnt(24,True),fill='#253b52')
    d.text((1060,1067),'CAP REMOVED  |  FULL HEADER',font=fnt(24,True),fill='#253b52')
    d.text((64,1123),'Source V3 R1 CAD; original header/cooler spatial positions. Only external pin tails are cropped below z=0. TEC pins 1/9; detector pins 7/8.',font=fnt(16),fill='#617084')
    detail_plate=Image.new('RGB',(1120,1230),'#fafbfd')
    detail_plate.paste(detail,(100,125))
    dd=ImageDraw.Draw(detail_plate)
    dd.text((70,35),'INTERIOR ELECTRICAL ROUTING | ENLARGED VIEW',font=fnt(26,True),fill='#243c54')
    dd.text((70,85),'Source V3 R1 geometry, orthographic camera. Outer flange ears cropped by framing.',font=fnt(17),fill='#617084')
    dd.text((70,1080),'TEC power terminals: header pins 1 and 9. Detector bias: pins 7 and 8.',font=fnt(19,True),fill='#2e4865')
    dd.text((70,1124),'Copper-colored loops are actual modeled leads; thin Au detector bonds remain in original positions.',font=fnt(16),fill='#617084')
    detail_plate.save(OUT/'cad_package_interior_detail.png',optimize=True)
    out=OUT/'cad_package_shaded.png'
    im.save(out,optimize=True)
    manifest={'source':'data/synthetic_v3_assembly_20261102/source_final/design.json',
       'source_sha256':hashlib.sha256((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest(),
       'source_body_count':len(B),'exterior_view':'original header geometry and cap/window, lead tails clipped at z=0',
       'interior_view':'same assembly, cap/window omitted; full header contour with original TEC pin 1/9 and detector pin 7/8 loops visible; lead tails clipped at z=0',
       'mesh':'original body analytic geometry tessellated, triangle depth-buffered; not computational solver mesh',
       'no_physics_runs':True,'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
       'render_scripts':['reports/current/solid_package_zbuffer.py','reports/current/zbuffer_raster.cpp'],
       'detail_image':'reports/current/figures/cad_package_interior_detail.png'}
    (OUT/'cad_package_shaded_source.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('READY',out,out.stat().st_size,'bytes')
