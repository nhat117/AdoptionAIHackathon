#!/usr/bin/env python3
"""Render the revised Markdown protocol as a paginated PDF."""
from pathlib import Path
from html import escape
import re
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
ROOT=Path(__file__).resolve().parent
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyResearch',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8,textColor=colors.HexColor('#243644')))
styles.add(ParagraphStyle(name='TitleResearch',fontName='Helvetica-Bold',fontSize=25,leading=29,spaceAfter=12,textColor=colors.HexColor('#153e56')))
styles.add(ParagraphStyle(name='SubtitleResearch',fontName='Helvetica',fontSize=13,leading=17,spaceAfter=15,textColor=colors.HexColor('#416275')))
styles.add(ParagraphStyle(name='HeadingResearch',fontName='Helvetica-Bold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=7,keepWithNext=True,textColor=colors.HexColor('#153e56')))
styles.add(ParagraphStyle(name='ReferenceResearch',fontName='Helvetica',fontSize=8.3,leading=11,spaceAfter=8,wordWrap='CJK'))
def markup(text):
    text=text.replace('×','x').replace('–','-').replace('—','-').replace('’',"'").replace('“','"').replace('”','"')
    s=escape(text)
    s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
    return s
story=[]
for block in (ROOT/'UPDATED_PROPOSAL.md').read_text().split('\n\n'):
    if not block.strip():continue
    if block.startswith('# '):style='TitleResearch';block=block[2:]
    elif block.startswith('## '):style='SubtitleResearch';block=block[3:]
    elif block.startswith('### '):style='HeadingResearch';block=block[4:]
    elif re.match(r'\[\d\]',block):style='ReferenceResearch'
    else:style='BodyResearch'
    story.append(Paragraph(markup(block).replace('\n',' '),styles[style]))
def page(canvas,doc):
    w,h=A4;canvas.saveState();canvas.setStrokeColor(colors.HexColor('#b8cbd6'));canvas.line(46,h-40,w-46,h-40)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#557080'))
    canvas.drawString(46,h-30,'AUTHORITY ACROSS LANGUAGES  |  REVISED EXPLORATORY PROTOCOL')
    canvas.drawString(46,29,'8 November 2026  |  Version 2.0  |  Observed results supplied separately')
    canvas.drawRightString(w-46,29,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(ROOT/'Updated_Proposal.pdf'),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=59,bottomMargin=47,
 title='Authority Across Languages - Revised Research Protocol',author='Research implementation')
doc.build(story,onFirstPage=page,onLaterPages=page)
print(ROOT/'Updated_Proposal.pdf')
