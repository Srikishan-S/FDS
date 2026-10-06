import argparse,json
from pathlib import Path
from dataclasses import replace
import pandas as pd
import plotly.express as px
from config import Config
from stream.stream_manager import SEEF

def run_experiments(config=None,steps=14000,seeds=(42,)):
    base=config or Config();histories=[];summaries=[]
    arms={'A Static':dict(static=True,use_memory=False),'B Retraining':dict(retrain=True,use_memory=False),'C SEEF without EAM':dict(use_memory=False),'D SEEF with EAM':dict(use_memory=True),'E SEEF unconditioned':dict(use_memory=True,conditioned=False)}
    for seed in seeds:
        for name,options in arms.items():
            engine=SEEF(replace(base,seed=seed,memory_path=':memory:',**options));engine.advance(steps)
            for row in engine.history:histories.append(dict(row,approach=name,seed=seed,f1=row['SEEF']))
            tail=engine.history[-5:];summaries.append(dict(approach=name,seed=seed,last_f1=sum(h['SEEF'] for h in tail)/len(tail),**engine.summary()))
            engine.memory.close()
    return pd.DataFrame(histories),pd.DataFrame(summaries)

def main():
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=14000);p.add_argument('--seeds',type=int,nargs='+',default=[42]);p.add_argument('--output',default='results');a=p.parse_args();out=Path(a.output);out.mkdir(exist_ok=True)
    h,s=run_experiments(steps=a.steps,seeds=a.seeds);h.to_csv(out/'comparison.csv',index=False);s.to_csv(out/'summary.csv',index=False)
    px.line(h,x='step',y='f1',color='approach',line_dash='seed',title='SEEF measured prequential F1').write_html(out/'comparison.html',include_plotlyjs=True)
    d=s.groupby('approach').mean(numeric_only=True)
    benefit=float(d.loc['D SEEF with EAM','mean_f1']-d.loc['C SEEF without EAM','mean_f1'])
    (out/'memory_benefit.json').write_text(json.dumps({'mean_f1_difference_with_minus_without_EAM':benefit,'seeds':a.seeds,'steps':a.steps},indent=2));print(s.to_string(index=False));print('Measured memory benefit:',benefit)
if __name__=='__main__':main()
