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
    def __init__(self,EvtProbPairsOrEvtOccPairs,Occs={},TotalOccs=0):
        super().__init__()
        Samples=EvtProbPairsOrEvtOccPairs.values()
        if all(Sample < 1 for Sample in Samples):
            EvtProbPairs=EvtProbPairsOrEvtOccPairs
            self.evtocc=Occs
            self.totalocc=TotalOccs
            if not self.sum_check():
                sys.exit('probability does not sum to one')
        else:
            if any(isinstance(Sample,float) for Sample in Samples):
                self.occadjusted=True
            else:
                self.occadjusted=False
            
            self.evtocc=EvtProbPairsOrEvtOccPairs
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

def get_cum_list(List):
    Cum=0;NewList=[]
    for El in List:
        NewList.append(Cum+El)
    return NewList

    
def rand_biased(DiscDist):
    from collections import OrderedDict
    CumDiscDist=OrderedDict();PrvProb=0
    for Evt,Prob in DiscDist.evtprob().items():
        CumDiscDist[PrvProb+Prob]=Evt
    RandFloat=random.random()
    Key=next(Upper>RandFloat for Upper in CumDiscDist.keys())
    return CumDiscDist[Key]
    
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
