"""parse_dirnames.py

Parse dirnames assuming the convention of metadata values preceded by their
respective names, e.g.

m1.0FeH0.0Y0.26dif1

for a solar mass, solar metallicity star with helium abundance of 0.26.

The values must be convertable to a Python int or float, but not including
values with a leading period (e.g. '.98' would be interpreted as 98.0).
"""
import os, re, argparse, unittest, sys
import pandas as pd

pattern = r'[+\-]?(?:0+|[1-9]\d*)\d*(?:\.\d+)?(?:[eE][+\-]?\d+)?'
"""Patten which finds numbers, modified from https://stackoverflow.com/a/658662

This allows for leading '+'/'-', scientific notation ('E'/'e'), integers and
leading zeros, but not leading periods.
"""

regex = re.compile(pattern)

def to_number(s):
    if '.' in s or 'e' in s.lower():
        return float(s)
    return int(s)

def explode(dirname):
    keys = regex.split(dirname)  # Finds the keys by assuming all non-numbers 
    values = [to_number(s) for s in regex.findall(dirname)]
    return dict(zip(keys, values))

def parse_dirnames(path):
    records = []
    dirnames = os.listdir(path)
    for dirname in dirnames:
        if dirname.startswith('.'):
            continue
        metadata = {'dirname': dirname}
        metadata.update(explode(dirname))
        records.append(metadata)
    return pd.DataFrame.from_records(records)


class TestRegex(unittest.TestCase):
    """Tests that regex is able to find valid numbers."""
    
    def assertAllRegexpMatches(self, s):
        """Asserts all in s.split() are valid regex."""
        self.assertEqual(regex.findall(s), s.split())

    def assertNotFullRegexpMatches(self, s):
        self.assertIsNone(regex.fullmatch(s))

    def test_leading_zeros(self):
        self.assertAllRegexpMatches('01 001 0001')

    def test_plus_minus(self):
        self.assertAllRegexpMatches('+0 -0 +1 -1')
    
    def test_integer(self):
        self.assertAllRegexpMatches('0 1 23')
    
    def test_decimal(self):
        self.assertAllRegexpMatches('0.0 1.0')
        
    def test_scientific(self):
        s = '1e5 1e+5 1e-5'
        self.assertAllRegexpMatches(s)
        self.assertAllRegexpMatches(s.upper())
    
    def test_valid_examples(self):
        self.assertAllRegexpMatches('9.9 099.99 0.12e3 +01E+23 -44e-44')
    
    def test_invalid_examples(self):
        self.assertNotFullRegexpMatches('.0')
        self.assertNotFullRegexpMatches('.1')
        self.assertNotFullRegexpMatches('0.1.2')
        self.assertNotFullRegexpMatches('01.e23')
        self.assertNotFullRegexpMatches('e0')
        self.assertNotFullRegexpMatches('1e0.1')
        self.assertNotFullRegexpMatches('1+1')
        self.assertNotFullRegexpMatches('01d23')


def run(args, _):
    if not os.path.isdir(args.path):
        raise FileNotFoundError(f'No such file or directory: {repr(args.path)}')
    
    data = parse_dirnames(args.path)
    
    if args.output is None:
        print(data)
    else:
        data.to_json(args.output)

def test(_, unknown_args):
    # A bit of a hack to get the program name
    argv = [sys.argv[1]] + unknown_args
    unittest.main(argv=argv)
     
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands", dest='subcommand')
    
    p = subparsers.add_parser('run', description='run script')
    p.add_argument('path', type=str, help='path to parse')
    p.add_argument('-o', '--output', type=str, help='filename to save JSON output')
    p.set_defaults(func=run)
    
    p = subparsers.add_parser('test', description='run unit tests',
                              add_help=False)
    p.set_defaults(func=test)
    
    args, unknown_args = parser.parse_known_args()
    args.func(args, unknown_args)

if __name__ == '__main__':
    main()
