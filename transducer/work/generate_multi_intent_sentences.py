#!/usr/bin/env python2.7

from __future__ import unicode_literals
import argparse
import json
import re
import sys
import os
import glob
import numpy as np
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
import logging
from sets import Set

import transducer
import imp
imp.reload(transducer)

from os import environ
from os.path import basename, dirname, expandvars, join, isfile
#stuff to use AnnotatedUtterance and unicorn signatures
sys.path.insert(0,environ['TOOLS'])
sys.path.append(join(environ['TOOLS'], 'apps', 'unicorn'))
from annotationlib.annotated_utterance import AnnotatedUtterance
from annotationlib.app_spec import AppSpec
from unicornlib.signature import AppSpecSignatures, Signature
from unicornlib.nlutils import appspec_parsetypes
from unicornlib.parsetype import Parsetype

DEFAULT_JOINER_PHRASES = [ ' and|<unk> ', ' and|<unk> then|<unk> ' ]
InflLangs=['ja-JP','ko-KR']


np.random.seed(12345)

def main():
    with open(parse_options().config) as din:
        config = json.load(din);

    Lang=os.getenv('lang')
    LangSuffix=Lang.split('-')[-1].lower()

    if any(Lang==InflLang for InflLang in InflLangs):
        myTrans,InfWds=transducer.make_transducer_fromjsons(os.path.join(os.getenv('MORETOOLS'),'multi-intent/transducer_'+LangSuffix+'.json'),os.path.join(os.getenv('MORETOOLS'),'multi-intent/inflection_mapping_'+LangSuffix+'.json'))
   

    #the parsetypes needs to be initialized so that the replacement of : with _ works correctly in signature.py
    with codecs.open(expandvars(config['app_spec']), 'r', 'utf-8') as fhi_appspec:
        appspec_obj = AppSpec.load_from_json_file(fhi_appspec)
        Parsetype._APP_PARSETYPES = set(appspec_parsetypes(appspec_obj))

    

    component_signatures = Set() #holds list of all allowed component signatures
    signature_pairs = [] #holds the list of expanded paired component signatures and their counts. Note that pairs can now be more than 2 signatures.
    for pair in config['pairs']:
        for elem in pair[0:-1]: #There could actually be more than 2 elements in pair. The last element is the count, need to exclude it
            if elem not in config['signature_groups']:
                sys.stderr.write('[ERROR]: ' + str(elem) + ' in pairs but not in signature_groups\n')
                exit(-1)
        sig_sets = [ config['signature_groups'][x] for x in pair[0:-1] ]
        expanded_sigs = expand_signatures(sig_sets)

        for expanded_pair in expanded_sigs:
            pair_to_add = []
            for i in range(len(expanded_pair)):
                sig = str(Signature.parse(expanded_pair[i], spec='app'))
                component_signatures.add(sig)
                pair_to_add.append(sig)
            pair_to_add.append(pair[-1]) #add the count to this expanded signature
            signature_pairs.append(pair_to_add) #add this expanded signature to the signature_pairs

               
    utts_per_sig = dict() #holds lists of utterances for each component_signature

   
    if not os.path.exists(parse_options().output_data_dir):
        os.makedirs(parse_options().output_data_dir)

    with open(parse_options().output_sigs_file, 'w') as sigs_out:
        for pair in signature_pairs: #print out all the expanded signatures and initialize utts_per_sig

            sigs_out.write('+'.join(pair[0:-1]) + '\n', )
            for elem in pair[0:-1]:
                utts_per_sig[elem] = dict()

        sigs_out.close()



    #read any multi-intent regtests, and output with chunks only as they are part of training:
    if 'multi_intent_regtests_dir' in config:
        with codecs.open(join(parse_options().output_data_dir, 'regtest.wfas'), 'w', 'utf-8') as data_out:
            for dataset in glob.glob(expandvars(config['multi_intent_regtests_dir']) + '/*.fieldannotatedstring'):
                with codecs.open(expandvars(dataset), 'r', 'utf-8') as fin:
                    for line in fin:
                        anno_sent = ''
                        validate_multi_intent_annotation(line, dataset)
                        for anno_word in line.strip().split('\t')[2].split():
                            word, annot = anno_word.split('|', 1)
                            anno_sent += word + '|' + re.sub('.*<(chunk(\#\d+)?)=.*',r'<\1>', annot) + ' '
                        data_out.write('1\tauto_main\t' + 'MULTI_INTENT=chunk' + '\t' + anno_sent.rstrip(' ') + '\n')
         #we also need to create a version of the regtests file with all tags, for Acacia/seq2seq training
        with codecs.open(join(parse_options().output_data_dir, 'regtest_full_tags.wfas'), 'w', 'utf-8') as data_out:
            for dataset in glob.glob(expandvars(config['multi_intent_regtests_dir']) + '/*.fieldannotatedstring'):
                with codecs.open(expandvars(dataset), 'r', 'utf-8') as fin:
                    for line in fin:
                        data_out.write('1\t'+line)


    joiner_phrases = config['joiner_phrases'] if 'joiner_phrases' in config else DEFAULT_JOINER_PHRASES
    for indx,phrase in enumerate(joiner_phrases):
        #make sure all joiner phrases have exactly one space at beginning and end
        if type(phrase).__name__=='list':
            phrase[0]=re.sub(' +', ' ', ' '+phrase[0]+' ')
        else:
            phrase=re.sub(' +', ' ', ' '+phrase+' ')
        joiner_phrases[indx] = phrase

    for dataset in config['source_data'].keys():
        for sig in utts_per_sig.keys():
            utts_per_sig[sig].clear()
            
        for wfas_file, file_weight in config['source_data'][dataset].items():
            sys.stderr.write('[INFO]: reading ' + wfas_file + '\n')
            with codecs.open(expandvars(wfas_file), 'r', 'utf-8') as fin:
                for line in fin:
                    annostring = AnnotatedUtterance.from_annotated_string(line)
                    if annostring.field_id() != 'auto_main':
                        continue
                    sig = annostring.signature()
                    if sig not in component_signatures:
                        continue
                    utt = line.strip().split('\t')[3]
                    weight = annostring.weight() * file_weight
                    if utt in utts_per_sig[sig]: 
                        utts_per_sig[sig][utt] += weight
                    else:
                        utts_per_sig[sig][utt] = weight

        for sig in utts_per_sig.keys():
            sys.stderr.write('[INFO]: number of ' + sig + ' : ' + str(len(utts_per_sig[sig])) + '\n')

              
        #normalize weights on utterances
        for sig in utts_per_sig:
            total = 0
            for utt in utts_per_sig[sig]:
                total += utts_per_sig[sig][utt]    
            for utt in utts_per_sig[sig]:  
                utts_per_sig[sig][utt] = float(utts_per_sig[sig][utt])/float(total)


                        


        #generate the data
        with codecs.open(join(parse_options().output_data_dir, dataset+".wfas"), 'w', 'utf-8') as data_out:

            for pair in signature_pairs:
    
                no_data=False
                for sig in pair[0:-1]:
                    if len(utts_per_sig[sig]) == 0:
                        sys.stderr.write('[WARNING]: Skipping pair ' + '+'.join(pair[0:-1]) +  ' for ' + dataset + ' because no data found for signature ' + sig + '\n')
                        no_data=True
                        break

                if no_data:
                    continue

                num_samples = pair[-1]

                #sample num_samples with replacement from the list of utts for each parsetype, using the normalized utterance weights
                samples = []
                for i in range(0, len(pair)-1):
                    sample_i = np.random.choice(utts_per_sig[pair[i]].keys(), size=num_samples, replace=True, p=utts_per_sig[pair[i]].values())
                    samples.append(sample_i)


                #remove <unk>, and add <parsetype=...> tags
                pts = [0]*(len(pair)-1)
                for i in range(0, len(pair)-1):
                    pts[i] = re.sub('{.*$', '', pair[i])

                for k in range(0,num_samples):

                    #sample len(pair)-2 joiner phrases
                    utterance_joiner_phrases = []
                    if len(pair[0:-1]) > 2: #if there are more than 2 sigs in the pair, we will sample the first n-1 joiner phrases from either the empty string or the specified joiner_phrases
                        for i in range(len(pair[0:-1])-2):
                            if np.random.rand() > 0.5:
                                joiner_phrase = ' '
                            else:
                                joiner_phrase =  joiner_phrases[int(np.random.rand() * len(joiner_phrases))];
                            utterance_joiner_phrases.append(joiner_phrase)
                    joiner_phrase =  joiner_phrases[int(np.random.rand() * len(joiner_phrases))];
                    utterance_joiner_phrases.append(joiner_phrase) 

                    utt_components = []
                    if dataset == 'train':
                        utt_i = re.sub('\|<[^>]+>', '|<chunk>', samples[0][k])
                        utt_components.append(utt_i)
                        for i in range(1, len(pair)-1): #chunks > 0 get numbered
                            utt_i = re.sub('\|<[^>]+>', '|<chunk#' + str(i) + '>', samples[i][k])
                            utt_components.extend([utterance_joiner_phrases[i-1],utt_i])
                    else: #format we agreed on with the Matthieus
                        utt_i = re.sub('(?<!>)\|', '|<chunk='+pts[0]+'>|', samples[0][k]) #parsetype chunk goes first
                        utt_i = re.sub('\|<unk>', '', utt_i)
                        utt_components.append(utt_i)
                        tags_in_first = set(re.findall('<([^>]+)>', samples[0][k]))
                        for i in range(1, len(pair)-1):
                            utt_i = re.sub('(?<!>)\|', '|<chunk#' + str(i) + '=' + pts[i]+'>|', renumber_tags(samples[i][k], tags_in_first)) #tags in nth chunk need to be renumbered so they don't collide with tags in first n-1 chunks
                            utt_i = re.sub('\|<unk>', '', utt_i)
                            utt_components.extend([utterance_joiner_phrases[i-1], utt_i])
                            tags_in_first = tags_in_first | set(re.findall('<([^>]+)>', utt_i))

            
                    #print the resulting 'joined' utterance with 'and' in between in HWFAS format

                        # this is the main call for jp/kr parse, coming from Yo Sato
                    if Lang in InflLangs and type(utt_components[1]).__name__=='list':

                        InflectedUtt1=inflect_utt1(utt_components[0],myTrans,utt_components[1][1],InfWds)
                        #except:
                         #   inflect_utt1(utt_components[0],myTrans,utt_components[1][1],InfWds)
                        if InflectedUtt1 is None:
                            utt_components=[utt_components[0],joiner_phrases[0],utt_components[-1]]
                        else:
                            utt_components=[InflectedUtt1,utt_components[1][0],utt_components[-1]]


                    data_out.write('1\tauto_main\t' + 'MULTI_INTENT=chunk' + '\t' + ''.join(utt_components) + '\n')
            data_out.close()

