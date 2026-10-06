from .generator import CATALOG
class Genealogy:
    def __init__(self):self.nodes={n:{'feature_name':n,'parents':[],'transformation':'original','deployment_status':'active','reuse_frequency':0,'performance_gain':0,'stability':1,'age':0} for n in ['x1','x2','x3']}
    def register(self,name,fp,status='Candidate'):
        _,cost,parents=CATALOG[name]
        if name not in self.nodes:self.nodes[name]={'feature_name':name,'parents':parents,'transformation':name,'created_during_drift':fp['id'],'fingerprint_id':fp['id'],'performance_gain':0,'deployment_status':status,'complexity':cost,'reuse_frequency':0,'stability':1,'age':0}
    def graph(self):
        import networkx as nx
        G=nx.DiGraph()
        for n,m in self.nodes.items():
            G.add_node(n,**m)
            for parent in m['parents']:G.add_edge(parent,n)
        return G
