import yaml
import sys
from camilladsp.plot_pipeline import plot_pipeline
from camilladsp.plot_filters import plot_filters, plot_all_filtersteps
from matplotlib import pyplot as plt

def main():
    fname = sys.argv[1]

    conffile = open(fname)

    conf = yaml.safe_load(conffile)

    plot_pipeline(conf)
    plot_filters(conf)
    plot_all_filtersteps(conf)

    plt.show()

if __name__ == "__main__":
    main()