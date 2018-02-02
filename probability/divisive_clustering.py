import numpy

def main0(ClusterR,UpToN=None):
    D=1;Fst=True
    if UpToN is None:
        IterCnt=len(ClusterR)-1
    else:
        IterCnt=UpToN+1

    while IterCnt:
        if Fst:
            Fst=False
        else:
            ClusterR=ClusterA if DiamA>DiamB else ClusterB
        (ClusterA,DiamA),(ClusterB,DiamB)=split_cluster(ClusterR)
        IterCnt=-1


def split_cluster(ClusterR,distFunc):
    ClusterA=ClusterR
    ClusterB=set()
    D=1
    PrvD=inf
    while D>0:
        for El in ClusterR:
            D=dist_clusters(El,distFunc,ClusterA,ClusterB)
            MaxSoFar=max(D,PrevD)
    return (ClusterA,DiamA),(ClusterB,DiamB)
    
def dist_clusters(TgtEl,distFunc,ClusterA,ClusterB):
    ClusterAMinusTgt=ClusterA-{TgtEl}
    return numpy.mean(ClusterAMinusTgt)-numpy.mean(ClusterB)

def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('-f','--data-file',required=True)
    Psr.add_argument('--numerical',action='store_true')
    Args=Psr.parse_args()
    with open(Args.data_file) as FSr:
        ClusterR=FSr.read().split()
    if Args.numerical:
        ClusterR=[float(El) for El in ClusterR]
    main0(ClusterR)



if __name__=='__main__':
    main()
