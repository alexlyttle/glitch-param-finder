import argparse, os, glob
from gyraffe import findall_glitch_params

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='input file containing directories to run gyraffe on')
    
    args = parser.parse_args()
    paths = args.input.read().splitlines()
    for path in paths:
        outfile = '.'.join([path, 'gparams', 'csv'])
        filenames = glob.glob(os.path.join(path, '*'))  # all files here
        outputs = findall_glitch_params(filenames)
        outputs.to_csv(outfile, index=False)

if __name__ == "__main__":
    main()
