"""Selected synthetic full-package geometry; no PDE/material fitting imports.

Coordinates mm. Source construction is stdlib; OCC only in explicit CAD roles.
V1/V2 are immutable inputs, never imported as mutable builders.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib,itertools,json,math,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/synthetic_v3_assembly_20261102'
LAYERS=(('Ti',.000075),('TiW',.000050),('Cu',.013625),('Ni',.001),('Au',.000250))
OUTER=(('Ti',.000075),('TiW',.000050),('Cu',.000625),('Ni',.001),('Au',.000250))
PAD=.50;TRACK=.30;TW=.30;TT=.030;R=.075;J=.020
OFFSET=1.5+.002+.00025+.080+sum(t for _,t in OUTER)
EPS=1e-9

def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,s):return [x*s for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return mul(a,1/norm(a))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def area(rects):
    xs=sorted(set(v for q in rects for v in (q[0],q[0]+q[2])));total=0.
    for lo,hi in zip(xs,xs[1:]):
        intervals=sorted((q[1],q[1]+q[3]) for q in rects if q[0]<(lo+hi)/2<q[0]+q[2])
        end=-math.inf;length=0.
        for a,b in intervals:length+=max(0,b-max(a,end));end=max(end,b)
        total+=(hi-lo)*length
    return total

def fillet(points,r):
    """Exact orthogonal neutral-path lines/arcs, used by independent source math."""
    points=[list(p) for p in points];parts=[];last=points[0]
    for j,(a,b) in enumerate(zip(points,points[1:])):
        if norm(sub(b,a))<(r if j in (0,len(points)-2) else 2*r)-EPS:raise ValueError('Bend consumes straight segment')
    for a,v,b in zip(points,points[1:],points[2:]):
        u,w=unit(sub(v,a)),unit(sub(b,v))
        if abs(dot(u,w))>1e-10:raise ValueError('Only orthogonal tangent joints')
        p,q=sub(v,mul(u,r)),add(v,mul(w,r));c=add(p,mul(w,r))
        if norm(sub(last,p))>EPS:parts.append(dict(type='line',a=last,b=p,length=norm(sub(p,last))))
        parts.append(dict(type='arc',a=p,b=q,c=c,r=r,length=math.pi*r/2));last=q
    parts.append(dict(type='line',a=last,b=points[-1],length=norm(sub(points[-1],last))))
    return parts

def samples(parts,spacing=.010):
    result=[]
    for p in parts:
        n=max(1,math.ceil(p['length']/spacing))
        if p['type']=='line':
            t=unit(sub(p['b'],p['a']))
            result.extend((add(p['a'],mul(sub(p['b'],p['a']),j/n)),t) for j in range(n+1))
        else:
            a=unit(sub(p['a'],p['c']));b=unit(sub(p['b'],p['c']))
            for j in range(n+1):
                v=math.pi*j/(2*n);rad=add(mul(a,math.cos(v)),mul(b,math.sin(v)))
                tangent=add(mul(a,-math.sin(v)),mul(b,math.cos(v)))
                result.append((add(p['c'],mul(rad,p['r'])),tangent))
    return result

def body_bbox(b):
    if b['shape']=='boxes':
        return [min(q[i] for q in b['boxes_mm']) for i in range(3)]+[max(q[i]+q[i+3] for q in b['boxes_mm']) for i in range(3)]
    if b['shape']=='tab':
        p=b['points'];return [b['x']-b['width']/2,min(v[0] for v in p),min(v[1] for v in p)-b['thickness']/2,b['x']+b['width']/2,max(v[0] for v in p),max(v[1] for v in p)+b['thickness']/2]
    if b['shape']=='wire':
        ss=samples(b['parts'],.002);r=b['radius'];return [min(p[i]-r*math.sqrt(max(0,1-t[i]**2)) for p,t in ss) for i in range(3)]+[max(p[i]+r*math.sqrt(max(0,1-t[i]**2)) for p,t in ss) for i in range(3)]
    if b['shape'] in ('cylinder','annulus'):
        x,y,z=b['base'];r=b['radius'];return[x-r,y-r,z,x+r,y+r,z+b['height']]
    return b['bbox_mm']

def design():
    old=read(ROOT/'data/tec_candidate_29114_v2_20261102/source_final/design.json')
    native=read(ROOT/'fem/results/geometry_complete_checkpoint_20261030/manifest.json')
    bodies=[];rects=defaultdict(list);contacts=[];feet=[]
    def put(name,kind,shape,group=None,**kw):
        b=dict(name=name,material=kind,shape=shape,group=group,**kw);bodies.append(b);return b
    def box(name,kind,q,group=None,**kw):return put(name,kind,'boxes',group,boxes_mm=[q],**kw)
    def rect(net,z,x,y,w,h):rects[(net,round(z,12))].append([x,y,w,h])
    def trace(net,z,points):
        for a,b in zip(points,points[1:]):
            if abs(a[0]-b[0])>EPS and abs(a[1]-b[1])>EPS:raise ValueError('Planar axis trace')
            rect(net,z,min(a[0],b[0])-TRACK/2,min(a[1],b[1])-TRACK/2,abs(a[0]-b[0])+TRACK,abs(a[1]-b[1])+TRACK)
    for b in old['bodies']:
        if b['kind'] in ('Al2O3','P','N','SnSb'):
            q=b['boxes_mm'][0][:];q[2]+=OFFSET
            box(b['name'],b['kind'],q,('LEG'+str(b['chain_index'])) if b['kind'] in ('P','N') else b.get('node'),
                **{k:v for k,v in b.items() if k not in ('name','kind','boxes_mm','volume_mm3','node')})
    for l in old['legs']:
        x,y=l['center_mm'];z=(.5,1.6,2.7)[l['stage']]
        for face,node,plane in [('hot',l['hot_node'],z),('cold',l['cold_node'],z+.6)]:
            rect(node,plane,x-PAD/2,y-PAD/2,PAD,PAD)
            contacts.append(dict(a=f'leg{l["index"]}_{l["polarity"]}',b=f'solder{l["index"]}_{face}',point=[x,y,OFFSET+z+(.05 if face=='hot' else .55)],area=.16,scope='PN_axial'))
    # Ordinary same-plane net pairs; pattern envelopes enlarged without moving legs.
    for (node,z),rr in list(rects.items()):
        if len(rr)==2:
            a,b=rr;rect(node,z,min(a[0],b[0]),min(a[1],b[1]),abs(a[0]-b[0])+PAD,abs(a[1]-b[1])+PAD)
    trace(0,.5,[[-2.03,-2.03],[-2.03,-2.80]]);rect(0,.5,-2.28,-3.05,.5,.5)
    trace(58,.5,[[1.45,2.03],[1.45,2.925]])
    trace(58,1.6,[[1.45,2.30],[1.45,.87]])
    trace(80,1.6,[[.29,-.87],[.29,-2.225]])
    trace(80,2.7,[[.29,-1.59],[.29,-1.30],[.87,-1.30],[.87,-.29]])
    trace(88,2.7,[[.87,.29],[.87,1.59]])
    trace(88,.5,[[.87,2.925],[.87,2.85],[-.50,2.85]])
    rect(88,.5,-.75,2.60,.50,.50)
    def foot(net,x,y,z,number):
        rect(net,z,x-.20,y-.15,.40,.30)
        feet.append(dict(net=net,x=x,y=y,z=z,number=number))
    for args in [(58,1.45,2.925,.5,0),(58,1.45,2.30,1.6,1),(80,.29,-2.225,1.6,2),(80,.29,-1.59,2.7,3),
                 (88,.87,2.925,.5,4),(88,.87,2.30,1.6,5),(88,.87,1.59,2.7,6)]:foot(*args)
    layer_names={}
    for (net,z),rr in sorted(rects.items()):
        direction=-1 if any(abs(z-v)<EPS for v in (1.1,2.2,3.3)) else 1
        accumulated=0
        for j,(mat,t) in enumerate(LAYERS):
            lo=OFFSET+z+(accumulated if direction>0 else -accumulated-t)
            name=f'net{net}_plane{z:.3f}_{mat}';qs=[[x,y,lo,w,h,t] for x,y,w,h in rr]
            put(name,mat,'boxes',net,boxes_mm=qs,plane=z,net=net,layer=j,source_rectangles=rr)
            layer_names[(net,z,mat)]=name;accumulated+=t
        for l in old['legs']:
            zz=(.5,1.6,2.7)[l['stage']];face='hot' if abs(z-zz)<EPS else 'cold' if abs(z-zz-.6)<EPS else None
            if face and l[face+'_node']==net:
                x,y=l['center_mm'];contacts.append(dict(a=f'solder{l["index"]}_{face}',b=layer_names[(net,z,'Au')],point=[x,y,OFFSET+z+(.015 if direction>0 else -.015)],area=.16,scope='PN_metal'))
    lo=lambda z:OFFSET+z+.015+J+TT/2
    tabs=[(58,1.45,[[3.075,lo(.5)],[2.70,lo(.5)],[2.70,lo(1.6)],[2.15,lo(1.6)]]),
          (80,.29,[[-2.375,lo(1.6)],[-2.0,lo(1.6)],[-2.0,lo(2.7)],[-1.44,lo(2.7)]]),
          (88,.87,[[3.075,lo(.5)],[2.70,lo(.5)],[2.70,lo(1.6)],[2.0,lo(1.6)],[2.0,lo(2.7)],[1.44,lo(2.7)]])]
    for net,x,pts in tabs:
        parts=fillet(pts,R);put('formed_tab'+str(net),'Cu','tab',net,x=x,width=TW,thickness=TT,points=pts,parts=parts)
    for f in feet:
        n,x,y,z,i=(f[k] for k in ('net','x','y','z','number'));bottom=OFFSET+z+.015
        q=[x-TW/2,y-.10,bottom,TW,.20,J]
        name='tab_joint'+str(i);box(name,'SnBi57_43',q,n)
        contacts.extend([dict(a=name,b=layer_names[(n,z,'Au')],point=[x,y,bottom],area=TW*.20,scope='tab_land'),
                         dict(a=name,b='formed_tab'+str(n),point=[x,y,bottom+J],area=TW*.20,scope='tab_foot')])
        # Real triangular side fillets: wet the foil side10um above its bottom.
        for side in (-1,1):
            put(f'fillet{i}_{side}','SnBi57_43','wedge',n,x=x+side*TW/2,y=y-.10,z=bottom,width=.010,height=J+.010,length=.20,side=side,
                bbox_mm=[x-TW/2-.010 if side<0 else x+TW/2,y-.10,bottom,x-TW/2 if side<0 else x+TW/2+.010,y+.10,bottom+J+.010])
    # Case/header: exact prior source contour and C pins, no original TEC solids.
    dims=native['registry']['dimensions'];r=lambda k:dims[k]['simulated']
    R0,ear,d=r('central_radius'),r('ear_radius'),r('hole_pitch')/2;aa=(R0-ear)/d;bb=math.sqrt(1-aa*aa)
    theta=math.acos(aa);outline=2*R0*R0*(math.pi/2-theta)+2*ear*ear*theta+2*d*bb*(R0+ear)
    hv=(outline-2*math.pi*(r('hole_diameter')/2)**2-9*math.pi*(r('glass_od')/2)**2)*r('header_thickness')
    put('VIGO_reference_header','Kovar','header','CASE',registry=native['registry'],volume_mm3=hv,bbox_mm=[-15.75,-8.75,0,15.75,8.75,1.5])
    for row in native['bodies']:
        if row['kind']!='pin':continue
        n=row['pin_number'];x,y=[v*1000 for v in row['center_xy_m']];group='PIN'+str(n)
        put('pin'+str(n),'Kovar_pin','cylinder',group,base=[x,y,-12.7],radius=.38,height=14.7,pin=n)
        put('glass'+str(n),'Glass','annulus',None,base=[x,y,0],radius=.65,inner_radius=.38,height=1.5)
        if n in (1,7,8,9):
            put('pin'+str(n)+'_Ni','Ni','cylinder',group,base=[x,y,2.0],radius=.38,height=.002)
            put('pin'+str(n)+'_Au','Au','cylinder',group,base=[x,y,2.002],radius=.38,height=.0015)
    # Both finishes and finite hot-side mount; oxide/metal layers explicit.
    z=1.5
    for mat,t in [('Ni',.002),('Au',.00025)]:box('header_finish_'+mat,mat,[-3.05,-3.05,z,6.1,6.1,t],'CASE');z+=t
    box('hot_mount_In52Sn48','In52Sn48',[-3,-3,z,6,6,.080],'CASE');z+=.080
    for mat,t in reversed(OUTER):box('underside_'+mat,mat,[-3.05,-3.05,z,6.1,6.1,t],'CASE');z+=t
    if abs(z-OFFSET)>1e-10:raise ValueError('Mount datum')
    z=OFFSET+3.8
    for mat,t in OUTER:box('cold_finish_'+mat,mat,[-1.05,-1.05,z,2.1,2.1,t],'COLD_FINISH');z+=t
    box('carrier_attach_EP29LPSP','EP29LPSP',[-.8,-.8,z,1.6,1.6,.020]);z+=.020
    box('sapphire_carrier','Sapphire',[-.8,-.8,z,1.6,1.6,.150]);z+=.150
    box('die_attach_EP29LPSP','EP29LPSP',[-.5,-.5,z,1,1,.020]);z+=.020
    box('p_HgCdTe_photoconductor','pHgCdTe_PC',[-.5,-.5,z,1,1,.200],'MCT');z+=.200
    detector_top=z
    for pin,x in ((7,.35),(8,-.35)):
        zz=z
        for mat,t in [('Au_ohmic',.0004),('Ni',.00075),('Au',.0015)]:
            box(f'det{pin}_{mat}',mat,[x-.1,-.25,zz,.2,.5,t],'DET'+str(pin));zz+=t
        box('det'+str(pin)+'_wedge_foot','Au',[x-.030,-.0175,zz,.060,.035,.006],'DET'+str(pin))
    # True leads and bond wires: continuous filleted circular sweeps, not graph links.
    def wire(name,group,start,end,height,radius,bend):
        points=[start,[start[0],start[1],height],[end[0],end[1],height],end]
        parts=fillet(points,bend);return put(name,'Cu' if radius>.05 else 'Au','wire',group,points=points,parts=parts,radius=radius)
    for n,node,x,y in ((1,0,-2.03,-2.80),(9,88,-.50,2.85)):
        pin=next(b for b in bodies if b['name']=='pin'+str(n));px,py,_=pin['base'];bottom=OFFSET+.515
        put('lead'+str(n)+'_land_joint','SnBi57_43','cylinder',node,base=[x,y,bottom],radius=.16,height=.020)
        put('lead'+str(n)+'_pin_joint','In52Sn48','cylinder','PIN'+str(n),base=[px,py,2.0035],radius=.20,height=.020)
        w=wire('TEC_lead'+str(n),node,[x,y,bottom+.020],[px,py,2.0235],2.72,.100,.25)
        contacts.extend([dict(a=w['name'],b='lead'+str(n)+'_land_joint',point=w['points'][0],area=math.pi*.1**2,scope='TEC_wire_land'),
                         dict(a=w['name'],b='lead'+str(n)+'_pin_joint',point=w['points'][-1],area=math.pi*.1**2,scope='TEC_wire_pin'),
                         dict(a='lead'+str(n)+'_land_joint',b=layer_names[(node,.5,'Au')],point=[x,y,bottom],area=math.pi*.16**2,scope='TEC_land_joint'),
                         dict(a='lead'+str(n)+'_pin_joint',b='pin'+str(n)+'_Au',point=[px,py,2.0035],area=math.pi*.20**2,scope='TEC_pin_joint')])
    for pin,x in ((7,.35),(8,-.35)):
        p=next(b for b in bodies if b['name']=='pin'+str(pin));px,py,_=p['base']
        box('pin'+str(pin)+'_wedge_foot','Au',[px-.030,py-.0175,2.0035,.060,.035,.006],'PIN'+str(pin))
        start=[x,0,detector_top+.00265+.006];end=[px,py,2.0095]
        w=wire('detector_bond'+str(pin),'DET'+str(pin),start,end,6.15,.009,.15)
        contacts.extend([dict(a=w['name'],b='det'+str(pin)+'_wedge_foot',point=start,area=math.pi*.009**2,scope='detector_wire_die'),
                         dict(a=w['name'],b='pin'+str(pin)+'_wedge_foot',point=end,area=math.pi*.009**2,scope='detector_wire_pin')])
    for n in (1,9):
        w=next(v for v in bodies if v['name']=='TEC_lead'+str(n));pts=[v[:] for v in w['points']]
        pts[0][2]+=.20;pts[-1][2]+=.20
        put('lead'+str(n)+'_insulation','Polyimide_candidate','wire',None,points=pts,parts=fillet(pts,.25),radius=.115,inner_radius=.100,
            scope='Selected15um coating;0.20mm stripped ends;capability/outgassing pending')
    put('cap_shell','Steel','annulus','CASE',base=[0,0,1.5],radius=7.6,inner_radius=7.1,height=8.15)
    put('cap_roof','Steel','annulus','CASE',base=[0,0,9.65],radius=7.6,inner_radius=2.95,height=.45)
    put('window','ZnSe_candidate','cylinder',None,base=[0,0,9.65],radius=2.95,height=.45)
    for i,b in enumerate(bodies):
        b['id']=i;b['bbox_mm']=body_bbox(b)
        if b['shape']=='boxes':
            qs=b['boxes_mm'];b['volume_mm3']=area([[q[0],q[1],q[3],q[4]] for q in qs])*qs[0][5]
        elif b['shape']=='tab':b['volume_mm3']=b['width']*b['thickness']*sum(p['length'] for p in b['parts'])
        elif b['shape']=='wire':b['volume_mm3']=math.pi*(b['radius']**2-b.get('inner_radius',0)**2)*sum(p['length'] for p in b['parts'])
        elif b['shape'] in ('cylinder','annulus'):b['volume_mm3']=math.pi*(b['radius']**2-b.get('inner_radius',0)**2)*b['height']
        elif b['shape']=='wedge':b['volume_mm3']=b['width']*b['height']*b['length']/2
    return dict(id='synthetic_architecture_B_v3',unit='mm',body_count=len(bodies),bodies=bodies,legs=old['legs'],feet=feet,
        explicit_contacts=contacts,core_offset_mm=OFFSET,layer_stack=LAYERS,outer_stack=OUTER,
        detector='p-type HgCdTe two-top-contact photoconductor;not a photovoltaic diode',thermistor='VACANT pins5/6',
        process_scope='Selected synthetic drawing requirements;capability,1A,transport,contact impedance andvacuum qualification pending')


def source(out):
    if out.exists():raise ValueError('New output only')
    out.mkdir(parents=True);d=design();write(out/'design.json',d)
    write(out/'producer.json',dict(source_sha256=sha(__file__),V2_sha256=sha(ROOT/'data/tec_candidate_29114_v2_20261102/source_final/design.json')))
    (out/'producer.py.source').write_bytes(Path(__file__).read_bytes())
    print('Source bodies',len(d['bodies']))

def _path_curves(occ,parts,lift=lambda p:p):
    curves=[]
    for p in parts:
        a=occ.addPoint(*lift(p['a']));b=occ.addPoint(*lift(p['b']))
        curves.append(occ.addLine(a,b) if p['type']=='line' else occ.addCircleArc(a,occ.addPoint(*lift(p['c'])),b))
    return curves

def make_tab(occ,b):
    """Analytic constant-width strip between exact offset curves; no mesh."""
    boundaries=[];parts=b['parts'];x=b['x']-b['width']/2
    for off in (b['thickness']/2,-b['thickness']/2):
        pp=[]
        for p in parts:
            if p['type']=='line':
                u=unit(sub(p['b'],p['a']));n=[-u[1],u[0]]
                pp.append(dict(type='line',a=add(p['a'],mul(n,off)),b=add(p['b'],mul(n,off))))
            else:
                aa=sub(p['a'],p['c']);bb=sub(p['b'],p['c']);sign=1 if aa[0]*bb[1]-aa[1]*bb[0]>0 else -1
                radius=p['r']-sign*off
                pp.append(dict(type='arc',a=add(p['c'],mul(unit(aa),radius)),b=add(p['c'],mul(unit(bb),radius)),c=p['c']))
        boundaries.append(pp)
    left,right=boundaries
    path=left+[dict(type='line',a=left[-1]['b'],b=right[-1]['b'])]
    path +=[dict(p,a=p['b'],b=p['a']) for p in reversed(right)]
    path +=[dict(type='line',a=right[0]['a'],b=left[0]['a'])]
    curves=_path_curves(occ,path,lambda p:[x,*p]);face=occ.addPlaneSurface([occ.addWire(curves,checkClosed=True)])
    out=[q for q in occ.extrude([(2,face)],b['width'],0,0) if q[0]==3]
    occ.remove([(2,face)],recursive=True)
    if len(out)!=1:raise ValueError('Tab extrusion split')
    return out[0][1]

def make_wire(occ,b):
    """Exact cylinders + oriented torus quarters, no generic-sweep distortion."""
    def rod(radius):
        objects=[]
        for p in b['parts']:
            if p['type']=='line':
                objects.append((3,occ.addCylinder(*p['a'],*sub(p['b'],p['a']),radius)))
                continue
            aa=unit(sub(p['a'],p['c']));bb=unit(sub(p['b'],p['c']));nn=unit(cross(aa,bb))
            t=occ.addTorus(0,0,0,p['r'],radius,angle=math.pi/2)
            axis=cross([0,0,1],nn);ss=norm(axis);cc=nn[2];xx=[1.,0.,0.]
            if ss>1e-12:
                ax=unit(axis);angle=math.atan2(ss,cc);occ.rotate([(3,t)],0,0,0,*ax,angle)
                xx=add(add(mul(xx,math.cos(angle)),mul(cross(ax,xx),math.sin(angle))),mul(ax,dot(ax,xx)*(1-math.cos(angle))))
            elif cc<0:occ.rotate([(3,t)],0,0,0,1,0,0,math.pi)
            angle=math.atan2(dot(nn,cross(xx,aa)),dot(xx,aa))
            if abs(angle)>1e-12:occ.rotate([(3,t)],0,0,0,*nn,angle)
            occ.translate([(3,t)],*p['c']);objects.append((3,t))
        result=occ.fuse(objects[:1],objects[1:])[0]
        if len(result)!=1:raise ValueError('Disconnected exact tube')
        return result
    result=rod(b['radius'])
    if b.get('inner_radius'):result=occ.cut(result,rod(b['inner_radius']))[0]
    if len(result)!=1:raise ValueError('Tube partition')
    return result[0][1]

def make_header(occ,b):
    r=b['registry']['dimensions'];v=lambda k:r[k]['simulated'];R0,rr=v('central_radius'),v('ear_radius');d=v('hole_pitch')/2
    a=(R0-rr)/d;bb=math.sqrt(1-a*a)
    xy=[(d+a*rr,-bb*rr),(d+a*rr,bb*rr),(a*R0,bb*R0),(-a*R0,bb*R0),(-d-a*rr,bb*rr),(-d-a*rr,-bb*rr),(-a*R0,-bb*R0),(a*R0,-bb*R0)]
    p=[occ.addPoint(x,y,0) for x,y in xy];c=[occ.addPoint(x,0,0) for x in (d,0,-d)]
    e=[occ.addCircleArc(p[0],c[0],p[1]),occ.addLine(p[1],p[2]),occ.addCircleArc(p[2],c[1],p[3]),occ.addLine(p[3],p[4]),occ.addCircleArc(p[4],c[2],p[5]),occ.addLine(p[5],p[6]),occ.addCircleArc(p[6],c[1],p[7]),occ.addLine(p[7],p[0])]
    f=occ.addPlaneSurface([occ.addWire(e,checkClosed=True)]);base=[q for q in occ.extrude([(2,f)],0,0,1.5) if q[0]==3]
    holes=[(3,occ.addCylinder(x,0,0,0,0,1.5,v('hole_diameter')/2)) for x in (-d,d)]
    holes +=[(3,occ.addCylinder(-5.4*math.cos(-n*math.pi/5),5.4*math.sin(-n*math.pi/5),0,0,0,1.5,.65)) for n in range(1,10)]
    result=occ.cut(base,holes)[0];occ.remove([(2,f)],recursive=True)
    if len(result)!=1:raise ValueError('Header split')
    return result[0][1]

def make_body(occ,b):
    if b['shape']=='boxes':
        tags=[(3,occ.addBox(*q)) for q in b['boxes_mm']]
        if len(tags)>1:tags=occ.fuse(tags[:1],tags[1:])[0]
        if len(tags)!=1:raise ValueError('Disconnected film pattern '+b['name'])
        return tags[0][1]
    if b['shape']=='tab':return make_tab(occ,b)
    if b['shape']=='wire':return make_wire(occ,b)
    if b['shape']=='header':return make_header(occ,b)
    if b['shape'] in ('cylinder','annulus'):
        t=occ.addCylinder(*b['base'],0,0,b['height'],b['radius'])
        if b.get('inner_radius'):
            hole=occ.addCylinder(*b['base'],0,0,b['height'],b['inner_radius']);return occ.cut([(3,t)],[(3,hole)])[0][0][1]
        return t
    if b['shape']=='wedge':
        x,y,z=b['x'],b['y'],b['z'];p=[occ.addPoint(*v) for v in ([x,y,z],[x+b['side']*b['width'],y,z],[x,y,z+b['height']])]
        f=occ.addPlaneSurface([occ.addWire([occ.addLine(p[0],p[1]),occ.addLine(p[1],p[2]),occ.addLine(p[2],p[0])],checkClosed=True)])
        t=[q for q in occ.extrude([(2,f)],0,b['length'],0) if q[0]==3][0][1];occ.remove([(2,f)],recursive=True);return t
    raise ValueError('Unregistered shape')

def support_planes(occ,scale=1.):
    faces=[]
    for axis in range(3):
        for sign in (-1,1):
            f=occ.addRectangle(-50*scale,-50*scale,0,100*scale,100*scale)
            if axis==0:occ.rotate([(2,f)],0,0,0,0,1,0,math.pi/2)
            if axis==1:occ.rotate([(2,f)],0,0,0,1,0,0,math.pi/2)
            v=[0.,0.,0.];v[axis]=sign*50*scale;occ.translate([(2,f)],*v);faces.append((axis,sign,f))
    return faces

def tight_bounds(occ,tag,planes,scale=1.):
    """BRep extrema to six supporting planes; no STL or FEM mesh generated."""
    lo=[0.]*3;hi=[0.]*3
    for axis,sign,f in planes:
        distance=occ.getDistance(3,tag,2,f)[0]
        if sign<0:lo[axis]=-50*scale+distance
        else:hi[axis]=50*scale-distance
    return lo+hi

def writer(out,src):
    import gmsh
    if out.exists():raise ValueError('Fresh CAD output required')
    out.mkdir(parents=True);start=time.monotonic();d=read(src/'design.json');records=[]
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    try:
        occ=gmsh.model.occ;gmsh.model.add('unit_control');occ.addBox(20,20,20,1,1,1);occ.synchronize();gmsh.write(str(out/'one_mm_cube.step'));gmsh.clear();gmsh.model.add('synthetic_V3')
        planes=support_planes(occ)
        for b in d['bodies']:
            t=make_body(occ,b);v=occ.getMass(3,t);relative=abs(v/b['volume_mm3']-1)
            if relative>1e-7:raise ValueError('Author volume '+b['name']+' '+str(relative))
            bbox=tight_bounds(occ,t,planes) if b['shape']=='wire' else list(occ.getBoundingBox(3,t))
            if max(abs(a-bb) for a,bb in zip(bbox,b['bbox_mm']))>.00021:raise ValueError('Author bbox '+b['name'])
            records.append(dict(name=b['name'],id=b['id'],tag=t,volume_m3=v*1e-9,bbox_m=[x*.001 for x in bbox]))
        occ.remove([(2,f) for _,_,f in planes],recursive=True);occ.synchronize()
        for r in records:gmsh.model.setEntityName(3,r['tag'],r['name'])
        gmsh.write(str(out/'synthetic_v3_mm.step'))
        result=dict(status='PASS mm author only; SI reader required',body_count=len(records),records=records,
            STEP_sha256=sha(out/'synthetic_v3_mm.step'),source_design_sha256=sha(src/'design.json'),source_sha256=sha(__file__),seconds=time.monotonic()-start,CAD_imports=0)
        write(out/'writer.json',result)
    except Exception as e:
        write(out/'failure.json',dict(error=repr(e),completed_bodies=len(records),last_records=records[-2:],source_sha256=sha(__file__),seconds=time.monotonic()-start));raise
    finally:gmsh.finalize();(out/'producer.py.source').write_bytes(Path(__file__).read_bytes())
    print('Full V3 author PASS',len(records))

def reader(out,src):
    import gmsh
    if (out/'si_reader.json').exists():raise ValueError('Reader output exists')
    start=time.monotonic();d=read(src/'design.json');w=read(out/'writer.json');gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','M');gmsh.option.setNumber('General.NumThreads',4)
    try:
        occ=gmsh.model.occ;cube=occ.importShapes(str(out/'one_mm_cube.step'));occ.synchronize()
        if len(cube)!=1 or abs(occ.getMass(*cube[0])/1e-9-1)>1e-7:raise ValueError('Unit cube')
        gmsh.clear();tags=occ.importShapes(str(out/'synthetic_v3_mm.step'));occ.synchronize()
        available={t for dim,t in tags if dim==3};rows=[];identities={}
        if len(available)!=d['body_count']:raise ValueError('SI body count')
        imported={t:dict(volume=occ.getMass(3,t),bbox=list(occ.getBoundingBox(3,t))) for t in available};planes=support_planes(occ,.001)
        for b in d['bodies']:
            expect=b['volume_mm3']*1e-9;box=[v*.001 for v in b['bbox_mm']]
            candidates=[t for t in available if abs(imported[t]['volume']/expect-1)<=1e-7 and max(abs(a-bb) for a,bb in zip(imported[t]['bbox'],box))<2e-4]
            if b['shape']=='wire':
                for t in candidates:imported[t]['bbox']=tight_bounds(occ,t,planes,.001)
            matches=[t for t in candidates if max(abs(a-bb) for a,bb in zip(imported[t]['bbox'],box))<=2.1e-7]
            if len(matches)!=1:raise ValueError('SI identity '+b['name']+' '+str(matches[:5]))
            t=matches[0];available.remove(t);identities[b['name']]=t
            rows.append(dict(name=b['name'],tag=t,relative_volume_error=abs(imported[t]['volume']/expect-1),bbox_error_m=max(abs(a-bb) for a,bb in zip(imported[t]['bbox'],box))))
        result=dict(status='PASS separate SI import',body_count=len(rows),cube_volume_m3=1e-9,max_relative_volume_error=max(r['relative_volume_error'] for r in rows),max_bbox_error_m=max(r['bbox_error_m'] for r in rows),records=rows,STEP_sha256=sha(out/'synthetic_v3_mm.step'),source_design_sha256=sha(src/'design.json'),source_sha256=sha(__file__),seconds=time.monotonic()-start)
        write(out/'si_reader.json',result)
    except Exception as e:write(out/'reader_failure.json',dict(error=repr(e),source_sha256=sha(__file__),seconds=time.monotonic()-start));raise
    finally:gmsh.finalize()
    print('Full V3 SI PASS',len(rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=('source','writer','reader'));p.add_argument('--out',type=Path,required=True);p.add_argument('--source-dir',type=Path)
    a=p.parse_args();source(a.out) if a.role=='source' else globals()[a.role](a.out,a.source_dir)
