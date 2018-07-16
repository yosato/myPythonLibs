import imp,sys,os
import mecab2juman as m2j
import mecabtools as mtools
imp.reload(mtools)
imp.reload(m2j)


def main0(OrgResDir,DicCorpus='both',NotRedoObjDic=True):
    if not OrgResDir:
        if not os.path.join(OrgResDir,'alphdics'):
            sys.exit('alphdic dir does not exist')
        else:
            mtools.create_indexing_dic(Args.resdir)

    PoSTable=m2j

    
    SeenFtsWds={}
    assert (mtools.dic_or_corpus(FP)==DicOrCorpus)
    with open(FP) as FSr:
        for LiNe in FSr:
            if DicOrCorpus=='corpus' and LiNe=='EOS\n':
                sys.stdout.write(LiNe)
                continue
            
            Line=LiNe.strip()
            Fts=mtools.pick_feats_fromline(Line,['orth','cat','subcat','lemma','infform','subcat2','reading'],DicOrCorpus=DicOrCorpus)
            FtsTuple=tuple(Fts)
            # this is the check of weather it's done already
            if FtsTuple in SeenFtsWds.keys():
                JumanWds=SeenFtsWds[FtsTuple]
                continue
            Fts=dict(Fts)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
            MecabWd=mtools.WordParse(Fts)
            
            JumanWds=m2j.mecabwd2jumanwd(MecabWd,PoSTable)
            SeenFtsWds[FtsTuple]=JumanWds
            for JumanWd in JumanWds:
                sys.stdout.write(JumanWd.get_jumanline()+'\n')
            

def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('resdir')
    Psr.add_argument('--not-redo-objdic',default=True)
    Psr.add_argument('--dic-corpus',default='both')
    Args=Psr.parse_args()

    if not os.path.isdir(Args.resdir):
        sys.exit(Args.resdir+' is not dir')
    
    main0(Args.resdir,DicCorpus=Args.dic_corpus,NotRedoObjdic=Args.not_redo_objdic)

if __name__=='__main__':
    main()
