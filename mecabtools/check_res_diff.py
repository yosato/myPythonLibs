import sys,os,imp
import mecabtools as mtools
imp.reload(mtools)

def main0(ResFP1,ResFP2,EssFts,AllFts):
    WithinDiffs=[]
    for ResFP in (ResFP1,):
        WithinDiffs.append(mtools.extract_differences_withinresource(ResFP,EssFts,AllFts))
    AccrossDiff=mtools.extract_differences_tworesources(ResFP1,ResFP2,EssFts,AllFts)
    return (WithinDiffs,AccrossDiff)

def main():
    ResFP1,ResFP2=sys.argv[1:3]
    Diffs=main0(ResFP1,ResFP2,('orth','cat','infform'),('orth','cat','subcat','phoneassim','infform','infpat','semcat','reading','pronunciation'))
    
if __name__=='__main__':
    main()
