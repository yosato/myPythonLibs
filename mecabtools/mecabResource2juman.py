import imp
import mecab2juman as m2j
import mecabtools as mtools
imp.reload(mtools)
imp.reload(m2j)


def main0(FP,PoSTable,DicOrCorpus='corpus'):
    MInhFtsJWds={}
    with open(FP) as FSr:
        for LiNe in FSr:
            Line=LiNe.strip()
            MInhFts=mtools.pick_feats_fromline(Line,['orth','cat','subcat','lemma'])
            # this is the check of weather it's done already
            if MInhFts in MInhFtsJWds.keys():
                JumanWd=MInhFtsJWds[MInhFts]
                continue
            MecabWd=mtools.MecabWordParse(MInhFts)
            JumanWd=mecabwd2jumanwd(MecabWd,PoSTable)
            Seen[MecabWd]=JumanWd
            sys.stdout.write(JumanWd.toString(),WithTailBreak=True)
            

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
