import numpy as np
import numpy.fft as fft
import csv
import yaml
import sys
from matplotlib import pyplot as plt
import math
import itertools


class Conv(object):

    DATATYPE = {
        "FLOAT64LE": float,
        "FLOAT32LE": np.float32,
        "S16LE": np.int16,
        "S24LE": np.int32,
        "S24LE3": np.uint8,
        "S32LE": np.int32,
    }

    SCALEFACTOR = {
        "FLOAT64LE": 1.0,
        "FLOAT32LE": 1.0,
        "S16LE": (2 ** 15),
        "S24LE": (2 ** 23),
        "S24LE3": (2 ** 23),
        "S32LE": (2 ** 31),
    }

    BYTESPERSAMPLE = {
        "FLOAT64LE": 8,
        "FLOAT32LE": 4,
        "S16LE": 2,
        "S24LE": 4,
        "S24LE3": 1,
        "S32LE": 4,
    }

    def __init__(self, conf, fs):
        if not conf:
            conf = {"values": [1.0]}
        if "filename" in conf:
            values = self._read_coeffs(conf)
        else:
            values = conf["values"]
        self.impulse = values
        self.fs = fs

    def _read_coeffs(self, conf):
        fname = conf["filename"]
        if "format" not in conf:
            conf["format"] = "TEXT"
        if "read_bytes_lines" not in conf or conf["read_bytes_lines"] == 0:
            read_nbr = None
        else:
            read_nbr = conf["read_bytes_lines"]
        if "skip_bytes_lines" not in conf:
            skip_nbr = 0
        else:
            skip_nbr = conf["skip_bytes_lines"]
        if conf["format"] == "TEXT":
            values = self._read_text_coeffs(fname, skip_nbr, read_nbr)
        else:
            values = self._read_binary_coeffs(fname, conf["format"], skip_nbr, read_nbr)
        return values

    def _read_text_coeffs(self, fname, skip_lines, read_lines):
        with open(fname) as f:
            rawvalues = itertools.islice(csv.reader(f), skip_lines, read_lines)
            values = [float(row[0]) for row in rawvalues]
        return values

    def _read_binary_coeffs(self, fname, sampleformat, skip_bytes, read_bytes):

        if read_bytes is None:
            count = -1
        else:
            count = read_bytes/self.BYTESPERSAMPLE[sampleformat]

        datatype = self.DATATYPE[sampleformat]
        factor = self.SCALEFACTOR[sampleformat]
        values = (
            np.fromfile(fname, offset=skip_bytes, count=count, dtype=datatype)
        )
        if sampleformat == "S24LE3":
            values = self._repack_24bit(values)
        values = values / factor
        return values

    def _repack_24bit(self, values):
        new_values = values[0::3].astype(np.int8)*2**16 + values[1::3]*2**8 + values[2::3]
        return new_values

    def complex_gain(self, f):
        impulselen = len(self.impulse)
        npoints = impulselen
        if npoints < 1024:
            npoints = 1024
        impulse = np.zeros(npoints * 2)
        impulse[0:impulselen] = self.impulse
        impfft = fft.fft(impulse)
        f_fft = np.linspace(0, self.fs / 2.0, npoints)
        cut = impfft[0:npoints]
        cut = np.interp(f, f_fft, cut)
        return f, cut

    def gain_and_phase(self, f):
        _f, A = self.complex_gain(f)
        gain = 20 * np.log10(np.abs(A) + 1e-15)
        phase = 180 / np.pi * np.angle(A)
        return f, gain, phase

    

    def get_impulse(self):
        t = np.linspace(
            0, len(self.impulse) / self.fs, len(self.impulse), endpoint=False
        )
        return t, self.impulse


class DiffEq(object):
    def __init__(self, conf, fs):
        self.fs = fs
        self.a = conf["a"]
        self.b = conf["b"]
        if len(self.a) == 0:
            self.a = [1.0]
        if len(self.b) == 0:
            self.b = [1.0]

    def complex_gain(self, f):
        z = np.exp(1j * 2 * np.pi * f / self.fs)
        print(self.a, self.b)
        A1 = np.zeros(z.shape)
        for n, bn in enumerate(self.b):
            A1 = A1 + bn * z ** (-n)
        A2 = np.zeros(z.shape)
        for n, an in enumerate(self.a):
            A2 = A2 + an * z ** (-n)
        A = A1 / A2
        return f, A

    def gain_and_phase(self, f):
        _f, A = self.complex_gain(f)
        gain = 20 * np.log10(np.abs(A))
        phase = 180 / np.pi * np.angle(A)
        return f, gain, phase

    def is_stable(self):
        # TODO
        return None


