
from camilladsp.filter_eval import Biquad, BiquadCombo, Conv, DiffEq
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import io

def plot_filter(filterconf, name=None, samplerate=44100, npoints=1000, toimage=False):
    if toimage:
        matplotlib.use('Agg')
    fvect = np.logspace(np.log10(1.0), np.log10((samplerate*0.95)/2.0), num=npoints, base=10.0)
    if name is None:
        name = "unnamed {}".format(filterconf['type'])
    if filterconf['type'] in ('Biquad', 'DiffEq', 'BiquadCombo'):
        if filterconf['type'] == 'DiffEq':
            currfilt = DiffEq(filterconf['parameters'], samplerate)
        elif filterconf['type'] == 'BiquadCombo':
            currfilt = BiquadCombo(filterconf['parameters'], samplerate)
        else:
            currfilt = Biquad(filterconf['parameters'], samplerate)
        plt.figure(num=name)
        fplot, magn, phase = currfilt.gain_and_phase(fvect)
        stable = currfilt.is_stable()
        plt.subplot(2,1,1)
        plt.semilogx(fplot, magn)
        plt.title("{}, stable: {}".format(name, stable))
        plt.ylabel("Magnitude")
        plt.subplot(2,1,2)
        plt.semilogx(fvect, phase)
        plt.ylabel("Phase")
    elif filterconf['type'] == 'Conv':
        if 'parameters' in filterconf:
            currfilt = Conv(filterconf['parameters'], samplerate)
        else:
            currfilt = Conv(None, samplerate)
        plt.figure(num=name)
        ftemp, magn, phase = currfilt.gain_and_phase()
        plt.subplot(2,1,1)
        plt.semilogx(ftemp, magn)
        plt.title("{}".format(name))
        plt.ylabel("Magnitude")
        plt.gca().set(xlim=(10, samplerate/2.0))
        t, imp = currfilt.get_impulse()
        plt.subplot(2,1,2)
        plt.plot(t, imp)
        plt.ylabel("Impulse response")
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
            plot_filter(fconf, samplerate=srate, name=filter)
