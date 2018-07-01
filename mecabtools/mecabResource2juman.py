import imp,sys
from pythonlib_ys import jp_morph
import mecab2juman as m2j
import mecabtools as mtools
imp.reload(mtools)
imp.reload(m2j)
imp.reload(jp_morph)



def main0(FP,PoSTable,DicOrCorpus,SrcDicDir):
    SeenFtsWds={}
    assert (mtools.dic_or_corpus(FP)==DicOrCorpus)
    aaa
    with open(FP) as FSr:
        for Katakana in jp_morph.GojuonStrK:
            for LiNe in FSr:
                if DicOrCorpus=='corpus' and LiNe=='EOS\n':
                    sys.stdout.write(LiNe)
                    continue
                Line=LiNe.strip()
                Fts=mtools.pick_feats_fromline(Line,['orth','cat','subcat','lemma','infform','subcat2','reading'],DicOrCorpus=DicOrCorpus)
                if Fts['reading'].startswith(Katakana):
                    
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
    Psr.add_argument('dir')
    Psr.add_argument('--dic-or-corpus',default='corpus')
    Args=Psr.parse_args()

    mtools.create_indexing_dic(Args.dir)
    PoSTable=m2j.PoSTable
    
    main0(Args.fp,PoSTable,Args.dic_or_corpus,Args.dir)

if __name__=='__main__':
    main()
