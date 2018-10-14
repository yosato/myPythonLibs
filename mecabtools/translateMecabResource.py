import imp,sys,os,re,glob,copy,time
from collections import defaultdict
#import mecab2juman as m2j
from pythonlib_ys import jp_morph
from pythonlib_ys import main as myModule
import mecabtools as mtools
imp.reload(mtools)
#imp.reload(m2j)
imp.reload(jp_morph)

def convtable_check(ConvTable):
    for MecabCat,TgtCats in ConvTable.items():
        sys.stderr.write(repr(MecabCat)+': ')
        for TgtCat in TgtCats:
            sys.stderr.write(repr(TgtCat)+'\n')

def main0(OrgResDir,TgtCatFP,SrcTgtMap,DicOutDir=None,IdioDic=None,CorpusDir=None, NotRedoObjDic=True,Debug=False):
    if CorpusDir:
        CorpusFPs=glob.glob(os.path.join(CorpusDir,'*.mecab'))

        for CorpusFP in CorpusFPs:
            if mtools.dic_or_corpus(CorpusFP)!='corpus':
                sys.exit(CorpusFP+' not corpus')
            
        assert all(mtools.dic_or_corpus(CorpusFP)=='corpus' for CorpusFP in CorpusFPs)

#    translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,DicOutDir,TgtSpec='csj',Debug=Debug)
    
    if CorpusDir:
        CorpusOutDir=re.sub('/$','', CorpusDir)+'_trans'
        for CorpusFP in CorpusFPs:
            OutFP=os.path.join(CorpusOutDir,CorpusFP)
            translate_corpus(CorpusFP,DicOutDir,OutFP)

def translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,TgtSpec,Debug=False):
    if not OrgResDir:
        if not os.path.join(OrgResDir,'alphdics'):
            sys.exit('alphdic dir does not exist')
        else:
            mtools.create_indexing_dic(OrgResDir)

    ODictFPs=glob.glob(os.path.join(OrgResDir,'*.objdic.pickle'))
    SrcODictNames=set(['.'.join(os.path.basename(FP).split('.')[:-3]) for FP in ODictFPs])
    
    if len(SrcODictNames)!=1:
        sys.exit('there are too many or no objdic stems')
    SrcODictName=SrcODictNames.pop()
    if OutDir is None:
        OutDir=re.sub('/$','',OrgResDir)+'_trans'
        if not os.path.isdir(OutDir):
            os.makedirs(OutDir)
    
    TgtCats=mtools.construct_tree_from_file(TgtCatFP)
    ConvTable=mtools.create_conversion_table(mtools.MecabIPACats,TgtCats,SrcTgtMap)
    if Debug:
        convtable_check(ConvTable)
    
    for Cntr,FP in enumerate(ODictFPs):
        Alph=FP.split('.')[-3]
        AlphObjDic=myModule.load_pickle(FP)

        Errors=defaultdict(list)
        NewWds={};Dups=defaultdict(list);ECnt=0
        for WdCntr,(EssentialEls,Wd) in enumerate(AlphObjDic.items()):
            NewWd,ErrorCode=translate_word(Wd,ConvTable,TgtSpec,Debug=Debug)
            if ErrorCode:
                Errors[ErrorCode].append(Wd)
#                ECnt+=1
 #               LostCnt=sum(len(List) for ErrCat,List in Errors.items())
  #              assert(ECnt==LostCnt)
            else:
                NewEssentialVals=tuple([ NewWd.__dict__[Att] for Att in NewWd.identityatts ])
                if NewEssentialVals in NewWds.keys():
                    Dups[NewEssentialVals].append(WdCntr)
                else:
                    NewWds[NewEssentialVals]=NewWd

        OrgWdCnt=WdCntr+1
        LostCnt=sum(len(List) for ErrCat,List in Errors.items())
        assert(OrgWdCnt==len(NewWds)+LostCnt+len(Dups))
        sys.stderr.write('\nDic for "'+Alph+'", '+str(OrgWdCnt)+' wds processed, ('+str(len(Dups))+' dups) '+str(LostCnt)+' wds lost\n')
        myModule.dump_pickle(NewWds,os.path.join(OutDir,SrcODictName+'_'+Alph+'.objdic'))
        
#        if DoCorpus and Cntr==0:
#            check_corpus(SampleCorpusFP)

