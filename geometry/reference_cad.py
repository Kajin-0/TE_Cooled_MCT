"""Compact *illustrative* CAD generator for HgCdTe/3-stage-TEC in detector TO-66.

Requires optional cadquery. The stage counts, gap fillers and contact/circuit
artwork are inferred. Do NOT use this generator as a validated FEM geometry.
"""
from pathlib import Path
import math
import json
import cadquery as cq

OUT = Path(__file__).resolve().parent / "generated"
OUT.mkdir(parents=True, exist_ok=True)
M = {"metal": cq.Color(0.72,0.74,0.77), "glass": cq.Color(0.2,0.45,0.55),
     "gold": cq.Color(0.84,0.66,0.29), "ceramic": cq.Color(0.90,0.91,0.88),
     "p": cq.Color(0.31,0.34,0.43), "n": cq.Color(0.23,0.24,0.28),
     "die": cq.Color(0.07,0.09,0.13)}

def block(x, y, z, px, py, pz):
    return cq.Workplane("XY").box(x,y,z).translate((px,py,pz)).val()

def cyl(r, z0, z1, x=0., y=0.):
    return cq.Solid.makeCylinder(r, z1-z0, cq.Vector(x,y,z0))

def add(assembly, label, solid, kind):
    assembly.add(solid,name=label,color=M[kind])

core=cq.Assembly(name="TO66_Detector_Core_Illustrative")
full=cq.Assembly(name="TO66_Detector_Full_Illustrative")
parts=[]

def place(label, solid, kind):
    add(core,label,solid,kind)
    add(full,label,solid,kind)
    parts.append(label)

# Manufacturer-style detector TO-66; ellipse is an intentional approximation
# of the tapered two-ear flange (not an OEM tooling profile).
header=cq.Workplane("XY").ellipse(15.75,8.75).extrude(1.10).translate((0,0,-0.65))
for x in (-12.2,12.2):
    header=header.cut(cq.Workplane("XY").circle(1.85).extrude(3).translate((x,0,-1)))
# Nine C-shaped feedthroughs, pitch circle 10.8 mm. The orientation is an
# unnumbered mechanical depiction; inspect pin numbering on the OEM drawing.
xy=[]
for i in range(9):
    ang=math.radians(36*(i+1))
    xy.append((5.4*math.cos(ang),5.4*math.sin(ang)))
for x,y in xy:
    header=header.cut(cq.Workplane("XY").circle(.57).extrude(3).translate((x,y,-1)))
place("header_flange",header.val(),"metal")
for i,(x,y) in enumerate(xy,1):
    place(f"hermetic_glass_{i:02d}",cyl(.55,-.65,.45,x,y),"glass")
    place(f"feedthrough_pin_{i:02d}",cyl(.22,-5.9,.9,x,y),"gold")

# TEC Microsystems 3MC04-044-05 aggregate: 6.4x6.4 / 2.4x2.4 mm,
# 3.8 mm overall, 44 P-N couples; stage split 28/12/4 is inferred.
base=.65
ceramic_t=.22
stage_leg_h=(1.07,.82,.64)
ceramics=(6.4,4.55,3.25,2.4)
counts=((8,7),(6,4),(4,2))
pitches=(.58,.55,.57)
contact_h=.065
z=base
for stage in range(3):
    size=ceramics[stage]
    place(f"ceramic_plate_{stage}",block(size,size,ceramic_t,0,0,z+ceramic_t/2),"ceramic")
    z+=ceramic_t
    n_x,n_y=counts[stage]
    pitch=pitches[stage]
    for j in range(n_y):
        for i in range(n_x):
            x=(i-(n_x-1)/2)*pitch
            y=(j-(n_y-1)/2)*pitch
            label=f"S{stage+1}_leg_{j*n_x+i+1:02d}"
            # Copper pad blocks abut the leg and ceramic surfaces. This is
            # a visual pad model, NOT a verified internal electrical netlist.
            place(label+"_lower_pad",block(.44,.44,contact_h,x,y,z+contact_h/2),"gold")
            place(label+"_BiTe",block(.40,.40,stage_leg_h[stage],x,y,z+contact_h+stage_leg_h[stage]/2),"p" if (i+j)%2 else "n")
            place(label+"_upper_pad",block(.44,.44,contact_h,x,y,z+contact_h+stage_leg_h[stage]+contact_h/2),"gold")
    z+=contact_h+stage_leg_h[stage]+contact_h
place("ceramic_plate_3_top",block(2.4,2.4,ceramic_t,0,0,z+ceramic_t/2),"ceramic")
z+=ceramic_t
assert abs((z-base)-3.8)<1e-7, (z-base)

place("cold_die_attach",block(1.25,1.25,.08,0,0,z+.04),"gold")
place("MCT_photoconductor_1mm",block(1.,1.,.12,0,0,z+.14),"die")
place("NTC_thermistor",block(.28,.40,.20,-.85,.77,z+.1),"die")

# Windowed enclosure (full assembly only) is shown with an amber substitute;
# real spectral ZnSe transmission/AR must be supplied experimentally.
can_z0=.45; can_z1=9.15
can=cyl(7.6,can_z0,can_z1).cut(cyl(7.1,can_z0-.05,can_z1-.45))
can=can.cut(cyl(2.95,can_z1-.55,can_z1+.1))
add(full,"hermetic_cap_window_opening",can,"metal")
add(full,"optical_window_illustrative",cyl(2.95,can_z1-.55,can_z1-.20),"glass")

core.save(str(OUT/"TO66_TEC_core_reference.step"))
full.save(str(OUT/"TO66_TEC_full_reference.step"))
(OUT/"geometry_manifest.json").write_text(json.dumps({
    "geometry_status":"illustrative, NOT simulation-qualified",
    "TEC_overall_height_mm":3.8,"leg_count":sum(a*b for a,b in counts),
    "couple_counts_estimated":[28,12,4],"stage_sides_mm":ceramics,
    "pin_count":9,"named_core_parts":len(parts),
    "limitations":["ellipse approximates header taper","no validated TEC series netlist",
      "contact resistances and solder layers not represented", "optical window material placeholder",
      "wire bonds / TEC supply leads not yet in reference generator"]
},indent=2))
print(f"Exported {len(parts)} core components to {OUT}")
