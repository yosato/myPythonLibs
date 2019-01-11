import sys,os,copy,imp,json,re
from collections import defaultdict

class Edge:
    def __init__(self,Org,Dst,LabelClass):
        self.labelclass=LabelClass
        self.origin=Org
        self.destination=Dst

class Transducer:
    def __init__(self,Edges,FinalPoss,Vocab,SpaceP=False):
        self.finalpositions=FinalPoss
        self.intermediatepositions=set([Edge.destination for Edge in Edges if Edge.destination not in self.finalpositions])
        self.edges=Edges if not SpaceP else Edges+self.space_edges()
        self.curpos=0
        if SpaceP:
            Vocab.update([('space',' ')])
        self.vocab=Vocab 
        self.pathstates=[]
        self.finalp=False
    def space_edges(self):
        SEdges=[]
        for IntPos in self.intermediatepositions:
            SEdges.append(Edge(IntPos,IntPos,'space'))
        return SEdges
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
        else:
            sys.stderr.write('No move possible\n')
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
        
def main0(StrFP,TransCfgJson,InfJsonFP,InfForm,ReverseP=False,SpaceP=False):
    myTrans=make_transducer(TransCfgJson,InfJsonFP,SpaceP=SpaceP)
    Results=stem_inflect_strings(StrFP,myTrans,InfForm,ReverseP=ReverseP)

    return Results


def stem_inflect_strings(StrFP,myTrans,InfForm,ReverseP=False):
    NewStrs=[]
    with open(StrFP) as FSr:
        for LiNe in FSr:
            Line=re.sub(r'[ 　]+',' ',LiNe).strip()
            NewStrs.append(stem_inflect_verb(Line,myTrans,InfForm,ReverseP=ReverseP))
    return NewStrs

def stem_inflect_mainverb(Str,myTrans,InfForm,ReverseP=False):
    Transes=traverse_transducer(myTrans,Str,Reverse=ReverseP)
    if Transes:
        ResTrans,RemStr=Transes[0]
        LstSeg=ResTrans.pathstates[-1][-1]
        Rest=[Tuple[1] for Tuple in ResTrans.pathstates[:-1]][::-1]
        NewSeg=extract_infform(InfForm,LstSeg,InfWds)
        if NewSeg:
            NewStr=RemStr+NewSeg
            RemStuff=''.join(Rest)
    return NewStr,RemStuff

def traverse_transducer(OrgTrans,OrgStr,Reverse=False):
    if type(OrgTrans).__name__!='Transducer':
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
        
        
def make_transducer(TransCfgJson,InfJsonFP,SpaceP=False):
    Objs=[]
    for JsonFP in (TransCfgJson,InfJsonFP):
        with open(JsonFP) as FSr:
            Objs.append(json.loads(FSr.read()))
    TransCfgs,InfWds=Objs

    EdgeCfgs=TransCfgs['edges']
    FinalPoss=TransCfgs['finals']
    Vocab=defaultdict(list)
    for InfWd in InfWds:
        Vocab[InfWd[0]].extend(InfWd[1].values())
    Edges=[]
    for (Org,Dst,LC) in EdgeCfgs:
        Edges.append(Edge(Org,Dst,LC))
    myTrans=Transducer(Edges,FinalPoss,Vocab,SpaceP=SpaceP)
    return myTrans


def main():
    import argparse,json,re
    Psr=argparse.ArgumentParser()
    Psr.add_argument('str_fp')
    Psr.add_argument('transcfg_fp')
    Psr.add_argument('inf_fp')
    Psr.add_argument('infform')
    Psr.add_argument('--reverse',action='store_true')
    Psr.add_argument('--allow-space',action='store_true')
    Args=Psr.parse_args()
    if Args.inf_fp.endswith('.txt'):
        List=eval(open(Args.inf_fp).read())
        InfJsonFP=re.sub(r'\.txt$','.json',Args.inf_fp)
        open(InfJsonFP,'wt').write(json.dumps(List,ensure_ascii=False,indent=2))
    else:
        InfJsonFP=Args.inf_fp
    main0(Args.str_fp,Args.transcfg_fp,InfJsonFP,'renyo-onbin',ReverseP=Args.reverse,SpaceP=Args.allow_space)


if __name__=='__main__':
    main()



    
