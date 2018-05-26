import imp,sys
import mecab2juman as m2j
import mecabtools as mtools
imp.reload(mtools)
imp.reload(m2j)


def main0(FP,PoSTable,DicOrCorpus='corpus'):
    SeenFtsWds={}
    with open(FP) as FSr:
        for LiNe in FSr:
            Line=LiNe.strip()
            Fts=mtools.pick_feats_fromline(Line,['orth','cat','subcat','lemma','sem','subcat2','reading'])
            FtsTuple=tuple(Fts)
            # this is the check of weather it's done already
            if FtsTuple in SeenFtsWds.keys():
                JumanWds=SeenFtsWds[FtsTuple]
                continue
            Fts=dict(Fts)
            MecabWd=mtools.MecabWdParse(Fts)
            
            JumanWds=m2j.mecabwd2jumanwd(MecabWd,PoSTable)
            SeenFtsWds[FtsTuple]=JumanWds
            for JumanWd in JumanWds:
                sys.stdout.write(JumanWd.get_jumanline())
            

def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('fp')
    Psr.add_argument('--dic',action='store_true')
    Args=Psr.parse_args()
    PoSTable=m2j.PoSTable
    
    main0(Args.fp,PoSTable,DicOrCorpus=Args.dic)

if __name__=='__main__':
    main()
