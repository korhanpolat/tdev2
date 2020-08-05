import os
import numpy as np
import editdistance
from .measures import Measure
from itertools import combinations

from tdev2.utils import read_config

class Ned(Measure):
    def __init__(self, disc, config_file, output_folder=None):
        self.metric_name = "ned"
        self.output_folder = output_folder
        self.disc = disc.clusters

        # measures
        self.n_pairs = None
        self.ned = None

        # read config params
        conf = read_config(config_file)
        self.excluded_units = conf['excluded_units']

    # @staticmethod
    def pairwise_ned(self, s1, s2):
        s1 = tuple(phn for phn in s1 if phn not in self.excluded_units)
        s2 = tuple(phn for phn in s2 if phn not in self.excluded_units)
        if max(len(s1), len(s2)) > 0:
            return float(editdistance.eval(s1, s2)) / max(len(s1), len(s2))
        else:
            return 1.0

    def compute_ned(self):
        """ compute edit distance over all discovered pairs and average across
            all pairs

            Input:
            :param disc:  a dictionnary containing all the discovered clusters.
                          Each key in the dict is a class, and its value is
                          all the intervals in this cluster.
            Output:
            :param ned:   the average edit distance of all the pairs
        """
        overall_ned = []
        for class_nb in self.disc:
            for discovered1, discovered2 in combinations(
                    self.disc[class_nb], 2):
                fname1, disc_on1, disc_off1, token_ngram1, ngram1 = discovered1
                fname2, disc_on2, disc_off2, token_ngram2, ngram2 = discovered2
                pair_ned = self.pairwise_ned(ngram1, ngram2)
                overall_ned.append(pair_ned)

        # get number of pairs and ned value
        self.n_pairs = len(overall_ned)
        if self.n_pairs > 0:
            self.ned = np.mean(overall_ned)
        else: 
            self.ned = 1.

    def write_score(self):
        if self.ned is None:
            raise AttributeError('Attempting to print scores but score'
                                 ' is not yet computed!')
        with open(os.path.join(self.output_folder, self.metric_name), 'w') as fout:
            fout.write("metric: {}\n".format(self.metric_name))
            fout.write("score: {}\n".format(self.ned))