# calling transducer to get inflected ut
def inflect_utt1(utt1,aTrans,inflSpec,InfWds):
    def separate_strstags(utt):
        strTags=utt.split()
        Strs=[];Tags=[]
        for strTag in strTags:
            Segs=strTag.split('|')
            if len(Segs)==2 :
                (Str,Tag)=Segs
                Strs.append(Str);Tags.append(Tag)
            else:
                return None
        return Strs,Tags

    def recover_tags(utt,tags):
        return newUtt
    StrsTags=separate_strstags(utt1)
    if StrsTags is None:
        return None
    else:
        Strs,Tags=StrsTags
    NewUttBase=transducer.parse_with_transducer(''.join(Strs),aTrans,inflSpec,InfWds,ReverseP=True)
    if NewUttBase:
        (InflectedStr,ConsumedStr)=NewUttBase
    else:
        return None
    InflectedUtt=[Char+'|<chunk>' for Char in InflectedStr]
    RestCnt=len(Strs)-len(ConsumedStr)-len(InflectedUtt)
    StrsTags=[Str+'|'+Tag for (Str,Tag) in zip(Strs[:RestCnt],Tags[:RestCnt])]+InflectedUtt
    newUtt1=' '.join(StrsTags)

    return newUtt1

def renumber_tags(anno_string, previous_tags_set):
    new_anno_words = []
    anno_utt = AnnotatedUtterance.from_annotated_string('dummy\t'+anno_string)
    coalesced = anno_utt.coalesce()
    for i in range(len(coalesced)):
        t = coalesced[i][1]
        if t != None:
            if t in previous_tags_set:
                inc_t = increment_tag(t)
                coalesced[i] = (coalesced[i][0], inc_t)
                previous_tags_set.add(inc_t)
            for j in range(len(coalesced[i][0])):
                new_anno_words.append(coalesced[i][0][j] + '|<' + coalesced[i][1] + '>')
        else:
            for j in range(len(coalesced[i][0])):
                new_anno_words.append(coalesced[i][0][j] + '|<unk>')

    return ' '.join(new_anno_words)