class Gain(object):
    def __init__(self, conf):
        self.gain = conf["gain"]
        self.inverted = conf["inverted"]

    def complex_gain(self, f):
        ones = np.ones(f.shape)        
        sign = -1.0 if self.inverted else 1.0
        gain = ones * 10.0**(self.gain/20.0) * sign
        return f, gain

    def gain_and_phase(self, f):
        ones = np.ones(f.shape)        
        phaseval = 180 / np.pi if self.inverted else 0
        gain = ones * self.gain
        phase = ones * phaseval
        return f, gain, phase

    def is_stable(self):
        return True


class BiquadCombo(object):
    def Butterw_q(self, order):
        odd = order % 2 > 0
        n_so = math.floor(order / 2.0)
        qvalues = []
        for n in range(0, n_so):
            q = 1 / (2.0 * math.sin((math.pi / order) * (n + 1 / 2)))
            qvalues.append(q)
        if odd:
            qvalues.append(-1.0)
        return qvalues

    def __init__(self, conf, fs):
        self.ftype = conf["type"]
        self.order = conf["order"]
        self.freq = conf["freq"]
        self.fs = fs
        if self.ftype == "LinkwitzRileyHighpass":
            # qvalues = self.LRtable[self.order]
            q_temp = self.Butterw_q(self.order / 2)
            if (self.order / 2) % 2 > 0:
                q_temp = q_temp[0:-1]
                qvalues = q_temp + q_temp + [0.5]
            else:
                qvalues = q_temp + q_temp
            type_so = "Highpass"
            type_fo = "HighpassFO"

        elif self.ftype == "LinkwitzRileyLowpass":
            q_temp = self.Butterw_q(self.order / 2)
            if (self.order / 2) % 2 > 0:
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
                bqconf = {"freq": self.freq, "q": q, "type": type_so}
            else:
                bqconf = {"freq": self.freq, "type": type_fo}
            self.biquads.append(Biquad(bqconf, self.fs))

    def is_stable(self):
        # TODO
        return None

    def complex_gain(self, f):
        A = np.ones(f.shape)
        for bq in self.biquads:
            _f, Atemp = bq.complex_gain(f)
            A = A * Atemp
        return f, A

    def gain_and_phase(self, f):
        _f, A = self.complex_gain(f)
        gain = 20 * np.log10(np.abs(A))
        phase = 180 / np.pi * np.angle(A)
        return f, gain, phase


