
__all__ = ["Attribute", "attribute"]

class Attribute(object):
   def __init__(self, attr):
      super(Attribute, self).__init__()
      self.attr = attr

   def __str__(self):
      return "attribute('%s')" % self.attr

   def __repr__(self):
      return "attribute('%s')" % self.attr

   def __cmp__(self, oth):
      s0 = str(self)
      s1 = str(oth)
      return (-1 if (s0 < s1) else (0 if (s0 == s1) else 1))


def attribute(value):
   return Attribute(value)
