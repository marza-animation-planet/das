import re
import das
import imp


class ValidationError(Exception):
   def __init__(self, msg):
      super(ValidationError, self).__init__(msg)


class TypeValidator(object):
   def __init__(self, default=None):
      super(TypeValidator, self).__init__()
      self.default_validated = False
      self.default = default

   def validate(self, value, key=None, index=None):
      mixins = (None if not das.has_bound_mixins(value) else das.get_bound_mixins(value))
      rv = self._validate(value, key=key, index=index)
      if mixins is not None:
         # Re-bind the same mixins that were found on original value
         das.mixin.bind(mixins, rv, reset=True)
      elif key is None and index is None and not das.has_bound_mixins(rv):
         # Bind registered mixins for return value type if nothing bound yet
         mixins = das.get_registered_mixins(das.get_schema_type_name(self))
         if mixins:
            das.mixin.bind(mixins, rv)
      return rv

   def _validate_self(self, value):
      raise ValidationError("'_validate_self' method is not implemented")

   def _validate(self, value, key=None, index=None):
      raise ValidationError("'_validate' method is not implemented")

   def make_default(self):
      if not self.default_validated:
         self.default = self.validate(self.default)
         self.default_validated = True
      return das.copy(self.default)

   def make(self, *args, **kwargs):
      return self._validate(args[0])

   def __str__(self):
      return self.__repr__()


class Boolean(TypeValidator):
   def __init__(self, default=None):
      super(Boolean, self).__init__(default=(False if default is None else default))

   def _validate_self(self, value):
      if not isinstance(value, bool):
         raise ValidationError("Expected a boolean value, got %s" % type(value).__name__)
      return value

   def _validate(self, value, key=None, index=None):
      return self._validate_self(value)

   def __repr__(self):
      s = "Boolean(";
      if self.default is not None:
         s += "default=%s" % self.default
      return s + ")"


class Integer(TypeValidator):
   def __init__(self, default=None, min=None, max=None, enum=None):
      super(Integer, self).__init__(default=(0 if default is None else default))
      self.min = min
      self.max = max
      self.enum = enum
      if self.enum is not None:
         self.enumvals = set(self.enum.values())

   def _validate_self(self, value):
      if self.enum is not None:
         if isinstance(value, basestring):
            if not value in self.enum:
               raise ValidationError("Expected a enumeration string in %s, got '%s'" % (self.enum.keys(), value))
            else:
               value = self.enum[value]
         elif isinstance(value, (int, long)):
            if not value in self.enumvals:
               raise ValidationError("Expected a enumeration value (string or integer) in %s, got %s" % (self.enum, value))
      if not isinstance(value, (int, long)):
         raise ValidationError("Expected an integer value, got %s" % type(value).__name__)
      if self.enum is None:
         if self.min is not None and value < self.min:
            raise ValidationError("Integer value out of range, %d < %d" % (value, self.min))
         if self.max is not None and value > self.max:
            raise ValidationError("Integer value out of range, %d > %d" % (value, self.max))
      return long(value)

   def _validate(self, value, key=None, index=None):
      return self._validate_self(value)

   def __repr__(self):
      s = "Integer(";
      sep = ""
      if self.default is not None:
         s += "default=%s" % self.default
         sep = ", "
      if self.min is not None:
         s += "%smin=%d" % (sep, self.min)
         sep = ", "
      if self.max is not None:
         s += "%smax=%d" % (sep, self.max)
         sep = ", "
      if self.enum is not None:
         s += "%senum={%s}" % (sep, ", ".join(map(lambda x: "'%s': %s" % x, self.enum.items())))
      return s + ")"


class Real(TypeValidator):
   def __init__(self, default=None, min=None, max=None):
      super(Real, self).__init__(default=(0.0 if default is None else default))
      self.min = min
      self.max = max

   def _validate_self(self, value):
      if not isinstance(value, (int, long, float)):
         raise ValidationError("Expected a real value, got %s" % type(value).__name__)
      if self.min is not None and value < self.min:
         raise ValidationError("Real value out of range, %d < %d" % (value, self.min))
      if self.max is not None and value > self.max:
         raise ValidationError("Real value out of range, %d < %d" % (value, self.min))
      return float(value)

   def _validate(self, value, key=None, index=None):
      return self._validate_self(value)

   def __repr__(self):
      s = "Real(";
      sep = ""
      if self.default is not None:
         s += "default=%s" % self.default
         sep = ", "
      if self.min is not None:
         s += "%smin=%d" % (sep, self.min)
         sep = ", "
      if self.max is not None:
         s += "%smax=%d" % (sep, self.max)
      return s + ")"


