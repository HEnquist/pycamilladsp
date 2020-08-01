
from filter_eval import Biquad, BiquadCombo, Conv, DiffEq
import numpy as np
from matplotlib import pyplot as plt

def plot_filter(filterconf, srate):
    fvect = np.linspace(1, (srate*0.95)/2.0, 10000)
    filter, fconf = filterconf
    if fconf['type'] in ('Biquad', 'DiffEq', 'BiquadCombo'):
        if fconf['type'] == 'DiffEq':
            kladd = DiffEq(fconf['parameters'], srate)
        elif fconf['type'] == 'BiquadCombo':
            kladd = BiquadCombo(fconf['parameters'], srate)
        else:
            kladd = Biquad(fconf['parameters'], srate)
        plt.figure(num=filter)
        fplot, magn, phase = kladd.gain_and_phase(fvect)
        stable = kladd.is_stable()
        plt.subplot(2,1,1)
        plt.semilogx(fplot, magn)
        plt.title("{}, stable: {}\nMagnitude".format(filter, stable))
        plt.subplot(2,1,2)
        plt.semilogx(fvect, phase)
        plt.title("Phase")
    elif fconf['type'] == 'Conv':
        if 'parameters' in fconf:
            kladd = Conv(fconf['parameters'], srate)
        else:
            kladd = Conv(None, srate)
        plt.figure(num=filter)
        ftemp, magn, phase = kladd.gain_and_phase()
        plt.subplot(2,1,1)
        plt.semilogx(ftemp, magn)
        plt.title("FFT of {}".format(filter))
        plt.gca().set(xlim=(10, srate/2.0))
        t, imp = kladd.get_impulse()
        plt.subplot(2,1,2)
        plt.plot(t, imp)
        plt.title("Impulse response of {}".format(filter))
            
def plot_filters(conf):
    srate = conf['devices']['samplerate']

    if 'filters' in conf:
        for filter, fconf in conf['filters'].items():
            plot_filter((filter, fconf), srate)
