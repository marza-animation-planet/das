import os
import re
import sys
import glob
import unittest
import importlib.util
import importlib.machinery


if __name__ == "__main__":
   # Setup PYTHONPATH
   testdir = os.path.abspath(os.path.dirname(__file__))

   sys.path.append(testdir)
   sys.path.append(os.path.join(testdir, "../python"))

   os.chdir(testdir)

   suite = unittest.TestSuite()
   loader = unittest.TestLoader()

   runtests = []
   runfuncs = {}
   for runtest in sys.argv[1:]:
      spl = runtest.split(".")
      if len(spl) > 2:
         print("Ignore invalid test specification: %s" % runtest)
         continue
      elif len(spl) == 2:
         testname, funcname = spl
         if not testname in runtests:
            lst = runfuncs.get(testname, [])
            if not funcname in lst:
               lst.append(funcname)
            runfuncs[testname] = sorted(lst)
      else:
         testname = spl[0]
         if not testname in runtests:
            if testname in runfuncs:
               del(runfuncs[testname])
            runtests.append(testname)

   runall = (len(runtests) + len(runfuncs) == 0)

   # Get list of available tests
   tests = [x for x in glob.glob("./*") if os.path.isdir(x) and re.match(r"^test\d{3}$", os.path.basename(x)) and os.path.isfile(x+"/__init__.py")]
   for test in sorted(tests):
      name = os.path.basename(test)

      test_path = os.path.join(test, '__init__.py')
      if name in runfuncs:
         # specific functions
         try:
            file_loader = importlib.machinery.SourceFileLoader(name, test_path)
            spec = importlib.util.spec_from_loader(name, loader)
            mod = importlib.util.module_from_spec(spec)
            file_loader.exec_module(mod)
            for fn in runfuncs[name]:
               print("Add '%s.%s' to test suite..." % (name, fn))
            names = ["TestCase.%s" % x for x in runfuncs[name]]
            suite.addTests(loader.loadTestsFromNames(names, module=mod))
         except Exception as e:
            print("Skipping '%s' (%s)" % (name, e))
      elif runall or (runtests and name in runtests):
         # whole tests
         try:
            file_loader = importlib.machinery.SourceFileLoader(name, test_path)
            spec = importlib.util.spec_from_loader(name, loader)
            mod = importlib.util.module_from_spec(spec)
            mod.__file__ = test_path
            file_loader.exec_module(mod)
            print("Add '%s' to test suite..." % name)
            suite.addTests(loader.loadTestsFromTestCase(mod.TestCase))
         except Exception as e:
            print("Skipping '%s' (%s)" % (name, e))
      else:
         print("Skip test '%s'" % name)
         continue

   unittest.TextTestRunner(verbosity=3).run(suite)