class String(TypeValidator):
   def __init__(self, default=None, choices=None, matches=None, strict=True):
      super(String, self).__init__(default=("" if default is None else default))
      self.choices = choices
      self.strict = strict
      self.matches = None
      if choices is None and matches is not None:
         if type(matches) in (str, unicode):
            self.matches = re.compile(matches)
         else:
            self.matches = matches

   def _validate_self(self, value):
      if not isinstance(value, (str, unicode)):
         raise ValidationError("Expected a string value, got %s" % type(value).__name__)
      if self.choices is not None and self.strict:
         if callable(self.choices):
            valid = (value in self.choices())
         else:
            valid = (value in self.choices)
         if not valid:
            choices = (self.choices if not callable(self.choices) else self.choices())
            raise ValidationError("String value must be on of %s, got '%s'" % (choices, value))
      if self.matches is not None and not self.matches.match(value):
         raise ValidationError("String value '%s' doesn't match pattern '%s'" % (value, self.matches.pattern))
      return str(value)

   def _validate(self, value, key=None, index=None):
      return self._validate_self(value)

   def __repr__(self):
      s = "String(";
      sep = ""
      if self.default is not None and self.default != "":
         s += "default='%s'" % self.default
         sep = ", "
      if self.choices is not None:
         if callable(self.choices):
            if self.choices.__module__ != "__main__":
               s += "%schoices=%s" % (sep, self.choices.__name__)
            else:
               s += "%schoices=%s.%s" % (sep, self.choices.__module__, self.choices.__name__)
         else:
            s += "%schoices=[" % sep
            sep = ""
            for c in self.choices:
               s += "%s'%s'" % (sep, c)
               sep = ", "
            s += "]"
         s += ", strict=%s" % self.strict
         sep = ", "
      if self.matches is not None:
         s += ", matches='%s'" % (sep, self.matches)
      return s + ")"


class Sequence(TypeValidator):
   def __init__(self, type, default=None, size=None, min_size=None, max_size=None):
      super(Sequence, self).__init__(default=([] if default is None else default))
      self.size = size
      self.min_size = min_size
      self.max_size = max_size
      self.type = type

   def _validate_self(self, value):
      if not isinstance(value, (tuple, list, set)):
         raise ValidationError("Expected a sequence value, got %s" % type(value).__name__)
      n = len(value)
      if self.size is not None:
         if n != self.size:
            raise ValidationError("Expected a sequence of fixed size %d, got %d" % (self.size, n))
      else:
         if self.min_size is not None and n < self.min_size:
            raise ValidationError("Expected a sequence of minimum size %d, got %d" % (self.min_size, n))
         if self.max_size is not None and n > self.max_size:
            raise ValidationError("Expected a sequence of maximum size %d, got %d" % (self.max_size, n))
      return value

   def _validate(self, value, key=None, index=None):
      if index is not None:
         return self.type.validate(value)
      else:
         self._validate_self(value)
         n = len(value)
         tmp = [None] * n
         for index, item in enumerate(value):
            try:
               tmp[index] = self.type.validate(item)
            except ValidationError, e:
               raise ValidationError("Invalid sequence element: %s" % e)
         rv = das.types.Sequence(tmp)
         rv._set_schema_type(self)
         return rv

   def make(self, *args, **kwargs):
      return self._validate(args)

   def __repr__(self):
      s = "Sequence(type=%s" % self.type
      sep = ", "
      if self.default is not None:
         s += "%sdefault=%s" % (sep, self.default)
      if self.size is not None:
         s += "%ssize=%d" % (sep, self.size)
      else:
         if self.min_size is not None:
            s += "%smin_size=%d" % (sep, self.min_size)
         if self.max_size is not None:
            s += "%smax_size=%d" % (sep, self.max_size)
      return s + ")"


class Tuple(TypeValidator):
   def __init__(self, *args, **kwargs):
      super(Tuple, self).__init__(default=kwargs.get("default", None))
      self.types = args

   def _validate_self(self, value):
      if not isinstance(value, (list, tuple)):
         raise ValidationError("Expected a tuple value, got %s" % type(value).__name__)
      n = len(value)
      if n != len(self.types):
         raise ValidationError("Expected a tuple of size %d, got %d", (len(self.types), n))
      return value

   def _validate(self, value, key=None, index=None):
      if index is not None:
         return self.types[index].validate(value)
      else:
         self._validate_self(value)
         n = len(value)
         tmp = [None] * n
         for i in xrange(n):
            try:
               tmp[i] = self.types[i].validate(value[i])
            except ValidationError, e:
               raise ValidationError("Invalid tuple element: %s" % e)
         rv = das.types.Sequence(tmp)
         rv._set_schema_type(self)
         return rv

   def make_default(self):
      if not self.default_validated and self.default is None:
         self.default = tuple([t.make_default() for t in self.types])
      return super(Tuple, self).make_default()

   def make(self, *args, **kwargs):
      return self._validate(args)

   def __repr__(self):
      s = "Tuple("
      sep = ""
      for t in self.types:
         s += "%s%s" % (sep, t)
         sep = ", "
      if self.default is not None:
         s += "%sdefault=%s" % (sep, self.default)
      return s + ")"


