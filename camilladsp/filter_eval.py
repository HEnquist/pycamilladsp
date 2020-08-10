import numpy as np
import numpy.fft as fft
import csv
import yaml
import sys
from matplotlib import pyplot as plt
import math

class Conv(object):
    def __init__(self, conf, fs):
        if not conf:
            conf = {"values": [1.0]}
        if 'filename' in conf:
            fname = conf['filename']
            values = []
            if 'format' not in conf:
                conf['format'] = "text"
            if conf['format'] == "text":
                with open(fname) as f:
                    values = [float(row[0]) for row in csv.reader(f)]
            elif conf['format'] == "FLOAT64LE":
                values = np.fromfile(fname, dtype=float)
            elif conf['format'] == "FLOAT32LE":
                values = np.fromfile(fname, dtype=np.float32)
            elif conf['format'] == "S16LE":
                values = np.fromfile(fname, dtype=np.int16)/(2**15-1)
            elif conf['format'] == "S24LE":
                values = np.fromfile(fname, dtype=np.int32)/(2**23-1)
            elif conf['format'] == "S32LE":
                values = np.fromfile(fname, dtype=np.int32)/(2**31-1)
        else:
            values = conf['values']
        self.impulse = values
        self.fs = fs

    def gain_and_phase(self):
        impulselen = len(self.impulse)
        npoints = impulselen
        if npoints < 300:
            npoints = 300
        impulse = np.zeros(npoints*2)
        impulse[0:impulselen] = self.impulse
        impfft = fft.fft(impulse)
        cut = impfft[0:npoints]
        f = np.linspace(0, self.fs/2.0, npoints)
        gain = 20*np.log10(np.abs(cut))
        phase = 180/np.pi*np.angle(cut)
        return f, gain, phase

    def get_impulse(self):
        t = np.linspace(0, len(self.impulse)/self.fs, len(self.impulse), endpoint=False)
        return t, self.impulse

class DiffEq(object):
    def __init__(self, conf, fs):
        self.fs = fs
        self.a = conf['a']
        self.b = conf['b']
        if len(self.a)==0:
            self.a=[1.0]
        if len(self.b)==0:
            self.b=[1.0]

    def gain_and_phase(self, f):
        z = np.exp(1j*2*np.pi*f/self.fs)
        A1=np.zeros(z.shape)
        for n, bn in enumerate(self.b):
            A1 = A1 + bn*z**(-n)
        A2=np.zeros(z.shape)
        for n, an in enumerate(self.a):
            A2 = A2 + an*z**(-n)  
        A = A1/A2  
        gain = 20*np.log10(np.abs(A))
        phase = 180/np.pi*np.angle(A)
        return f, gain, phase
    
    def is_stable(self):
        # TODO
        return None

class BiquadCombo(object):

    def Butterw_q(self, order):
        odd = order%2 > 0
        n_so = math.floor(order/2.0)
        qvalues = []
        for n in range(0, n_so):
            q = 1/(2.0*math.sin((math.pi/order)*(n + 1/2)))
            qvalues.append(q)
        if odd:
            qvalues.append(-1.0)
        return qvalues

    def __init__(self, conf, fs):
        self.ftype = conf['type']
        self.order = conf['order']
        self.freq = conf['freq']
        self.fs = fs
        if self.ftype == "LinkwitzRileyHighpass":
            #qvalues = self.LRtable[self.order]
            q_temp = self.Butterw_q(self.order/2)
            if (self.order/2)%2 > 0:
                q_temp = q_temp[0:-1]
                qvalues = q_temp + q_temp + [0.5]
            else:
                qvalues = q_temp + q_temp
            type_so = "Highpass"
            type_fo = "HighpassFO"

        elif self.ftype == "LinkwitzRileyLowpass":
            q_temp = self.Butterw_q(self.order/2)
            if (self.order/2)%2 > 0:
                q_temp = q_temp[0:-1]
                qvalues = q_temp + q_temp + [0.5]
            else:
                qvalues = q_temp + q_temp
            type_so = "Lowpass"
            type_fo = "LowpassFO"
        elif self.ftype == "ButterworthHighpass":
            qvalues = self.Butterw_q(self.order)
            type_so = "Highpass"
            type_fo = "HighpassFO"
        elif self.ftype == "ButterworthLowpass":
            qvalues = self.Butterw_q(self.order)
            type_so = "Lowpass"
            type_fo = "LowpassFO"
        self.biquads = []
        print(qvalues)
        for q in qvalues:
            if q >= 0:
                bqconf = {'freq': self.freq, 'q': q, 'type': type_so}
            else:
                bqconf = {'freq': self.freq, 'type': type_fo}
            self.biquads.append(Biquad(bqconf, self.fs))

    def is_stable(self):
        # TODO
        return None

    def gain_and_phase(self, f):
        A = np.ones(f.shape)
        for bq in self.biquads:
            A = A * bq.complex_gain(f)
        gain = 20*np.log10(np.abs(A))
        phase = 180/np.pi*np.angle(A)
        return f, gain, phase

