class VersionRegistry:
    def __init__(self):self.versions=[{'id':'SEEF_v1','feature':'identity','params':None,'status':'active','step':0}]
    def deploy(self,feature,params,step,performance):
        self.versions[-1]['status']='stable'
        v={'id':f'SEEF_v{len(self.versions)+1}','feature':feature,'params':params,'step':step,'performance':performance,'status':'active'};self.versions.append(v);return v
    def rollback(self):
        if len(self.versions)<2:return None
        self.versions[-1]['status']='rolled back'
        prior=next((v for v in reversed(self.versions[:-1]) if v['status'] in ['stable','active']),self.versions[0]);prior['status']='active';return prior
