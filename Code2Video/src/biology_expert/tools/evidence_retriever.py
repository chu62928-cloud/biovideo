"""Legacy retrieval interface uses the generic planned-source retriever."""
from ..contract_builder import ScientificEvidenceRetriever
class EvidenceRetriever(ScientificEvidenceRetriever):
 def __init__(self,root,max_requests=24,timeout=18):super().__init__(root,max_requests)
 def retrieve(self,scope,plan=None):
  if plan is None:return {'evidence':[],'failures':[],'research_status':'RESEARCH_PLAN_REQUIRED','reason':'No fixed topic source catalogue is auto-loaded'}
  return super().retrieve(scope,plan)
 def fetch_source(self,url):return {'evidence':[self.fetch(url,'manual_source')],'failures':[]}
