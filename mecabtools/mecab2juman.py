# let's do just PoS conversion, relying on 'neologd2juman' for format changes
import os,re
from collections import defaultdict
from pythonlib_ys import main as myModule

MecabToolsDir=os.path.join(os.environ.get('HOME'),'myProjects/myPythonLibs/mecabtools')
JumanCatsFN='juman_cats.txt'
JumanCatsFP=os.path.join(MecabToolsDir,JumanCatsFN)

JCatLeafCnt=45

CurSuperCat=None
SubSuperJ={}
SuperSubJ=defaultdict(set)
CatCnt=0
with open(JumanCatsFP) as FSr:
    for LiNe in FSr:
        LineR=LiNe.rstrip()
        if not LineR.lstrip():
            continue
        LineEls=LineR.split('\t')
        if LineEls[0]:
            CurSuperCat=LineEls[0]
        #SubSuperJ[LineEls[1]]=CurSuperCat
        if len(LineEls)>=2:
            SuperSubJ[CurSuperCat].add(LineEls[1])
        else:
            SuperSubJ[CurSuperCat]=set()

SubSuperJ={};JCatLeaves=[]
for (SuperCat,SubCats) in SuperSubJ.items():
    if SubCats:
        for SubCat in SubCats:
            SubSuperJ[SubCat]=SuperCat
            JCatLeaves.append(SubCat)
    else:
        JCatLeaves.append(SuperCat)
assert(len(JCatLeaves)==JCatLeafCnt)


ConvTableFN='mecab_juman_pos_conv_table.txt'

ConvTableFP=os.path.join(MecabToolsDir,ConvTableFN)

def equi_interval(List,Intl=None):
    if len(List)<=1:
        Bool=True
    else:
        Bool=True
        Intl=List[1]-List[0] if Intl is None else Intl
        for i in range(1,len(List)):
            if List[i]-List[i-1]!=Intl:
                Bool=False
                break
    return Bool

assert(equi_interval([1,2,3,4]))
equi_interval([1,3],Intl=1)
assert(not equi_interval([1,3],Intl=1))
assert(equi_interval([6,4,2,0]))
assert(not equi_interval([6,4,2,0],Intl=1))
assert(equi_interval([2,4,6]))
assert(not equi_interval([2,3,4,6]))
    

def pos_table_m2j(TableFP):
    CurCats=[None,None,None,None]
    Table={}
    with open(TableFP) as FSr:
        for LiNe in FSr:
            Line=LiNe[:LiNe.index('#')]
            LineEls=[El.rstrip() for El in Line.rstrip().split('|')]
            if len(LineEls)<2:
                print('funny line')
                print(LineEls)
                continue
            JCatsInit=LineEls[-1].strip().split('-')
            if JCatsInit[0] =='id':
                continue
            JCats=tuple(JCatsInit)
            for JCat in JCats:
                JCatS=JCat[:-1] if re.match(r'.*[1-9]$',JCat) else JCat
                assert(JCatS in JCatLeaves)
            MCatsInit=LineEls[0].rstrip().split('\t')
            MCatsInit=MCatsInit+(['*']*(4-len(MCatsInit)))
            assert(len(MCatsInit)==4)
            #constraint
            EmpInds=[Ind for (Ind,MCat) in enumerate(MCatsInit) if MCat=='']
            StarInds=[Ind for (Ind,MCat) in enumerate(MCatsInit) if MCat=='*']
            #assert(EmpInds[-1]!=2 and contiguous
            if EmpInds:
                assert(equi_interval(EmpInds,Intl=1) and EmpInds[-1]!=3)
            if StarInds:
                assert(equi_interval(StarInds,Intl=1) and StarInds[0]!=0)
            print();print(MCatsInit)
            print(JCats)
            print()
            for Ind,MCatInit in enumerate(MCatsInit):
                if MCatInit != '':
                    CurCats[Ind]=MCatInit

            if EmpInds:
                for EmpInd in EmpInds:
                    MCatsInit[EmpInd]=CurCats[EmpInd]
            MCats=tuple(MCatsInit)

            JSupSubs=tuple([ (SubSuperJ[JCat],JCat) if JCat in SubSuperJ.keys() else (JCat,'*') for JCat in JCats ])

            print(MCats);print(JCats)

            Table[MCats]=JSupSubs

    return Table

PoSTable=pos_table_m2j(ConvTableFP)

#assert(len({Values[0] for Values in PoSTable.values()})==CatCnt)

def mecabwd2jumanwd(MecabWd,PoSTable):
    JumanPoSs=PoSTable[(MecabWd.cat,MecabWd.subcat,MecabWd.subcat2,MecabWd.infform)]
    JumanWds=[]
    for JumanPoS in JumanPoSs:
        JumanWds.append(MecabWd.change_feats({'cat':JumanPoS[0],'subcat':JumanPoS[1],'reading':myModule.kana2kana_wd(MecabWd.reading)},CopyP=True))
    return JumanWds