class Struct(dict, TypeValidator):
   def __init__(self, **kwargs):
      hasdefault = ("default" in kwargs)
      default = None
      if hasdefault:
         default = kwargs["default"]
         print("[das] 'default' treated as a standard field for Struct type")
         del(kwargs["default"])
      TypeValidator.__init__(self)
      if hasdefault:
         kwargs["default"] = default
      dict.__init__(self, **kwargs)

   def _validate_self(self, value):
      if not isinstance(value, (dict, das.types.Struct)):
         raise ValidationError("Expected a dict value, got %s" % type(value).__name__)
      for k, v in self.iteritems():
         if not k in value and not isinstance(v, Optional):
            raise ValidationError("Missing key '%s'" % k)
      return value

   def _validate(self, value, key=None, index=None):
      if key is not None:
         vtype = self.get(key, None)
         if vtype is None:
            # return das.adapt_value(value)
            raise ValidationError("Invalid key '%s'" % key)
         else:
            vv = self[key].validate(value)
            if vv is not None and isinstance(vtype, Deprecated):
               das.print_once(vtype.message) 
            return vv
      else:
         self._validate_self(value)
         rv = das.types.Struct()
         # don't set schema type just yet
         for k, v in self.iteritems():
            try:
               vv = v.validate(value[k])
               if vv is not None and isinstance(v, Deprecated):
                  das.print_once(v.message)
               rv[k] = vv
            except KeyError, e:
               if not isinstance(v, Optional):
                  raise ValidationError("Invalid value for key '%s': %s" % (k, e))
            except ValidationError, e:
               raise ValidationError("Invalid value for key '%s': %s" % (k, e))
         rv._set_schema_type(self)
         return rv

   def make_default(self):
      if not self.default_validated and self.default is None:
         self.default = das.types.Struct()
         for k, t in self.iteritems():
            if isinstance(t, Optional):
               continue
            self.default[k] = t.make_default()
         self.default._set_schema_type(self)
      return super(Struct, self).make_default()

   def make(self, *args, **kwargs):
      rv = self.make_default()
      for k, v in kwargs.iteritems():
         setattr(rv, k, v)
      return rv

   def __hash__(self):
      return object.__hash__(self)

   def __repr__(self):
      s = "Struct("
      sep = ""
      keys = [k for k in self]
      keys.sort()
      for k in keys:
         v = self[k]
         s += "%s%s=%s" % (sep, k, v)
         sep = ", "
      return s + ")"


class StaticDict(Struct):
   def __init__(self, **kwargs):
      super(StaticDict, self).__init__(**kwargs)
      das.print_once("[das] Schema type 'StaticDict' is deprecated, use 'Struct' instead")


class Dict(TypeValidator):
   def __init__(self, ktype, vtype, default=None, **kwargs):
      super(Dict, self).__init__(default=({} if default is None else default))
      self.ktype = ktype
      self.vtype = vtype
      self.vtypeOverrides = {}
      for k, v in kwargs.iteritems():
         self.vtypeOverrides[k] = v

   def _validate_self(self, value):
      if not isinstance(value, (dict, das.types.Struct)):
         raise ValidationError("Expected a dict value, got %s" % type(value).__name__)
      return value

   def _validate(self, value, key=None, index=None):
      if key is not None:
         sk = str(key)
         return self.vtypeOverrides.get(sk, self.vtype).validate(value)
      else:
         self._validate_self(value)
         rv = das.types.Dict()
         for k in value:
            try:
               ak = self.ktype.validate(k)
            except ValidationError, e:
               raise ValidationError("Invalid key value '%s': %s" % (k, e))
            try:
               sk = str(ak)
               rv[ak] = self.vtypeOverrides.get(sk, self.vtype).validate(value[k])
            except ValidationError, e:
               raise ValidationError("Invalid value for key '%s': %s" % (k, e))
         rv._set_schema_type(self)
         return rv

   def make(self, *args, **kwargs):
      return self._validate(kwargs)

   def __repr__(self):
      s = "Dict(ktype=%s, vtype=%s" % (self.ktype, self.vtype)
      if self.default is not None:
         s += ", default=%s" % self.default
      for k, v in self.vtypeOverrides.iteritems():
         s += ", %s=%s" % (k, v)
      return s + ")"


class DynamicDict(Dict):
   def __init__(self, ktype, vtype, default=None, **kwargs):
      super(DynamicDict, self).__init__(ktype, vtype, default=default, **kwargs)
      das.print_once("[das] Schema type 'DynamicDict' is deprecated, use 'Dict' instead")


