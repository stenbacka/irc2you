#!/usr/bin/env python

import logging, sys, os, tempfile, socket

log = logging.getLogger('notify')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


def main(*args):

    namedsocket = os.path.join(tempfile.gettempdir(), 'irc2you_socket');

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(namedsocket)

    s.send("<notification>"
           "  <sender>Tigge</sender>"
           "  <message>Message is fun stuff</message>"
           "  <channel>#channel</channel>"
           "  <away>false</away>"
           "  <attached>true</attached>"
           "  <context>"
           "    <context_item from='stenbacka' username='stenbacka@lol.se' "
           "timestamp='1314223685'/>"
           "    <context_item from='stenbacka' username='stenbacka@lol.se' "
           "timestamp='1314223610'/>"
           "  </context>"
           "</notification>");

    s.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(main(*sys.argv))
