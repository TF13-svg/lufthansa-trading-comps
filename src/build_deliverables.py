from pathlib import Path
import sys,json,base64,csv,io,zipfile
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
import valuation
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

df,result=valuation.main()
summary=json.loads((root/'outputs/summary.json').read_text())
registry=json.loads((root/'data/source_registry.json').read_text())
price=summary['observed_price']
eb=result[result.metric=='EBITDA']
lookup={r['group']:r for _,r in eb.iterrows()}

def table_md(frame):
    cols=list(frame.columns)
    rows=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
    for _,r in frame.iterrows():rows.append('| '+' | '.join(str(x) for x in r)+' |')
    return '\n'.join(rows)

readme=f'''# Lufthansa Trading Comparables Valuation

**Valuation date: 9 September 2026 | Educational valuation case study**

This project values Lufthansa using European airline trading multiples, with auditable financial bridges, issuer source references and a frozen market-data snapshot. It illustrates valuation work relevant to M&A; it does not model a transaction or claim prior deal experience.

## Main finding

Peer choice matters more than the appearance of numerical precision. The network-carrier EBITDA reference midpoint is EUR {lookup['Network carriers']['median']:.2f} per share, compared with EUR {lookup['All peers']['median']:.2f} for all five peers and EUR {lookup['Low-cost carriers']['median']:.2f} for the low-cost set. The observed Lufthansa close is EUR {price:.2f}. These are outputs of a **reported-net-debt baseline**, not fully adjusted target prices. Network carriers are the primary business-model reference; only two core peers are available.

{table_md(eb[['group','n','low','median','high','range_basis']].round(2))}

The two-company range is the observed min-max. Larger groups use peer 25th-75th percentiles, which are not confidence intervals. EV/Revenue is secondary because margins and business mixes differ materially.

![Valuation ranges](outputs/football_field.png)

## Read first

- [Three-page valuation brief](outputs/Lufthansa_Valuation_Brief.pdf)
- [Methodology and limitations](docs/METHODOLOGY.md)
- [German interview guide](docs/INTERVIEW_GUIDE_DE.md)
- [Notebook](notebooks/lufthansa_comps_analysis.ipynb)

## Run

Python3.12 is recommended. From the project directory:

```sh
python -m pip install -r requirements.txt
python src/valuation.py
python tests/test_valuation.py
```

Open the notebook in JupyterLab and Run All. No network access is required for the valuation: prices and source inputs are frozen under `data/`. Running the valuation updates CSVs, chart and summary.json. To refresh the README, PDF and notebook's saved outputs from that same run, use `python src/build_deliverables.py`. The report builder uses reportlab; it does not require the local-only preparation scripts.

## Data and audit trail

`data/ltm_bridges.csv` contains FY/interim components, period ends, report IDs, page locations and known disclosure differences. `data/net_debt_bridges.csv` reconciles debt and cash. `data/companies.csv` records share-count dates, sources and conventions. `data/source_registry.json` lists issuer reports and issuer-authored announcements. `data/market_snapshot.csv` and `data/market_raw/` preserve actual unadjusted closes and the provider response. Source links point to third-party publications; original reports are not bundled.

## Improvements from the original

- Corrected IAG issued shares for disclosed treasury holdings.
- Rebuilt Ryanair lease-inclusive net debt from the balance sheet instead of rounded net cash.
- Used explicit company-reported Wizz Air rolling EBITDA; retained the unexplained EUR1.3m bridge difference in the audit trail.
- Removed manual README results; all reported values now come from the same model output.
- Added assertions against missing values, future dates, duplicate rows and broken LTM arithmetic.
- Used consistent spot FX for GBP amounts; identified pence conversion explicitly.
- Added leave-one-out, EBITDA/multiple, Ryanair exceptional-charge and expanded EV-bridge sensitivities.

## Limits that remain

AF-KLM revenue uses a provisional bridge across original FY and IFRS18-restated interim comparatives. easyJet is deliberately lagged to H1 and has offer-related price risk. Some share counts are issued-share proxies or older disclosures, not exact-day outstanding counts. EBITDA definitions differ. The expanded EV-bridge scenario uses book proxies for selected pensions, minority interests and perpetuals; it is not a complete fair-value harmonization. These constraints matter and are explained in the methodology, not hidden behind a precise share price.

The `original/` folder preserves the user's initial version for comparison. The revised case study was researched and developed collaboratively with AI assistance. The candidate should personally verify and understand all assumptions before using it as an interview work sample.
'''
(root/'README.md').write_text(readme,encoding='utf-8')

cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(keepends=True)))
def code(s,text=None,image=None):
    outputs=[]
    if text is not None:outputs.append(dict(output_type='stream',name='stdout',text=text.splitlines(keepends=True)))
    if image is not None:outputs.append(dict(output_type='display_data',metadata={},data={'image/png':base64.b64encode(image).decode(),'text/plain':['<Valuation ranges>']}))
    cells.append(dict(cell_type='code',metadata={},source=s.splitlines(keepends=True),execution_count=1+sum(c['cell_type']=='code' for c in cells),outputs=outputs))
md('# Lufthansa Comparable Companies Valuation\n\nValuation date: 9 September 2026. Educational case study with a frozen market snapshot. Start with the source audit, not the headline share price. See `../docs/METHODOLOGY.md` for assumptions and open limitations.')
code("from pathlib import Path\nimport sys\nimport pandas as pd\nROOT = Path.cwd()\nif ROOT.name == 'notebooks': ROOT = ROOT.parent\nif not (ROOT / 'src' / 'valuation.py').exists():\n    raise RuntimeError('Open this notebook from the project root or notebooks directory')\nsys.path.insert(0, str(ROOT / 'src'))\nfrom valuation import load_data, main, ranges\n",'')
md('## 1. Sources, LTM and net debt\nAll amounts in millions. Rolling EBITDA disclosures override independently constructed figures where marked. AF-KLM revenue remains provisional; Wizz Air has a EUR1.3m disclosure difference.')
code("bridges = pd.read_csv(ROOT / 'data' / 'ltm_bridges.csv')\nprint(bridges[['company','metric','fy','prior_comparable','current_comparable','calculated_ltm','reported_ltm']].to_string(index=False))",pd.read_csv(root/'data/ltm_bridges.csv')[['company','metric','fy','prior_comparable','current_comparable','calculated_ltm','reported_ltm']].to_string(index=False))
code("print(pd.read_csv(ROOT / 'data' / 'net_debt_bridges.csv').to_string(index=False))",pd.read_csv(root/'data/net_debt_bridges.csv').to_string(index=False))
md('## 2. Market snapshot and share counts\nRaw quote.close is used, not adjclose. GBP quotes in pence are converted before EUR translation. IAG treasury shares are deducted. Source dates are earlier than the valuation date, but some disclosed share counts are older proxies.')
code("print(pd.read_csv(ROOT / 'data' / 'market_snapshot.csv')[['ticker','date','close','currency']].to_string(index=False))",pd.read_csv(root/'data/market_snapshot.csv')[['ticker','date','close','currency']].to_string(index=False))
md('## 3. Compute the reported-net-debt baseline\nEV=equity value+lease-inclusive net debt. This baseline omits other capital claims. Do not describe it as fully adjusted enterprise value.')
code("comps, results = main()\nprint(comps[['company','shares_m','equity_value','net_debt_eur','enterprise_value','Revenue_eur','EBITDA_eur','EV_EBITDA']].round(2).to_string(index=False))",result[['group','metric','n','low','median','high']].round(2).to_string(index=False)+'\n'+df[['company','shares_m','equity_value','net_debt_eur','enterprise_value','Revenue_eur','EBITDA_eur','EV_EBITDA']].round(2).to_string(index=False))
md('## 4. Business-model comparison\nNetwork carriers are the closest business-model reference, but n=2 is a small sample. Their range is min-max; larger sets show peer quartiles. These ranges are not confidence intervals.')
code("from IPython.display import display, Image\ndisplay(Image(filename=str(ROOT / 'outputs' / 'football_field.png')))",image=(root/'outputs/football_field.png').read_bytes())
md('## 5. Sensitivities\nExpanded bridge adds selected book proxies to peers and subtracts the corresponding target claims from enterprise value. It is not a complete fair-value EV bridge. Leave-one-out shows peer dependence. EBITDA shocks are scenarios, not forecasts.')
for filename in ['expanded_bridge_sensitivity.csv','leave_one_out.csv','ryanair_exceptional_addback_sensitivity.csv']:
 code(f"print(pd.read_csv(ROOT / 'outputs' / '{filename}').round(2).to_string(index=False))",pd.read_csv(root/'outputs'/filename).round(2).to_string(index=False))
