import os
import sys
import imp
import glob


ReservedNames = set(['_is_reserved',
                     '_adapt_value',
                     '_update',
                     '_has_key',
                     '_get',
                     '_keys',
                     '_iterkeys',
                     '_values',
                     '_itervalues',
                     '_items',
                     '_iteritems',
                     '_pop',
                     '_popitem',
                     '_clear',
                     '_copy',
                     '_setdefault',
                     '_validate'])

ExceptOnReservedNameUsage = True


class ReservedNameError(Exception):
   def __init__(self, name):
      super(ReservedNameError, self).__init__("'%s' is a reserved name" % name)

class DaS(object):
   def __init__(self, *args, **kwargs):
      super(DaS, self).__init__()
      self.__dict__["_dict"] = {}
      self.__dict__["_schema"] = None
      self._update(*args, **kwargs)

   def __getattr__(self, k):
      try:
         return self._dict[k]
      except KeyError:
         raise AttributeError("'DaS' has not attribute '%s'" % k)

   def __setattr__(self, k, v):
      if not self._is_reserved(k):
         self._dict[k] = v

   def __delattr__(self, k):
      del(self._dict[k])

   def __getitem__(self, k):
      return self._dict.__getitem__(k)

   def __setitem__(self, k, v):
      if not self._is_reserved(k):
         self._dict.__setitem__(k, v)

   def __delitem__(self, k):
      return self._dict.__delitem__(k)

   def __contains__(self, k):
      return self._dict.__contains__(k)

   def __cmp__(self, oth):
      return self._dict.__cmp__(oth._dict if isinstance(oth, DaS) else oth)

   def __eq__(self, oth):
      return self._dict.__eq__(oth._dict if isinstance(oth, DaS) else oth)

   def __ge__(self, oth):
      return self._dict.__ge__(oth._dict if isinstance(oth, DaS) else oth)

   def __le__(self, oth):
      return self._dict.__le__(oth._dict if isinstance(oth, DaS) else oth)

   def __gt__(self, oth):
      return self._dict.__gt__(oth._dict if isinstance(oth, DaS) else oth)

   def __lt__(self, oth):
      return self._dict.__lt__(oth._dict if isinstance(oth, DaS) else oth)

   def __iter__(self):
      return self._dict.__iter__()

   def __len__(self):
      return self._dict.__len__()

   def __str__(self):
      return self._dict.__str__()

   def __repr__(self):
      return self._dict.__repr__()

   def _has_key(self, k):
      return self._dict.has_key(k)

   def _get(self, k, default=None):
      return self._dict.get(k, default)

   def _keys(self):
      return self._dict.keys()

   def _iterkeys(self):
      return self._dict.iterkeys()

   def _values(self):
      return self._dict.values()

   def _itervalues(self):
      return self._dict.itervalues()

   def _items(self):
      return self._dict.items()

   def _iteritems(self):
      return self._dict.iteritems()

   def _pop(self, *args):
      return self._dict.pop(*args)

   def _popitem(self):
      return self._dict.popitem()

   def _clear(self):
      self._dict.clear()

   def _copy(self):
      return DaS(self._dict.copy())

   def _setdefault(self, *args):
      if len(args) >= 1:
         if self._is_reserved(args[0]):
            return
      if len(args) >= 2:
         args[1] = self._adapt_value(args[1])
      self._dict.setdefault(*args)

   def _update(self, *args, **kwargs):
      self._dict.update(*args, **kwargs)
      for k, v in self._dict.items():
         if not self._is_reserved(k):
            self._dict[k] = self._adapt_value(v)

   def _is_reserved(self, k):
      if k in ReservedNames:
         e = ReservedNameError(k)
         if ExceptOnReservedNameUsage:
            raise e
         else:
            print("[DaS] %s" % e)
            return True
      else:
         return False

   def _adapt_value(self, value):
      t = type(value)
      if t == dict:
         return DaS(**value)
      elif t in (list, set, tuple):
         n = len(value)
         l = [None] * n
         i = 0
         for item in value:
            l[i] = self._adapt_value(item)
            i += 1
         return t(l)
      else:
         return value

   def _validate(self, schema=None):
      if schema is None:
         schema = self.__dict__["_schema"]
      if schema is not None:
         schema._validate(self)
      self.__dict__["_schema"] = schema

# ---

def Copy(d, deep=True):
   if not deep:
      return d._copy()
   else:
      rv = DaS(d._dict)
      for k, v in rv._dict.items():
         if isinstance(v, DaS):
            rv._dict[k] = Copy(v, deep=True)
      return rv

def PrettyPrint(d, stream=None, indent="  ", depth=0, inline=False, eof=True):
   if stream is None:
      stream = sys.stdout

   tindent = indent * depth

   if not inline:
      stream.write(tindent)

   t = type(d)

   if t in (DaS, dict):
      stream.write("{\n")
      n = len(d)
      i = 0
      keys = [k for k in d]
      keys.sort()
      for k in keys:
         stream.write("%s%s'%s': " % (tindent, indent, k))
         v = d[k]
         PrettyPrint(v, stream, indent=indent, depth=depth+1, inline=True, eof=False)
         i += 1
         if i >= n:
            stream.write("\n")
         else:
            stream.write(",\n")
      stream.write("%s}" % tindent)

   elif t == list:
      stream.write("[\n")
      n = len(d)
      i = 0
      for v in d:
         PrettyPrint(v, stream, indent=indent, depth=depth+1, inline=False, eof=False)
         i += 1
         if i >= n:
            stream.write("\n")
         else:
            stream.write(",\n")
      stream.write("%s]" % tindent)

   elif t == set:
      stream.write("set([\n")
      n = len(d)
      i = 0
      for v in d:
         PrettyPrint(v, stream, indent=indent, depth=depth+1, inline=False, eof=False)
         i += 1
         if i >= n:
            stream.write("\n")
         else:
            stream.write(",\n")
      stream.write("%s])" % tindent)

   elif t in (str, unicode):
      stream.write("'%s'" % d)

   else:
      stream.write(str(d))

   if eof:
      stream.write("\n")

def Read(path, schema=None, **funcs):
   if schema is not None:
      sch = GetSchema(schema)
      mod = GetSchemaModule(schema)
      if mod is not None and hasattr(mod, "__all__"):
         for item in mod.__all__:
            funcs[item] = getattr(mod, item)
   else:
      sch, mod = None, None

   rv = DaS()
   with open(path, "r") as f:
      rv._update(**eval(f.read(), globals(), funcs))

   rv._validate(sch)

   return rv

def Write(d, path, indent="  "):
   # Validate before writing
   d._validate()
   with open(path, "w") as f:
      PrettyPrint(d, stream=f, indent=indent)


from . import schema
from .validation import LoadSchemas, ListSchemas, GetSchema, GetSchemaModule, Validate
