import imp,sys,math,copy,collections,fractions,pdb,decimal,random
from collections import defaultdict
from pythonlib_ys import main as myModule
imp.reload(myModule)
Debug=1

if Debug:
    from pdb import set_trace

__author__ = 'yosato'

def floating_point(Float):
    return abs(decimal.Decimal(str(Float)).as_tuple().exponent)

class EquivalEqual:
    def __init__(self):
        def __eq__(self,Tgt):
            if type(self)!=type(Tgt):
                return False
                for Attr, Val in self.__dict__():
                    if Tgt.__dict__[Attr]!=Val:
                        return False
            return True

# use this guy for unigrams. to be used for posthoc dist also.
class DiscDist(EquivalEqual):
    '''
      discrete distribution of one random var. from occurrences, you mainly get marginal prob.
      obligatory input: normally a dict representing {evt:occ} 
    '''
    def __init__(self,EvtProbPairsOrEvtOccPairs,Smooth=False,Occs={},TotalOccs=0):
        super().__init__()
        Samples=EvtProbPairsOrEvtOccPairs.values()
        # this is the case of probabilities, each needs to be a float
        if all(type(Sample).__name__=='float' for Sample in Samples) and sum(Samples)==1:
            EvtProbPairs=EvtProbPairsOrEvtOccPairs
            self.occs=0
            self.evtocc=Occs
            self.totalocc=TotalOccs

        # this is the case of occurrences
        else:
            EvtsOccs=EvtProbPairsOrEvtOccPairs
            if any(isinstance(Sample,float) for Sample in Samples):
                self.occadjusted=True
            else:
                self.occadjusted=False
            
            self.evtocc=(EvtsOccs if not Smooth else { Evt:Occ+1 for (Evt,Occ) in EvtsOccs.items()})
            
            self.occs=[ Occ for Occ in self.evtocc.values() ]
            self.totalocc=sum(self.occs)
            
            self.evtcount=len(EvtProbPairsOrEvtOccPairs.keys())
            EvtProbPairs=self.evtocc2evtprob()

            

        self.evtprob=EvtProbPairs
        self.probs=[ Probs for Probs in self.evtprob.values() ]
      #  self.sum_check()
     #  self.evtprob=EvtProbPairs

    def filter_evts(self,Thresh):
        if type(Thresh).__name__=='int':
            Items=self.evtocc.items()
        elif type(Thresh).__name__=='float':
            Items=self.evtprob.items()
        return { Evt:Occ  for (Evt,Occ) in Items if Occ>Thresh }
            
    def evtocc2evtprob(self):
        if self.occadjusted:
            TotalOccFloatP=floating_point(self.totalocc)
            EvtProb={}
            for Evt,Occ in self.evtocc.items():
                FloatP=floating_point(Occ)
                if TotalOccFloatP < FloatP:
                    Coeff=math.pow(10,TotalOccFloatP)
                    IntOcc=int(Coeff*round(Occ,TotalOccFloatP))
                    IntTotalOcc=int(Coeff*self.totalocc)
                    
                else:
                    # you should here adjust to the event occ
                    Coeff=math.pow(10,FloatP)
                    IntTotalOcc=int(round(self.totalocc,FloatP)*Coeff)
                    IntOcc=int(Coeff*Occ)
                Prob=fractions.Fraction(IntOcc,IntTotalOcc)
                EvtProb[Evt]=Prob
            return EvtProb
        else:    
            return { Evt:fractions.Fraction(Occ,self.totalocc) for Evt,Occ in self.evtocc.items() }
        
    def format_check(self,EvtProbPairs):
        Bool=True
        for Evt,Prob in EvtProbPairs:
            if not type(Evt).__name__!='str' or not type(Prob).__name__!='float':
                return False
        return Bool
    def sum_check(self):
        if sum(self.probs)==1:
            return True
        else:
            return False

class CondDists:
    def __init__(self,CDsR):
        self.u1s_pds={Wd:DiscDist(PostD) for (Wd,PostD) in CDsR.items()}
        self.u1scnts={Wd:PostD.totalocc for (Wd,PostD) in self.u1s_pds.items()}
        self.totalocc_bi=sum([PD.totalocc for PD in self.u1s_pds.values()])
        
        U2sCnts=defaultdict(int)
        for PostD in self.u1s_pds.values():
            for Wd,Cnt in PostD.evtocc.items():
                U2sCnts[Wd]+=Cnt
        self.u2scnts=U2sCnts
        self.totalocc_u2var=sum(self.u2scnts.values())

    def get_uniprob_specwd(self,SpecWd,OneTwo):
        if OneTwo==1:
            return self.u1scnts[SpecWd]/self.totalocc_bi
        if OneTwo==2:
            return self.u2scnts[SpecWd]/self.totalocc_u2var
    