class Class(TypeValidator):
   def __init__(self, klass, default=None):
      if not isinstance(klass, (str, unicode)):
         self.klass = self._validate_class(klass)
      else:
         self.klass = self._class(klass)
      super(Class, self).__init__(default=(self.klass() if default is None else default))

   def _validate_class(self, c):
      if not hasattr(c, "copy"):
         raise Exception("Schema class '%s' has no 'copy' method" % c.__name__)
      try:
         c()
      except:
         raise Exception("Schema class '%s' constructor cannot be used without arguments" % c.__name__)
      return c

   def _class(self, class_name):
      c = None
      for i in class_name.split("."):
         if c is None:
            g = globals()
            if not i in g:
               c = imp.load_module(i, *imp.find_module(i))
            else:
               c = globals()[i]
         else:
            c = getattr(c, i)
      return self._validate_class(c)

   def _validate_self(self, value):
      if not isinstance(value, self.klass):
         raise ValidationError("Expected a %s value, got %s" % (self.klass.__name__, type(value).__name__))
      return value

   def _validate(self, value, key=None, index=None):
      return self._validate_self(value)

   def __repr__(self):
      cmod = self.klass.__module__
      if cmod != "__main__":
         cmod += "."
      else:
         cmod = ""
      return "Class(\"%s.%s\")" % (cmod, self.klass.__name__)


class Or(TypeValidator):
   def __init__(self, *types, **kwargs):
      super(Or, self).__init__(default=kwargs.get("default", None))
      if len(types) < 2:
         raise Exception("Schema type 'Or' requires at least two types") 
      self.types = types

   def _validate_self(self, value):
      for typ in self.types:
         try:
            return typ._validate_self(value)
         except ValidationError, e:
            continue
      raise ValidationError("Value of type %s doesn't match any of the allowed types" % type(value).__name__)
      return None

   def _validate(self, value, key=None, index=None):
      for typ in self.types:
         try:
            return typ.validate(value, key=key, index=index)
         except ValidationError, e:
            continue
      raise ValidationError("Value of type %s doesn't match any of the allowed types" % type(value).__name__)
      return None

   def make_default(self):
      if not self.default_validated and self.default is None:
         self.default = self.types[0].make_default()
      return super(Or, self).make_default()

   def make(self, *args, **kwargs):
      return self.types[0].make(*args, **kwargs)

   def __repr__(self):
      s = "Or(%s" % ", ".join(map(str, self.types))
      if self.default is not None:
         s += ", default=%s" % self.default
      return s + ")"


class Optional(TypeValidator):
   def __init__(self, type):
      super(Optional, self).__init__()
      self.type = type

   def _validate_self(self, value):
      return self.type._validate_self(value)

   def _validate(self, value, key=None, index=None):
      return self.type.validate(value, key=key, index=index)

   def make_default(self):
      return self.type.make_default()

   def make(self, *args, **kwargs):
      return self.type.make(*args, **kwargs)

   def __repr__(self):
      return "Optional(type=%s)" % self.type


class Deprecated(Optional):
   def __init__(self, type, message="[das] Deprecated"):
      super(Deprecated, self).__init__(type)
      self.message = message

   def _validate_self(self, value):
      if value is None:
         return True
      else:
         return super(Deprecated, self)._validate_self(value)

   def _validate(self, value, key=None, index=None):
      if value is None:
         return True
      else:
         return super(Deprecated, self)._validate(value, key=key, index=index)

   def make_default(self):
      return None

   def __repr__(self):
      return "Deprecated(type=%s)" % self.type


class Empty(TypeValidator):
   def __init__(self):
      super(Empty, self).__init__()

   def _validate_self(self, value):
      if value is not None:
         raise ValidationError("Expected None, got %s" % type(value).__name__)
      return value

   def _validate(self, value, key=None, index=None):
      return self._validate_self(value)

   def make_default(self):
      return None

   def __repr__(self):
      return "Empty()"


class SchemaType(TypeValidator):
   CurrentSchema = ""

   def __init__(self, name, default=None):
      super(SchemaType, self).__init__(default=default)
      if not "." in name:
         self.name = self.CurrentSchema + "." + name
      else:
         self.name = name

   def _validate_self(self, value):
      st = das.get_schema_type(self.name)
      return st._validate_self(value)

   def _validate(self, value, key=None, index=None):
      st = das.get_schema_type(self.name)
      return st.validate(value, key=key, index=index)

   def make_default(self):
      if not self.default_validated and self.default is None:
         st = das.get_schema_type(self.name)
         self.default = st.make_default()
      return super(SchemaType, self).make_default()

   def make(self, *args, **kwargs):
      st = das.get_schema_type(self.name)
      return st.make(*args, **kwargs)

   def __repr__(self):
      s = "SchemaType('%s'" % self.name
      if self.default is not None:
         s += ", default=%s" % str(self.default)
      return s + ")"
