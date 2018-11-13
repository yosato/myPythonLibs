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

def main0(OrgResDir,TgtScheme,DicOutDir=None,IdioDic=None,CorpusDir=None, NotRedoObjDic=True,MakeTextDicToo=False,Strict=False,Debug=False):

    TagDir=os.path.join(os.getcwd(),'tagsets')
    (TgtCatFP,Mapping)= (os.path.join(TagDir,'juman_cats.txt'),mtools.MecabJumanMapping) if TgtScheme=='juman' else (os.path.join(TagDir,'csj_cats.txt'),mtools.MecabCSJMapping)

    if DicOutDir is None:
        DicOutDir=re.sub('/$','',OrgResDir)+'_trans_'+TgtScheme
        if not os.path.isdir(DicOutDir):
            os.makedirs(DicOutDir)
    ODicOutDir=os.path.join(DicOutDir,'objdics')
    if not os.path.isdir(ODicOutDir):
        os.makedirs(ODicOutDir)
    if not MakeTextDicToo:
        TDicOutDir=None
    else:
        TDicOutDir=os.path.join(DicOutDir,'textdics')
        if not os.path.isdir(TDicOutDir):
            os.makedirs(TDicOutDir)

    if CorpusDir:
        CorpusFPs=glob.glob(os.path.join(CorpusDir,'*.mecab'))
        ProblemFiles=[]
        for CorpusFP in CorpusFPs:
            if mtools.dic_or_corpus(CorpusFP)!='corpus':
                ProblemFiles.append(CorpusFP)
        if ProblemFiles:
            sys.stderr.write('problem corpus files '+repr(ProblemFiles)+'\n')
            if Strict:
                sys.exit()
            else:
                CorpusFPs=list(set(CorpusFPs)-set(ProblemFiles))
            
        assert all(mtools.dic_or_corpus(CorpusFP)=='corpus' for CorpusFP in CorpusFPs)

    translate_dic(OrgResDir,TgtCatFP,Mapping,ODicOutDir,TDicOutDir=TDicOutDir,TgtSpec='csj',Debug=Debug,MakeTextDicToo=MakeTextDicToo)
    
    if CorpusDir:
        CorpusOutDir=re.sub('/$','', CorpusDir)+'_trans_'+TgtScheme
        for CorpusFP in CorpusFPs:
            OutFP=myModule.change_ext(os.path.join(CorpusOutDir,CorpusFP),TgtScheme)
            translate_corpus(CorpusFP,DicOutDir)

def translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,TgtSpec,TDicOutDir=None,MakeTextDicToo=False,Debug=False):
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
            NewWd,ErrorCode=translate_word(Wd,ConvTable,TgtSpec,NewInhAtts=('orth','cat','subcat','lemma','infpat','infform','reading'),Debug=Debug)
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
        FNStem=SrcODictName+'_'+Alph
        myModule.dump_pickle(NewWds,os.path.join(OutDir,FNStem+'.objdic'))
        if TDicOutDir:
            output_textdic(NewWds,os.path.join(TDicOutDir,FNStem+'.textdic'))
        
#        if DoCorpus and Cntr==0:
#            check_corpus(SampleCorpusFP)

def output_textdic(Dict,FP):
    with open(FP,'wt') as FSw:
        for Wd in Dict.values():
            FSw.write(Wd.get_mecabline()+'\n')

def translate_word(Wd,CatConvTable,TgtSpec,NewInhAtts=None,MaxLevel=4,Debug=False):
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
    if NewInhAtts:
        NewWd.inhatts=NewInhAtts
    
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

def translate_corpus(MecabCorpusFP,ObjDicDir):
    CorpusEssAttsLines=mtools.extract_identityattvals(MecabCorpusFP,'corpus',['cat','lemma','infform'])
    CorpusEssAtts=set(CorpusEssAttsLines.keys())
    ObjDicFPs=glob.glob(ObjDicDir+'/*.pickle')
    FndWds={}
    for ObjDicFP in ObjDicFPs:
        ObjDic=myModule.load_pickle(ObjDicFP)
        for DicEssAtt in ObjDic.keys():
            if DicEssAtt in CorpusEssAtts:
                FndWds[CorpusEssAttsLines[DicEssAtt]]=ObjDic[DicEssAtt]
        
    with open(MecabCorpusFP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if LiNe=='EOS\n':
                TransWdStr=LiNe.strip()
            else:
                WdIfFnd=next((Wd for (Inds,Wd) in FndWds.items() if Cntr in Inds), None)
                if WdIfFnd is None:
                    TransWdStr=fallback_trans('FALLBACK\t'+LiNe.strip())
                else:
                    TransWdStr=WdIfFnd.get_mecabline()

            sys.stdout.write(TransWdStr+'\n')
            
def fallback_trans(Line):
    return Line
    



def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('resdir')
    Psr.add_argument('target_scheme')
    Psr.add_argument('--out-dir',default=None)
    Psr.add_argument('--not-redo-objdic',default=True)
    Psr.add_argument('--idiodic',default=None)
    Psr.add_argument('--corpus-dir',default=None)
    Psr.add_argument('--textdic-too',action='store_true')
    Psr.add_argument('--debug',action='store_true')

    Args=Psr.parse_args()

    assert(Args.target_scheme in ('csj','juman'))

    if not os.path.isdir(Args.resdir) or (Args.out_dir and not os.path.isdir(Args.out_dir)) or (Args.corpus_dir and not os.path.isdir(Args.corpus_dir)):
        sys.exit('non dir specified for a dir')
    
    main0(Args.resdir, Args.target_scheme, Args.out_dir, Args.idiodic, CorpusDir=Args.corpus_dir, NotRedoObjDic=Args.not_redo_objdic,MakeTextDicToo=Args.textdic_too,Debug=Args.debug)

if __name__=='__main__':
    main()
