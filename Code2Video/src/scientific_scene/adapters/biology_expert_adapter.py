"""Contract-based adapter; no topic-specific scientific prompt."""
class BiologyExpertSceneAdapter:
 def __init__(self,agent,root):self.agent=agent;self.root=root
 def review_ir(self,graph,pack=None,contract=None,observations=None):
  if contract is None:raise ValueError('Frozen Scientific Contract is required')
  return self.agent.audit_contract(contract,graph,observations or {})
