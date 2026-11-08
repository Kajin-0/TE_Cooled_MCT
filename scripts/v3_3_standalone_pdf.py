#!/usr/bin/env python3
"""Render the generated self-contained Markdown science monograph to PDF.

Independent reader needs only the PDF: all data, tables, equations and
model conditions are inside. Uses ReportLab Platypus to split long tables
across pages. Keep document source and final PDF together.
"""
from pathlib import Path
import os,sys,re,html
sys.path.insert(0,'/var/tmp/tec_standalone_reportlab_20261108')
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle,KeepTogether,PageBreak
ROOT=Path(__file__).resolve().parents[1]
MD=ROOT/'reports/generated/TEC_HgCdTe_Reference_V3_3_Standalone_Method_20261108.md'
PDF=ROOT/'reports/generated/TEC_HgCdTe_Reference_V3_3_Standalone_Method_20261108.pdf'
FONT='/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DVS',FONT+'/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVS-Bold',FONT+'/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DVS',normal='DVS',bold='DVS-Bold',italic='DVS',boldItalic='DVS-Bold')
NAVY=colors.HexColor('#152238')
PINK=colors.HexColor('#7739a9')
BORDER=colors.HexColor('#d8dce5')
def clean(text):
 s=html.escape(text.strip(),quote=False)
 s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)',r'<i>\1</i>',s)
 s=s.replace('**','')
 return s
styles={
 'title':ParagraphStyle('TITLE',fontName='DVS-Bold',fontSize=16,leading=22,textColor=NAVY,spaceBefore=0,spaceAfter=12),
 'subtitle':ParagraphStyle('SUBTITLE',fontName='DVS',fontSize=9,leading=14,textColor=PINK,spaceAfter=12),
 'section':ParagraphStyle('SECTION',fontName='DVS-Bold',fontSize=11,leading=15,textColor=NAVY,spaceBefore=14,spaceAfter=8,keepWithNext=True),
 'paragraph':ParagraphStyle('PARA',fontName='DVS',fontSize=8.4,leading=13.1,spaceAfter=6),
 'quote':ParagraphStyle('QUOTE',fontName='DVS',fontSize=8.1,leading=12,leftIndent=15,rightIndent=8,textColor=NAVY,spaceAfter=4),
 'table':ParagraphStyle('TABLE',fontName='DVS',fontSize=6.5,leading=9),
 'tableheader':ParagraphStyle('TABLEHEAD',fontName='DVS-Bold',fontSize=6.4,leading=9,textColor=NAVY),
 }
PAGE_W,PAGE_H=A4
L,R=44,44
USABLE=PAGE_W-L-R
def make_table(rows):
 count=len(rows[0])
 widths={
  2:[USABLE*.64,USABLE*.36],
  3:[USABLE*.36,USABLE*.32,USABLE*.32],
  4:[USABLE*.34,USABLE*.22,USABLE*.22,USABLE*.22],
  5:[USABLE*.25,USABLE*.15,USABLE*.13,USABLE*.235,USABLE*.235],
  6:[USABLE*.21]+[USABLE*.158]*5,
  7:[USABLE*.105,USABLE*.13,USABLE*.13,USABLE*.13,USABLE*.13,USABLE*.13,USABLE*.245],
 } .get(count,[USABLE/count]*count)
 if count==7 and rows[0][0].strip()=='T (K)':
  widths=[USABLE*.09]+[USABLE*.1516667]*6
 if count==7 and rows[0][0].strip()=='Ceramic':
  widths=[USABLE*.08,USABLE*.09,USABLE*.13,USABLE*.13,USABLE*.13,USABLE*.16,USABLE*.28]
 widths[-1]+=USABLE-sum(widths)
 data=[]
 for i,row in enumerate(rows):
  data.append([Paragraph(clean(str(v)),styles['tableheader'] if i==0 else styles['table']) for v in row])
 tab=LongTable(data,colWidths=widths,repeatRows=1,hAlign='CENTER',splitByRow=1)
 tab.setStyle(TableStyle([
  ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f0edf6')),
  ('GRID',(0,0),(-1,-1),.3,BORDER),
  ('VALIGN',(0,0),(-1,-1),'TOP'),
  ('LEFTPADDING',(0,0),(-1,-1),4),
  ('RIGHTPADDING',(0,0),(-1,-1),4),
  ('TOPPADDING',(0,0),(-1,-1),4),
  ('BOTTOMPADDING',(0,0),(-1,-1),4),
  ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fafbfc')]),
 ]))
 return tab
def running(canvas,doc):
 canvas.saveState()
 canvas.setStrokeColor(BORDER)
 canvas.setLineWidth(.4)
 canvas.line(L,PAGE_H-46,PAGE_W-R,PAGE_H-46)
 canvas.setFont('DVS',7)
 canvas.setFillColor(NAVY)
 canvas.drawString(L,PAGE_H-38,'TEC-COOLED HgCdTe VIRTUAL DEVICE | STANDALONE REPRODUCTION')
 canvas.drawRightString(PAGE_W-R,PAGE_H-38,'TECHNICAL METHODS / 2026')
 canvas.line(L,42,PAGE_W-R,42)
 canvas.setFont('DVS',7)
 canvas.drawString(L,28,'Physics-based synthetic reference design | conditional numerical results')
 canvas.drawRightString(PAGE_W-R,28,f'Page {doc.page}')
 canvas.restoreState()
def parse(content):
 lines=content.splitlines()
 out=[]
 i=0
 while i<len(lines):
  raw=lines[i];line=raw.strip()
  if not line:
   out.append(Spacer(1,3));i+=1;continue
  if line.startswith('|'):
   block=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    r=[a.strip() for a in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r':?-+:?',a or '-') for a in r):
     block.append(r)
    i+=1
   if len(block)>=2:
    out.append(make_table(block));out.append(Spacer(1,6))
   continue
  if line.startswith('# '):
   out.append(Paragraph(clean(line[2:]),styles['title']));i+=1;continue
  if line.startswith('## '):
   out.append(Paragraph(clean(line[3:]),styles['section']));i+=1;continue
  if line.startswith('> '):
   out.append(Paragraph(clean(line[2:]),styles['quote']));i+=1;continue
  if re.match(r'^(\d+\.|[-*])\s',line):
   out.append(Paragraph(clean(line),styles['paragraph']));i+=1;continue
  para=[line]
  i+=1
  while i<len(lines) and lines[i].strip() and not (lines[i].startswith(('#','>','|')) or re.match(r'^(\d+\.|[-*])\s',lines[i].strip())):
   para.append(lines[i].strip());i+=1
  txt=' '.join(para)
  style=styles['subtitle'] if 'Standalone scientific reproduction monograph' in txt else styles['paragraph']
  out.append(Paragraph(clean(txt),style))
 return out
def main():
 assert MD.is_file()
 assert not PDF.exists()
 doc=SimpleDocTemplate(str(PDF),pagesize=A4,leftMargin=L,rightMargin=R,topMargin=60,bottomMargin=57,
  title='Reference TEC-Cooled HgCdTe Detector - Standalone Physical and Numerical Reproduction, V3.3',
  author='Independent Scientific Reference Model',
  subject='Complete synthetic 29/11/4 TEC, HgCdTe detector, 3D ceramic FEM, pressure dependent gas and radiation, 84 material values, 88 leg coordinates and 95 native face loads')
 story=parse(MD.read_text())
 doc.build(story,onFirstPage=running,onLaterPages=running)
 print('STANDALONE_PDF_GENERATED',PDF,'bytes',PDF.stat().st_size)
if __name__=='__main__':main()
