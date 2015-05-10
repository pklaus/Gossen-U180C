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

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analysis software for a U189A energy counter with U180C LAN interface.')
    parser.add_argument('input_file', help='The data file to read', nargs="?")
    parser.add_argument('output_file', help='The data file to write', nargs="?")
    parser.add_argument('--append', action='store_true', help='Append the data to the output file (if applicable)')
    parser.add_argument('--doc', action='store_true', help='Open the documentation in the Browser')

    args = parser.parse_args()

    msg = ''
    script_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(script_path, 'ANALYSIS.md'), 'r', encoding='utf-8') as f:
        msg = f.read()
    if args.doc:
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
        sys.exit(0)

    if not args.input_file: parser.error('Please state an input file to read from.')

    if args.input_file.lower().endswith('.csv'):
        df = pd.io.parsers.read_csv(args.input_file, sep=';', parse_dates=[['Date', 'Time']], dayfirst=True)
        df.set_index('Date_Time', inplace = True)
        if 'SN' in df.columns: df.drop('SN', axis=1, inplace = True)
        if 'kWh SYS_exp' in df.columns:
            df['kWhSYS_exp'] = df['kWh SYS_exp']
            df.drop('kWh SYS_exp', axis=1, inplace = True)
        ## divide columns with kW / kVA / kvar by 1000 to get the unit right:
        #relevant_fragments = ['kW', 'kVA', 'kvar']
        #relevant_fragments += [''.join(p) for p in product(['P', 'S', 'Q'], ['1', '2', '3', 'SYS'])]
        #for col in df.columns:
        #    if any(x in col for x in relevant_fragments):
        #        df[col] = df[col]/1000.
        # change all columns of type np.float64 to type np.float32:
        for column in df.columns:
            if df[column].dtype == np.float64:
                df[column] = df[column].astype(np.float32)
        print("Finished reading the data file in.")

    if args.input_file.lower().endswith('.h5'):
        #df = read_hdf(args.input_file., 'table', where = ['index>2'])
        df = pd.read_hdf(args.input_file, 'df')

        #store = pd.HDFStore(args.input_file, mode='r')
        #for chunk in read_csv('file.csv', chunksize=50000):
        #         store.append('df',chunk)
        #store.close()
        print("Finished saving the data to HDF5.")

    if args.output_file:
        if args.output_file.lower().endswith('.h5'):
            # For appending, we should probably check for duplicates first?!
            df.to_hdf(args.output_file, 'df', format='table', append=args.append, complib='zlib', data_columns=True)

    print(msg)

    embed()

if __name__ == "__main__":
    main()
