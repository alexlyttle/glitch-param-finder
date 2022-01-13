import os, argparse
import pandas as pd

from multiple_gyraffe import read_infile

def strip_extensions(filename):
    return filename.split('.')[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('r'), help='tracklist')
    parser.add_argument('--path', type=str, default='',
                        help='path to prepend to tracklist')
    parser.add_argument('-o', '--outfile', type=argparse.FileType('r'))
    
    args = parser.parse_args()
    paths = read_infile(args.infile)
    
    dfs = []
    for path in paths:
        gparamfile = os.path.join(args.path, path, 'profile_gparams.csv')
        
        gparams = pd.read_csv(gparamfile)
        gparams['filename'] = gparams['filename'].apply(strip_extensions)
        
        # indexfile = os.path.join(args.path, path, 'profiles.index')        
        # index = pd.read_table(indexfile, delimiter=r'\s+', skiprows=1,
        #                       names=['model_number', 'priority', 'profile_number'])
        historyfile = os.path.join(args.path, path, '.'.join([path, 'csv']))
        history = pd.read_csv(historyfile)
        
        df = history.merge(gparams, on='filename')
        df['dirname'] = path
        dfs.append(df)
        
    df = pd.concat(dfs, axis=0)
    df.to_csv(args.outfile, index=False)
    
if __name__ == '__main__':
    main()
