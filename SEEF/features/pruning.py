def prune(genealogy,active):
    for name,node in genealogy.nodes.items():
        if not node['parents']:continue
        node['age']+=1
        node['survival_score']=node['performance_gain']+node['stability']*.15+node['reuse_frequency']*.05-node.get('complexity',1)*.02
        if name!=active and node['age']>20 and node['survival_score']<.18:node['deployment_status']='Pruned'
        elif name!=active and node['deployment_status'] in ['Active','Stable']:node['deployment_status']='Dormant'
