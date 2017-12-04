import os
import sys
from pprint import pprint

# Setup environment for tests
thisdir = os.path.dirname(__file__)
pydir = os.path.join(thisdir, "../python")
sys.path.insert(0, pydir)
os.environ["DAS_SCHEMA_PATH"] = thisdir

# High level API tests
import DaS

print("=== Available schemas")
pprint(DaS.ListSchemas())

print("=== 'hud' schema module content")
pprint(filter(lambda x: not (x.startswith("__") and x.endswith("__")), dir(DaS.schema.hud)))

print("=== Read data...")
hud = DaS.Read("%s/test.hud" % thisdir, schema="hud.HUD")
DaS.PrettyPrint(hud)

print("=== Write data...")
DaS.Write(hud, "%s/out.hud" % thisdir)

print("=== Read written data...")
hud2 = DaS.Read("%s/out.hud" % thisdir, schema="hud.HUD")
DaS.PrettyPrint(hud2)

print("=== Comparison")
print(hud == hud2)
print("--- Changed some value")
hud2.text.elements[2].opacity = 0.5
print(hud == hud2)

print("=== Write data with errors...")
hud2.text.elements[2].align = ("top", "left")
try:
   DaS.Write(hud2, "%s/out2.hud" % thisdir)
except Exception, e:
   print(e)
   print("--- Fix invalid data and write")
   hud2.text.elements[2].align = ("left", "top")
   DaS.Write(hud2, "%s/out2.hud" % thisdir)
   print("--- Read and compare again")
   hud3 = DaS.Read("%s/out2.hud" % thisdir, schema="hud.HUD")
   print(hud2 == hud3)