def increment_tag(tag_to_inc):
    number = re.search('#(\d+)', tag_to_inc)
    if number is not None:
        new_number = int(number.groups(0)) + 1
        tag = tag_to_inc + '#' + str(new_number)
    else:
        tag = tag_to_inc + "#1"
    return tag


def expand_signatures(siglists): #siglist should be a list of lists of signatures [ [sig1, sig2], [sig3, sig4], [sig5] ] that should be expanded combinatorially
    combined_sigs = [ [sig] for sig in siglists[0] ] #this will eventually hold a list of lists combining all possible signatures in siglist, e.g., [ [sig1, sig3, sig5], [sig2, sig3, sig5], [sig1, sig4, sig5], [sig2, sig4, sig5] ]. Start with just [ [sig1], [sig2] ]
    for i in range(1,len(siglists)):
        combined_sigs = signatures_combine(combined_sigs, siglists[i])
    return combined_sigs

def signatures_combine(partial_combined_signatures, signature_list):
    combined_signatures = []
    for combined_sig in partial_combined_signatures:
         for sig2 in signature_list:
            combined_signatures.append(combined_sig + [sig2]) #add all possible next signatures onto the previous set of signatures; append to list of all possible signatures
    return combined_signatures

def validate_multi_intent_annotation(annotatedline, filename):
    fid, pt, taggedstr = annotatedline.strip().split('\t')    
    if pt != "MULTI_INTENT=chunk":
        raise ValueError('error in ' + filename + ' expected MULTI_INTENT=chunk in parsetype field, found ' + pt)
    for anno_word in taggedstr.split():
        word, annot = anno_word.split('|', 1)
        if annot != '<unk>' and re.search('<chunk', annot) == None:
            raise ValueError('error in ' + filename + ' expected chunk tag on ' + anno_word)      


def parse_options():
    parser = argparse.ArgumentParser(description='generate utterances that are combinations of two or more intents, in valid HWFAS format. For train data, output chunk mentions only for training the splitter. For dev/blind data, output all tags for full testing in uima. ')
    parser.add_argument('config', help='json configuration listing the valid parsetype pairs and the number of samples to generate for each pair, along with valid signatures, source data and app-spec. See example_multi_intent_config.json in this directory.')
    parser.add_argument('--output_data_dir', action='store', help='the output dir for the generated data', required='true', type=str)
    parser.add_argument('--output_sigs_file', action='store', help='the output file for the generated (expanded) signatures', required='true', type=str)
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args();


    return args;


if __name__ == '__main__':
    main()
