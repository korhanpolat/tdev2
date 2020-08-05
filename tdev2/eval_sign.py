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

from tdev2.utils import zrexp2tde, sdtw2tde, narrow_gold
import json
import traceback
from os.path import join

cols = [
            'ned', 'coverage', 'coverageNS', 'coverageNS_f', 
            'grouping_F', 'grouping_P', 'grouping_R', 
            'token_F', 'token_P', 'token_R', 
            'type_F', 'type_P', 'type_R',
            'boundary_F', 'boundary_P', 'boundary_R'
        ]


def prf2dict(dct, measurename, obj):
    dct[measurename + '_P'] = obj.precision
    dct[measurename + '_R'] = obj.recall
    dct[measurename + '_F'] = obj.fscore
    
    return dct


def compute_scores(gold, disc, measures=[], **kwargs):
    scores = dict()
    
    # Launch evaluation of each metric
    if len(measures) == 0 or "boundary" in measures:
        print('Computing Boundary...')
        boundary = Boundary(gold, disc)
        boundary.compute_boundary()
        scores = prf2dict(scores, 'boundary', boundary)
        
    if len(measures) == 0 or "grouping" in measures:
        print('Computing Grouping...')
        grouping = Grouping(disc,  njobs=kwargs['njobs'])
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
        coverageNS = Coverage_NoSingleton(gold, disc, config_file=kwargs['config_file'])
        coverageNS.compute_coverage()
        scores['coverageNS'] = coverageNS.coverage
        scores['coverageNS_f'] = coverageNS.coverage_frames

        
    if len(measures) == 0 or "ned" in measures:
        print('Computing NED...')
        ned = Ned(disc, config_file=kwargs['config_file'])
        ned.compute_ned()
        scores['ned'] = ned.ned
    
    scores['n_clus'] = len(disc.clusters)
    scores['n_node'] = sum([len(x) for k,x in disc.clusters.items()])

    return scores


def try_compute_scores(gold, disc, measures=[], **kwargs):
    
    # scores = dict()
    scores = {k:0.0 for k in cols}
    scores['ned'] = 1


    if len(measures) == 0: 
        measures = ['boundary', 'grouping', 'token/type', 
                    'coverage','coverageNS', 'ned']

    for measure in measures:
        try: 
            tmp_score = compute_scores(gold, disc, measures=measure, **kwargs)
            scores = {**scores, **tmp_score}

        except Exception as exc:
            print('WARNING: Computing {} scores failed ! '.format(measure))
            print(traceback.format_exc())
            print(exc)
 

    # round decimals
    for k,v in scores.items(): 
        if k in cols:
            scores[k] = round(v*100,2) 

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
                        choices=['phoenix','phoenixClean', 'mdgsClean_right', 'mdgsClean_both'],
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

    parser.add_argument('--njobs', '-n',
                        default=1,
                        type=int,
                        help="number of cpus to be used in grouping")   

    parser.add_argument('--config_file', '-cnf',
                        default='../../../config.json',
                        type=str,
                        help="path to .json file from which get the configuration")   

    args = parser.parse_args()

    kwargs = {'njobs': args.njobs, 'config_file': args.config_file}
    # load the corpus alignments
    wrd_path = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('tdev2'),
            'tdev2/share/{}.wrd'.format(args.corpus))
    phn_path = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse('tdev2'),
            'tdev2/share/{}.phn'.format(args.corpus))
 
    print('Reading gold')
    gold = Gold(wrd_path=wrd_path, 
                phn_path=phn_path,
                **kwargs)

    # select only the included files from gold 
    gold = narrow_gold(gold, args.exp_path)


    print('Generating discovered -class- file')
    if args.UTDsys == 'zr17':
        disc_clsfile = zrexp2tde(args.exp_path)
    elif args.UTDsys == 'sdtw':
        disc_clsfile = sdtw2tde(args.exp_path)

    print('Reading discovered classes')
    disc = Disc(disc_clsfile, gold) 

    output = args.output

    print('Computing scores..')
    scores = try_compute_scores(gold, disc, args.measures, **kwargs)

    # for k,v in scores.items(): print('{}:\t{:.4f}'.format(k,v))
    scores['exp_path'] = args.exp_path

    with open(args.output, 'w') as file:
        json.dump(scores, file)
    
    # save clusters info
    with open(join(args.exp_path, 'clusters_tde.json'),'w') as f:
        json.dump(disc.clusters, f)

if __name__ == "__main__": 
    main()
