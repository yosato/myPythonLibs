import copy,collections

def nestedlist2pairs(NestedList):
    Pairs=[((None,(0,0)),NestedList)]
    CurrentList=[copy.copy(NestedList)]
    CurDepth=0
    while True:
     #   print(str(CurDepth)+' to '+str(CurDepth+1)+' starting')
        #Pairs=[]
        WidthPerDepth=0;ListExistP=False;NextList=[]
        for Width,El in enumerate(CurrentList):
            #WidthPerDepth+=Width
            if isinstance(El,list):
                SubElsPerEl=[(((CurDepth,Width),(CurDepth+1,WidthPerDepth+SubWidth)),SubEl) for SubWidth,SubEl in enumerate(El)]
                Pairs.extend(SubElsPerEl)
                ListExistP=True
                WidthPerDepth+=len(SubElsPerEl)
            else:
                if El not in [Pair[1] for Pair in Pairs]:
                    WidthPerDepth+=1
                    Pairs.append((((CurDepth,Width),(CurDepth+1,WidthPerDepth)),El))

        if not ListExistP:
            return dict(collections.OrderedDict(Pairs))
        print(str(CurDepth)+' to '+str(CurDepth+1)+' done')
        CurDepth+=1
#        print(CurrentList)
        CurrentList=one_level_flatten(CurrentList)
 #       print(CurrentList)
  #      for pair in Pairs:
   #         print(pair)
    #    print()
#        return collections.OrderedDict(Pairs)        

        
def one_level_flatten(OrgList):
    Flattened=[];List=copy.copy(OrgList)
    for El in List:
        if isinstance(El,list):
            Flattened=Flattened+El
    return Flattened



TestLists=[
    ([['a',['b','c']],'d',[['e',['f','g']],['h','i']]][['a',['b','c']],'d',[['e',['f','g']],['h','i']]],{(None,(0,0)):[['a',['b','c']],'d',[['e',['f','g']],['h','i']]],((0,0),(1,0)):['a',['b','c']]})
]

for List in TestLists:
    Pairs=nestedlist2pairs(List)
