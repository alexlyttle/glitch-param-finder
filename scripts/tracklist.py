# Get tracklist
import argparse
import numpy as np
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('r'))
    parser.add_argument('-o', '--outfile', type=argparse.FileType('w'))
    parser.add_argument('-m', '--mass', type=float, nargs='+')
    parser.add_argument('-f', '--metallicity', type=float, nargs='+')
    parser.add_argument('-y', '--helium', type=float, nargs='+')
    parser.add_argument('-a', '--alpha', type=float, nargs='+')
    
    args = vars(parser.parse_args())

    with args['infile'] as file:
        data = pd.read_json(file)
    
    cols = {
        'mass': 'm',
        'metallicity': 'FeH',
        'helium': 'Y',
        'alpha': 'MLT',
    }
    
    conditions = []
    for key, col in cols.items():
        if args[key] is None:
            continue
        conditions.append(data[col].isin(args[key]))

    if len(conditions) > 0:
        mask = conditions[0]
        for cond in conditions[1:]:
            mask = np.logical_and(mask, cond)
            
        dirnames = data.loc[mask, 'dirname'].to_list()
    else:
        dirnames = data['dirname'].to_list()

    if args['outfile'] is None:
        if len(dirnames) > 50:
            for d in dirnames[:5]:
                print(d)
            print('...')
            for d in dirnames[-5:]:
                print(d)
        else:
            for d in dirnames:
                print(d)
    else:
        with args['outfile'] as file:
            file.write('\n'.join(dirnames))

if __name__ == '__main__':
    main()
