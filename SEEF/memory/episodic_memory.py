import json,sqlite3
from .similarity import cosine
class EpisodicMemory:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY, body TEXT NOT NULL)')
    def all(self):
        return [dict(json.loads(b),id=f'E{i:03d}') for i,b in self.db.execute('SELECT id,body FROM episodes ORDER BY id')]
    def add(self,episode):
        self.db.execute('INSERT INTO episodes(body) VALUES (?)',(json.dumps(episode),));self.db.commit()
    def query(self,vector,k=3):
        return sorted([(e,cosine(vector,e['fingerprint_vector'])) for e in self.all() if e['performance_gain']>0],key=lambda e:-e[1])[:k]
    def close(self):self.db.close()
