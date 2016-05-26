# -*- coding: utf-8 -*-
##
##   [2012] - [2016] Mensia Technologies SA
##   Copyright, All Rights Reserved.
##

from __future__ import print_function, division
import numpy as np

class RandomStimulatorBox(OVBox):
    """Box that generates target and non-target stimulations

    Stimulations will be generated according to the Clock Frequency
    (Hz) parameter of the Python scripting box in OpenViBE. The choice
    between target and non-target is decided randomly, following a
    Bernouilli distribution with probability p (i.e. like unfair
    coin-toss)

    Inputs:
    -----------
    None

    Outputs:
    -----------
    output 0: stimulations

    Parameters:
    -----------
    Target stimulation label: stimulation code
        the code for the target stimulations

    Non-Target stimulation label: stimulation code
        the code for the non-target stimulations

    Target probability: float
        the probability p of generating a target stimulation

    """

    def __init__(self):
        """ Create a box instance """
        super(RandomStimulatorBox, self).__init__()
        self.code_target     = None
        self.code_non_target = None
        self.probability = 0.5

    def initialize(self):
        """ Initialize box and parameters """
        assert len(self.input) == 0, 'RandomStimulatorBox needs 0 inputs'
        assert len(self.output) == 1, 'RandomStimulatorBox needs exactly 1 output'

        # Initialize parameters from settings

        # Target stimulation codes must be converted from string to
        # OpenViBE internal codes, using the OpenViBE_stimulation
        # dictionary (imported by default)
        stim_label1 = self.setting['Target stimulation label']
        self.code_target = OpenViBE_stimulation[stim_label1]
        stim_label2 = self.setting['Non-Target stimulation label']
        self.code_non_target = OpenViBE_stimulation[stim_label2]

        # Convert probability to float, and force it to be between 0 and 1
        self.probability = float(self.setting['Target probability'])
        self.probability = np.clip(self.probability, 0 , 1)

        # Send a stimulation header with time=0 for downstream boxes
        self.output[0].append(OVStimulationHeader(0., 0.))

    def process(self):
        # Each process will generate one stimulation chunk. It's
        # starting time is the current time and the end is the time
        # step between two calls. This means that the distance between
        # stimulations will be controlled by the Python scripting box
        # parameter "Clock Frequency (Hz)"

        # OVStimulationSet is the specialized chunk for 0 or more
        # stimulations
        stimSet = OVStimulationSet(self.getCurrentTime(),
                                   self.getCurrentTime()+1./self.getClock())

        # Randomly select a stimulation code with probability p
        code = np.random.choice((self.code_target, self.code_non_target), size=1,
                                p=(self.probability, 1-self.probability))

        # Add stimulation to chunk. Assume that the stimulation
        # happens at the beginning of the current time. Note that if
        # we wanted to, we could add more OVStimulation
        stimSet.append(OVStimulation(code, self.getCurrentTime(), 0.))

        # Send chunk
        self.output[0].append(stimSet)

    def uninitialize(self):
        # Send a stream end for downstream boxes
        end = self.getCurrentTime()
        self.output[0].append(OVStimulationEnd(end, end))

box = RandomStimulatorBox()
