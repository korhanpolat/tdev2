#!/usr/bin/env python
import time
import argparse
import pkg_resources 

from tdev2.measures.ned import *
from tdev2.measures.boundary import *
from tdev2.measures.grouping import *
from tdev2.measures.coverage import *
from tdev2.measures.token_type import *
from tdev2.readers.gold_reader import *
from tdev2.readers.disc_reader import *

from tdev2.utils import zrexp2tde, sdtw2tde
import json

def prf2dict(dct, measurename, obj):
    dct[measurename + '_P'] = obj.precision
    dct[measurename + '_R'] = obj.recall
    dct[measurename + '_F'] = obj.fscore
    
    return dct


def compute_scores(gold, disc, measures=[]):
    scores = dict()
    
    # Launch evaluation of each metric
    if len(measures) == 0 or "boundary" in measures:
        print('Computing Boundary...')
        boundary = Boundary(gold, disc)
        boundary.compute_boundary()
        scores = prf2dict(scores, 'boundary', boundary)
        
    if len(measures) == 0 or "grouping" in measures:
        print('Computing Grouping...')
        grouping = Grouping(disc)
        grouping.compute_grouping()
        scores = prf2dict(scores, 'grouping', grouping)    
        
    if len(measures) == 0 or "token/type" in measures:
        print('Computing Token and Type...')
        token_type = TokenType(gold, disc)
        token_type.compute_token_type()
        scores['token_P'],scores['token_R'],scores['token_F'] = token_type.precision[0], token_type.recall[0], token_type.fscore[0]
        scores['type_P'],scores['type_R'],scores['type_F'] = token_type.precision[1], token_type.recall[1], token_type.fscore[1]        
        
    if len(measures) == 0 or "coverage" in measures:
        print('Computing Coverage...')
        coverage = Coverage(gold, disc)
        coverage.compute_coverage()
        scores['coverage'] = coverage.coverage

        
    if len(measures) == 0 or "coverageNS" in measures:
        print('Computing Coverage No Single...')
        coverage = Coverage_NoSingleton(gold, disc)
        coverage.compute_coverage()
        scores['coverageNS'] = coverage.coverage

        
    if len(measures) == 0 or "ned" in measures:
        print('Computing NED...')
        ned = Ned(disc)
        ned.compute_ned()
        scores['ned'] = ned.ned
    
    return scores


def main():
    parser = argparse.ArgumentParser(
        prog='TDE',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Evaluate sign term discovery',
        epilog="""Example usage:
    
    $ ./english_eval2 my_sample.classes resultsdir/
    
    evaluates STD output `my_sample.classes` on the english dataset and stores the
    output in `resultsdir/`.
    
    Classfiles must be formatted like this:
    
    Class 1 (optional_name)
    fileID starttime endtime
    fileID starttime endtime
    ...
    
    Class 2 (optional_name)
    fileID starttime endtime
    ...
    """)
    parser.add_argument('exp_path', metavar='experiment_fullpath', type=str)
    parser.add_argument('corpus', metavar='language', type=str, 
                        choices=['phoenix','phoenixClean'],
                        help='Choose the corpus you want to evaluate')
    parser.add_argument('--measures', '-m',
                        nargs='*',
                        default=[],
                        choices=['boundary', 'grouping', 
                                 'token/type', 'coverage','coverageNS',
                                 'ned'])
    parser.add_argument('UTDsys', type=str, choices=['zr17','sdtw'],
                        help="type of UTD system")

    parser.add_argument('output', type=str,
                        help="path to .json file in which to write the output")

    args = parser.parse_args()

    # load the corpus alignments
    wrd_path = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('tdev2'),
            'tdev2/share/{}.wrd'.format(args.corpus))
    phn_path = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('tdev2'),
            'tdev2/share/{}.phn'.format(args.corpus))
 
    print('Reading gold')
    gold = Gold(wrd_path=wrd_path, 
                phn_path=phn_path)

    print('Generating discovered -class- file')
    if args.UTDsys == 'zr17':
        disc_clsfile = zrexp2tde(args.exp_path)
    elif args.UTDsys == 'sdtw':
        disc_clsfile = sdtw2tde(args.exp_path)

    print('Reading discovered classes')
    disc = Disc(disc_clsfile, gold) 

    measures = args.measures
    output = args.output

    print('Computing scores..')
    scores = compute_scores(gold, disc)
    scores['n_clus'] = len(disc.clusters)
    scores['n_node'] = len(disc.intervals)

    for k,v in scores.items(): print('{}:\t{:.4f}'.format(k,v))

    with open(args.output, 'w') as file:
        json.dump(scores, file)
    

if __name__ == "__main__": 
    main()
