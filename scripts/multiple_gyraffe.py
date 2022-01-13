import argparse, os, logging, zipfile, tqdm
from gyraffe import find_glitch_params, get_version
import pandas as pd

def read_infile(infile):
    with infile as f:
        paths = f.read().splitlines()
    return paths

def find_in_archive(archive, logger):
    outputs = []
    for name in tqdm.tqdm(archive.namelist()):
        logger.debug(f"Finding glitch params for file '{name}'")
        with archive.open(name) as file:
            output = find_glitch_params(file)
        if output is not None:
            outputs.append(output)
    return outputs

def main():    
    logger = logging.getLogger('gyraffe')  # Log all in gyraffe module

    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='input file containing directories to run gyraffe on')
    parser.add_argument('--log-file', type=str,
                        help='filename to which to output log')
    parser.add_argument('--log-level', type=str, default='WARNING',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        )
    parser.add_argument('--archive-name', type=str, default='GYRE.zip',
                        help='name of profile archive under provided paths')
    parser.add_argument('--path', type=str, default='',
                        help='path to prepend to tracklist')

    args = parser.parse_args()
    
    if args.log_file is not None:
        formatter = logging.Formatter('%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
        handler = logging.FileHandler(args.log_file)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(args.log_level)
    logger.info(f'Using gyraffe v{get_version()}')

    paths = read_infile(args.infile)

    for path in paths:
        outfile = os.path.join(args.path, path, 'profile_gparams.csv')
        archive_name = os.path.join(args.path, path, 'GYRE.zip')
        logger.info(f"Running gyraffe for profiles in archive '{archive_name}'")
        with zipfile.ZipFile(archive_name, 'r') as archive:
            outputs = find_in_archive(archive, logger)
        # try:
        #     with zipfile.ZipFile(archive_name, 'r') as archive:
        #         outputs = find_in_archive(archive)
        # except Exception as err:
        #     msg = f"Unexpected exception of type '{type(err).__name__}' occurred while " + \
        #           f"finding glitch params in archive '{archive_name}': {err}"
        #     logger.error(msg)
        #     continue
            
        pd.DataFrame(outputs).to_csv(outfile, index=False)
        logger.info(f"Results output to file '{outfile}'")

if __name__ == "__main__":
    main()
