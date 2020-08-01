import yaml
import sys
from plot_pipeline import plot_pipeline
from plot_filters import plot_filters
from matplotlib import pyplot as plt

def main():
    fname = sys.argv[1]

    conffile = open(fname)

    conf = yaml.safe_load(conffile)

    plot_pipeline(conf, 1)
    plot_filters(conf)

    plt.show()

if __name__ == "__main__":
    main()