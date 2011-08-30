#!/usr/bin/env python

import os
import sys
import notifier
import logging
from lxml import etree
from lxml import objectify

def initParser(schemaFile):
  if not os.path.exists(schemaFile):
    log.error("Could not find schema. There should be a file named '"+schemaFile+"' in the script directory")
    sys.exit(1)
  try:
    messageSchema = etree.XMLSchema(file=open(schemaFile, "r"))
    return objectify.makeparser(schema = messageSchema)
  except etree.XMLSyntaxError as error:
    log.error("Could not parse schema. Message: " + error.msg + ", File: " + schemaFile)
    sys.exit(1)

log = logging.getLogger('notify')
configParser = initParser("resources/irc2you_config.xsd");

class ConfigManager:

  def __init__(self):
    self.configs = {}; 

  def parseNotifier(self, xml):
    return notifier.parse(xml)

  def retrieveConfig(self, userName):
    confPath = '/home/' + userName + '/.irssi/irssi2you_config.xml'
    if (not os.path.exists(confPath)):
      log.error("Missing config file for user: " + userName)
      return None,0

    confFile = open(confPath, 'r')
    try:
      conf = objectify.parse(confFile, parser=configParser)

      log.debug("Parsing " + str(conf.getroot().countchildren()) + " notifiers")
      notifiers = []
      for notifier in conf.getroot().iterchildren():
        n = self.parseNotifier(notifier)
        if n:
          notifiers.append(n)
      return Config(notifiers),os.stat(confPath).st_mtime
    except etree.XMLSyntaxError as element:
      log.warn("Failed to parse config. Message: " + element.msg + ", User: " + userName)
      return None,0

  def configChanged(self,userName,modtime):
    confPath = '/home/' + userName + '/.irssi/irssi2you_config.xml'
    if (not os.path.exists(confPath)):
      log.error("Missing config file in configChanged, for user: " + userName)
      return False
    stat = os.stat(confPath)
    if stat.st_mtime != modtime:
      log.debug("Modtime: " + str(modtime) + " stat:" + str(stat.st_mtime))
      return True
    else:
      return False

  def getConfig(self, userName):
    log.debug("Getting config for " + userName)
    if userName in self.configs:
      log.debug("Had cached config for " + userName)
      c,m = self.configs[userName];
      if self.configChanged(userName,m):
        log.debug("Cached config changed for " + userName)
        c,m = self.retrieveConfig(userName)
        if c is not None:
          self.configs[userName] = c,m;
        else:
          del self.configs[userName]
    else:
      log.debug("No cached config for " + userName)
      c,m = self.retrieveConfig(userName)
      if c is not None:
        log.debug("Caching config for " + userName)
        self.configs[userName] = c,m;
      
    return c

    


class Config:
  def __init__(self,_notifiers):
    self.notifiers = _notifiers

#conf = ConfigManager().getConfig('erik')
#for n in conf.notifiers:
#  n.execute("<doc><user>Tigge</user><message>Tigger: Hej hopp</message></doc>")
