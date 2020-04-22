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



from tdev2 import config
#excluded_units = ['SIL','__ON__','__OFF__','__EMOTION__','SPN']
excluded_units = config.excluded_units


class Coverage_NoSingleton(Measure):
    def __init__(self, gold, disc, output_folder=None):
        self.metric_name = "coverage_nosingleton"
        self.output_folder = output_folder



        phones = []
        for fname in gold.phones:
            phones.extend([
                ph for on, off, ph in gold.phones[fname]
                if (ph not in excluded_units)])
            
        unique, counts = np.unique(phones, return_counts=True)
        discoverable_units = unique[counts>1] # unique set of labels
        n_discoverable = np.sum(counts[counts>1]) # total number of their occurences

        self.covered_phn = set(
            (fname, phn_on, phn_off, phn)
            for fname, disc_on, disc_off, token_ngram, ngram
            in disc.intervals
            for phn_on, phn_off, phn in token_ngram
            if ((phn not in excluded_units) and (phn in discoverable_units)))

        self.n_phones = n_discoverable

        self.coverage = 0


    def compute_coverage(self):
        """ For coverage, simply compute the ratio of discovered units over all 'discoverable' units

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



