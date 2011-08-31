#!/usr/bin/env python

import logging

log = logging.getLogger('notify')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


import threading
import os
import sys
import tempfile
import SocketServer
import xml.dom.minidom
import configmanager
import struct
import socket
import pwd

from lxml import etree
from lxml import objectify
from configmanager import ConfigManager

def initParser(schemaFile):
  if not os.path.exists(schemaFile):
      log.error("Could not find schema for messages. There should be a "
                "file named '"+schemaFile+"' in the script directory")
      sys.exit(1)
  messageSchema = etree.XMLSchema(file=open(schemaFile, "r"))
  return objectify.makeparser(schema = messageSchema)

messageParser = initParser("resources/irc2you_message.xsd")
configManager = ConfigManager()



class MyHandler(SocketServer.StreamRequestHandler):

    def finish(self):
        log.debug("socket closed")
        pass

    def handle(self):
        while(True):
            log.debug("waiting for message")
            messageXML = self.request.makefile().readline()
            self.wfile.write(messageXML);
            log.debug("Message: " + messageXML)

            # Find username from unix socket
            pid, uid, gid = struct.unpack('3i', \
                    self.server.socket.getsockopt(socket.SOL_SOCKET, 17, \
                    struct.calcsize('3i')))
            username = pwd.getpwuid(uid).pw_name

            #log.debug("client: " + str(self.server.socket));
            log.debug("pid: " + str(pid) + " uid: " + str(uid) + " gid: " + str(gid));
            log.debug(pwd.getpwuid(uid))

            try:
                message = objectify.fromstring(messageXML, messageParser)

                conf = configManager.getConfig(username)
                if conf:
                    for n in conf.notifiers:
                        log.debug("Executing notifier")
                        n.execute(message)
            except etree.XMLSyntaxError as element:
                log.warn("Failed to parse message. Message: " + element.msg + \
                         ", XML: " + messageXML)

    #def setup(self, *args, **kwargs):
        #self.messageParser = self.initParser("irssi2you_message.xsd")
        #self.configManager = ConfigManager()
    #    SocketServer.StreamRequestHandler(self, *args, **kwargs)
    #    log.debug("set up socket")


def main(*args):
    class ThreadingUnixStreamServer(SocketServer.ThreadingMixIn, \
            SocketServer.UnixStreamServer): pass

    # Set named socket path and delete old socket, if any
    namedsocket = os.path.join(tempfile.gettempdir(), 'irc2you_socket');
    if(os.path.exists(namedsocket)):
        os.remove(namedsocket);

    server = SocketServer.UnixStreamServer(namedsocket, MyHandler)
    os.chmod(namedsocket, 0777);
    server.serve_forever()

    return 0

if __name__ == '__main__':
    sys.exit(main(*sys.argv))



