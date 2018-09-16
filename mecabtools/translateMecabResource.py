import imp,sys,os,re,glob,copy
#import mecab2juman as m2j
from pythonlib_ys import jp_morph
from pythonlib_ys import main as myModule
import mecabtools as mtools
imp.reload(mtools)
#imp.reload(m2j)
imp.reload(jp_morph)


def main0(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,IdioDic=None,DoCorpus=False,CorpusFP=None, NotRedoObjDic=True):
    assert (DoCorpus and CorpusFP) or (not DoCorpus and not CorpusFP)
    if DoCorpus:
        assert mtools.dic_or_corpus(CorpusFP)=='dic'

    translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,TgtSpec='csj')
    if DoCorpus:
        translate_corpus(CorpusFP,OrgResDir+'/alphdics',OutDir+'/alphadics')

def translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,TgtSpec):
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
    
    NewWds={}
    for Cntr,FP in enumerate(ODictFPs):
        AlphObjDic=myModule.load_pickle(FP)

        for (EssentialEls,Wd) in AlphObjDic.items():
            NewWd=translate_word(Wd,ConvTable,TgtSpec)
            NewWds[EssentialEls]=NewWd
        
        myModule.dump_pickle(NewWds,os.path.join(OutDir,SrcODictName+'_'+Alph+'.objdic'))

#        if DoCorpus and Cntr==0:
#            check_corpus(SampleCorpusFP)

def translate_word(Wd,CatConvTable,TgtSpec,MaxLevel=4):
    Feats=Wd.populated_catfeats()
    TgtCats=CatConvTable[Feats][0]
    OrgCats=('cat','subcat','subcat2','sem')
    NewAttsVals={}
    for Ind,Cat in enumerate(OrgCats):
        if Ind+1>MaxLevel:
            break
        else:
            if Ind+1<=len(TgtCats):
                NewAttsVals[Cat]=TgtCats[Ind]
            else:
                NewAttsVals[Cat]='*'
    NewAttsVals['infform']=translate_infform(Wd.infform,TgtSpec)
    NewPat,SNote=translate_infpat(Wd.infpat,Wd.lemma,TgtSpec)
    NewAttsVals['infpat']=NewPat
    NewWd=copy.deepcopy(Wd)
    NewWd.change_feats(NewAttsVals)
    return NewWd

def translate_infform(MInfF,TgtSpec='csj'):
    FstTwo=MInfF[:2]
    if FstTwo in ('連用','仮定','命令','基本'):
        NewMInf=('終止' if FstTwo=='基本' else FstTwo)+'形'
    elif FstTwo=='未然':
        NewMInf='未然形' if NewMInf=='未然形' else '未然形４'
    elif FstTwo=='体言':
        NewMInf='連体形'
    return NewMInf
    
    
    

def translate_infpat(MInfP,Lemma,TgtSpec='csj'):
    SpecialNote=None
    DanGyo=MInfP.split('・')
    assert(len(DanGyo)<=2)
    Dan=DanGyo[0]
    Gyo=None if not DanGyo[1:] else DanGyo[1]
    if Dan=='一段':
        NewDan='下一段' if jp_morph.identify_dan(lemma[-2])=='e' else '上一段'
    else:
        NewDan=Dan
    if Dan=='カ変' or Dan=='サ変':
        NewGyo=None
    else:
        NewGyo=Gyo[:2]
        if len(Gyo)>=3:
            SpecialNote=Dan[2:]
    NewDanGyo=Gyo+Dan
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
    Psr.add_argument('out_dir')
    Psr.add_argument('--not-redo-objdic',default=True)
    Psr.add_argument('--idiodic',default=None)
    Psr.add_argument('--do-corpus',default=False)
    Args=Psr.parse_args()

    assert(Args.target_scheme in ('csj','juman'))

    TagDir=os.path.join(os.getcwd(),'tagsets')
    (TgtCatFP,Mapping)= (os.path.join(TagDir,'juman_cats.txt'),mtools.MecabJumanMapping) if Args.target_scheme=='juman' else (os.path.join(TagDir,'csj_cats.txt'),mtools.MecabCSJMapping)

    if not os.path.isdir(Args.resdir) or not os.path.isdir(Args.out_dir):
        sys.exit(Args.resdir+' is not dir')
    
    main0(Args.resdir, TgtCatFP, Mapping, Args.out_dir, Args.idiodic, DoCorpus=Args.do_corpus, NotRedoObjDic=Args.not_redo_objdic)

if __name__=='__main__':
    main()
