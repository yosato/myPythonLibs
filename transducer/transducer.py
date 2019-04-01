import sys,os,copy,imp,json
from collections import defaultdict

class Lexeme:
    def __init__(self,ParadigmMap):
        AllForms=[];AllAtts=[]
        for (InfFAtt,InfFVal) in ParadigmMap.items():
            self.__dict__[InfFAtt]=InfFVal
            AllForms.append(InfFVal);AllAtts.append(InfFAtt)
        self.allforms=AllForms
        self.allatts=AllAtts

class Edge:
    def __init__(self,Org,Dst,LabelClass):
        self.labelclass=LabelClass
        self.origin=Org
        self.destination=Dst

class Transducer:
    def __init__(self,Edges,FinalPoss,Vocab,SpaceP=True):
        self.edges=Edges
        self.finalpositions=FinalPoss
        self.intermediatepositions=set([Edge.destination for Edge in Edges if Edge.destination not in self.finalpositions])
        self.edges=Edges if not SpaceP else Edges+self.space_edges()
        self.curpos=0
        if SpaceP:
            Vocab.update([(u'space',' ')])
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
    def find_labelclasses_for_periphery(self,Str,Vocab,Reverse=False,Debug=False):
        FndLCs=[];FndMorphs=[]
        for (LC,Morphs) in Vocab.items():
            if Debug:    
                print(LC)
#                for Morph in Morphs:
  #                  print(Morph)
            FndMorph=next((Morph for Morph in Morphs if Str.endswith(Morph)),None)
            if Debug:
                Msg='FOUND!!' if FndMorph else 'not found'
                print(Msg)
            if FndMorph:
                FndLCs.append(LC)
                FndMorphs.append(FndMorph)

        return FndLCs,FndMorphs
        


def traverse_transducer(OrgTrans,OrgStr,Reverse=False,Debug=False):
    if not isinstance(OrgTrans,Transducer):
        sys.exit('not a transducer')
    Transes=[];Str=OrgStr
    for Trans in OrgTrans.generate_started_copy():
        while Str:
            if Debug: print(Str)
            LCs,Strs=Trans.find_labelclasses_for_periphery(Str,Trans.vocab,Reverse=Reverse,Debug=Debug)
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
        
def extract_infform(TgtInfFormName,Str,VLexs):
    for VLex in VLexs:
        if Str in VLex.allforms:
            return VLex.__dict__[TgtInfFormName]
    return None

def make_transducer_fromjsons(TransCfgJsonFP,InfJsonFP,Debug=False):        
    Objs=[]
    for JsonFP in (TransCfgJsonFP,InfJsonFP):
        with open(JsonFP) as FSr:
            Str=FSr.read()
            Obj=json.loads(Str)
            Objs.append(Obj)
    TransCfgs,OrgWdLs=Objs

    EdgeCfgs=TransCfgs['edges']
    FinalPoss=TransCfgs['finals']
    CatsLexSets=defaultdict(list)
    for WdCat,InfFormAttsVals in OrgWdLs:
        CatsLexSets[WdCat].append(Lexeme(InfFormAttsVals))

    Vocab=defaultdict(list)
    for (Cat,LexSet) in CatsLexSets.items():
        AllForms=[El for Sublist in [Lex.allforms for Lex in LexSet] for El in Sublist]
        Vocab[Cat].extend(AllForms)

    return make_transducer(EdgeCfgs,FinalPoss,Vocab),CatsLexSets
        
def make_transducer(EdgeCfgs,FinalPoss,Vocab):
    Edges=[]
    for (Org,Dst,LC) in EdgeCfgs:
        Edges.append(Edge(Org,Dst,LC))
    return Transducer(Edges,FinalPoss,Vocab)

def parse_with_transducer(Str,Trans,InfForm,VLexs,ReverseP=False,Debug=True):

    NewTranses=traverse_transducer(Trans,Str,Reverse=ReverseP,Debug=Debug)
    if NewTranses:
        ResTrans,NotConsumedStr=NewTranses[0]
        LstSeg=ResTrans.pathstates[-1][-1]
        ConsumedStrs=[Tuple[1] for Tuple in ResTrans.pathstates[:-1]][::-1]
        NewSeg=extract_infform(InfForm,LstSeg,VLexs)
        if NewSeg:
#            NewStr=RemStr+NewSeg
            ConsumedStr=''.join(ConsumedStrs)
            return NewSeg,LstSeg,ConsumedStr

    else:
        return None


def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('str_fp')
    Psr.add_argument('transcfg_jsonfp')
    Psr.add_argument('inf_jsonfp')
    Psr.add_argument('--reverse',action='store_true')
    Psr.add_argument('--debug',action='store_true')
    Args=Psr.parse_args()
    myTrans,CatsLexSets=make_transducer_fromjsons(Args.transcfg_jsonfp,Args.inf_jsonfp,Debug=Args.debug)
    LexsMainV=CatsLexSets['mainV']
    Results=[]
    with open(Args.str_fp) as FSr:
        for LiNe in FSr:
            Line=LiNe.strip()
            if not Line:
                continue
            OrgSent=LiNe.strip().split('\t')[0].decode('utf8')
            #print(OrgSent)
            #print()
            for InfFN in LexsMainV[0].allatts:
                try:
                    Result=parse_with_transducer(OrgSent,myTrans,InfFN,LexsMainV,ReverseP=Args.reverse,Debug=Args.debug)
                    Results.append(Result)
                except:
                    parse_with_transducer(OrgSent,myTrans,InfFN,InfWds,ReverseP=Args.reverse)
                


if __name__=='__main__':
    main()
