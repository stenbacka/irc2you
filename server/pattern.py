import os
import logging
from lxml import objectify

log = logging.getLogger("notify")

class Pattern:

  def __init__(self,_include,_items):
    self.include = _include
    self.items = _items

  def __repr__(self):
    val = "Pattern: [" + str(self.include) + "]"
    for pi in self.items:
      val += " " + str(pi)
    return val

  def match(self,msg):
    for i in self.items:
      log.debug("Matching on " + i.__class__.__name__ + " with include: " + str(self.include))
      mat = i.match(msg)
      if self.include:
        if not mat:
          return False
      else:
        log.debug("eclude filter")
        if mat:
          log.debug("mat " + str(mat))
          return False
    return True

def parseAll(notifier):
  if not objectify.ObjectPath("notifier.patterns").hasattr(notifier) or notifier.patterns.countchildren() == 0: return []

  log.debug('About to parse ' + str(notifier.patterns.countchildren()) + ' patterns')
  ps = []
  for pattern in notifier.patterns.iterchildren():
    incl = pattern.get("type")
    if incl == "include":
      i = True
    else:
      i = False
    log.debug('About to parse pattern items with include: ' + str(i))
    cs = []
    for x in pattern.iterchildren():
      pi = parsePatternItem(x)
      if pi:
        cs.append(pi)
    ps.append(Pattern(i,cs))

  log.debug("parseAll returns " + str(ps))
  return ps

def parsePatternItem(patternItem):
  log.debug("parsePatternItem: " + str(patternItem.tag))
  if patternItem.tag == "sender":
    return UserPatternItem(patternItem.text)
  elif patternItem.tag == "channel":
    return ChannelPatternItem(patternItem.text)
  elif patternItem.tag == "away":
    return AwayPatternItem(patternItem.text)
  elif patternItem.tag == "attached":
    return AttachedPatternItem(patternItem.text)
  else:
    log.warning("Failed to parse pattern item with tag: " + patternItem.tag)
    return None


class PatternItem():
  def __init__(self,val):
    self.value = val
  def match(self,msg):
    return True
  def __repr__(self):
    return self.__class__.__name__ + ": " + self.value


class UserPatternItem(PatternItem):
  def match(self,msg):
    log.debug("Comparing " + msg['sender'] + " and " + self.value + " is " + str(msg.sender.text.strip() == self.value.strip()))
    return msg.sender.text.strip() == self.value.strip()

class ChannelPatternItem(PatternItem):
  def match(self,msg):
    log.debug("Comparing " + msg['channel'] + " and " + self.value + " is " + str(msg.channel.text.strip() == self.value.strip()))
    return msg.channel.text.strip() == self.value.strip()

class AwayPatternItem(PatternItem):
  def match(self,msg):
    log.debug("Comparing " + msg.away + " and " + str(self.value) + " is " + str(msg.away == str(self.value)))
    return msg.away.text == str(self.value)

class AttachedPatternItem(PatternItem):
  def match(self,msg):
    log.debug("Comparing " + msg.away + " and " + str(self.value) + " is " + str(msg.away == str(self.value)))
    return msg.away.text == str(self.value)

'''
<notifier>
    <module type="email">
      <param name="address">john.doe@gmail.com</param>
      <param name="mode">daily-summary</param>
    </module>
    <patterns>
      <pattern type="include">
        <channel>#it06</channel> 
      </pattern>
      <pattern type="exclude">
        <user>alex</user> 
      </pattern>
    </patterns>
  </notifier>
'''
