import os
import xml.dom.minidom
import pattern
import notificationengine
import logging

log = logging.getLogger("notify")

class Notifier:

  def __init__(self,_engine,_engineParams,_patterns):
    self.engine = _engine
    self.engineParams = _engineParams
    self.patterns = _patterns

  def execute(self, msg):
    go = True
    log.debug("About to check patterns")
    if self.patterns:
      for p in self.patterns:
        if not p.match(msg): go = False
    failed=""
    if not go: failed = "not"
    log.debug("This notifier will " + failed + " execute")
    if go:
      log.debug("About to execute engine")
      if self.engine:
        self.engine.execute(msg,self.engineParams)
      else:
        log.warn("Could not send notification because engine is None. User: " + msg.user)

  
    
def parse(notifier):
  fs = pattern.parseAll(notifier)
  e, ep = notificationengine.parse(notifier)
  return Notifier(e,ep,fs)