class Biquad(object):
    def __init__(self, conf, fs):
        ftype = conf['type']
        if ftype == "Free":
            a0 = 1.0
            a1 = conf['a1']
            a2 = conf['a1']
            b0 = conf['b0']
            b1 = conf['b1']
            b2 = conf['b2']
        if ftype == "Highpass":
            freq = conf['freq']
            q = conf['q']
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / (2.0 * q)
            b0 = (1.0 + cs) / 2.0
            b1 = -(1.0 + cs)
            b2 = (1.0 + cs) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha
        elif ftype == "Lowpass":
            freq = conf['freq']
            q = conf['q']
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / (2.0 * q)
            b0 = (1.0 - cs) / 2.0
            b1 = 1.0 - cs
            b2 = (1.0 - cs) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha
        elif ftype == "Peaking":
            freq = conf['freq']
            q = conf['q']
            gain = conf['gain']
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            ampl = 10.0**(gain / 40.0)
            alpha = sn / (2.0 * q)
            b0 = 1.0 + (alpha * ampl)
            b1 = -2.0 * cs
            b2 = 1.0 - (alpha * ampl)
            a0 = 1.0 + (alpha / ampl)
            a1 = -2.0 * cs
            a2 = 1.0 - (alpha / ampl)
        elif ftype == "HighshelfFO":
            freq = conf['freq']
            gain = conf['gain']
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0**(gain / 40.0)
            tn = np.tan(omega/2)
            b0 = ampl*tn + ampl**2
            b1 = ampl*tn - ampl**2
            b2 = 0.0
            a0 = ampl*tn + 1
            a1 = ampl*tn - 1
            a2 = 0.0
        elif ftype == "Highshelf":
            freq = conf['freq']
            slope = conf['slope']
            gain = conf['gain']
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0**(gain / 40.0)
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / 2.0 * np.sqrt((ampl + 1.0 / ampl) * (1.0 / (slope/12.0) - 1.0) + 2.0)
            beta = 2.0 * np.sqrt(ampl) * alpha
            b0 = ampl * ((ampl + 1.0) + (ampl - 1.0) * cs + beta)
            b1 = -2.0 * ampl * ((ampl - 1.0) + (ampl + 1.0) * cs)
            b2 = ampl * ((ampl + 1.0) + (ampl - 1.0) * cs - beta)
            a0 = (ampl + 1.0) - (ampl - 1.0) * cs + beta
            a1 = 2.0 * ((ampl - 1.0) - (ampl + 1.0) * cs)
            a2 = (ampl + 1.0) - (ampl - 1.0) * cs - beta
        elif ftype == "LowshelfFO":
            freq = conf['freq']
            gain = conf['gain']
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0**(gain / 40.0)
            tn = np.tan(omega/2)
            b0 = ampl**2*tn + ampl
            b1 = ampl**2*tn - ampl
            b2 = 0.0
            a0 = tn + ampl
            a1 = tn - ampl
            a2 = 0.0
        elif ftype == "Lowshelf":
            freq = conf['freq']
            slope = conf['slope']
            gain = conf['gain']
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0**(gain / 40.0)
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / 2.0 * np.sqrt((ampl + 1.0 / ampl) * (1.0 / (slope/12.0) - 1.0) + 2.0)
            beta = 2.0 * np.sqrt(ampl) * alpha
            b0 = ampl * ((ampl + 1.0) - (ampl - 1.0) * cs + beta)
            b1 = 2.0 * ampl * ((ampl - 1.0) - (ampl + 1.0) * cs)
            b2 = ampl * ((ampl + 1.0) - (ampl - 1.0) * cs - beta)
            a0 = (ampl + 1.0) + (ampl - 1.0) * cs + beta
            a1 = -2.0 * ((ampl - 1.0) + (ampl + 1.0) * cs)
            a2 = (ampl + 1.0) + (ampl - 1.0) * cs - beta
        elif ftype == "LowpassFO":
            freq = conf['freq']
            omega = 2.0 * np.pi * freq / fs
            k = np.tan(omega/2.0)
            alpha = 1 + k
            a0 = 1.0
            a1 = -((1 - k)/alpha)
            a2 = 0.0
            b0 = k/alpha
            b1 = k/alpha
            b2 = 0
        elif ftype == "HighpassFO":
            freq = conf['freq']
            omega = 2.0 * np.pi * freq / fs
            k = np.tan(omega/2.0)
            alpha = 1 + k
            a0 = 1.0
            a1 = -((1 - k)/alpha)
            a2 = 0.0
            b0 = 1.0/alpha
            b1 = -1.0/alpha
            b2 = 0
        elif ftype == "Notch":
            freq = conf['freq']
            q = conf['q']
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / (2.0 * q)
            b0 = 1.0
            b1 = -2.0 * cs
            b2 = 1.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha
        elif ftype == "Bandpass":
            freq = conf['freq']
            q = conf['q']
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / (2.0 * q)
            b0 = alpha
            b1 = 0.0
            b2 = -alpha
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha
        elif ftype == "Allpass":
            freq = conf['freq']
            q = conf['q']
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = sn / (2.0 * q)
            b0 = 1.0 - alpha
            b1 = -2.0 * cs
            b2 = 1.0 + alpha
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha
        elif ftype == "AllpassFO":
            freq = conf['freq']
            omega = 2.0 * np.pi * freq / fs
            tn = np.tan(omega/2.0)
            alpha = (tn + 1.0)/(tn - 1.0)
            b0 = 1.0
            b1 = alpha
            b2 = 0.0
            a0 = alpha
            a1 = 1.0
            a2 = 0.0
        elif ftype == "LinkwitzTransform":
            f0 = conf['freq_act']
            q0 = conf['q_act']
            qt = conf['q_target']
            ft = conf['freq_target']

            d0i = (2.0 * np.pi * f0)**2
            d1i = (2.0 * np.pi * f0)/q0
            c0i = (2.0 * np.pi * ft)**2
            c1i = (2.0 * np.pi * ft)/qt
            fc = (ft+f0)/2.0

            gn = 2 * np.pi * fc/math.tan(np.pi*fc/fs)
            cci = c0i + gn * c1i + gn**2

            b0 = (d0i+gn*d1i + gn**2)/cci 
            b1 = 2*(d0i-gn**2)/cci
            b2 = (d0i - gn*d1i + gn**2)/cci
            a0 = 1.0
            a1 = 2.0 * (c0i-gn**2)/cci
            a2 = ((c0i-gn*c1i + gn**2)/cci)


        self.fs = fs
        self.a1 = a1 / a0
        self.a2 = a2 / a0
        self.b0 = b0 / a0
        self.b1 = b1 / a0
        self.b2 = b2 / a0
        
    def complex_gain(self, f):
        z = np.exp(1j*2*np.pi*f/self.fs)
        A = (self.b0 + self.b1*z**(-1) + self.b2*z**(-2))/(1.0 + self.a1*z**(-1) + self.a2*z**(-2))
        return A

    def gain_and_phase(self, f):
        A = self.complex_gain(f)
        gain = 20*np.log10(np.abs(A))
        phase = 180/np.pi*np.angle(A)
        return f, gain, phase

    def is_stable(self):
        return abs(self.a2)<1.0 and abs(self.a1) < (self.a2+1.0)
        

