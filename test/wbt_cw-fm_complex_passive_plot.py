# -*- coding: utf-8 -*-
"""
@author: rick.towler

This is a script to plot up the differences between pyEcholab outputs
and outputs created by Echoview and MATLAB.

The data file is from a 5 WBT system configured with the 18 and 38 kHz as
CW and the 70, 120, and 200 as FM. The system is in passive mode and data
are recorded to 500m.

EK80 Software version: 1.11.1.0
Raw file format version: 1.20


Echoview data were exported using EV 11.1.49 which included the bug fix
for gain lookup in raw files without a broadband calibration. No .ecs file
was used. All calibration parameters are taken from the raw file.

The MATLAB conversion codes are based on Lars Nonboe Andersen's (Simrad)
MATLAB code. The code has been modified to work with 3 sector channels and
to extract transceiver impedance from the configuration header (if
available). It also was modified to get the default sound speed from the
first environmental datagram. Both Echoview and Echolab get the default
sound speed from the environmental datagrams so this ensures the MATLAB
code uses the same sound speed in these comparisons. The MATLAB code
used to generate the data files is in: echolab2/instruments/resources/lib

"""

import scipy.io
from echolab2.instruments import EK80
import echolab2.processing.processed_data as processed_data
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt

#  specify the difference echogram's threshold.
diff_threshold = [-0.1, 0.1]

#  specify the color table used for the difference echograms
#  The matplotlib diverging maps are best here:
#  https://matplotlib.org/stable/tutorials/colors/colormaps.html#diverging
diff_cmap='PuOr'

# Specify the input raw file
in_file = './data/DY1803-FM_Passive_DY1803_EK80-D20180322-T020144.raw'

