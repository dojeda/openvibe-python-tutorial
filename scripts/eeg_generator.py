from __future__ import print_function, division
import numpy as np

def generate_random_EEG(num_channels, Fs, num_samples):
    f = np.fft.rfftfreq(num_samples, 1/Fs)

    x = np.zeros((num_channels, num_samples))
    for ch in range(num_channels):
        # Assume power of f is inversely proportional to f
        X = np.exp(-0.1*f)
        # add alpha as a Gaussian around 10Hz
        X += 0.25 * np.exp(-0.5*(f-10)**2)
        # add beta as a Gaussian around 20Hz
        X += 0.15 * np.exp(-0.1*(f-20)**2)
        # add 60Hz noise
        X[np.isclose(f,60,atol=0.01)] += 2
        # add random noise
        X += np.random.uniform(low=0, high=0.1, size=X.shape)
        # amplify
        X *= 1e6
        # convert power to a random complex
        radii = np.random.uniform(low=0, high=2*np.pi, size=X.shape)
        X = X * np.exp(1j*radii)
        # zero and Nyquist bin should not have an imaginary part
        X[0] = X[0].real
        X[-1] = X[-1].real
        # transform from frequencies to time. Drop complex part that
        # may not be zero due to numerical errors
        x[ch,:] = np.array(np.fft.irfft(X).real)

    return x


class GeneratorBox(OVBox):
    def __init__(self):
        super(GeneratorBox, self).__init__()

    def initialize(self):
        # Ensure the user has set the correct input/outputs
        assert len(self.input) == 0,   'This box needs exactly 0 inputs'
        assert len(self.output) == 1,  'This box needs exactly 1 output'
        assert len(self.setting) == 2, 'This box needs exactly 2 parameters'

        self.num_channels  = int(self.setting['Number of channels'])
        self.epoch_samples = int(self.setting['Samples per epoch'])
        self.sampling_freq = self.epoch_samples * self.getClock()

        # Prepare dimensions and labels for output header
        dimensions = (self.num_channels, self.epoch_samples)
        labels = ['ch{}'.format(i) for i in range(self.num_channels)]
        labels.extend(['']*self.epoch_samples)

        header = OVSignalHeader(0, 0, dimensions, labels, self.sampling_freq)
        self.output[0].append(header)

        # Create an artificial template EEG of 1000 epochs, the
        # template has num_channels rows and as many columns as
        # samples
        self.Nrandom = 1000
        self.artificial_eeg = generate_random_EEG(self.num_channels,
                                                  self.sampling_freq,
                                                  self.Nrandom*self.epoch_samples)
        self.artificial_index = 0

    def uninitialize(self):
        end = self.getCurrentTime()
        self.output[0].append(OVSignalEnd(end, end))

    def process(self):
        # calculate start and end time for output buffer
        start_time = self.getCurrentTime()
        end_time   = start_time + 1/self.getClock()

        # select a slice of the artificial EEG template
        index = slice(self.artificial_index*self.epoch_samples,
                      (self.artificial_index+1)*self.epoch_samples)
        eeg = self.artificial_eeg[:, index] # all channels, some samples
        self.artificial_index += 1
        self.artificial_index %= self.Nrandom

        # flatten EEG matrix in row-major and prepare output buffer
        signal_buffer = OVSignalBuffer(start_time, end_time, eeg.ravel())

        # send output buffer
        self.output[0].append(signal_buffer)


box = GeneratorBox()
