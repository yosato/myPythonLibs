import copy,sys,os
from itertools import combinations

def main0(ClusterR,distFunc,Debug=False,UpToN=None):
    Clusters=[]
    Fst=True
    MaxClusterCnt=len(ClusterR)-1
    if UpToN is None:
        UpToN=MaxClusterCnt
    elif UpToN>MaxClusterCnt:
        sys.exit('specified count exceeds maximum')
    ClusterB=[];Cntr=0;ElCnt=len(ClusterR)
    while len(Clusters)<=UpToN:
        Cntr+=1
        if Fst:
            Fst=False
        else:
            IndexForSplit,_=choose_cluster2split(Clusters,distFunc)
            if Debug: print('index to split: '+str(IndexForSplit))
            ClusterR=Clusters[IndexForSplit]
            del Clusters[IndexForSplit]
        (ClusterA,ClusterB)=split_cluster(ClusterR,distFunc)
        Clusters.append(ClusterA)
        Clusters.append(ClusterB)
        if Debug:
            sys.stderr.write(repr(Clusters)+'\n')
        assert(len(Clusters)==Cntr+1)
        assert(sum(len(Cluster) for Cluster in Clusters)==ElCnt)
    return Clusters

def choose_cluster2split(Clusters,distFunc):
    MaxDiam=-float('inf')
    for (Ind,Cluster) in enumerate(Clusters):
        MaxStat,_,_=diffstats_list(Cluster,distFunc)
        if MaxStat[0]>MaxDiam:
            MaxDiam=MaxStat[0];MaxInd=Ind
    return MaxInd,MaxDiam
    

def split_cluster(ClusterR,distFunc):
    if len(ClusterR)==2:
        return [ClusterR[0]],[ClusterR[1]]
    ClusterB=[]
    while True:
        Dist,MaxEl=find_max_distance_per_elem(ClusterR,ClusterB,distFunc)
        print(Dist)
        if Dist<=0:
            break
        else:
            ClusterR.remove(MaxEl)
            ClusterB.append(MaxEl)
            
    
    return ClusterR,ClusterB
    
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

def find_max_distance_per_elem(ClusterR,ClusterB,distFunc):
    PrvMaxD=-float('inf')
    for Cntr,El in enumerate(ClusterR):
        MaxD=dist_clusters(El,distFunc,ClusterR,ClusterB)
        if MaxD>PrvMaxD:
            MaxEl=El
            PrvMaxD=MaxD
    return MaxD,MaxEl

def el_against_list_distancesum(TgtEl,List,distFunc):
    DistSum=0
    for El in List:
        DistSum+=distFunc(TgtEl,El)
    return DistSum

def el_against_list_av(TgtEl,List,distFunc):
    if len(List)==0:
        Av=0
    else:
        Av=el_against_list_distancesum(TgtEl,List,distFunc)/len(List)
    return Av

def dist_clusters(TgtEl,distFunc,ClusterAOrg,ClusterBOrg):
    ClusterAMinusTgt=copy.copy(ClusterAOrg)
    ClusterB=copy.copy(ClusterBOrg)
    ClusterAMinusTgt.remove(TgtEl)
    
    AvDA=el_against_list_av(TgtEl,ClusterAMinusTgt,distFunc)
    AvDB=el_against_list_av(TgtEl,ClusterB,distFunc)

    return AvDA-AvDB


                   
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
        Args.dist_func=lambda A,B: abs(A-B)
    with open(Args.data_file) as FSr:
        ClusterR=set(FSr.read().split())
    if Args.numerical:
        ClusterR=[float(El) for El in ClusterR]
    main0(ClusterR,Args.dist_func,UpToN=Args.up_to_n,Debug=Args.debug)



if __name__=='__main__':
    main()
