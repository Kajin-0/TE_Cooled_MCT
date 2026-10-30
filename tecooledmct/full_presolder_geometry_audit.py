"""Read-only geometry-authority, pin-view and actual solved lead endpoint audit."""
import argparse,csv,gzip,json,tempfile,shutil
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull,cKDTree
from .g2d_data import ROOT,sha,dump
from .full_presolder_guard import preserve
from .flux_presolder_common import node_map

VIGO='https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf'
TEC='https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf'


def pin_profile(view='bottom'):
    """Drawing convention: page-up retained; top x=-bottom x (normal reverses)."""
    if view not in ('bottom','top'):raise ValueError('Unknown viewing convention')
    functions={1:'TEC+',2:'unused',3:'unused',4:'unused',5:'thermistor',6:'thermistor',7:'detector cathode / active',8:'detector anode / active',9:'TEC-'}
    rows=[]
    for i in range(1,10):
        theta=np.deg2rad(-36*i);x=5.4*np.cos(theta);y=5.4*np.sin(theta)
        rows.append({'pin':i,'x_mm':float(x if view=='bottom' else -x),'y_mm':float(y),'function':functions[i]})
    return rows


def authority_matrix():
    return [
      {'parameter':'header envelope / profile','baseline':'31.5x17.5mm mathematical ellipse;1.1mm thick','VIGO_family':'31.5x17.5mm, two-ear contour;1.5mm drawing header dimension','generic_user_reference':'31.5x14.7mm; contour/manufacturer not identified','classification':'drawing family and user reference differ; ellipse is a modeling approximation','source':VIGO},
      {'parameter':'cap OD','baseline':'15.2mm','VIGO_family':'15.2mm dimension','generic_user_reference':'12.44mm','classification':'different envelope hypotheses, not interchangeable product data','source':VIGO},
      {'parameter':'height/window','baseline':'8.6mm above header, clear diameter5.9mm','VIGO_family':'8.25+/-0.35mm drawing datum, diameter6 aperture; verify datum before new CAD','generic_user_reference':'not identified','classification':'old height/window are hypotheses, not exact drawing match','source':VIGO},
      {'parameter':'pins / views','baseline':'nine generic0.44mm pins; no OEM identities; source view unspecified','VIGO_family':'nine0.76mm pins,10.8mm PCD,C arrangement; numbering is bottom view','generic_user_reference':'not identified','classification':'both pin geometry and endpoint functions require correction','source':VIGO},
      {'parameter':'TEC hot/cold widths / height','baseline':'6.4/2.4mm;3.8mm','VIGO_family':'drawing does not identify the chosen TEC part','generic_user_reference':'6.05mm bottom in user render, not tied to this TEC','classification':'6.4/2.4 are sourced for selected3MC04-044-05, not geometry errors; package compatibility unverified','source':TEC},
      {'parameter':'TEC stages and inner construction','baseline':'28/12/4 couples;4.55/3.25mm intermediate plates','VIGO_family':'unknown internal artwork and exact cooler','generic_user_reference':'unknown','classification':'inferred geometry, never OEM-verified','source':TEC},
      {'parameter':'leads','baseline':'Cu0.202mm diameter x8mm; pins2/3 to module ports103/104','VIGO_family':'TEC pins1/9; detector7/8; thermistor5/6','generic_user_reference':'0.28mm illustrative in Revision6','classification':'model instances are not OEM pin numbers; return module port is mid-stack','source':VIGO},
      {'parameter':'enclosure physics','baseline':'pureN2 100Pa;gray eps;opaque window;passive package potential','VIGO_family':'no matched gas/pressure/coating/thermal contact qualification supplied','generic_user_reference':'unknown','classification':'unvalidated hypotheses; no manufactured-device accuracy','source':VIGO}]


def endpoints(case,operator,out):
    import meshio
    archive=ROOT/'fem/results/g3b_checkpoint_20261029';base=archive/'cases'/case;fieldbase=archive/'fields'/case;mesh=archive/'operators'/operator
    r=json.loads((base/'metrics.json').read_text());d=np.load(mesh/'mesh.npz');p,f,tags=[d[k] for k in ('points','faces','boundaries')]
    cache=ROOT/'outputs/full-presolder-cache';cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        raw=Path(tmp)/'field.vtu'
        with gzip.open(fieldbase/'fields_t0001.vtu.gz','rb') as inp,raw.open('wb') as target:shutil.copyfileobj(inp,target)
        expected=json.loads((fieldbase/'uncompressed_sha256.json').read_text())['fields_t0001.vtu']
        if sha(raw)!=expected:raise ValueError('Changed actual field')
        field=meshio.read(raw)
    ix,_=node_map(p,field.points);t=field.point_data['temperature'].ravel()[ix]
    def endpoint(tag):
        faces=f[tags==tag];xyz=p[faces];a=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
        return {'tag':tag,'centroid_m':(a@xyz.mean(1)/a.sum()).tolist(),'temperature_k':float(a@t[faces].mean(1)/a.sum()),'area_m2':float(a.sum())}
    rows=[];A=np.pi*(.000202/2)**2;G=400*A/.008;J=.1**2*1.72e-8*.008/A
    for i,(warm,cold,stage) in enumerate([(204,103,0),(206,104,2)]):
        w=endpoint(warm);c=endpoint(cold);distance=float(np.linalg.norm(np.array(w['centroid_m'])-c['centroid_m']));q=G*(w['temperature_k']-c['temperature_k'])
        wn=np.unique(f[tags==warm]);cn=np.unique(f[tags==cold]);nearest=float(cKDTree(p[cn]).query(p[wn])[0].min());rw=float(np.linalg.norm(p[wn]-w['centroid_m'],axis=1).max());rc=float(np.linalg.norm(p[cn]-c['centroid_m'],axis=1).max())
        if abs(q-r['supply_leads'][i]['heat_into_cold_w'])>1e-10:raise ValueError('Lead power reproduction failed')
        rows.append({'lead':i,'warm_endpoint':w,'TEC_endpoint':c,'terminal_stage':stage,'terminal_is_module_hot_side':stage==0,'assumed_length_m':.008,'patch_centroid_straight_line_m':distance,'centroid_model_length_consistent':distance<=.008+1e-12,'surface_distance_lower_bound_m':max(0.,distance-rw-rc),'closest_mesh_vertex_pair_upper_bound_m':nearest,'attachment_pair_within_assumed_length_exists':nearest<=.008,'length_scope':'centroid consistency is not physical impossibility; finite attachments and wire arcs are unknown','G_W_K':G,'conduction_into_TEC_W':q,'joule_W':J,'basis':'actual area-averaged raw VTU temperatures/mesh face coordinates; no PDE executed'})
    return {'case':case,'actual_field_sha256':expected,'leads':rows,'net_conduction_into_TEC_W':sum(v['conduction_into_TEC_W'] for v in rows),'total_lead_Joule_W':2*J}


