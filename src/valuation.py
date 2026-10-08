"""Offline, auditable comparable-company valuation. All financial amounts in millions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATE='2026-09-09'
GROUP={'Lufthansa':'Network','Air France-KLM':'Network','IAG':'Network',
       'easyJet':'Low-cost','Ryanair':'Low-cost','Wizz Air':'Low-cost'}

def implied_price(multiple,metric,bridge,shares):
    if not np.isfinite([multiple,metric,bridge,shares]).all() or metric<=0 or shares<=0:
        raise ValueError('Non-finite input or non-positive denominator')
    return (multiple*metric-bridge)/shares

def load_data():
    data=ROOT/'data'
    registry=json.loads((data/'source_registry.json').read_text(encoding='utf-8'))
    assert all(v['publication_date']<=DATE for v in registry.values())
    financials=pd.read_csv(data/'companies.csv')
    bridges=pd.read_csv(data/'ltm_bridges.csv')
    market=pd.read_csv(data/'market_snapshot.csv')
    if market.ticker.duplicated().any() or financials.company.duplicated().any():
        raise ValueError('Duplicate company or market input')
    if not (market.date==DATE).all():raise ValueError('Market observation after/before valuation date')
    if not (financials.financial_date<=DATE).all() or not (financials.share_count_date<=DATE).all():
        raise ValueError('Look-ahead input')
    for _,b in bridges.iterrows():
        if b.source_fy not in registry or b.source_interim not in registry:raise ValueError('Missing source')
        if pd.notna(b.fy) and abs(b.fy-b.prior_comparable+b.current_comparable-b.calculated_ltm)>0.01:
            raise ValueError('LTM arithmetic mismatch')
    for metric in ['Revenue','EBITDA']:
        subset=bridges[bridges.metric==metric].copy()
        subset['value']=subset.reported_ltm.fillna(subset.calculated_ltm)
        financials=financials.merge(subset[['company','value']],on='company',validate='one_to_one').rename(columns={'value':metric})
    df=financials.merge(market[['ticker','close','currency']],on='ticker',validate='one_to_one')
    fx=float(market.loc[market.ticker=='GBPEUR=X','close'].iloc[0])
    # All GBP amounts translated at one spot rate. This preserves native-currency multiples.
    df['price_eur']=df.close*np.where(df.currency.isin(['GBp','GBX']),0.01,1)*np.where(df.currency.isin(['GBP','GBp','GBX']),fx,1)
    df['financial_fx']=np.where(df.financial_currency=='GBP',fx,1)
    for name in ['Revenue','EBITDA','net_debt']:df[name+'_eur']=df[name]*df.financial_fx
    df['equity_value']=df.price_eur*df.shares_m
    df['enterprise_value']=df.equity_value+df.net_debt_eur
    df['margin']=df.EBITDA_eur/df.Revenue_eur
    df['EV_Revenue']=df.enterprise_value/df.Revenue_eur
    df['EV_EBITDA']=df.enterprise_value/df.EBITDA_eur
    df['group']=df.company.map(GROUP)
    columns=['shares_m','price_eur','Revenue_eur','EBITDA_eur','net_debt_eur','enterprise_value']
    if not np.isfinite(df[columns]).all().all():raise ValueError('Missing/non-finite input')
    if (df[['shares_m','price_eur','Revenue_eur','EBITDA_eur']]<=0).any().any():raise ValueError('Non-positive denominator')
    return df,bridges,registry

def ranges(df,ev_column='enterprise_value',target_bridge=None):
    t=df.loc[df.company=='Lufthansa'].iloc[0]; peers=df[df.company!='Lufthansa'].copy()
    result=[]
    for label,selection in [('Network carriers',peers[peers.group=='Network']),('All peers',peers),('Low-cost carriers',peers[peers.group=='Low-cost'])]:
        for metric in ['Revenue','EBITDA']:
            mult=selection[ev_column]/selection[metric+'_eur']
            # A two-company group is too small for persuasive quartiles: show the observed min/max.
            lo,mid,hi=mult.min(),mult.median(),mult.max()
            kind='Observed min-max'
            if len(selection)>=3:
                lo,hi=mult.quantile(.25),mult.quantile(.75);kind='Peer 25th-75th percentile'
            bridge=t.net_debt_eur if target_bridge is None else target_bridge
            values=[implied_price(x,t[metric+'_eur'],bridge,t.shares_m) for x in [lo,mid,hi]]
            result.append(dict(group=label,metric=metric,n=len(selection),range_basis=kind,
                               low_multiple=lo,median_multiple=mid,high_multiple=hi,
                               low=values[0],median=values[1],high=values[2],change=values[1]/t.price_eur-1))
    return pd.DataFrame(result)

def draw_chart(result,price):
    colors={'Network carriers':'#173f59','All peers':'#397f92','Low-cost carriers':'#a3aab2'}
    fig,ax=plt.subplots(figsize=(10,5.3))
    for i,r in result.iterrows():
        color=colors[r['group']];ax.hlines(i,r.low,r.high,color=color,linewidth=8,alpha=.35)
        ax.scatter(r['median'],i,color=color,s=65,zorder=3)
        ax.annotate(f"EUR {r['median']:.2f}",(r['median'],i),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
    ax.axvline(price,ls='--',color='#bf6b39',label=f'Observed close: EUR {price:.2f}')
    ax.set_yticks(range(len(result)));ax.set_yticklabels([f"{r['group']} | EV/{r.metric} (n={r.n})" for _,r in result.iterrows()])
    ax.set_xlabel('Implied Lufthansa share price (EUR)');ax.invert_yaxis()
    ax.grid(axis='x',alpha=.15);ax.spines[['top','right','left']].set_visible(False)
    ax.legend(frameon=False,loc='upper right');fig.tight_layout()
    fig.savefig(ROOT/'outputs/football_field.png',dpi=220,bbox_inches='tight');plt.close(fig)

def main():
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    df,bridges,registry=load_data();t=df.loc[df.company=='Lufthansa'].iloc[0]
    result=ranges(df)
    df.to_csv(out/'comps_table.csv',index=False);result.to_csv(out/'valuation_ranges.csv',index=False)
    bridges.to_csv(out/'ltm_audit.csv',index=False)
    # Book-value bridge illustration; not a harmonized fair-value EV adjustment.
    alt=df.copy();adds={'Lufthansa':1585+65,'Air France-KLM':1268+2136,'IAG':6}
    alt['additional_claims']=alt.company.map(adds).fillna(0)
    alt['expanded_ev']=alt.enterprise_value+alt.additional_claims
    expanded=ranges(alt,'expanded_ev',t.net_debt_eur+1585+65)
    expanded.to_csv(out/'expanded_bridge_sensitivity.csv',index=False)
    loo=[]
    peers=df[df.company!='Lufthansa']
    for name in peers.company:
        subset=peers[peers.company!=name];multiple=subset.EV_EBITDA.median()
        loo.append(dict(excluded=name,n=len(subset),multiple=multiple,implied_price=implied_price(multiple,t.EBITDA_eur,t.net_debt_eur,t.shares_m)))
    pd.DataFrame(loo).to_csv(out/'leave_one_out.csv',index=False)
    sensitivities=[]
    for e in [.8,.9,1,1.1,1.2]:
        for m in [2,3,4,5,6]:
            sensitivities.append(dict(ebitda_factor=e,multiple=m,price=implied_price(m,t.EBITDA_eur*e,t.net_debt_eur,t.shares_m)))
    pd.DataFrame(sensitivities).to_csv(out/'ebitda_multiple_sensitivity.csv',index=False)
    ry=df.copy();ry.loc[ry.company=='Ryanair','EBITDA_eur']+=85
    ranges(ry).to_csv(out/'ryanair_exceptional_addback_sensitivity.csv',index=False)
    draw_chart(result,t.price_eur)
    summary=dict(valuation_date=DATE,observed_price=float(t.price_eur),results=result.to_dict('records'),
                 status='Educational reported-net-debt baseline; limitations in docs/METHODOLOGY.md',
                 validations='Finite inputs, positive denominators, LTM arithmetic, unique rows and source dates checked')
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(result[['group','metric','n','low','median','high']].round(2).to_string(index=False))
    return df,result

if __name__=='__main__':main()
