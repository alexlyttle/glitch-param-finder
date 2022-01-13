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
    parser.add_argument('-o', '--outfile', type=argparse.FileType('w'))
    
    args = parser.parse_args()
    paths = read_infile(args.infile)
    
    dfs = []
    for path in paths:
        
        historyfile = os.path.join(args.path, path, '.'.join([path, 'csv']))

        if not os.path.exists(historyfile):
            df = pd.DataFrame()
            df['dirname'] = path
            dfs.append(df)
            continue
        
        history = pd.read_csv(historyfile)

        # historyfile = os.path.join(args.path, path, 'history_ms.data')
        # history = pd.read_table(historyfile, delimiter=r'\s+', header=4)
        # indexfile = os.path.join(args.path, path, 'profiles.index')
        # index = pd.read_table(indexfile, delimiter=r'\s+', skiprows=1,
        #                         names=['model_number', 'priority', 'profile_number'])
                    
        gparamfile = os.path.join(args.path, path, 'profile_gparams.csv')
        
        gparams = pd.read_csv(gparamfile)
        gparams['filename'] = gparams['filename'].apply(strip_extensions)

        df = history.merge(gparams, on='filename')
        
        df['dirname'] = path
        dfs.append(df)
        
    df = pd.concat(dfs, axis=0)
    df.to_csv(args.outfile, index=False)
    
if __name__ == '__main__':
    main()