# Echoview power, Sv, TS, and angles data exports of above raw file
ev_Sv_filename = {}
ev_Sv_filename[18000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-18khz.Sv.mat'
ev_Sv_filename[38000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-38khz.Sv.mat'
ev_Sv_filename[70000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-70khz.Sv.mat'
ev_Sv_filename[120000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-120khz.Sv.mat'
ev_Sv_filename[200000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-200khz.Sv.mat'

ev_TS_filename = {}
ev_TS_filename[18000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-18khz.ts.csv'
ev_TS_filename[38000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-38khz.ts.csv'
ev_TS_filename[70000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-70khz.ts.csv'
ev_TS_filename[120000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-120khz.ts.csv'
ev_TS_filename[200000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-200khz.ts.csv'

ev_power_filename = {}
ev_power_filename[18000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-18khz.power.csv'
ev_power_filename[38000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-38khz.power.csv'
ev_power_filename[70000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-70khz.power.csv'
ev_power_filename[120000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-120khz.power.csv'
ev_power_filename[200000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-200khz.power.csv'

ev_angles_filename = {}
ev_angles_filename[18000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-18khz.angles.csv'
ev_angles_filename[38000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-38khz.angles.csv'
ev_angles_filename[70000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-70khz.angles.csv'
ev_angles_filename[120000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-120khz.angles.csv'
ev_angles_filename[200000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-200khz.angles.csv'

# The paths to the MATLAB outputs
MATLAB_filename = {}
MATLAB_filename[18000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-18khz-MATLAB.Sv.mat'
MATLAB_filename[38000] = './data/DY1803_EK80-D20180322-T020144-Passive-CW-38khz-MATLAB.Sv.mat'
MATLAB_filename[70000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-70khz-MATLAB.Sv.mat'
MATLAB_filename[120000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-120khz-MATLAB.Sv.mat'
MATLAB_filename[200000] = './data/DY1803_EK80-D20180322-T020144-Passive-FM-200khz-MATLAB.Sv.mat'


#  read in the .raw data file
print('Reading the raw file %s' % (in_file))
ek80 = EK80.EK80()
ek80.read_raw(in_file)

#  now iterate through the reference files and display results
for idx, channel_id in enumerate(ek80.raw_data):

    #  I know that for the purposes of these comparisons, I am
    #  only reading a single data type per channel so I can assume
    #  there will be only 1 raw_data object in the list and it will
    #  be at index 0.
    raw_data = ek80.raw_data[channel_id][0]

    #  get the tx frequency
    frequency = raw_data.get_frequency(unique=True)[0]

    #  get the transducer frequency
    transducer_frequency = raw_data.configuration[0]['transducer_frequency']

    #  The calibration object provides all of the parameters required to
    #  convert raw data to the various processed forms. Here we will get
    #  a cal object that is populated with parameters from the .raw data
    #  file. While you don't *have* to pass a calibration object to the
    #  conversion methods, it is most efficient to get a cal object from
    #  your raw_data, modify values as needed, and then pass that to your
    #  conversion method(s).
    calibration = raw_data.get_calibration()

    #  Convert the raw data. Some computed conversion parameters are cached
    #  in the calibration object during conversion. Normally they are
    #  discarded at the end of the conversion process but since we will
    #  be calling multiple conversion methods below, we'll set the clear_cache
    #  keyword to False to keep that data. By keeping it, the next method
    #  called doesn't need to recompute it.

    #  convert to power
    ek80_power = raw_data.get_power(calibration=calibration, clear_cache=False)

    #  convert to Sv
    ek80_Sv = raw_data.get_Sv(calibration=calibration, clear_cache=False)

    #  and convert to Ts
    ek80_Ts = raw_data.get_Sp(calibration=calibration, clear_cache=False)

    # Try to get the angle data (not all files have angle data)
    try:
        alongship, athwartship = raw_data.get_physical_angles(calibration=calibration)
    except:
        alongship, athwartship = (None, None)


    #  read in the echoview data - we can read .mat and .csv files exported
    #  from EV 7+ directly into a processed_data object
    ev_filename = ev_Sv_filename[transducer_frequency]
    print('Reading the echoview file %s' % (ev_Sv_filename[transducer_frequency]))
    ev_Sv_data = processed_data.read_ev_mat('', frequency, ev_filename,
            data_type='Sv')

    ev_filename = ev_TS_filename[transducer_frequency]
    print('Reading the echoview file %s' % (ev_TS_filename[transducer_frequency]))
    ev_Ts_data = processed_data.read_ev_csv('', frequency, ev_filename,
            data_type='Ts')

    ev_filename = ev_power_filename[transducer_frequency]
    print('Reading the echoview file %s' % (ev_power_filename[transducer_frequency]))
    ev_power_data = processed_data.read_ev_csv('', frequency, ev_filename,
            data_type='Power')

    # Try to read the EV angle data (not all files have angle data)
    try:
        ev_filename = ev_angles_filename[transducer_frequency]
        print('Reading the echoview file %s' % (ev_angles_filename[transducer_frequency]))
        ev_alongship, ev_athwartship = processed_data.read_ev_csv('', frequency,
                ev_filename, data_type='angles')
    except:
        ev_alongship, ev_athwartship = (None, None)


    #  read in the power, angle, and Sv data generated from MATLAB code based on Lars
    #  Andersen's EK80 codes.
    ml_filename = MATLAB_filename[transducer_frequency]
    matlab_data = scipy.io.loadmat(ml_filename, struct_as_record=False,
            squeeze_me=True)


    #  now plot all of this up

    #  show the Echolab Sv and TS echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Sv, threshold=[-70,-34])
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 Sv " + str(frequency) + " kHz")
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Ts, threshold=[-70,-34])
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 Ts " + str(frequency) + " kHz")


    #  compute the difference of EV and Echolab power data
    diff = ek80_power - ev_power_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 power - EV power " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab Sv data
    diff = ek80_Sv - ev_Sv_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 Sv - EV Sv " + str(frequency) + " kHz")

    #  compute the difference of MATLAB and Echolab Sv data
    diff = ek80_Sv - matlab_data['sv']
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 Sv - MATLAB Sv " + str(frequency) + " kHz")

    #  compute the difference of MATLAB and EV Sv data
    diff = ev_Sv_data - matlab_data['sv']
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("EV Sv - MATLAB Sv " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab TS data
    diff = ek80_Ts - ev_Ts_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 TS - EV TS " + str(frequency) + " kHz")

    #  plot angle diffs if we have them
    if alongship:
        #  compute the difference of EV and Echolab alongship angles
        diff = alongship - ev_alongship
        fig = plt.figure()
        eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
        eg.add_colorbar(fig, units='deg')
        eg.axes.set_title("Echolab2 alongship - EV alongship " + str(frequency) + " kHz")

        #  compute the difference of EV and Echolab athwartship angles
        diff = athwartship - ev_athwartship
        fig = plt.figure()
        eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
        eg.add_colorbar(fig, units='deg')
        eg.axes.set_title("Echolab2 athwartship - EV athwartship " + str(frequency) + " kHz")

    #  plot up a single Sv ping
    fig2 = plt.figure()
    plt.plot(matlab_data['sv'][-1,:], matlab_data['r'], label='MATLAB', color='orange', linewidth=1)
    plt.plot(ev_Sv_data[-1], ev_Sv_data.range, label='Echoview', color='blue', linewidth=1)
    plt.plot( ek80_Sv[-1], ek80_Sv.range, label='Echolab2', color='red', linewidth=1)
    plt.gca().invert_yaxis()
    fig2.suptitle("Ping " + str(ev_Sv_data.n_pings) + " comparison EV vs Echolab2 vs MATLAB")
    plt.xlabel("Sv (dB)")
    plt.ylabel("Range (m)")
    plt.legend()

    # Show our figures.
    plt.show()

