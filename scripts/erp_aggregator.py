# -*- coding: utf-8 -*-
##
##   [2012] - [2016] Mensia Technologies SA
##   Copyright, All Rights Reserved.
##

from __future__ import print_function, division
import numpy as np


def generate_random_ERP(time, x, start_time, coefs):
    x = x.copy()
    t = (time - start_time) * 1000
    for ch in range(x.shape[0]):
        x[ch,:] +=  coefs[0]*np.exp(-1.25e-3*(t-100)**2) # peak at 100 ms
        x[ch,:] +=  coefs[1]*np.exp(-1.25e-3*(t-200)**2) # peak at 200 ms
        x[ch,:] +=  coefs[2]*np.exp(-6.25e-4*(t-300)**2) # wider peak at 300 ms
    return x


class ERPGeneratorBox(OVBox):
    def __init__(self):
        super(ERPGeneratorBox, self).__init__()
        self.num_channels  = 0
        self.sampling_rate = 0
        self.num_samples   = 0
        self.last_time     = 0
        self.stimulations  = []

    def initialize(self):
        assert len(self.input)  == 2,  'This box needs exactly 2 input'
        assert len(self.output) == 1,  'This box needs exactly 1 output'

        stim_label1 = self.setting['Target stimulation label']
        stim_label2 = self.setting['Non-Target stimulation label']
        self.code_target = OpenViBE_stimulation[stim_label1]
        self.code_non_target = OpenViBE_stimulation[stim_label2]

        self.last_time = self.getCurrentTime()
        self.stimulations = []

    def uninitialize(self):
        pass

    def process(self):
        if not self.input[0] and not self.input[1]:
            return

        # obtain all chunks of signals received in the first input
        merged_signals = np.empty((self.num_channels, 0))
        merged_start_time = self.last_time
        merged_end_time   = self.last_time
        while self.input[0]:
            chunk = self.input[0].pop()

            if type(chunk) == OVSignalHeader:

                # handle header: we are sending the same information
                # so the output header should be the same
                input_header  = chunk
                self.sampling_rate = input_header.samplingRate
                self.num_channels  = input_header.dimensionSizes[0]
                self.num_samples   = input_header.dimensionSizes[1]
                output_header = OVSignalHeader(input_header.startTime,
                                               input_header.endTime,
                                               input_header.dimensionSizes,
                                               input_header.dimensionLabels,
                                               input_header.samplingRate)
                self.output[0].append(output_header)

            elif type(chunk) == OVSignalBuffer:

                if self.last_time != chunk.startTime:
                    raise Exception('Chunk times do not match')

                input_signal = np.reshape(chunk, (self.num_channels, self.num_samples))
                merged_signals = np.hstack((merged_signals, input_signal))
                self.last_time = chunk.endTime
                merged_end_time = self.last_time


            elif type(chunk) == OVSignalEnd:

                self.output[0].append(chunk)

        # obtain all stimulations
        stimulations = self.stimulations[:]
        while self.input[1]:
            chunk = self.input[1].pop()
            if type(chunk) == OVStimulationSet:
                for stim in chunk:
                    #if stim.identifier == self.code_target:
                    stimulations.append((stim.date,
                                         stim.identifier))

        if stimulations and merged_signals.shape[1] > 0:
            saved_stimulations = []
            # Create a time reference for the received signal
            t = np.arange(0, merged_signals.shape[1], dtype=float) / self.sampling_rate
            t += merged_start_time

            for stim_date, stim_id in stimulations:
                if stim_id == self.code_target:
                    # print('Adding ERP target at ', stim_date)
                    merged_signals = generate_random_ERP(t, merged_signals, stim_date,
                                                         [500, -700, 1250])
                elif stim_id == self.code_non_target:
                    # print('Adding ERP non target at', stim_date)
                    merged_signals = generate_random_ERP(t, merged_signals, stim_date,
                                                         [500, -500, 0])
                # keep only 2 seconds-old stimulations
                if merged_start_time - stim_date <= 2:
                    saved_stimulations.append((stim_date, stim_id))

            self.stimulations = saved_stimulations
        else:
            self.stimulations = stimulations

        # write signal buffers to output
        start_time = merged_start_time
        for i in range(0, merged_signals.shape[1], self.num_samples):
            chunk = merged_signals[:,i:i+self.num_samples].ravel()
            signal_buffer = OVSignalBuffer(start_time,
                                           start_time+self.num_samples/self.sampling_rate,
                                           chunk)
            self.output[0].append(signal_buffer)


box = ERPGeneratorBox()
