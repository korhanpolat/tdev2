"""Set of functions used by the metrics.

   check_boundary: check if a phone is covered by checking
                   if the discovered interval overlaps with
                   at least either 50% of the phone duration
                   or 30ms of the phone duration.

   overlap:        return the percentage of overlap and the
                   duration (in seconds) of the overlap
                   between two intervals.
                   The percentage is computed w.r. to the
                   second interval (i.e. if the first completely
                   overlaps the second one, even if the first is bigger,
                   ov=1.0)
"""

import os
from tdev2 import config


ovth = config.overlap_th


def write_disc_class_file(dedups_, nodes_, outfile):
    # creating the output class used by eval
    t_ = ''
    for n, class_ in enumerate(dedups_, start=1):
        t_ += 'Class {}\n'.format(n)
        for element in class_:
            file_, start_, end_ = nodes_[element]
            t_ += '{} {:.2f} {:.2f}\n'.format(file_, start_, end_)
        t_ += '\n'

    # stdout or save to file file
    if outfile is None:
        print(t_)
    else:
        with open(outfile, 'w') as output:
            output.write(t_) 



def zr2tde(nodesfile, dedupsfile, outfile):
    # Decode nodes file
    nodes_ = dict()
    with open(nodesfile) as nodes:
        for n, node in enumerate(nodes, start=1):
            try:
                wavfile, start, end  = node.split()[:3]
                nodes_[n] = [wavfile, float(start)/1.0, float(end)/1.0] 
            except:
                raise 

    # decode dedups file
    dedups_ = list()
    with open(dedupsfile) as dedups:
        for dedup in dedups:
            try:
                dedups_.append([int(n) for n in dedup.split() ])  
            except:
                raise

    write_disc_class_file(dedups_, nodes_, outfile)



def zrexp2tde(exp_path):

    nodesfile = os.path.join(exp_path, 'results','master_graph.nodes')
    dedupsfile = os.path.join(exp_path, 'results','master_graph.dedups')
    outfile = os.path.join(exp_path, 'results','master_graph.class')
    zr2tde(nodesfile, dedupsfile, outfile)
    
    return outfile 



def sdtw2tde(postdisc_path):

    import pandas as pd
    import pickle 

    with open(os.path.join(postdisc_path,'clusters.pkl'),'rb') as f: 
        dedups_ = pickle.load(f)

    nodes_df = pd.read_pickle(os.path.join(postdisc_path,'nodes.pkl'))
    subset = nodes_df[['filename','start','end']]
    # very important, in order to let index start from 1
    nodes_ = [None] + [tuple(x) for x in subset.to_numpy()] 

    outfile = os.path.join(postdisc_path,'master_graph.class')

    write_disc_class_file(dedups_, nodes_, outfile)

    return outfile



def select_included_seqs_from_gold(seqs_included, gold ):
    # select boundaries    
    allkeys = gold.boundaries[0].keys()
    for key in list(allkeys):
        if key not in seqs_included:
            for i in range(2):
                gold.boundaries[i].pop(key)
    
    # select phones
    gold.phones = { name: gold.phones[name] for name in seqs_included }
    
    # select words
    gold.words = { name: gold.words[name] for name in seqs_included }
    
    return gold


def narrow_gold(gold, seqfiledir):

    with open(os.path.join(seqfiledir, 'seq_names.txt'), 'r') as f: 
        seqs_included = f.read().split('\n')

    return select_included_seqs_from_gold(seqs_included, gold )


def check_boundary(gold_times, disc_times):
    """ Consider phone discovered if the found interval overlaps
        with either more thant 50% or more than 'ovth' of the
        gold phone.

        Input
        :param gold_times: tuples, contains the timestamps of the gold phone
        :type gold_times:  tuples of float
        :param disc_times: tuples: contains the timestamps of the
                                   discovered phone
        :type disc_times:  tuples of float
        :param ovth: overlap threshold, include transcription if more than 'ovth'
        :type ovth:  float

        Output
        :return:           Bool, True if phone is considered discovered,
                           False otherwise
    """

    gold_dur = round(gold_times[1] - gold_times[0], 3)
    ov, ov_time = overlap(disc_times, gold_times)

    # if gold phone is over 2*'ovth', rule is phone is considered if
    # overlap is over 'ovth'. Else, rule is phone considered if
    # overlap is over 50% of phone duration.
    if ((gold_dur >= 2*ovth and ov_time >= ovth) or
       (gold_dur < 2*ovth and ov >= 0.5)):
        return True
    elif ((gold_dur >= 2*ovth and ov_time < ovth) or
          (gold_dur < 2*ovth and ov < 0.5)):
        return False

def overlap(disc, gold):
    ov = (min(disc[1], gold[1]) - max(disc[0], gold[0])) \
        / (gold[1] - gold[0])
    time = round(min(disc[1], gold[1]) - max(disc[0], gold[0]), 3)
    return ov, time
