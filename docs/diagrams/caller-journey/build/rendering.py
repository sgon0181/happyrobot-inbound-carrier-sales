"""Shared SVG/PDF primitives and consistent legend for documentation diagrams."""

from pathlib import Path
from html import escape

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT = Path(__file__).resolve().parent.parent
PAGES = OUT / 'pages'
W, H = 1680, 1188
C = {'ink':'#14283F','muted':'#52647A','line':'#CBD5E1','paper':'#FFFFFF',
     'hr':'#713EB5','hrbg':'#F5F0FC','svc':'#14786B','svcbg':'#EDF8F4',
     'data':'#285EA6','databg':'#EFF5FF','ext':'#9B6512','extbg':'#FFF6E4',
     'build':'#8B5F0A','buildbg':'#FFF4D3','soft':'#F5F7FA'}


class Page:
    def __init__(self, stem, title, desc):
        self.stem, self.svg, self.issues = stem, [], []
        self.pdf = canvas.Canvas(str(PAGES / f'{stem}.pdf'), pagesize=landscape(A3))
        self.pdf.setTitle(title)
        self.pdf.setAuthor('Tech-Challenge documentation')
        self.pdf.scale(landscape(A3)[0]/W, landscape(A3)[1]/H)
        self.svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>')
        self.rect(0, 0, W, H, C['paper'], C['paper'])

    def rect(self, x, y, w, h, fill='none', stroke=None, radius=0, dash=False, sw=1):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{sw}"'+(' stroke-dasharray="6 4"' if dash else '')+'/>')
        p=self.pdf; p.saveState(); p.setLineWidth(sw)
        if fill!='none': p.setFillColor(colors.HexColor(fill))
        if stroke: p.setStrokeColor(colors.HexColor(stroke))
        if dash:p.setDash(6,4)
        p.roundRect(x,H-y-h,w,h,radius,stroke=bool(stroke),fill=fill!='none'); p.restoreState()

    def path(self, pts, fill='none', stroke=None, sw=1):
        self.svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
        p=self.pdf;p.saveState();p.setLineWidth(sw)
        if fill!='none':p.setFillColor(colors.HexColor(fill))
        if stroke:p.setStrokeColor(colors.HexColor(stroke))
        q=p.beginPath();q.moveTo(pts[0][0],H-pts[0][1])
        for x,y in pts[1:]:q.lineTo(x,H-y)
        q.close();p.drawPath(q,stroke=bool(stroke),fill=fill!='none');p.restoreState()

    def line(self, x1,y1,x2,y2,color=None,sw=1,dash=False,arrow=False):
        color=color or C['line']; self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')
        p=self.pdf;p.saveState();p.setStrokeColor(colors.HexColor(color));p.setLineWidth(sw)
        if dash:p.setDash(5,4)
        p.line(x1,H-y1,x2,H-y2);p.restoreState()
        if arrow:
            import math
            angle=math.atan2(y2-y1,x2-x1); size=6
            self.path([(x2,y2),(x2-size*math.cos(angle-0.45),y2-size*math.sin(angle-0.45)),(x2-size*math.cos(angle+0.45),y2-size*math.sin(angle+0.45))],color)

    def text(self,x,y,text,size=14,color=None,font='Helvetica',width=None,leading=None):
        color=color or C['ink']; leading=leading or size*1.28
        lines=[]
        for raw in str(text).split('\n'):
            if width is None:lines.append(raw);continue
            words=raw.split(' ');line=''
            for word in words:
                trial=f'{line} {word}'.strip()
                if stringWidth(trial,font,size)<=width or not line:line=trial
                else:lines.append(line);line=word
            lines.append(line)
        family='Courier New, monospace' if font=='Courier' else 'Arial, Helvetica, sans-serif'
        weight='bold' if font=='Helvetica-Bold' else 'normal'
        for i,t in enumerate(lines):
            yy=y+i*leading
            if width and stringWidth(t,font,size)>width+1:self.issues.append(f'Overflow {self.stem}: {t}')
            self.svg.append(f'<text x="{x}" y="{yy}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(t)}</text>')
            self.pdf.setFillColor(colors.HexColor(color));self.pdf.setFont(font,size);self.pdf.drawString(x,H-yy,t)
        return y+len(lines)*leading

    def badge(self,x,y,value,kind='call'):
        if kind=='call':
            self.rect(x,y,34,27,C['ink'],C['ink'],13);self.text(x+6,y+19,value,13,C['paper'],'Helvetica-Bold')
        else:
            self.path([(x+6,y),(x+37,y),(x+43,y+13),(x+37,y+26),(x+6,y+26),(x,y+13)],C['buildbg'],C['build'])
            self.text(x+10,y+18,value,12,C['build'],'Helvetica-Bold')

    def file(self,x,y,name,build=None,size=13):
        self.path([(x,y-11),(x+9,y-11),(x+14,y-6),(x+14,y+3),(x,y+3)],C['paper'],C['muted'])
        self.line(x+9,y-11,x+9,y-6,C['muted']);self.line(x+9,y-6,x+14,y-6,C['muted'])
        self.text(x+21,y+1,name,size,C['ink'],'Courier')
        if build:self.badge(x+21,y+8,build,'build')

    def store(self,x,y,w,h,title,body,size=13):
        self.rect(x,y+7,w,h-14,C['databg'],C['data'],0)
        for yy in [y,y+h-14]:
            self.svg.append(f'<ellipse cx="{x+w/2}" cy="{yy+7}" rx="{w/2}" ry="7" fill="{C["databg"]}" stroke="{C["data"]}"/>')
            p=self.pdf;p.setFillColor(colors.HexColor(C['databg']));p.setStrokeColor(colors.HexColor(C['data']));p.ellipse(x,H-yy-14,x+w,H-yy,fill=1,stroke=1)
        self.text(x+11,y+29,title,size,C['data'],'Helvetica-Bold',w-22)
        if body:
            end=self.text(x+11,y+44,body,size,C['ink'],width=w-22,leading=size*1.18)
            if end-size*1.18>y+h-16:self.issues.append(f'Store height {title}: {end-y}>{h}')

    def common(self,number,title,subtitle):
        self.text(44,48,f'{number} / 3',16,C['svc'],'Helvetica-Bold')
        self.text(123,50,title,29,C['ink'],'Helvetica-Bold')
        self.text(44,82,subtitle,16,C['muted'])
        self.rect(44,100,1592,64,C['soft'],C['line'],8)
        self.text(60,124,'IMPLEMENTED PATH: main 2678845. Successful call = Twin reservation + mocked handoff, not a TMS booking.',16,C['ink'],'Helvetica-Bold')
        self.text(60,148,'Local code / V4 draft shown; repo notes record V3 and an older App as live. Illustrative success path; mocked checkpoints do not establish voice reliability.',14,C['muted'])
        self.rect(44,176,1592,67,C['paper'],C['line'],8)
        self.badge(58,189,'C1');self.text(101,207,'call moment',13)
        self.badge(211,189,'B2','build');self.text(264,207,'build slice',13)
        self.file(373,207,'file.py');self.text(466,207,'= code',13)
        self.rect(546,187,125,28,C['databg'],C['data'],14);self.text(560,206,'Data object',13,C['data'])
        self.store(705,190,35,24,'','',12);self.text(753,207,'Stored state',13,C['data'])
        for x,key,label in [(918,'hr','HappyRobot'),(1085,'svc','Service'),(1223,'ext','External')]:
            self.rect(x,189,14,14,C[key],C[key],3);self.text(x+22,202,label,13)
        self.text(1374,202,'Border: solid = built;',12,C['muted']);self.text(1374,221,'dashed = conditional',12,C['muted'])
        self.text(58,232,'B1 Foundations  |  B2 Verify + storage  |  B3 Sell + reserve + close  |  B4 Operate + submit  |  B5 QA + delivery. Build order is not call order.',12.3,C['build'])

    def footer(self):
        self.text(44,1169,'Source: main 2678845. File paths are relative to service/ unless marked. C1-C7 are call moments; B1-B5 are build slices. Money is illustrative, not a live trace.',10.9,C['muted'])
        self.text(44,1183,'Shared I/O: api.py routes JSON; adapters/twin.py version-checks SQL writes. TMS [B1]: client.py query/get -> protocol.py encode_request/parse_reply -> mapping.py to_summary/to_load.',10.8,C['muted'])
        self.svg.append('</svg>');(PAGES/f'{self.stem}.svg').write_text('\n'.join(self.svg)+'\n')
        self.pdf.showPage();self.pdf.save()
        return self.issues