code("s = pd.read_csv(ROOT / 'outputs' / 'ebitda_multiple_sensitivity.csv')\nprint(s.pivot(index='ebitda_factor', columns='multiple', values='price').round(2).to_string())",pd.read_csv(root/'outputs/ebitda_multiple_sensitivity.csv').pivot(index='ebitda_factor',columns='multiple',values='price').round(2).to_string())
md('## 6. Conclusion\nBusiness model, EBITDA definition and capital-claim treatment drive the result. A credible work sample explains these choices and their limits rather than presenting the full-peer median as an intrinsic value. Next steps are full EBITDA harmonization, date-aligned share counts, AF-KLM restatement reconciliation, updated easyJet data and a cash-flow-based cross-check.')
notebook=dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},nbformat=4,nbformat_minor=5)
for i,cell in enumerate(cells):cell['id']=f'cell-{i:02}'
(root/'notebooks/lufthansa_comps_analysis.ipynb').write_text(json.dumps(notebook,indent=1),encoding='utf-8')

pdf=root/'outputs/Lufthansa_Valuation_Brief.pdf'
c=canvas.Canvas(str(pdf),pagesize=A4); W,H=A4
c.setTitle('Lufthansa | Trading Comparables Valuation | Till Fichtelberger')
navy=colors.HexColor('#173f59'); grey=colors.HexColor('#586775'); y=0
body=ParagraphStyle('body',fontName='Helvetica',fontSize=9.1,leading=12,textColor=navy)
small=ParagraphStyle('small',parent=body,fontSize=7.6,leading=10)
def paragraph(text,style=body,gap=9):
 global y
 p=Paragraph(text,style);_,h=p.wrap(W-80,H);p.drawOn(c,40,y-h);y-=h+gap
 assert y>42,('overflow',y,text[:40])
def header(number,label):
 global y
 c.setFillColor(navy);c.rect(0,H-80,W,80,fill=1,stroke=0)
 c.setFillColor(colors.white);c.setFont('Helvetica-Bold',20);c.drawString(40,H-40,'Lufthansa')
 c.setFont('Helvetica',10);c.drawString(40,H-59,label)
 c.setFillColor(grey);c.setFont('Helvetica',8);c.drawString(40,26,'Till Fichtelberger | Valuation date: 9 September 2026 | Educational case study')
 c.drawRightString(W-40,26,str(number));y=H-100
