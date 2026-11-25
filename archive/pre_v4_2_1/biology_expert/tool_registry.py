"""No command execution in the Agent action space."""
import time
class ToolRegistry:
 def __init__(self,state,max_calls=48):
  self.tools={};self.state=state;self.max_calls=max_calls;self.used=0
 def register(self,name,callback):
  if name in self.tools:raise ValueError('Duplicate tool')
  self.tools[name]=callback
 def invoke(self,name,arguments,goal,reason):
  if name not in self.tools:raise ValueError('Tool not on whitelist')
  if self.used>=self.max_calls:raise RuntimeError('Tool budget exhausted')
  self.used+=1;start=time.monotonic()
  self.state.log('tool_selected',goal=goal,available_tools=sorted(self.tools),selected_tool=name,reason=reason,input=arguments)
  try:
   out=self.tools[name](**arguments)
   self.state.log('tool_output',tool=name,output=out,elapsed_seconds=round(time.monotonic()-start,4))
   return out
  except Exception as exc:
   self.state.log('tool_error',tool=name,error_type=type(exc).__name__,error=str(exc)[:500])
   raise
