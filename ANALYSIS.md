A short HowTo for U180C_analyze
-------------------------------

The values are read into a **[Pandas DataFrame][]** stored in the variable **`df`**.

[Pandas Dataframe]: http://pandas.pydata.org/pandas-docs/dev/generated/pandas.DataFrame.html

Now, you can **plot measures** like this:

    df.loc[:,['P1', 'P2', 'P3']].plot()
    plt.show()

To get a **list of all available measures**, type:

    " ".join(df.columns)

You can also *look at individual days* like this:

    df['2015-04-10'].P1.plot()

or at a *date range* like that:

    df['2015-04-09':'2015-04-10']

You can get a **statistical description** of the data like this:

    percentiles=[.25,.5,.75]
    #percentiles=[.05,.5,.95]
    kwargs = dict(percentiles=percentiles)
    df.loc[:, ['V1N','V2N', 'V3N']].describe(percentiles=percentiles)
    df.loc[:, ['V12','V23', 'V31']].describe(**kwargs)
    df.loc[:, 'A1 A2 A3 AN ASYS'.split()].describe(**kwargs)
    df.loc[:, 'PF1 PF2 PF3 PFSYS'.split()].abs().describe(**kwargs)
    df.loc[:, 'P1 P2 P3 PSYS'.split()].describe(**kwargs)
    df.loc[:, 'S1 S2 S3 SSYS'.split()].describe(**kwargs)
    df.loc[:, 'Q1 Q2 Q3 QSYS'.split()].describe(**kwargs)
    df.loc[:, ['F']].describe(**kwargs)
    df.loc[:, 'kWh1_imp kWh2_imp kWh3_imp kWhSYS_imp'.split()].describe(**kwargs)

You can *combine columns*:

    for phase in '1 2 3 SYS'.split():
        df['kVAh'+ phase + '_imp'] = df['kVAh'+ phase + '_L_imp'] + df['kVAh'+ phase + '_C_imp']

You can also **do calculations** with individual columns.
Here, the absolute value of Q1 (the reactive power) is written to the column abs_Q1:

    phase = '1'
    df['abs_Q'+phase] = df['Q'+phase].abs()
    # plot it together with the actual and apparent power:
    df.loc[:,['S'+phase, 'P'+phase, 'abs_Q'+phase]].plot()
    plt.show()

If you want to **thin out** (= resample) the dataframe, you can do it like this:

    dfr = df.resample("5min", how='mean')
    # how can be: min max median mean add prod ohlc var

To calculate a **rolling average** with a window comprising 60 rows
(equivalent to 5 minutes if 5 seconds is the sampling period).

    pd.rolling_mean(df.P1, 60)

Calculating an **exponentially weighted moving average** is also easy:

    pd.ewma(df.P1, span=20)

A nice plot - the actual power averaged over five minutes wrapped in its **min/max band**:

    dfr = df.loc[:,['P1', 'P2', 'P3', 'PSYS']].resample("5min", how=['min', 'max', 'mean'])
    # for the phases individually:
    plt.plot(dfr.index, dfr.P1['mean'])
    plt.fill_between(dfr.index, dfr.P1['min'],dfr.P1['max'],facecolor='b',alpha=0.5)
    plt.plot(dfr.index, dfr.P2['mean'])
    plt.fill_between(dfr.index, dfr.P2['min'],dfr.P2['max'],facecolor='g',alpha=0.5)
    plt.plot(dfr.index, dfr.P3['mean'])
    plt.fill_between(dfr.index, dfr.P3['min'],dfr.P3['max'],facecolor='r',alpha=0.5)
    plt.show()
    # or for the sum of all phases:
    plt.plot(dfr.index, dfr.PSYS['mean'])
    plt.fill_between(dfr.index, dfr.PSYS['min'],dfr.PSYS['max'],facecolor='r',alpha=0.5)
    plt.show()

How about an **area plot for the actual power** (after resampling to 5mins)
(the plot is stacked automatically).

    df.resample("5min", how='mean').loc[:, ['P3', 'P1', 'P2']].plot(kind='area')

