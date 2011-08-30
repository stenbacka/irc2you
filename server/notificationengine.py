import logging
import notificationenginemanager


log = logging.getLogger('notify')

def _parseParams(engine):
  log.debug("About to parse params")
  params = {}
  for param in engine.iterchildren():
    params[param.get("name")] = param.text
  log.debug("Parsed params. Got: " + str(params))
  return params

def _parseEngine(engine):
  t = engine.get("type")
  if not t: return None
  return notificationenginemanager.get(t)

def parse(notifier):
  engine = notifier.engine
  params = _parseParams(engine)
  return _parseEngine(engine),params
