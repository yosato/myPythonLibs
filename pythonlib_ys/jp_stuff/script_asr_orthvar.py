import os,sys,importlib
import jp_orth_alignment
importlib.reload(jp_orth_alignment)

def main(ASR_FP,UpTo=float('inf')):
    OrthVarPairs=[];EmptyCnt=0
    with open(ASR_FP) as FSr:
        for Cntr,Chunk in enumerate(get_chunk(FSr)):
            if not Chunk:
                EmptyCnt+=1
                continue
            if Cntr-EmptyCnt>UpTo:
                break
            if len(Chunk)!=6:
                continue
            Ref=Chunk[2]
            Pred=Chunk[3].split()[1]
            if jp_orth_alignment.orth_variant_p(Ref,Pred):
                OrthVarPairs.append((Cntr,Chunk[1],(Ref,Pred)))
    return OrthVarPairs


def get_chunk(FSr):
    Chunk=[]
    for LiNe in FSr:
        Line=LiNe.strip()
        if Line:
            Chunk.append(LiNe.strip())
        else:
            yield Chunk
            Chunk=[]

if __name__=='__main__':
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('fp')
    Psr.add_argument('--out-fp')
    Psr.add_argument('--up-to',type=float,default=float('inf'))
    Args=Psr.parse_args()
    
    OrthVars=main(Args.fp,UpTo=Args.up_to)
    Out=open(Args.out_fp,'wt') if Args.out_fp else sys.stdout
    
    for OrthVar in OrthVars:
        Out.write(OrthVar[1]+'\n')
        Out.write(OrthVar[2][0]+'\n')
        Out.write(OrthVar[2][1]+'\n')
        Out.write('\n')
