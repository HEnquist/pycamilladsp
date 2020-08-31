
from camilladsp.filter_eval import Biquad, BiquadCombo, Conv, DiffEq, Gain
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
        ftemp, magn, phase = currfilt.gain_and_phase(fvect)
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

def plot_filterstep(conf, pipelineindex, name="filterstep", npoints=1000, toimage=False):
    if toimage:
        matplotlib.use('Agg')
    samplerate = conf['devices']['samplerate']
    fvect = np.logspace(np.log10(1.0), np.log10((samplerate*0.95)/2.0), num=npoints, base=10.0)
    pipelinestep = conf['pipeline'][pipelineindex]
    cgain=np.ones(fvect.shape, dtype=complex)
    for filt in pipelinestep['names']:
        filterconf = conf['filters'][filt]
        if filterconf['type'] == 'DiffEq':
            currfilt = DiffEq(filterconf['parameters'], samplerate)
        elif filterconf['type'] == 'BiquadCombo':
            currfilt = BiquadCombo(filterconf['parameters'], samplerate)
        elif filterconf['type'] == "Biquad":
            currfilt = Biquad(filterconf['parameters'], samplerate)
        elif filterconf['type'] == "Conv":
            currfilt = Conv(filterconf['parameters'], samplerate)
        elif filterconf['type'] == "Gain":
            currfilt = Gain(filterconf['parameters'])
        else:
            continue
        _, cgainstep = currfilt.complex_gain(fvect)
        cgain = cgain * cgainstep
    gain = 20 * np.log10(np.abs(cgain) + 1e-15)
    phase = 180 / np.pi * np.angle(cgain)
    plt.figure(num=name)
    plt.subplot(2,1,1)
    plt.semilogx(fvect, gain)
    plt.title(name)
    plt.ylabel("Magnitude")
    plt.subplot(2,1,2)
    plt.semilogx(fvect, phase)
    plt.ylabel("Phase")
    if toimage:
        buf = io.BytesIO()
        plt.savefig(buf, format='svg')
        buf.seek(0)
        plt.close()
        return buf

def plot_all_filtersteps(conf, npoints=1000, toimage=False):
    if 'pipeline' in conf:
        for idx, step in enumerate(conf['pipeline']):
            if step["type"] == "Filter":
                plot_filterstep(conf, idx, name="Pipeline step {}".format(idx), npoints=npoints, toimage=toimage)