def heading(s):paragraph('<b>'+s+'</b>',ParagraphStyle('h',parent=body,fontSize=12,leading=15),6)
def table(rows,widths):
 global y
 th=ParagraphStyle('th',parent=small,textColor=colors.white)
 formatted=[[Paragraph(str(x),th if i==0 else small) for x in row] for i,row in enumerate(rows)]
 t=Table(formatted,colWidths=widths,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f4f6'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 # Paragraphs have their own text colour, including header cells.
 _,h=t.wrap(W-80,H);t.drawOn(c,40,y-h);y-=h+12
 assert y>42,('table overflow',y)
header(1,'Trading comparables | Peer choice changes the valuation')
heading('A valuation range, rather than a single target price')
paragraph(f'Lufthansa traded at <b>EUR {price:.2f}</b> on the valuation date. The closest available network-carrier set gives an EBITDA-based midpoint of <b>EUR {lookup["Network carriers"]["median"]:.2f}</b>; the five-peer midpoint is <b>EUR {lookup["All peers"]["median"]:.2f}</b>. These are relative indications under a reported-net-debt baseline, with incomplete harmonization of other capital claims.')
rows=[['EV/EBITDA set','Peers','Range (EUR)','Midpoint (EUR)']]
for _,r in eb.iterrows():rows.append([r['group'],r.n,f'{r.low:.2f} - {r.high:.2f}',f'{r["median"]:.2f}'])
table(rows,[190,40,135,150])
img=ImageReader(str(root/'outputs/football_field.png'));iw,ih=img.getSize();h=(W-80)*ih/iw
c.drawImage(img,40,y-h,width=W-80,height=h);y-=h+10
paragraph('Network set: observed min-max across two companies. Other sets: peer 25th-75th percentiles. Dots are medians; ranges are not confidence intervals.',small)
heading('Analyst interpretation')
paragraph('Air France-KLM and IAG provide the closer business-model reference. Low-cost peers are an explicit sensitivity: their growth, fleet ownership, leasing and business mix differ. Lufthansa also contains substantial logistics and MRO operations. EV/Revenue produces much higher indications because it ignores the target\'s lower EBITDA margin; it is a secondary cross-check, not an equal-weight valuation anchor.')
paragraph('Source inputs: company reports [1]-[12], share disclosures [13]-[18], and the saved Yahoo Finance market snapshot. Key limitations and source links follow.',small)
c.showPage();header(2,'Financial audit | Decisions that matter')
heading('Comparable-company snapshot')
rows=[['EURm, except multiples','LTM revenue','LTM EBITDA','Net debt','EV/EBITDA']]
for _,r in df.iterrows():rows.append([r.company,f'{r.Revenue_eur:,.0f}',f'{r.EBITDA_eur:,.0f}',f'{r.net_debt_eur:,.0f}',f'{r.EV_EBITDA:.2f}x'])
table(rows,[145,105,105,80,80])
paragraph('GBP inputs translated consistently at valuation-date spot FX. EBITDA definitions differ across companies. easyJet is measured at March 2026; the other financial observations are June 2026. Net debt includes leases; do not add them twice.',small)
heading('Corrections and disclosed differences')
paragraph('<b>IAG:</b> 4,611.67m issued shares less 241.65m treasury shares gives 4,370.02m external shares, using the latest located pre-cutoff disclosure. <b>Ryanair:</b>lease-inclusive debt less cash and term deposits gives EUR-2,621.6m, replacing rounded EUR-2,700m.')
paragraph('<b>Wizz Air:</b>explicit company-reported rolling EBITDA is EUR1,164.2m. The FY-minus-prior-quarter bridge gives EUR1,165.5m; the EUR1.3m difference remains flagged. <b>AF-KLM:</b>the revenue bridge gives EUR34,155m, but mixes original FY and IFRS18-restated interim comparatives; this remains provisional.')
heading('Enterprise-value bridge sensitivity')
expanded=pd.read_csv(root/'outputs/expanded_bridge_sensitivity.csv')
rows=[['EV/EBITDA set','Baseline midpoint','Expanded bridge midpoint']]
for _,r in eb.iterrows():
 er=expanded[(expanded['group']==r['group'])&(expanded.metric=='EBITDA')].iloc[0]
 rows.append([r['group'],f'EUR {r["median"]:.2f}',f'EUR {er["median"]:.2f}'])
table(rows,[190,150,175])
paragraph('Expanded scenario adds Lufthansa net pensions 1,585 and minorities 65; AF-KLM parent perpetuals 1,268 and NCI 2,136; IAG NCI 6 (EURm). The corresponding Lufthansa claims are also subtracted in the EV-to-equity conversion. These are book proxies, not fully harmonized fair-value adjustments. AF-KLM NCI already includes subsidiary perpetuals. June balances may be changed by subsequent redemptions.',small)
heading('What must be explained in an interview')
paragraph('Why the core group is limited to two peers; how EBITDA adjustments affect comparisons; why leasing and treasury shares matter; and why the reported-net-debt baseline is incomplete. Additional diligence remains on share-count timing, AF-KLM restatement, easyJet\'s newer trading update and offer effects, pensions, hybrids and non-operating investments.')
c.showPage();header(3,'Source register | Reports published before the valuation date')
paragraph('Full URLs are clickable below. Input-level page locations, calculations and differences are recorded in the project\'s CSV files. PDF page numbers refer to physical PDF pages. Market-data responses and the exact unadjusted closes are saved separately.',small)
for i,(key,v) in enumerate(registry.items(),1):
 paragraph(f'<b>[{i}] {key}</b> | {v["publication_date"]}<br/><link href="{v["url"].replace("&","&amp;")}" color="#397f92">{v["title"]}</link>',small,6)
paragraph('<b>Market data:</b>Yahoo Finance chart endpoint; quote.close for each exchange listing and GBP/EUR on 9 September 2026. Retrieval occurs after the historical date. Point-in-time figures are reconstructed from dated public disclosures; exact daily share-count reconstruction is not claimed.',small)
c.save()
print('Built report and notebook',pdf)