class Biquad(object):
    def __init__(self, conf, fs):
        ftype = conf["type"]
        if ftype == "Free":
            a0 = 1.0
            a1 = conf["a1"]
            a2 = conf["a1"]
            b0 = conf["b0"]
            b1 = conf["b1"]
            b2 = conf["b2"]
        if ftype == "Highpass":
            freq = conf["freq"]
            q = conf["q"]
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
            freq = conf["freq"]
            q = conf["q"]
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
            freq = conf["freq"]
            q = conf["q"]
            gain = conf["gain"]
            omega = 2.0 * np.pi * freq / fs
            sn = np.sin(omega)
            cs = np.cos(omega)
            ampl = 10.0 ** (gain / 40.0)
            alpha = sn / (2.0 * q)
            b0 = 1.0 + (alpha * ampl)
            b1 = -2.0 * cs
            b2 = 1.0 - (alpha * ampl)
            a0 = 1.0 + (alpha / ampl)
            a1 = -2.0 * cs
            a2 = 1.0 - (alpha / ampl)
        elif ftype == "HighshelfFO":
            freq = conf["freq"]
            gain = conf["gain"]
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0 ** (gain / 40.0)
            tn = np.tan(omega / 2)
            b0 = ampl * tn + ampl ** 2
            b1 = ampl * tn - ampl ** 2
            b2 = 0.0
            a0 = ampl * tn + 1
            a1 = ampl * tn - 1
            a2 = 0.0
        elif ftype == "Highshelf":
            freq = conf["freq"]
            slope = conf["slope"]
            gain = conf["gain"]
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0 ** (gain / 40.0)
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = (
                sn
                / 2.0
                * np.sqrt((ampl + 1.0 / ampl) * (1.0 / (slope / 12.0) - 1.0) + 2.0)
            )
            beta = 2.0 * np.sqrt(ampl) * alpha
            b0 = ampl * ((ampl + 1.0) + (ampl - 1.0) * cs + beta)
            b1 = -2.0 * ampl * ((ampl - 1.0) + (ampl + 1.0) * cs)
            b2 = ampl * ((ampl + 1.0) + (ampl - 1.0) * cs - beta)
            a0 = (ampl + 1.0) - (ampl - 1.0) * cs + beta
            a1 = 2.0 * ((ampl - 1.0) - (ampl + 1.0) * cs)
            a2 = (ampl + 1.0) - (ampl - 1.0) * cs - beta
        elif ftype == "LowshelfFO":
            freq = conf["freq"]
            gain = conf["gain"]
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0 ** (gain / 40.0)
            tn = np.tan(omega / 2)
            b0 = ampl ** 2 * tn + ampl
            b1 = ampl ** 2 * tn - ampl
            b2 = 0.0
            a0 = tn + ampl
            a1 = tn - ampl
            a2 = 0.0
        elif ftype == "Lowshelf":
            freq = conf["freq"]
            slope = conf["slope"]
            gain = conf["gain"]
            omega = 2.0 * np.pi * freq / fs
            ampl = 10.0 ** (gain / 40.0)
            sn = np.sin(omega)
            cs = np.cos(omega)
            alpha = (
                sn
                / 2.0
                * np.sqrt((ampl + 1.0 / ampl) * (1.0 / (slope / 12.0) - 1.0) + 2.0)
            )
            beta = 2.0 * np.sqrt(ampl) * alpha
            b0 = ampl * ((ampl + 1.0) - (ampl - 1.0) * cs + beta)
            b1 = 2.0 * ampl * ((ampl - 1.0) - (ampl + 1.0) * cs)
            b2 = ampl * ((ampl + 1.0) - (ampl - 1.0) * cs - beta)
            a0 = (ampl + 1.0) + (ampl - 1.0) * cs + beta
            a1 = -2.0 * ((ampl - 1.0) + (ampl + 1.0) * cs)
            a2 = (ampl + 1.0) + (ampl - 1.0) * cs - beta
        elif ftype == "LowpassFO":
            freq = conf["freq"]
            omega = 2.0 * np.pi * freq / fs
            k = np.tan(omega / 2.0)
            alpha = 1 + k
            a0 = 1.0
            a1 = -((1 - k) / alpha)
            a2 = 0.0
            b0 = k / alpha
            b1 = k / alpha
            b2 = 0
        elif ftype == "HighpassFO":
            freq = conf["freq"]
            omega = 2.0 * np.pi * freq / fs
            k = np.tan(omega / 2.0)
            alpha = 1 + k
            a0 = 1.0
            a1 = -((1 - k) / alpha)
            a2 = 0.0
            b0 = 1.0 / alpha
            b1 = -1.0 / alpha
            b2 = 0
        elif ftype == "Notch":
            freq = conf["freq"]
            q = conf["q"]
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
            freq = conf["freq"]
            q = conf["q"]
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
            freq = conf["freq"]
            q = conf["q"]
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
            freq = conf["freq"]
            omega = 2.0 * np.pi * freq / fs
            tn = np.tan(omega / 2.0)
            alpha = (tn + 1.0) / (tn - 1.0)
            b0 = 1.0
            b1 = alpha
            b2 = 0.0
            a0 = alpha
            a1 = 1.0
            a2 = 0.0
        elif ftype == "LinkwitzTransform":
            f0 = conf["freq_act"]
            q0 = conf["q_act"]
            qt = conf["q_target"]
            ft = conf["freq_target"]

            d0i = (2.0 * np.pi * f0) ** 2
            d1i = (2.0 * np.pi * f0) / q0
            c0i = (2.0 * np.pi * ft) ** 2
            c1i = (2.0 * np.pi * ft) / qt
            fc = (ft + f0) / 2.0

            gn = 2 * np.pi * fc / math.tan(np.pi * fc / fs)
            cci = c0i + gn * c1i + gn ** 2

            b0 = (d0i + gn * d1i + gn ** 2) / cci
            b1 = 2 * (d0i - gn ** 2) / cci
            b2 = (d0i - gn * d1i + gn ** 2) / cci
            a0 = 1.0
            a1 = 2.0 * (c0i - gn ** 2) / cci
            a2 = (c0i - gn * c1i + gn ** 2) / cci

        self.fs = fs
        self.a1 = a1 / a0
        self.a2 = a2 / a0
        self.b0 = b0 / a0
        self.b1 = b1 / a0
        self.b2 = b2 / a0

    def complex_gain(self, f):
        z = np.exp(1j * 2 * np.pi * f / self.fs)
        A = (self.b0 + self.b1 * z ** (-1) + self.b2 * z ** (-2)) / (
            1.0 + self.a1 * z ** (-1) + self.a2 * z ** (-2)
        )
        return f, A

    def gain_and_phase(self, f):
        _f, A = self.complex_gain(f)
        gain = 20 * np.log10(np.abs(A))
        phase = 180 / np.pi * np.angle(A)
        return f, gain, phase

    def is_stable(self):
        return abs(self.a2) < 1.0 and abs(self.a1) < (self.a2 + 1.0)