def translate_word(Wd,CatConvTable,TgtSpec,MaxLevel=4,Debug=False):
    InfCats=['動詞','形容詞','助動詞']
    Feats=Wd.populated_catfeats()
    if Feats not in CatConvTable.keys():
        if Debug:
            sys.stderr.write(repr(Feats)+' not found in table\n')
            sys.stderr.write(repr(Wd.__dict__)+'\n')
            time.sleep(5)
        return None,'convtable'
    TgtCats=CatConvTable[Feats][0]
    OrgCats=('cat','subcat','subcat2','sem')
    if Wd.cat in InfCats:
        (NewInfPat,NewInfForm)=process_yogen(Wd,TgtSpec)
        if any(Var is None for Var in (NewInfPat,NewInfForm)):
            if NewInfPat is None and NewInfForm is None:
                ErrorCode='infboth'
            elif NewInfPat is None:
                ErrorCode='infpat'
            else:
                ErrorCode='infform'
            return None,ErrorCode
    else:
        assert(Wd.infform=='*' and Wd.infpat=='*')
        NewInfForm='*';NewInfPat='*'
        
    NewAttsVals={}
    NewAttsVals['infform']=NewInfForm
    NewAttsVals['infpat']=NewInfPat
    NewWd=copy.deepcopy(Wd)
    NewWd.change_feats(NewAttsVals)
    
    for Ind,Cat in enumerate(OrgCats):
        if Ind+1>MaxLevel:
            break
        else:
            if Ind+1<=len(TgtCats):
                NewAttsVals[Cat]=TgtCats[Ind]
            else:
                NewAttsVals[Cat]='*'
    return NewWd,None

def process_yogen(Wd,TgtSpec):    
    NewInfF=translate_infform(Wd.infform,TgtSpec)
    NewPat,SNote=translate_infpat(Wd.infpat,Wd.lemma,TgtSpec)
    return NewPat,NewInfF


def translate_infform(MInfF,TgtSpec='csj'):
    FstTwo=MInfF[:2]
    if FstTwo in ('連用','仮定','命令','基本'):
        NewMInf=('終止' if FstTwo=='基本' else FstTwo)+'形'
    elif FstTwo=='未然':
        NewMInf='未然形' if MInfF=='未然形' else '未然形４'
    elif FstTwo=='体言':
        NewMInf='連体形'
    else:
        NewMInf=None
    return NewMInf


def translate_infpat(MInfP,Lemma,TgtSpec='csj'):
    SpecialNote=None
    DanGyo=MInfP.split('・')
    assert(len(DanGyo)<=2)
    Dan=DanGyo[0]
    Gyo=None if not DanGyo[1:] else DanGyo[1]
    if Gyo is None:
        NewGyo=''
        if Dan=='一段':
            if len(Lemma)<2:
                return None, None
            NewDan='下一段' if jp_morph.identify_dan(Lemma[-2])=='e' else '上一段'
        else:
            NewDan=Dan
    elif Dan=='カ変' or Dan=='サ変':
        NewGyo='';NewDan=Dan
    else:
        NewGyo=Gyo[:2]
        NewDan=Dan
        if len(Gyo)>=3:
            SpecialNote=Dan[2:]
    NewDanGyo=NewGyo+NewDan
    return NewDanGyo,SpecialNote

def translate_corpus(MecabCorpusFP,DstDicDir,DicStem):
    for Alph in jp_morph.Alphs:
        DstAlphDicFP=os.path.join(DstDicDir,DicStem+Alph+'.objdic')
        if os.path.isfile(DstAlphDicFP):
            DstAlphDic=myModule.load_pickle(DstAlphDicFP)
        else:
            sys.stderr.write(OrgAlphDicFP+' is not there\n')

        with open(MecabCorpusFP) as FSr:
            for LiNe in FSr:
                Line=LiNe.strip()
                LineAlph=mtools.extract_alph(Line)
                if Alph==LineAlph:
                    IAttsVals=extract_idattsvals(LiNe.strip(),mtools.IdentityAtts)
                    IVals=IAttsVals.values()

                DstWd=DstAlphDic[IVals] if IVals in DstAlphDic.keys() else reconstruct_word(IVals)
                Str=DstWd.get_mecabline()

                sys.stdout.write(Str)



def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('resdir')
    Psr.add_argument('target_scheme')
    Psr.add_argument('--out-dir',default=None)
    Psr.add_argument('--not-redo-objdic',default=True)
    Psr.add_argument('--idiodic',default=None)
    Psr.add_argument('--corpus-dir',default=None)    
    Psr.add_argument('--debug',action='store_true')

    Args=Psr.parse_args()

    assert(Args.target_scheme in ('csj','juman'))

    TagDir=os.path.join(os.getcwd(),'tagsets')
    (TgtCatFP,Mapping)= (os.path.join(TagDir,'juman_cats.txt'),mtools.MecabJumanMapping) if Args.target_scheme=='juman' else (os.path.join(TagDir,'csj_cats.txt'),mtools.MecabCSJMapping)

    if not os.path.isdir(Args.resdir) or (Args.out_dir and not os.path.isdir(Args.out_dir)) or (Args.corpus_dir and not os.path.isdir(Args.corpus_dir)):
        sys.exit('non dir specified for a dir')
    
    main0(Args.resdir, TgtCatFP, Mapping, Args.out_dir, Args.idiodic, CorpusDir=Args.corpus_dir, NotRedoObjDic=Args.not_redo_objdic,Debug=Args.debug)

if __name__=='__main__':
    main()
