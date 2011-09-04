import logging 
import configmanager

#import amazon_ses

log = logging.getLogger("notify")

class notificationengine:

  def execute(self,msg,params):
    if msg == None:
      s = "--"
    else:
      s = msg
    print "Would send msg if I were a concreate class " + msg.message
    return True

class EmailNotificationEngine (notificationengine):

  def __init__(self):
    pass

  def execute(self,msg,params):
#    try:
      #amazonSes = amazon_ses.AmazonSES(AWSAccessKeyId, AWSSecretKey)

      if params['subject']:
        subject = params['subject']
        log.debug(subject + "   " + str(type(subject)))
        log.debug(msg.message + "   " + str(type(msg.message)))
        subject = subject.replace('%m', str(msg.message)).replace("%c", str(msg.channel)).replace("%s", str(msg.sender))
      else:
        subject = "You got Mail!"

      if params['body']:
        body = params['body'].replace('%m', str(msg.message)).replace("%c", str(msg.channel)).replace("%s", str(msg.sender))
      else:
        body = msg.message.text

      #emailmessage = amazon_ses.EmailMessage()
      #emailmessage.subject = unicode(subject, "UTF-8")
      #emailmessage.bodyText = body.encode("UTF-8")

      #amazonSes.sendEmail('Jag och mitt moln <admin@cloud.tigge.org>',
      #        params["address"], emailmessage    )
      log.debug("Subject: " + subject)
      log.debug("Body: " + body)
      return True
#    except amazon_ses.AmazonError as e:
#        log.error("Could not send mail. Type: " + e.errorType + ", code: " + e.code + ", message:" + e.message)
#        return False



class andoidnotificationengine(notificationengine):
  
  def __init__(self):
    pass

  def execute(self,msg,params):
    log.error("Tried to send android notification while the engine was not implemented")
    print "I would send the message " + msg.message + " if I was implemented"
    return True


class EchoNotificationEngine(notificationengine):
  def __init__(self):
    pass

  def execute(self,msg,params):
    if 'echoer' in params:
      conf = configmanager.configManager.getConfig(params['echoer'])
      if conf:
        if conf.messageQueue:
          log.info("EchoNotifier: sending message")
          conf.messageQueue.put(dict({'channel':msg.channel,'message':msg.message.text}))
          return True
        else:
          return False
          log.error("EchoEngine could not find message queue for " + params['echoer'])
      else:
        return False
        log.error("EchoEngine could not find config for " + params['echoer'])
    else:
      log.error("EchoEngine is missing param: echoer")
      return False



class LogNotificationEngine(notificationengine):
  def __init__(self):
    pass

  def execute(self,msg,params):
    if params['body']:
      body = params['body'].replace('%m', str(msg.message)).replace("%c", str(msg.channel)).replace("%s", str(msg.sender))
    else:
      body = msg.message.text
    log.info("LogEngine -- Message:" + body)
    return True

emailEngine = EmailNotificationEngine()
androidEngine = andoidnotificationengine()
logEngine = LogNotificationEngine()
echoEngine = EchoNotificationEngine()

def get(engineName):
  if engineName == "email":
    return emailEngine
  elif engineName == "android":
    return androidEngine
  elif engineName == "log":
    return logEngine
  elif engineName == "echo":
    return echoEngine
  else:
    return None


