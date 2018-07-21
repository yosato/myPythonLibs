import imp,sys,os,re
import mecab2juman as m2j
import mecabtools as mtools
imp.reload(mtools)
imp.reload(m2j)


def main0(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,DoCorpus=(True,CorpusFP), NotRedoObjDic=True):
    assert (DoCorpus and CorpusFP) or (not DoCorpus and not CorpusFP)
    if DoCorpus[0]:
        assert mtools.dic_or_corpus(CorpusFP)

    translate_dic(OrgResDir,TgtCapFP,SrcTgtMap,OutDir)
    if DoCorpus:
        translate_corpus(CorpusFP,OrgResDir+'/alphdics',OutDir+'/alphadics')

def translate_dic(OrgResDir,TgtCapFP,SrcTgtMap,OutDir):

    if not OrgResDir:
        if not os.path.join(OrgResDir,'alphdics'):
            sys.exit('alphdic dir does not exist')
        else:
            mtools.create_indexing_dic(Args.resdir)
    SrcODictNames=set([re.sub(r'._objdic$','',os.path.basename(FP)) for FP in glob.glob(os.path.join(OrgResDir,'objdics'))])

    if len(ODictNames)!=1:
        sys.exit('there are too many or no objdic stems')
    SrcODictName=SrcODictNames.pop()


    ConvTable=mtools.create_conversion_table(mtools.MecabIPACats,mtools.construct_tree_from_file(TgtCatFP),SrcTgtMap)
    
    NewWds={}
    for Cntr,Alph in enumerate(jp_morph.Katakanas):
        FP=os.path.join(OrgResDir,objdics,SrcODictName+Alph)
        AlphObjDic=myModule.load_pickle(FP)

        for (EssentialEls,Wd) in AlphaObjDic:
            NewWd=translate_word(Wd,ConvTable)
            NewWds[Essentials]=NewWds
        
        dump_pickle(NewWds,os.path.join(OutDir,SrcODictName+'_'+Alph+'.objdic'))

        if DicCorpus=='both' and Cntr==0:
            check_corpus(SampleCorpusFP)
    
        
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
    Psr.add_argument('src_tgt_mapping')
    Psr.add_argument('out_dir')
    Psr.add_argument('--not-redo-objdic',default=True)
    Psr.add_argument('--do-corpus',default=(False,None))
    Args=Psr.parse_args()

    if not os.path.isdir(Args.resdir) or not os.path.isdir(Args.out_dir):
        sys.exit(Args.resdir+' is not dir')
    
    main0(Args.resdir,Args.target_cat_fp,Args.src_tgt_mapping,Args.out_dir,DoCorpus=Args.do_corpus,NotRedoObjdic=Args.not_redo_objdic)

if __name__=='__main__':
    main()
