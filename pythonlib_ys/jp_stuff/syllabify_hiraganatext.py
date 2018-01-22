import sys,os,string,imp
import jp_morph
imp.reload(jp_morph)

WSs=list(string.whitespace)
OrthsSyls={Syl.orth:Syl for Syl in jp_morph.Syllables}


def main0(FP,Delim='\n',EOS='\n',OutFP=None):
    Out=sys.stdout if OutFP is None else open(OutFP,'wt')
    with open(FP) as FSr:
        for LiNe in FSr:
            SylOrths=[]
            for Char in LiNe.strip():
                if Char in WSs:
                    continue
                if Char in ('ゃ','ゅ','ょ','ぅ','ぃ','ぇ'):
                    SylOrths[-1]=SylOrths[-1]+Char
                else:
                    SylOrths.append(Char)
            for Orth in SylOrths:
                if Orth not in OrthsSyls.keys():
                    Syl=jp_morph.Syllable(Orth)
                else:
                    Syl=OrthsSyls[Orth]
                FtStrs=Syl.feat_strs()
                Out.write('\t'.join([Orth]+FtStrs)+'\n')


def main():
    FP='/rawData/KyotoCorpus4.0_utf8/all_hiragana.txt'
    if not os.path.isfile(FP):
        sys.exit(FP+'does not exist')
    main0(FP)

if __name__=='__main__':
    main()
