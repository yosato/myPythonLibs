import copy
from itertools import combinations

def main0(ClusterR,distFunc,UpToN=None):
    Clusters=[]
    Fst=True
    MaxClusterCnt=len(ClusterR)-2
    if UpToN is None:
        UpToN=MaxClusterCnt
    elif UpToN>MaxClusterCnt:
        sys.exit('specified count exceeds maximum')
    DiamA=0;DiamB=0;ClusterB=[];Cntr=0
    while len(Clusters)<=UpToN:
        Cntr+=1
        if Fst:
            Fst=False
        else:
            MaxDiam=-float('inf')
            for (Ind,(_,Diam)) in enumerate(Clusters):
                if Diam>MaxDiam:
                    MaxDiam=Diam;MaxInd=Ind
            del Clusters[MaxInd]
        (ClusterA,DiamA),(ClusterB,DiamB)=split_cluster(ClusterR,distFunc)
        Clusters.append((ClusterA,DiamA,))
        Clusters.append((ClusterB,DiamB,))
        
    return Clusters

    

def split_cluster(ClusterR,distFunc):
    if len(ClusterR)==2:
        return ([ClusterR[0]],0),([ClusterR[1]],0)
    ClusterB=[]
    PrvD=-float('inf')
    while True:
        for Cntr,El in enumerate(ClusterR):
            D,DiamA,DiamB=dist_clusters(El,distFunc,ClusterR,ClusterB)
            if D>PrvD:
                MaxEl=El
                MaxDiamA=DiamA
                MaxDiamB=DiamB
                PrvD=D
        if D<0:
            break
        else:
            print(str(MaxEl)+' chosen')
            ClusterR.remove(MaxEl)
            ClusterB.append(MaxEl)
            print(ClusterR)
            print(ClusterB)
            PrvD=-float('inf')

    
    return (ClusterR,MaxDiamA),(ClusterB,MaxDiamB)
    
def diameter_set(Set):
    if not Set:
        return 0
    else:
        return max(Set)

def dist_clusters(TgtEl,distFunc,ClusterAOrg,ClusterBOrg):
    ClusterAMinusTgt=copy.copy(ClusterAOrg)
    ClusterB=copy.copy(ClusterBOrg)
    ClusterAMinusTgt.remove(TgtEl)
    LenA=len(ClusterAMinusTgt);LenB=len(ClusterB)
    DistsA=all_dists(distFunc,ClusterAMinusTgt)
    DistsB=all_dists(distFunc,ClusterB)
    D=(0 if not ClusterAMinusTgt else sum(DistsA)/LenA-1)-(0 if not ClusterB else (sum(DistsB)/LenB-1))
    DiamA=diameter_set(DistsA)
    DiamB=diameter_set(DistsB)
    return D,DiamA,DiamB

def all_dists(distFunc,Set):
    Return=[]
    for Comb in combinations(Set,2):
        Return.append(distFunc(Comb[0],Comb[1]))
        #yield distFunc(Comb[0],Comb[1])
    return Return
                   
def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('-f','--data-file',required=True)
    Psr.add_argument('--numerical',action='store_true')
    Psr.add_argument('--up-to-n',type=int)
    Psr.add_argument('-d','--dist-func')
    Args=Psr.parse_args()
    if Args.dist_func is None:
        Args.dist_func=lambda A,B: abs(A-B)
    with open(Args.data_file) as FSr:
        ClusterR=set(FSr.read().split())
    if Args.numerical:
        ClusterR=[float(El) for El in ClusterR]
    main0(ClusterR,Args.dist_func,Args.up_to_n)



if __name__=='__main__':
    main()
