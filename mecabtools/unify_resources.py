import sys,os,imp,copy
import mecabtools as mtools
from collections import defaultdict
from pythonlib_ys import main as myModule
imp.reload(mtools)
imp.reload(myModule)

def main0(ResFP1,ResFP2,EssFts,AllFts):
    TwoResFPs=(ResFP1,ResFP2)
#    CorDs=[mtools.dic_or_corpus(ResFP,FullCheckP=False) for ResFP in TwoResFPs]
    CorDs=['corpus','dic']
    ResLineCnts=[myModule.get_linecount(ResFP) for ResFP in TwoResFPs]
    assert all(CorD is not None for CorD in CorDs)
    TwoResFPsWithType=zip(TwoResFPs,CorDs)
    IntFPs=[ResFP+'.singleunified' for ResFP in TwoResFPs]
    sys.stderr.write('starting extracting diffs...\n')
    unify_diffs(TwoResFPs,EssFts,AllFts,ResLineCnts=tuple(ResLineCnts),ResTypes=tuple(CorDs))

def compose_lists(Lists):
    SoFar=Lists[0]
    for List in Lists[1:]:
        SoFar=SoFar+List
        return SoFar
    
def unify_diffs(ResFPs,EssFts,AllFts,OutFP=None,ResTypes=None,ResLineCnts=None):
#    ResLineCnt=ResLineCnt if ResLineCnt is not None else myModule.get_linecount(ResFP)
    ResTypes=ResTypes if ResTypes is not None else mtools.dic_or_corpus(ResFP,FullCheckP=False)
    PickleFP=os.path.join(os.path.dirname(ResFPs[0]),myModule.merge_filenames([os.path.basename(ResFP) for ResFP in ResFPs])+'.pickle')
    (DiffDic,_),_=myModule.ask_filenoexist_execute_pickle(PickleFP,extract_resdiffs_unify,([ResFPs,EssFts,AllFts],{'ResTypes':ResTypes,'ResLineCnts':ResLineCnts}),StoreEmptyP=True)
    
    output_lineresstatssets(DiffDic.values())

def extract_resdiffs_unify(ResFPs,EssFts,AllFts,ResTypes=None,ResLineCnts=None):
    DiffDic=mtools.extract_resdiffs(ResFPs,EssFts,AllFts,ResTypes=ResTypes,ResLineCnts=ResLineCnts)
    sys.stderr.write('now unifying diffs...\n')
    UnifiedDiffDic,DiffInds=unify_normalise_resdiffs(DiffDic)
    return UnifiedDiffDic,DiffInds
        
def allequal_p(iterator):
   return len(set(iterator)) <= 1

def unify_normalise_resdiffs(OrgDiffDic):
    OrgLen=len(OrgDiffDic);ChangedInds=[];DiffDic=copy.deepcopy(OrgDiffDic)
    for Cntr,(EssAtts,LineResStats) in enumerate(DiffDic.items()):
        FtSets=LineResStats.lines
        #Freqs=LineResStats.linefreqs
        Freqs=[[len(Linums) for Linums in LRS.resslinums.values()] for LRS in LineResStats.lineresstats]
        NewFtSets=mtools.unify_normalise_ftsets(FtSets,Freqs)
        assert(len(NewFtSets)==len(FtSets))
        for LineResStat,(FtSet,NewFtSet) in zip(LineResStats.lineresstats,zip(FtSets,NewFtSets)):
            if FtSet!=NewFtSet:
                LineResStat.lineels=NewFtSet
                if Cntr not in ChangedInds:
                    ChangedInds.append(Cntr)
    assert OrgLen==len(DiffDic)
    return DiffDic,ChangedInds