Another way to look at the data is to check for changes in the power consumption.  
To do so, you can draw a **histogram for the absolute differences of the actual power from one measurement to the next**.
This should allow to identify consumers with fixed power consumption at switching time:

    df['P1'].diff().abs().hist(histtype='stepfilled', linewidth=0, range=(1.,1000.), bins=999, log=True)
    
    # or check the difference between every second measurement:
    df['P1'].diff(periods=2).abs().hist(histtype='stepfilled', linewidth=0, range=(1.,1000.), bins=999, log=True)
    plt.show()
    
    # or add the differences between subsequent, and higher periods together
    # and plot their histogram:
    start_end = (1., 1000.)
    nbins = 999
    data1 = df.ix[:,'P1'].diff(periods=1)
    data1 = data1.append(df.ix[:,'P1'].diff(periods=2))
    data1 = data1.append(df.ix[:,'P1'].diff(periods=3))
    data1 = data1.append(df.ix[:,'P1'].diff(periods=4))
    data2 = df.ix[:,'P2'].diff(periods=1)
    data2 = data2.append(df.ix[:,'P2'].diff(periods=2))
    data2 = data2.append(df.ix[:,'P2'].diff(periods=3))
    data2 = data2.append(df.ix[:,'P2'].diff(periods=4))
    data3 = df.ix[:,'P3'].diff(periods=1)
    data3 = data3.append(df.ix[:,'P3'].diff(periods=2))
    data3 = data3.append(df.ix[:,'P3'].diff(periods=3))
    data3 = data3.append(df.ix[:,'P3'].diff(periods=4))
    data1.abs().hist(histtype='stepfilled', linewidth=0, range=start_end, bins=nbins, log=True, alpha=0.5)
    data2.abs().hist(histtype='stepfilled', linewidth=0, range=start_end, bins=nbins, log=True, alpha=0.5)
    data3.abs().hist(histtype='stepfilled', linewidth=0, range=start_end, bins=nbins, log=True, alpha=0.5)
    plt.show()

For the power consumption itself it can also be plotted but the signal will not be *clean*:

    start_end = (.001, 1.)
    nbins = 999
    df.P1.hist(histtype='stepfilled', linewidth=0, range=start_end, bins=nbins, log=True, alpha=0.5)
    df.P2.hist(histtype='stepfilled', linewidth=0, range=start_end, bins=nbins, log=True, alpha=0.5)
    df.P3.hist(histtype='stepfilled', linewidth=0, range=start_end, bins=nbins, log=True, alpha=0.5)
    plt.show()

Or plot the **variance of the power differences** (for ΔP < 50 W):

    measure = 'P1'
    pd = df[measure].diff()
    pd *= 1000.
    pd = pd.ix[pd.abs() < 50.]
    np.sqrt(pd.resample("5min", how='var')).plot()
    plt.show()

plt.axvspan(76, 76, facecolor='g', alpha=1)
plt.annotate('This is awesome!', 
             xy=(76, 0.75),  
             xycoords='data',
             textcoords='offset points',
             arrowprops=dict(arrowstyle="->"))
plt.show()

Also an important task is the calculation of the **energy consumed per day**:

    dfr = df.loc[:,['kWh1_imp','kWh2_imp', 'kWh3_imp']].resample("D", how=['min', 'max'])
    dfr['L1'] = dfr['kWh1_imp']['max'] - dfr['kWh1_imp']['min']
    dfr['L2'] = dfr['kWh2_imp']['max'] - dfr['kWh2_imp']['min']
    dfr['L3'] = dfr['kWh3_imp']['max'] - dfr['kWh3_imp']['min']
    dfr.columns = dfr.columns.droplevel(level=1)
    dfr = dfr.loc[:, ['L1', 'L2', 'L3']]
    dfr['all'] = dfr.L1 + dfr.L2 + dfr.L3
    ax = dfr.plot(title='energy used per day', lw=2,colormap='jet',marker='.',markersize=10)
    ax.set_ylabel("kWh")
    plt.show()

A **Fourier transform** of the power data:
<http://nbviewer.ipython.org/github/ipython-books/cookbook-code/blob/master/notebooks/chapter10_signal/01_fourier.ipynb>

    import scipy as sp
    import scipy.fftpack
    measure = 'P1'
    data_fft = sp.fftpack.fft(df[measure])
    data_psd = np.abs(data_fft) ** 2
    fftfreq = sp.fftpack.fftfreq(len(data_psd), 5) # 5 sec spacing
    i = fftfreq>0

    #plt.plot(fftfreq[i], 10*np.log10(data_psd[i]))
    plt.plot(fftfreq, 10*np.log10(data_psd))
    #plt.xlim(0, 5)
    plt.xlabel('Frequency (1/second)')
    plt.ylabel('PSD (dB)')

Or a **spectrogram of the voltage V1N**:

    # frequency in 1/minute
    plt.specgram(df.V1N, NFFT=256*4, Fs=60/5)
    plt.show()

You might want to set the matplotlib behaviour of IPython like this:

    %matplotlib osx
