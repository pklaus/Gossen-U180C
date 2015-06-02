#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from matplotlib import pyplot as plt, pylab
import matplotlib.dates as mdates
from IPython import embed
import numpy as np
#import seaborn as sns
#sns.set(palette="Set2")
import sys
from itertools import product
from datetime import datetime as dt, timedelta, date
import datetime
import os

from append_csv_to_hdf5 import read_csv

def read_data_file(csv_or_h5_filename):
    lower_filename = csv_or_h5_filename.lower()
    if lower_filename.endswith('.csv'):
        return read_csv(csv_or_h5_filename)
    if lower_filename.endswith('.h5'):
        return pd.read_hdf(csv_or_h5_filename, 'df')
        #return read_hdf(csv_or_h5_filename, 'df', where = ['index>2'])

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analysis software for a U189A energy counter with U180C LAN interface.')
    parser.add_argument('input_file', help='The data file to read', nargs="?")
    parser.add_argument('output_file', help='The data file to write', nargs="?")
    parser.add_argument('--append', action='store_true', help='Append the data to the output file (if applicable)')
    parser.add_argument('--doc', action='store_true', help='Open the documentation in the Browser')

    args = parser.parse_args()

    if args.doc:
        msg = ''
        script_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(script_path, 'ANALYSIS.md'), 'r', encoding='utf-8') as f:
            msg = f.read()
        try:
            import webbrowser
            import tempfile
            import markdown
            fp = tempfile.NamedTemporaryFile(mode='wb', suffix='.html', delete=False)
            filename = fp.name
            with fp:
                fp.write(markdown.markdown(msg).encode('utf-8'))
                fp.close()
            webbrowser.open_new_tab('file://' + filename)
        except Exception as e:
            print(str(e))
        print(msg)
        sys.exit(0)

    if not args.input_file: parser.error('Please state an input file to read from.')

    df = read_data_file(args.input_file)
    print("Finished reading the data file in.")

    if args.output_file:
        if args.output_file.lower().endswith('.h5'):
            # For appending, we should probably check for duplicates first?!
            df.to_hdf(args.output_file, 'df', format='table', append=args.append, complib='zlib', data_columns=True)
            print("Finished storing the output file.")

    embed()

if __name__ == "__main__":
    main()