def output_lineresstatssets(ResStatSets):
    '''
    for each unique 
    '''
    # get per-resource linums and lineels
    RessLinumsLineEls={}
    for ResStats in ResStatSets:
        LineElsLinums=defaultdict(list)
        for ResPath in ResStats.respathsids.keys():
            Linums=ResStats.get_linums_perres(ResPath)
            ResType=ResStats.respath2restype(ResPath)
            for ResStat in ResStats.lineresstats:
                LineEls=ResStat.lineels
                LineElsLinums[LineEls].extend(Linums)
        LinumsLineEls={tuple(Linums):LineEls for (LineEls,Linums) in LineElsLinums.items()}
        RessLinumsLineEls[(ResPath,ResType)]=LinumsLineEls
            
    for (ResPath,ResType),LinumsLineEls in RessLinumsLineEls.items():
        TgtLinums=myModule.flatten(LinumsLineEls.keys())
        OutFP=ResPath+'.unified'
        with open(OutFP,'wt') as FSw:
            with open(ResPath) as FSr:
                for Cntr,LiNe in enumerate(FSr):
                    Linum=Cntr+1
                    if Linum in TgtLinums:
                        LineEls=next(LineEls for (Linums,LineEls) in LinumsLineEls.items() if Linum in Linums)
                        if ResType=='dic':
                            NewLine=','.join([LineEls[0],'0','0','0']+LineEls[1:])
                        else:
                            NewLine=','.join(LineEls)
                        NewLiNe=NewLine+'\n'
                    else:
                        NewLiNe=LiNe
                    FSw.write(NewLiNe)
                    

        


def  pick_unifiedline_if_exist(ResFP,LinumsUnified,OutFP):
    PConsts=myModule.prepare_progressconsts(ResFP)
    MSs=None
    with open(ResFP,'rt') as FSr:
        with open(OutFP,'wt') as FSw:
            for Cntr,LiNe in enumerate(FSr):
                if Cntr!=0 and Cntr%1000==0:
                    MSs=myModule.progress_counter(MSs,PConsts,Cntr)
            
                Linum=Cntr+1
                if Linum in LinumsUnified.keys():
                    Unified=LinumsUnified[Linum]
                    NewLiNe=LiNe.strip().split()[0]+'\t'+','.join(Unified)+'\n'
                    del LinumsUnified[Linum]
                else:
                    NewLiNe=LiNe
                FSw.write(NewLiNe)
                
def unify_betweendiffs(TwoResFPs,EssFts,AllFts,ResLineCnts=(None,None,),ResTypes=(None,None,)):
    ResFP1,ResFP2=TwoResFPs
    PickleFP=os.path.join(os.path.dirname(TwoResFPs[0]),myModule.merge_filenames([os.path.basename(FP) for FP in TwoResFPs])+'.tworesdiff.pickle')
    AcrossDiff,_=myModule.ask_filenoexist_execute_pickle(PickleFP,mtools.extract_differences_tworesources,([ResFP1,ResFP2,EssFts,AllFts],{'ResLineCnts':ResLineCnts,'ResTypes':ResTypes}),StoreEmptyP=True)
    OutFPs=[ResFP+'.unified' for ResFP in TwoResFPs]
    LinumsUnified12=[{},{}]
    for FtsUnified in AcrossDiff.values():
        for (Fts1,Fts2),(Unified,(Linums1,Linums2)) in FtsUnified.items():
            if Unified:
                for Ind,Linums in zip((0,1),(Linums1,Linums2)):
                    for Linum in Linums:
                        LinumsUnified12[Ind][Linum]=Unified
    for ResFP,(LinumsUnified,OutFP) in zip(TwoResFPs,zip(LinumsUnified12,OutFPs)):
        pick_unifiedline_if_exist(ResFP,LinumsUnified,OutFP)
    

def main():
    ResFP1,ResFP2=sys.argv[1:3]
    Diffs=main0(ResFP1,ResFP2,('orth','cat','subcat','infform','infpat','pronunciation'),('orth','cat','subcat','phoneassim','infform','infpat','reading','pronunciation'))
    
if __name__=='__main__':
    main()
