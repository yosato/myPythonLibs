import sys,os,copy,imp,json
from collections import defaultdict

class Edge:
    def __init__(self,Org,Dst,LabelClass):
        self.labelclass=LabelClass
        self.origin=Org
        self.destination=Dst

class Transducer:
    def __init__(self,Edges,FinalPoss,Vocab):
        self.edges=Edges
        self.finalpositions=FinalPoss
        self.curpos=0
        self.vocab=Vocab
        self.pathstates=[]
        self.finalp=False
    def next_pot_edges(self):
        return [Edge for Edge in self.edges if Edge.origin == self.curpos]
    def get_next_poss_withlc(self,LabelClass):
        return [ Edge.destination for Edge in self.next_pot_edges() if Edge.labelclass==LabelClass ]

    def traverse_next_pos(self,LC,Str):
        NextPoss=self.get_next_poss_withlc(LC)
        if NextPoss:
            self.curpos=NextPoss[0]
            self.pathstates.append((LC,Str,))
            if self.curpos in self.finalpositions:
                self.finalp=True
        #else:
         #   sys.stderr.write('No move possible\n')
        return NextPoss

    def generate_started_copy(self):
        self.curpos=0
        Copies=[]
        for Pos in self.get_next_poss_withlc('null'):
            Copy=copy.deepcopy(self)
            Copy.curpos=Pos
            Copies.append(Copy)
        return Copies
    def find_labelclasses_for_periphery(self,Str,Vocab,Reverse=False):
        FndLCs=[];FndMorphs=[]
        for (LC,Morphs) in Vocab.items():
            FndMorph=next((Morph for Morph in Morphs if Str.endswith(Morph)),None)
            if FndMorph:
                FndLCs.append(LC)
                FndMorphs.append(FndMorph)

        return FndLCs,FndMorphs
        


def traverse_transducer(OrgTrans,OrgStr,Reverse=False):
    if not isinstance(OrgTrans,Transducer):
        sys.exit('not a transducer')
    Transes=[];Str=OrgStr
    for Trans in OrgTrans.generate_started_copy():
        while Str:
            LCs,Strs=Trans.find_labelclasses_for_periphery(Str,Trans.vocab,Reverse=Reverse)
            if Strs:
                Rtn=Trans.traverse_next_pos(LCs[0],Strs[0])
                if not Rtn:
                    break
                else:
                    Str=Str[:-len(Strs[0])]
            else:
                break
        if Trans.finalp:
            Transes.append((Trans,Str,))

        Str=OrgStr

    return Transes
        
def extract_infform(TgtInfFormName,Str,InfTable):
    for InfPatName,Dic in InfTable:
        if Str in Dic.values():
            return Dic[TgtInfFormName]
    return None

def make_transducer_fromjsons(TransCfgJson,InfJson):        
    InfWds=[]
    with open(InfJson) as FSr:
        for LiNe in FSr:
            InfWds.append(json.loads(LiNe.strip()))
    
    with open(TransCfgJson) as FSr:
        TransCfgs=json.loads(FSr.read())

    EdgeCfgs=TransCfgs['edges']
    FinalPoss=TransCfgs['finals']
    Vocab=defaultdict(list)
    for InfWd in InfWds:
        Vocab[InfWd[0]].extend(InfWd[1].values())
    return make_transducer(EdgeCfgs,FinalPoss,Vocab),InfWds
        
def make_transducer(EdgeCfgs,FinalPoss,Vocab):
    Edges=[]
    for (Org,Dst,LC) in EdgeCfgs:
        Edges.append(Edge(Org,Dst,LC))
    return Transducer(Edges,FinalPoss,Vocab)

def parse_with_transducer(Str,Trans,InfForm,InfWds,ReverseP=False):

    NewTranses=traverse_transducer(Trans,Str,Reverse=ReverseP)
    if NewTranses:
        ResTrans,NotConsumedStr=NewTranses[0]
        LstSeg=ResTrans.pathstates[-1][-1]
        ConsumedStrs=[Tuple[1] for Tuple in ResTrans.pathstates[:-1]][::-1]
        NewSeg=extract_infform(InfForm,LstSeg,InfWds)
        if NewSeg:
#            NewStr=RemStr+NewSeg
            ConsumedStr=''.join(ConsumedStrs)
            return NewSeg,ConsumedStr
    else:
        return None


def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('str_fp')
    Psr.add_argument('transcfg_jsonfp')
    Psr.add_argument('inf_jsonfp')
    Psr.add_argument('--reverse',action='store_true')
    Args=Psr.parse_args()
    with open(Args.str_fp) as FSr:
        for LiNe in FSr:
            make_transducer(LiNe.strip(),Args.transcfg_jsonfp,Args.inf_jsonfp,'renyo-onbin',ReverseP=Args.reverse)


if __name__=='__main__':
    main()
