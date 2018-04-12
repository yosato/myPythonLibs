import copy,sys,os,time
from itertools import combinations

def main0(ClusterR,distFunc,Debug=False,UpToN=None):
    Clusters=[]
    Fst=True
    MaxClusterCnt=len(ClusterR)-1
    if UpToN is None:
        UpToN=MaxClusterCnt
    elif UpToN>MaxClusterCnt:
        sys.exit('specified count exceeds maximum')
    ClusterB=[];Cntr=0;ElCnt=len(ClusterR);SeenResults={}
    while len(Clusters)<UpToN:
        Cntr+=1
        if Fst:
            Fst=False
        else:
            IndexForSplit,_=choose_cluster2split(Clusters,distFunc)
            if Debug: print('index to split: '+str(IndexForSplit))
            ClusterR=Clusters[IndexForSplit]
            del Clusters[IndexForSplit]
        (ClusterA,ClusterB),SeenResults=split_cluster(ClusterR,ClusterB,distFunc,SeenResults)
        Clusters.append(ClusterA)
        Clusters.append(ClusterB)
#        if Debug:
 #           sys.stderr.write(repr(Clusters)+'\n')
        assert(len(Clusters)==Cntr+1)
        assert(sum(len(Cluster) for Cluster in Clusters)==ElCnt)
    return Clusters

def choose_cluster2split(Clusters,distFunc,Linkage='ave'):
    BestDiam=-float('inf')
    for (Ind,Cluster) in enumerate(Clusters):
        MaxStat,MinStat,AvStat=diffstats_list(Cluster,distFunc)
        if Linkage=='max' and MaxStat[0]>BestDiam:
            BestInd=Ind;BestDiam=MaxStat[0]
        elif Linkage=='ave' and AvStat[0]>BestDiam:
            BestInd=Ind; BestDiam=AvStat[0]
    return BestInd,BestDiam
    

def split_cluster(ClusterR,ClusterB,distFunc,SeenResults):
    OrgClusterLen=len(ClusterR);ClusterBNew=copy.copy(ClusterB)
    if OrgClusterLen==2:
        return [ClusterR[0]],[ClusterR[1]]
    CloseZeroCnt=0;CloseZeroThr=OrgClusterLen/50
    while True:
        (Dist,MaxEl),SeenResults=find_max_distance_per_elem(ClusterR,ClusterB,distFunc,SeenResults)
        print(str(len(ClusterR))+': '+str(Dist));time.sleep(2)
        if Dist<=0.01:
            CloseZeroCnt+=1
            if CloseZeroCnt>=CloseZeroThr:
                break
        ClusterR.remove(MaxEl)
        ClusterBNew.append(MaxEl)
    return (ClusterR,ClusterBNew),SeenResults
    
def diffstats_list(List,distFunc):
    if len(List)==0:
        print('diameter of list with no element does not make sense')
        return None,None,None
    elif len(List)==1:
        return (0,[]),(0,[]),(0,0)
    else:
        Inf=float('inf')
        MaxD=-Inf;MinD=Inf;Sum=0
        for Comb in combinations(List,2):
            CurD=distFunc(Comb[0],Comb[1])
            if CurD>MaxD:
                MaxD=CurD
                MaxElPair=(Comb[0],Comb[1])
            if CurD<MinD:
                MinD=CurD
                MinElPair=(Comb[0],Comb[1])
            Sum+=CurD
        return (MaxD,MaxElPair),(MinD,MinElPair),(Sum,Sum/(len(List)-1))

def dist_el_against_list(TgtEl,List,distFunc,SeenResults={}):
    Inf=float('inf')
    MaxD=-Inf;MinD=Inf;Sum=0;MaxEl=None;MinEl=None
    for El in List:
        TgtASs=tuple(sorted(list(TgtEl[-1])))
        CandASs=tuple(sorted(list(El[-1])))
        Index=(TgtASs,CandASs) if len(TgtASs)<len(CandASs) else (CandASs,TgtASs)
        if Index in SeenResults.keys():
            Dist=SeenResults[Index]
        else:
            Dist=distFunc(TgtEl,El)
            SeenResults[Index]=Dist
        if Dist<MinD:
            MinEl=El;MinD=Dist
        if Dist>MaxD:
            MaxEl=El;MaxD=Dist
        Sum+=Dist
    return ((MaxD,MaxEl),(MinD,MinEl),(Sum,0 if not List else Sum/len(List))),SeenResults
        
    
def find_max_distance_per_elem(ClusterR,ClusterB,distFunc,SeenResults):
    MaxD=-float('inf')
    for Cntr,El in enumerate(ClusterR):
        D,SeenResults=dist_clusters(El,distFunc,ClusterR,ClusterB,SeenResults)
        if D>MaxD:
            MaxEl=El
            MaxD=D
    return (MaxD,MaxEl),SeenResults

def dist_clusters(TgtEl,distFunc,ClusterAOrg,ClusterBOrg,SeenResults):
    ClusterAMinusTgt=copy.copy(ClusterAOrg)
    ClusterB=copy.copy(ClusterBOrg)
    ClusterAMinusTgt.remove(TgtEl)
#    average_d=lambda C,F:0 if len(C)<=1 else dist_el_against_list()[-1][-1]
    AvDA,SeenResults=dist_el_against_list(TgtEl,ClusterAMinusTgt,distFunc,SeenResults=SeenResults)
    AvDB,SeenResults=dist_el_against_list(TgtEl,ClusterB,distFunc,SeenResults=SeenResults)

    return AvDA[-1][-1]-AvDB[-1][-1],SeenResults


                   
def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('-f','--data-file',required=True)
    Psr.add_argument('--numerical',action='store_true')
    Psr.add_argument('--up-to-n',type=int)
    Psr.add_argument('-d','--dist-func')
    Psr.add_argument('--debug',action='store_true')
    Args=Psr.parse_args()
    if not os.path.isfile(Args.data_file):
        sys.exit('named data file ('+Args.data_file+') does not exist')
    if Args.dist_func is None:
        print('you should really set a distance function yourself!!! we use the default, i.e. product diff, this time round')
        time.sleep(2)
    with open(Args.data_file) as FSr:
        ClusterR=set(FSr.read().split())
    if Args.numerical:
        ClusterR=[float(El) for El in ClusterR]
    main0(ClusterR,distFunc=Args.dist_func,UpToN=Args.up_to_n,Debug=Args.debug)



if __name__=='__main__':
    main()
