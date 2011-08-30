import os
import xml.dom.minidom

class Filter:

  def __init__(self,_include,_items):
    self.include = _include
    self.items = _items

  def match(self,msg):
    for i in self.items:
      if not i.match(msg):
        return False
    return True

def parseAll(xml):
  fs = Filter.parse(xml.getElementsByTagName("filters"))[0];
  return Filter(True, [UserFilterItem("alex")])



class FilterItem():
  def match(self,msg):
    return True


class UserFilterItem(FilterItem):
  
  def __init__(self,value):
    self.name = value

  def match(self,msg):
    return True
