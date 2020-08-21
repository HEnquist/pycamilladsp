# show_config.py

import numpy as np
import numpy.fft as fft
import csv
import yaml
import sys
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import math
import io

class Block(object):
    def __init__(self, label):
        self.label = label
        self.x = None
        self.y = None

    def place(self, x, y):
        self.x = x
        self.y = y

    def draw(self, ax):
        rect = Rectangle((self.x-0.5, self.y-0.25), 1.0, 0.5, linewidth=1,edgecolor='r',facecolor='none')
        ax.add_patch(rect)
        ax.text(self.x, self.y, self.label, horizontalalignment='center', verticalalignment='center')


    def input_point(self):
        return self.x-0.5, self.y

    def output_point(self):
        return self.x+0.5, self.y

def draw_arrow(ax, p0, p1, label=None):
    x0, y0 = p0
    x1, y1 = p1
    ax.arrow(x0, y0, x1-x0, y1-y0, width=0.01, length_includes_head=True, head_width=0.1)
    if y1 > y0:
        hal = 'right'
        val = 'bottom'
    else:
        hal = 'right'
        val = 'top'
    if label is not None:
        ax.text(x0+(x1-x0)*2/3, y0+(y1-y0)*2/3, label, horizontalalignment=hal, verticalalignment=val)

def draw_box(ax, level, size, label=None):
    x0 = 2*level-0.75
    y0 = -size/2
    rect = Rectangle((x0, y0), 1.5, size, linewidth=1,edgecolor='g',facecolor='none', linestyle='--')
    ax.add_patch(rect)
    if label is not None:
        ax.text(2*level, size/2, label, horizontalalignment='center', verticalalignment='bottom')


def plot_pipeline(conf, toimage=False):
    if toimage:
        matplotlib.use('Agg')
    stages = []
    fig = plt.figure(num='Pipeline')
    
    ax = fig.add_subplot(111, aspect='equal')
    # add input
    channels = []
    active_channels = int(conf['devices']['capture']['channels'])
    for n in range(active_channels):
        label = "ch {}".format(n) 
        b = Block(label)
        b.place(0, -active_channels/2 + 0.5 + n)
        b.draw(ax)
        channels.append([b])
    if 'device' in conf['devices']['capture']:
        capturename = conf['devices']['capture']['device']
    else:
        capturename = conf['devices']['capture']['filename']
    draw_box(ax, 0, active_channels, label=capturename)
    stages.append(channels)

    # loop through pipeline

    total_length = 0
    stage_start = 0
    if 'pipeline' in conf:
        for step in conf['pipeline']:
            if step['type'] == 'Mixer':
                total_length += 1
                name = step['name']
                mixconf = conf['mixers'][name]
                active_channels = int(mixconf['channels']['out'])
                channels = [[]]*active_channels
                for n in range(active_channels):
                    label = "ch {}".format(n)
                    b = Block(label)
                    b.place(total_length*2, -active_channels/2 + 0.5 + n)
                    b.draw(ax)
                    channels[n] = [b]
                for mapping in mixconf['mapping']:
                    dest_ch = int(mapping['dest'])
                    for src in mapping['sources']:
                        src_ch = int(src['channel'])
                        label = "{} dB".format(src['gain'])
                        if src['inverted'] == 'False':
                            label = label + '\ninv.'
                        src_p = stages[-1][src_ch][-1].output_point()
                        dest_p = channels[dest_ch][0].input_point()
                        draw_arrow(ax, src_p, dest_p, label=label)
                draw_box(ax, total_length, active_channels, label=name)
                stages.append(channels)
                stage_start = total_length
            elif step['type'] == 'Filter':
                ch_nbr = step['channel']
                for name in step['names']:
                    b = Block(name)
                    ch_step = stage_start + len(stages[-1][ch_nbr])
                    total_length = max((total_length, ch_step))
                    b.place(ch_step*2, -active_channels/2 + 0.5 + ch_nbr)
                    b.draw(ax)
                    src_p = stages[-1][ch_nbr][-1].output_point()
                    dest_p = b.input_point()
                    draw_arrow(ax, src_p, dest_p)
                    stages[-1][ch_nbr].append(b)


    total_length += 1
    channels = []
    for n in range(active_channels):
        label = "ch {}".format(n) 
        b = Block(label)
        b.place(2*total_length, -active_channels/2 + 0.5 + n)
        b.draw(ax)
        src_p = stages[-1][n][-1].output_point()
        dest_p = b.input_point()
        draw_arrow(ax, src_p, dest_p)
        channels.append([b])
    if 'device' in conf['devices']['playback']:
        playname = conf['devices']['playback']['device']
    else:
        playname = conf['devices']['playback']['filename']
    draw_box(ax, total_length, active_channels, label=playname)
    stages.append(channels)
    
    nbr_chan = [len(s) for s in stages]
    ylim = math.ceil(max(nbr_chan)/2.0) + 0.5
    ax.set(xlim=(-1, 2*total_length+1), ylim=(-ylim, ylim))
    plt.axis('off')
    if toimage:
        buf = io.BytesIO()
        plt.savefig(buf, format='svg')
        buf.seek(0)
        plt.close()
        return buf


def main():
    fname = sys.argv[1]

    conffile = open(fname)

    conf = yaml.safe_load(conffile)
    plot_pipeline(conf, 1)

if __name__ == "__main__":
    main()

