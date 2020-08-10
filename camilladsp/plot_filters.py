
from camilladsp.filter_eval import Biquad, BiquadCombo, Conv, DiffEq
import numpy as np
from matplotlib import pyplot as plt
import io

def plot_filter(filterconf, srate, toimage=False):
    fvect = np.linspace(1, (srate*0.95)/2.0, 1000)
    filter, fconf = filterconf
    if fconf['type'] in ('Biquad', 'DiffEq', 'BiquadCombo'):
        if fconf['type'] == 'DiffEq':
            currfilt = DiffEq(fconf['parameters'], srate)
        elif fconf['type'] == 'BiquadCombo':
            currfilt = BiquadCombo(fconf['parameters'], srate)
        else:
            currfilt = Biquad(fconf['parameters'], srate)
        plt.figure(num=filter)
        fplot, magn, phase = currfilt.gain_and_phase(fvect)
        stable = currfilt.is_stable()
        plt.subplot(2,1,1)
        plt.semilogx(fplot, magn)
        plt.title("{}, stable: {}\nMagnitude".format(filter, stable))
        plt.subplot(2,1,2)
        plt.semilogx(fvect, phase)
        plt.title("Phase")
    elif fconf['type'] == 'Conv':
        if 'parameters' in fconf:
            currfilt = Conv(fconf['parameters'], srate)
        else:
            currfilt = Conv(None, srate)
        plt.figure(num=filter)
        ftemp, magn, phase = currfilt.gain_and_phase()
        plt.subplot(2,1,1)
        plt.semilogx(ftemp, magn)
        plt.title("FFT of {}".format(filter))
        plt.gca().set(xlim=(10, srate/2.0))
        t, imp = currfilt.get_impulse()
        plt.subplot(2,1,2)
        plt.plot(t, imp)
        plt.title("Impulse response of {}".format(filter))
    if toimage:
        buf = io.BytesIO()
        plt.savefig(buf, format='svg')
        buf.seek(0)
        plt.close()
        return buf
            
def plot_filters(conf):
    srate = conf['devices']['samplerate']

    if 'filters' in conf:
        for filter, fconf in conf['filters'].items():
            plot_filter((filter, fconf), srate)
