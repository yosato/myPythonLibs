import imp,sys,os
import mecabtools as mtools
imp.reload(mtools)



def main0(FP,Mapping):
    DicOrCorpus=mtools.dic_or_corpus(FP)
    if DicOrCorpus:
        with open(FP) as FSr:
            for LiNe in FSr:
                if LiNe=='EOS\n':
                    NewLiNe=LiNe
                else:
                    NewLine=add_semcat(LiNe,Mapping,DicOrCorpus)
                    NewLiNe=NewLine+'\n'
                sys.stdout.write(NewLiNe)

    
def add_semcat(Line,Mapping,DicOrCorpus):
    Orth,Fts,Costs=mtools.decompose_mecabline(Line,DicOrCorpus)
    if Fts[0]=='名詞':
        Lemma=Fts[-2]
        if Lemma in Mapping.keys():
            SemCat=Mapping[Lemma]
        else:
            SemCat='*'
    else:
        SemCat='*'
    NewFts=Fts[:-2]+[SemCat[0]]+Fts[-2:]
    FtStr=','.join(NewFts)
    NonFtStr=Orth+'\t' if DicOrCorpus=='corpus' else ','.join([Orth]+Costs)+','
    return NonFtStr+FtStr

def main():
    import sem_mapping
    FP=sys.argv[1]
    Mapping={}
    Mapping.update(sem_mapping.Mapping)
    main0(FP,Mapping)
    
if __name__=='__main__':
    main()
