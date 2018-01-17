import sys,os,glob
from difflib import SequenceMatcher
from collections import defaultdict
import mecabtools
from pythonlib_ys import main as myModule

def main0(FPCorpusDir,DicDir):
    CorpusFPs=glob.glob(FPCorpusDir+'/*.KNP')
    OccDic={}
    for CorpusFP in CorpusFPs:
        OccDic=myModule.merge_countdics(OccDic,make_occurringdic(CorpusFP))
    CorrespondDics=make_corresponddic(OccDic,DicDir)
    for CorpusFP in CorpusFPs:
        render_corpus(CorpusFP,CorrespondDics)

def make_occurringdic(FP):
    Dic=defaultdict(set)
    FLineStarts=['EOS','* ','# ']
    with open(FP) as FSr:
        for LiNe in FSr:
            if any(LiNe.startswith(FLine) for FLine in FLineStarts):
                continue
            LineEls=LiNe.strip().split()
            (SF,Read,Lemma,PoS,SubCat,InfPat,InfForm)=LineEls
            Dic[(SF,PoS)].add((SubCat,InfPat,InfForm,Lemma))
    return Dic

def make_corresponddic(OccDic,DicDir,Debug=False):
    CorrespondDicUnamb=defaultdict(set);CorrespondDicAmb=defaultdict(set)
    OccSFPoSs=OccDic.keys()
#    OccSFs=[SFOcc for (SFOcc,_) in OccSFPoSs ]
    for DicFP in glob.glob(DicDir+'/*.csv'):
        with open(DicFP,errors='replace') as FSr:
            for LiNe in FSr:
                (SF,_,_,_,PoS,DSubCat,DInfPat,DInfForm,DLemma)=LiNe.strip().split(',')
                if (SF,PoS) in OccSFPoSs:
                    if len(OccDic[(SF,PoS)])==1:
                        if list(OccDic[(SF,PoS)])[0]!=(DSubCat,DInfPat,DInfForm,DLemma):
                            CorrespondDicUnamb[(SF,PoS)].add((DSubCat,DInfPat,DInfForm,DLemma))
                        else:
                            if Debug:
                                sys.stderr.write('no addition nec\n')
                    else:
                        CorrespondDicAmb[((SF,PoS),tuple(OccDic[SF,PoS]))].add((DSubCat,DInfPat,DInfForm,DLemma))
#                else:
#                    if SF in OccSFs:
 #                       CorrespondDicSFOnly[SF].add((PoS,SubCat,InfPat,InfForm,Lemma))
    CorrespondDicAmb={(SF,PoS):(set(OccItems),DicItems) for (((SF,PoS),OccItems),DicItems) in CorrespondDicAmb.items() }

    CorrespondDicAmb=disambiguate_dict(CorrespondDicAmb)
    
    return CorrespondDicUnamb,CorrespondDicAmb

def disambiguate_line(LineSet,DicSets):
        Stats=[]
        for DicSet in DicSets:
            Stats.append([SequenceMatcher(None, LineEl,DicEl).ratio() for (LineEl,DicEl) in zip(LineSet,DicSet)])
        Sums=[sum(Stat) for Stat in Stats]
        ChosenNum=Sums.index(max(Sums))
        return DicSets[ChosenNum]



def disambiguate_dict(AmbDict):
    
    def match_elements(Set1,Set2):
        L=[]
        for El1 in Set1:
            Chosen=disambiguate_line(El1,Set2)
            L.append((El1,Chosen))
        return L

    Dict=defaultdict(set)
    for ((SF,PoS),(OccSet,DicSet)) in AmbDict.items():
        Matches=match_elements(OccSet,list(DicSet))
        for OccEl,DicEl in Matches:
            Dict[(SF,PoS)+OccEl].add(DicEl)
    return Dict

    
def render_corpus(FPCorpus,CorrespondDics):
    CorrespondDicUnamb,CorrespondDicAmb=CorrespondDics
    FLineStarts=['* ','# ']
    with open(FPCorpus) as FSr:
        for LiNe in FSr:
            if any(LiNe.startswith(FLine) for FLine in FLineStarts):
                continue
            if LiNe=='EOS\n':
                NewLine='EOS'
            else:
                LineEls=LiNe.strip().split()
                (SF,Read,Lemma,PoS,SubCat,InfPat,InfForm)=LineEls
                if (SF,PoS) in CorrespondDicUnamb.keys():
                    List=list(CorrespondDicUnamb[(SF,PoS)])
                    if len(List)==1:
                        ChosenSet=(PoS,)+List[0]
                    else:
                        ChosenSet=(PoS,)+disambiguate_line((SubCat,InfPat,InfForm,Lemma),List)
                elif (SF,PoS,SubCat,InfPat,InfForm,Lemma) in CorrespondDicAmb.keys():
                    ChosenSet=(PoS,)+list(CorrespondDicAmb[(SF,PoS,SubCat,InfPat,InfForm,Lemma)])[0]
                else:
                    ChosenSet=(PoS,SubCat,InfPat,InfForm,Lemma)
                if ChosenSet[-1]=='*':
                    ChosenSet=ChosenSet[:-1]+(SF,)
                NewLine=SF+'\t'+','.join(ChosenSet)
                
            sys.stdout.write(NewLine+'\n')
            
def main():
    import argparse
    ArgPsr=argparse.ArgumentParser()
    ArgPsr.add_argument('-c','--corpus-dir',required=True)
    ArgPsr.add_argument('-d','--dic-dir',required=True)
    Args=ArgPsr.parse_args()
    if not os.path.isdir(Args.dic_dir):
        sys.exit(Args.dic_dir+' not found')
    if not os.path.isdir(Args.corpus_dir):
        sys.exit(Args.corpus_dir+' not found')
#    RootDir='/rawData'
#    FPCorpus=sys.argv[1]
#    FPCorpusDir=RootDir+'/KyotoCorpus4.0_utf8/syn'
#    FPDicDir=sys.argv[2]
#    FPDicDir=RootDir+'/mecabStdJp/mecab-jumandic_proc'
    main0(Args.corpus_dir,Args.dic_dir)

if __name__=='__main__':
    main()
    