def get_cum_list(List):
    Cum=0;NewList=[]
    for El in List:
        NewList.append(Cum+El)
    return NewList

    
def rand_biased(DiscDist):
    # this gives a random float 0-1
    RandFloat=random.random()
    Items=list(DiscDist.evtprob.items())
    #and you cumulate the probs of evts
    CumProb=0
    for Evt,Prob in Items:
        CumProb=CumProb+Prob
        # and if the random float exceeds, return that event 
        if CumProb>RandFloat:
            return Evt
    return Items[-1][0]

    
def sents2countdic(Sents):
    CntDic={}
    for Sent in Sents:
        SentUnits=Sent.strip().split()
        for SentUnit in SentUnits:
            myModule.increment_diccount(CntDic,SentUnit)
    return CntDic

    
def rawfile2objs(RawFPWdPerLine,OutputFP=None):
    if not OutputFP:
        OutputFP=RawFPWdPerLine+'.occ'
    UniDict={}; BiDict={}; Prv=''
    for Wd in open(RawFPWdPerLine):
        myModule.increment_dictcnt(UniDict,Wd)
        if Prv in BiDict.keys():
            myModule.increment_dictcnt(BiDict[Prv])
        else:
            BiDict[Prv]={Wd:1}
        
    myUGs=DiscDist(UniDict)
    myBGStats=[]
    for Wd,Dict in BiDict.items():
        myBGStats.append(BiStat(Wd,Dict))

    return myUGs,myBGStats
        

def remove_adjust_distribution(OrgDist,Items2Remove):
    Prob2Remove=0
    DiscDist=copy.deepcopy(OrgDist)
#    (NonSeenCnt,SmthdProb)=copy.copy(OrgSmthedDist[1])
    for Item in Items2Remove:
        Prob2Remove=Prob2Remove+DiscDist[Item]
        del DiscDist[Item]
    Coeff=1+(Prob2Remove/1)
    NewDiscDist={}
    for (Key,Prob) in DiscDist.items():
        NewDiscDist[Key]=Prob*Coeff
#    NewSmthd=(NonSeenCnt,SmthdProb*Coeff)
    Val=check_sumzero(NewDiscDist)
    return NewDiscDist

def check_sumzero(Dist):
    return sum(Dist.values())

#======================
#Entropy related funcs
# heavily used!!!!
#=====================

def info_gain(Entropy1,Item,Dist):
    Entropy2=entropy(remove_adjust_distribution(Dist,[Item]))
    return Entropy2,Entropy1-Entropy2


def entropy(DiscDist):
    NEntropy=0
#    DiscDist,Smoothed=SmoothedDiscDist
    for _EventName,Prob in DiscDist.items():
        NEntropy=NEntropy+entropy_unit(Prob)
#    (Cnt,Prob)=Smoothed
#    Entropy=Entropy+(entropy_moto(Prob)*Cnt)

    return -NEntropy

def entropy_unit(Prob):
    return math.log(Prob,2)*Prob

def mutual_info_unit(Marg1,Marg2,Joint):
    return pointwise_mutual_info(Marg1,Marg2,Joint)*Joint

def all_mis(M1,M2,Joint):
    M1=float(M1); M2=float(M2); Joint=float(Joint)
    if Joint==1:
        PMI=NPMI=MI=NMI=0
    else:
        PMI=pointwise_mutual_info(M1,M2,Joint)
        NPMI=normalised_pmi(PMI,Joint)
        MI=mutual_info_unit(M1,M2,Joint)
        NMI=MI/-math.log(Joint,2)
    return (MI,NMI),(PMI,NPMI)

def pointwise_mutual_info(Marg1,Marg2,Joint):
    return math.log(Joint/(Marg1*Marg2),2)

def normalised_pmi(PMI,Joint):
    return PMI/-math.log(Joint,2)

def condprob_fromjoint(Joint,MargGiven):
    return Joint/MargGiven
