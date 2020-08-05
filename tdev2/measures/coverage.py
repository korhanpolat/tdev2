import os
import numpy as np

from .measures import Measure


class Coverage(Measure):
    def __init__(self, gold, disc, output_folder=None):
        self.metric_name = "coverage"
        self.output_folder = output_folder

        # self.all_intervals = set()
        self.n_phones = 0

        for fname in gold.phones:
            # TODO remove SIL here ?
            self.n_phones += len([
                ph for on, off, ph in gold.phones[fname]
                if (ph != "SIL" and ph != "SPN")])

        self.covered_phn = set(
            (fname, phn_on, phn_off, phn)
            for fname, disc_on, disc_off, token_ngram, ngram
            in disc.intervals
            for phn_on, phn_off, phn in token_ngram
            if (phn != "SIL" and phn != "SPN"))

        self.coverage = 0

    def compute_coverage(self):
        """ For coverage, simply compute the ratio of discovered phones over all phone

            Input:
            :param covered_phn:  a set containing all the covered phones

            Output:
            :param coverage:     the ratio of number of covered phones over
                                 the overall number of phones in the corpus
        """
        self.coverage = len(self.covered_phn) / self.n_phones

    def write_score(self):
        if not self.coverage:
            raise AttributeError('Attempting to print scores but score'
                                 ' is not yet computed!')
        with open(os.path.join(self.output_folder, self.metric_name), 'w') as fout:
            fout.write("metric: {}\n".format(self.metric_name))
            fout.write("coverage: {}\n".format(self.coverage))



# from tdev2 import config
#excluded_units = ['SIL','__ON__','__OFF__','__EMOTION__','SPN']

from tdev2.utils import read_config

class Coverage_NoSingleton(Measure):
    def __init__(self, gold, disc, output_folder=None, config_file=None):
        self.metric_name = "coverage_nosingleton"
        self.output_folder = output_folder
        self.config_file = config_file
        
        # read config params
        conf = read_config(config_file)
        excluded_units = conf['excluded_units']
        discoverable_th = conf['discoverable_th']

        phones = []
        for fname in gold.phones:
            phones.extend([
                ph for on, off, ph in gold.phones[fname]
                if (ph not in excluded_units)])
            
        unique, counts = np.unique(phones, return_counts=True)
        discoverable_units = unique[counts>discoverable_th] # unique set of labels
        n_discoverable = np.sum(counts[counts>discoverable_th]) # total number of their occurences

        self.covered_phn = set(
            (fname, phn_on, phn_off, phn)
            for fname, disc_on, disc_off, token_ngram, ngram
            in disc.intervals
            for phn_on, phn_off, phn in token_ngram
            if ((phn not in excluded_units) and (phn in discoverable_units)))

        self.n_phones = n_discoverable

        # compute in terms of #frames, instead of #units
        self.total_covered = 0
        for (fname,phn_on, phn_off, phn) in self.covered_phn:
            self.total_covered += phn_off - phn_on
        
        self.total_discoverable = 0
        for fname in gold.phones:
            for on, off, phn in gold.phones[fname]: 
                if ((len(phn )>0) and (phn not in excluded_units) and (phn in discoverable_units)):
                    self.total_discoverable += (off-on) 

        self.coverage = 0
        self.coverage_frames = 0


    def compute_coverage(self):
        """ For coverage, simply compute the ratio of discovered units over all 'discoverable' units

            Input:
            :param covered_phn:  a set containing all the covered phones

            Output:
            :param coverage:     the ratio of number of covered phones over
                                 the overall number of phones in the corpus
        """
        self.coverage = len(self.covered_phn) / self.n_phones
        self.coverage_frames = self.total_covered / self.total_discoverable

    def write_score(self):
        if not self.coverage:
            raise AttributeError('Attempting to print scores but score'
                                 ' is not yet computed!')
        with open(os.path.join(self.output_folder, self.metric_name), 'w') as fout:
            fout.write("metric: {}\n".format(self.metric_name))
            fout.write("coverage: {}\n".format(self.coverage))



