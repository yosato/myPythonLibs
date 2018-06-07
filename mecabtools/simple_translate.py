import os,sys,imp
import mecabtools
imp.reload(mecabtools)

def main0(SrcResFP,TgtDicFPs):
    mecabtools.simpletranslate_resources(SrcResFP,'corpus',['orth','cat','subcat','subcat2','infform','infpat','lemma','pronunciation'],TgtDicFPs,'dic',['orth','cat','subcat','subcat2','sem','infform','infpat','lemma','reading','pronunciation'])

def main():
    import argparse,glob
    Psr=argparse.ArgumentParser()
    Psr.add_argument('srcfp')
    Psr.add_argument('tgtdir')
    Args=Psr.parse_args()
    DicFPs=glob.glob(Args.tgtdir+'/*.csv')
    if not DicFPs:
        sys.exit('no dics found')
    main0(Args.srcfp,DicFPs)
if __name__=='__main__':
    main()