def main(out):
    integrity=preserve();out.mkdir(parents=True,exist_ok=False);archive=ROOT/'fem/results/g3b_checkpoint_20261029';manifest=json.loads((archive/'operators/operator_h0p1/manifest.json').read_text())
    data={'status':'ASSUMED-GEOMETRY SANDBOX ONLY; no single manufactured package identified','geometry_authority_selected':False,'baseline_integrity':integrity,'authority_matrix':authority_matrix(),'pinout_bottom_view':pin_profile(),'pinout_top_view':pin_profile('top'),'view_transform':'with page-up fixed: x_top=-x_bottom,y_top=y_bottom; always retain the viewing normal and datum; not a pin-number rotation','current_construction_pin_centres_m':manifest['package_registry']['feedthroughs']['centers_xy_m'],'current_terminal_planes':manifest['terminal_planes'],'full_package_geometry_corrected':False,'historical_15page_report_status':'unchanged historical hypothetical assembly, not an OEM-validated external-facing device study','lead_audits':[endpoints('nitrogen_patch1','operator_h0p1',out),endpoints('nitrogen_0','operator_h0',out)]}
    solid=json.loads((archive/'cases/solid_reference_h0/metrics.json').read_text());leads=json.loads((archive/'cases/lead_only_0/metrics.json').read_text());data['same_coarse_mesh_lead_only_control']={'die_shift_k':leads['die_mean_k']-solid['die_mean_k'],'scope':'gas/radiation off, Au retained, Cu leads added; NOT the N2/radiation operating point or a new fine-mesh test'}
    dump(out/'audit.json',data)
    with (out/'authority_matrix.csv').open('w') as stream:w=csv.DictWriter(stream,fieldnames=list(data['authority_matrix'][0]));w.writeheader();w.writerows(data['authority_matrix'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(10,5))
    for ax,view in zip(axs,['bottom','top']):
        for row in pin_profile(view):
            colour='#b74b43' if row['pin'] in (1,9) else '#3b6b91' if row['pin'] in (7,8) else '#8a7b40' if row['pin'] in (5,6) else '#777777'
            ax.scatter(row['x_mm'],row['y_mm'],color=colour,s=50);ax.annotate(str(row['pin']),(row['x_mm'],row['y_mm']),xytext=(4,4),textcoords='offset points')
        ax.set(title=f'VIGO family {view} view (explicit mirror)',xlabel='x (mm)',ylabel='y (mm)',xlim=(-7,7),ylim=(-7,7));ax.set_aspect('equal');ax.grid(alpha=.2)
    fig.suptitle('Reference pin identities only; current assumed mesh is not this verified pinout');fig.tight_layout();fig.savefig(out/'pin_view_audit.png',dpi=250);plt.close(fig)
    theta=np.linspace(0,2*np.pi,720,endpoint=False);cloud=[]
    for x,radius in [(0,8.75),(-12.2,3.55),(12.2,3.55)]:cloud.extend(np.c_[x+radius*np.cos(theta),radius*np.sin(theta)])
    cloud=np.array(cloud);hull=ConvexHull(cloud);outline=cloud[hull.vertices];fig,ax=plt.subplots(figsize=(9,4));ax.plot(15.75*np.cos(theta),8.75*np.sin(theta),label='Actual FEM ellipse31.5x17.5');ax.plot(*np.vstack([outline,outline[:1]]).T,label='Dimension-constrained two-ear tangent hypothesis');ax.add_patch(plt.Circle((0,0),7.6,fill=False,color='gray',ls='--',label='VIGO-family15.2mm cap'));ax.add_patch(plt.Circle((0,0),6.22,fill=False,color='orange',ls=':',label='Separate user12.44mm cap reference'));ax.set(xlabel='x (mm)',ylabel='y (mm)',title='Do not splice different package envelopes');ax.set_aspect('equal');ax.legend(frameon=False,fontsize=8);fig.tight_layout();fig.savefig(out/'flange_profile_discrepancy.png',dpi=250);plt.close(fig)
    print('Read-only geometry/lead audit:',out,[(r['case'],r['net_conduction_into_TEC_W']) for r in data['lead_audits']],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();main(args.out.resolve())
