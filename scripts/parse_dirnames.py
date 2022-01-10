"""parse_dirnames.py

Parse MESA/GYRE profile dirnames assuming the convention of

<metadata1.name><metadata1.value><metadata2.name><metadata2.value>

where value can be converted to a Python float.
"""
import os, re, argparse, unittest, sys
import pandas as pd

pattern = r'[+\-]?(?:0+|[1-9]\d*)\d*(?:\.\d+)?(?:[eE][+\-]?\d+)?'
"""Patten which finds floats, modified from https://stackoverflow.com/a/658662

This allows for leading '+'/'-', scientific notation ('E'/'e'), integers and
leading zeros, but not leading periods.
"""

regex = re.compile(pattern)

def explode(dirname):
    keys = regex.split(dirname)  # Finds the keys by assuming all non-numbers 
    values = regex.findall(dirname)
    return dict(zip(keys, values))

def parse_dirnames(path):
    data = []
    dirnames = os.listdir(path)
    for dirname in dirnames:
        if dirname.startswith('.'):
            continue
        data.append(explode(dirname))
    return pd.DataFrame.from_records(data)


class TestRegex(unittest.TestCase):

    def test_leading_zeros(self):
        s = '01 001 0001'
        self.assertEqual(regex.findall(s), s.split())

    def test_plus_minus(self):
        s = '+0 -0 +1 -1'
        self.assertEqual(regex.findall(s), s.split())
        
        self.assertIsNone(regex.fullmatch('1+'))
        self.assertIsNone(regex.fullmatch('1-'))
    
    def test_integer(self):
        s = '0 1'
        self.assertEqual(regex.findall(s), s.split())
    
    def test_decimal(self):
        s = '0.0 0.1 1.0 1.1'
        self.assertEqual(regex.findall(s), s.split())
        
        self.assertIsNone(regex.fullmatch('0.0.0'))
        self.assertIsNone(regex.fullmatch('1.1.1'))
        
    def test_scientific(self):
        s = '1e5 1e+5 1e-5'
        self.assertEqual(regex.findall(s), s.split())
        self.assertEqual(regex.findall(s.upper()), s.upper().split())
    
    def test_examples(self):
        s = '9.9 099.99 0.12e3 +01E+23 -44e-44'
        self.assertEqual(regex.findall(s), s.split())
    
    def test_invalid(self):
        self.assertIsNone(regex.fullmatch('.0'))
        self.assertIsNone(regex.fullmatch('.1'))
        self.assertIsNone(regex.fullmatch('0.1.2'))
        self.assertIsNone(regex.fullmatch('01.e23'))
        self.assertIsNone(regex.fullmatch('e0'))


def run(args, _):
    if not os.path.isdir(args.path):
        raise FileNotFoundError(f'No such file or directory: {repr(args.path)}')
    
    data = parse_dirnames(args.path)
    
    if args.output is None:
        print(data)
    else:
        data.to_csv(args.output, index=False)

def test(_, unknown_args):
    # A bit of a hack to get the program name
    argv = [sys.argv[1]] + unknown_args
    unittest.main(argv=argv)
     
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands", dest='subcommand')
    
    p = subparsers.add_parser('run', description='run script')
    p.add_argument('path', type=str, help='path to parse')
    p.add_argument('-o', '--output', type=str, help='path to save output to')
    p.set_defaults(func=run)
    
    p = subparsers.add_parser('test', description='run unit tests',
                              add_help=False)
    p.set_defaults(func=test)
    
    args, unknown_args = parser.parse_known_args()
    args.func(args, unknown_args)

if __name__ == '__main__':
    main()
