"""Reader-facing and external provenance gates for the corrected review PDF."""
import hashlib,json,re,subprocess,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reader(text):
    from reports.validate_report import validate_reader_text
    validate_reader_text(text)
    s=' '.join(unicodedata.normalize('NFKC',text).casefold().split())
    if re.search(r'\bcold\s*(?:20|30)(?:um)?\b|\bg[123][abcd]?\b|\boutputs/|\.git\b',s):raise ValueError('Internal model or machine identifier in reader text')
    return s
def provenance(d):
    if d['report_revision']!=3 or d['full_qualification'] or d['OEM_validated']:raise ValueError('False review qualification')
    if (d['mesh_nodes'],d['tetrahedra'],d['solid_domains'],d['thermoelectric_legs'])!=(159991,647657,216,88):raise ValueError('Obsolete geometry or unexpected field')
    if not d['tetrahedra_bijection_verified'] or d['node_bijection_max_distance_m']>1e-12:raise ValueError('Unverified solved-field map')
    expected='fem/results/cold_interface_convergence_20261030/device/cold20um_FAILED/mesh/mesh.npz'
    if expected not in d['inputs'] or d['mesh_sha256']!=d['inputs'][expected]:raise ValueError('Corrected geometry provenance missing')
    if any('/g3b' in x or 'revision6/' in x for x in d['inputs']):raise ValueError('Obsolete figure input')
    if 'normal_volume_study' in d:
        study=d['normal_volume_study'];key='fem/results/cold_bath_rev3_20261030/checksums.json'
        if study['full_numerical_release'] or key not in d['inputs'] or not {'cold1','bath2','bath3'}<=set(study['actual_completed_cases']):raise ValueError('Unqualified or untraced new field supplement')
    return True
def verify_edition(out):
    d=json.loads((out/'report_inputs.json').read_text());provenance(d)
    for n,h in json.loads((out/'edition_checksums.json').read_text()).items():
        if sha(out/n)!=h:raise ValueError('Published edition changed: '+n)
    for n,h in d['inputs'].items():
        if sha(ROOT/n)!=h:raise ValueError('Archived report input changed: '+n)
    for n,h in d['generator'].items():
        if sha(out/'source_snapshot'/(n+'.source'))!=h:raise ValueError('Edition generator snapshot differs')
    v=json.loads((out/'validation.json').read_text());visual=json.loads((out/'visual_review.json').read_text())
    if not v['passed'] or not visual['all_pages_inspected'] or visual['pdf_sha256']!=sha(out/'report.pdf'):raise ValueError('Unreviewed PDF')
    return True
def validate(out):
    if (out/'edition_checksums.json').exists():
        verify_edition(out)
        return json.loads((out/'validation.json').read_text())
    d=json.loads((out/'report_inputs.json').read_text());provenance(d)
    for name,digest in d['inputs'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Archived figure input changed: '+name)
    for name,digest in d['figures'].items():
        if sha(out/'figures'/name)!=digest:raise ValueError('Figure changed: '+name)
    text=subprocess.check_output(['mutool','draw','-q','-F','txt',str(out/'report.pdf')],stderr=subprocess.DEVNULL).decode();s=reader(text)
    for required in ['revision 3 review draft','full thermal verification incomplete','not a commercially verified assembly','6.48%','1.29%','fail','177','0.76','0.1','300','same production mesh']:
        if required not in s:raise ValueError('Missing honest review content: '+required)
    if 'normal_volume_study' in d:
        for required in ['4.795','1.069','1.093','nonmonotone']:
            if required not in s:raise ValueError('Missing actual new failed-gate evidence: '+required)
    (out/'reader.txt').write_text(text)
    from reports.validate_report import decode_pdf_metadata
    metadata=decode_pdf_metadata(subprocess.check_output(['mutool','show',str(out/'report.pdf'),'trailer/Info']).decode());reader(metadata)
    if re.search(r'/Author\s*\((?!\s*\))',metadata):raise ValueError('Personal PDF author metadata')
    (out/'metadata.txt').write_text(metadata)
    pages=int(subprocess.check_output(['mutool','show',str(out/'report.pdf'),'trailer/Root/Pages/Count']).strip())
    if not 10<=pages<=16:raise ValueError('Unexpected draft pagination')
    log=(out/'build-3.log').read_text()
    if any(x in log for x in ['Overfull \\hbox','Overfull \\vbox','undefined references','LaTeX Error']):raise ValueError('Typesetting overflow or unresolved reference')
    structured=subprocess.check_output(['mutool','draw','-q','-F','stext.json',str(out/'report.pdf')],stderr=subprocess.DEVNULL)
    (out/'page_structure.json').write_bytes(structured);stats=[]
    for page in json.loads(structured)['pages']:
        count=0
        for block in page.get('blocks',[]):
            if block.get('type')!='text':continue
            for line in block.get('lines',[]):
                count+=len(line.get('text','').strip());box=line['bbox']
                if box['x']<0 or box['y']<0 or box['x']+box['w']>596 or box['y']+box['h']>843:raise ValueError('Text outside page')
        if count<200:raise ValueError('Near-blank page')
        stats.append(count)
    renders=out/'renders';renders.mkdir(exist_ok=True)
    subprocess.run(['mutool','draw','-q','-r','100','-o',str(renders/'page-%02d.png'),str(out/'report.pdf')],check=True)
    # Use the pinned image for Pillow, keeping host dependencies unchanged.
    code="from pathlib import Path; from PIL import Image,ImageOps,ImageDraw; p=Path('"+str(renders.relative_to(ROOT))+"'); fs=sorted(p.glob('page-*.png')); w=300; thumbs=[ImageOps.contain(Image.open(f).convert('RGB'),(w,440)) for f in fs]; sheet=Image.new('RGB',(w*3,460*((len(fs)+2)//3)),'#dddddd'); [sheet.paste(im,((i%3)*w,(i//3)*460)) for i,im in enumerate(thumbs)]; sheet.save(p/'contact-sheet.png')"
    subprocess.run([str(ROOT/'fem/run.sh'),'python','-c',code],cwd=ROOT,check=True)
    result={'passed':True,'review_draft':True,'full_qualification':False,'pages':pages,'pdf_sha256':sha(out/'report.pdf'),'all_pages_rendered':len(list(renders.glob('page-*.png')))==pages,'page_text_characters':stats,'reader_and_metadata_checked':True,'corrected_field_provenance_checked':True,'visual_inspection':'required separately before publication'}
    if not result['all_pages_rendered']:raise ValueError('Missing rendered page')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');return result
