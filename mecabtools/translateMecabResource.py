import imp,sys,os,re,glob
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

    translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir)
    if DoCorpus:
        translate_corpus(CorpusFP,OrgResDir+'/alphdics',OutDir+'/alphadics')

def translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir):
    if not OrgResDir:
        if not os.path.join(OrgResDir,'alphdics'):
            sys.exit('alphdic dir does not exist')
        else:
            mtools.create_indexing_dic(OrgResDir)
    SrcODictNames=set(['.'.join(os.path.basename(FP).split('.')[:-3]) for FP in glob.glob(os.path.join(OrgResDir,'objdics/*.objdic.pickle'))])

    if len(SrcODictNames)!=1:
        sys.exit('there are too many or no objdic stems')
    SrcODictName=SrcODictNames.pop()
    
    JumanCats=mtools.construct_tree_from_file(TgtCatFP)
    ConvTable=mtools.create_conversion_table(mtools.MecabIPACats,JumanCats,SrcTgtMap)
    
    NewWds={}
    for Cntr,Alph in enumerate(jp_morph.GojuonStrLargeH):
        FP=os.path.join(OrgResDir,'objdics',SrcODictName+Alph)
        AlphObjDic=myModule.load_pickle(FP)

        for (EssentialEls,Wd) in AlphObjDic:
            NewWd=translate_word(Wd,ConvTable)
            NewWds[EssentialEls]=NewWd
        
        myModule.dump_pickle(NewWds,os.path.join(OutDir,SrcODictName+'_'+Alph+'.objdic'))

#        if DoCorpus and Cntr==0:
#            check_corpus(SampleCorpusFP)

def translate_word(Wd,ConvTable,MaxLevel=None):
    TgtCats=ConvTable[Wd.populated_catfeats()]
    IndsCats={0:'cat',1:'subcat',2:'subcat2',3:'sem'}
    NewAttsVals={}
    for Cntr,TgtCat in enumerate(TgtCats):
        if Cntr+1>MaxLevel:
            break
        else:
            NewAttsVals[IndsCats[Cntr]]=TgtCat
    NewWd=Wd.change_feats(NewAttsVals)
    return NewWd
        
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
    Psr.add_argument('target_cat_fp')
    Psr.add_argument('out_dir')
    Psr.add_argument('--not-redo-objdic',default=True)
    Psr.add_argument('--idiodic',default=None)
    Psr.add_argument('--do-corpus',default=False)
    Args=Psr.parse_args()

    if not os.path.isdir(Args.resdir) or not os.path.isdir(Args.out_dir):
        sys.exit(Args.resdir+' is not dir')
    
    main0(Args.resdir, Args.target_cat_fp, mtools.JumanMapping, Args.out_dir, Args.idiodic, DoCorpus=Args.do_corpus, NotRedoObjDic=Args.not_redo_objdic)

if __name__=='__main__':
    main()