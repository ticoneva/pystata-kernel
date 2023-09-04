import unittest
from pystata-kernel.helpers import clean_code

class Test_clean_code(unittest.TestCase):

    def test_forvalues(self):
        raw = """forvalues i=1/10 {
               sum a
               }
              """
        out = """noisily forvalues i=1/10 {
                noisily sum a
              }"""
        self.assertEqual(clean_code(raw), out)
