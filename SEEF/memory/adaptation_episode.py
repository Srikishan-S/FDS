from datetime import datetime,timezone

def episode(fp,names,selected,strategy,before,after,latency,complexity,stability,reward,step,reused):
    return {'fingerprint':fp,'fingerprint_vector':fp['fingerprint_vector'],'candidate_features':names,'selected_features':[selected],'adaptation_strategy':strategy,'performance_before':before,'performance_after':after,'performance_gain':after-before,'latency_cost':latency,'complexity_cost':complexity,'stability_score':stability,'reward':reward,'timestamp':datetime.now(timezone.utc).isoformat(),'step':step,'reused':reused}
