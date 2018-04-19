# let's do just PoS conversion, relying on 'neologd2juman' for format changes
import os,sys,argparse,imp

MecabToolsDir=os.path.join(os.environ.get('HOME'),'myProjects/myPythonLibs/mecabtools')
JumanCatsFN='juman_cats.txt'
JumanCatsFP=os.path.join(MecabToolsDir,JumanCatsFN)

CurSuperCat=None
SubSuperJ={}
with open(JumanCatsFP) as FSr:
    for LiNe in FSr:
        LineR=LiNe.rstrip()
        if not LineR.lstrip():
            continue
        LineEls=LineR.split('\t')
        CatCnt+=1
        if len(LineEls)==2:
            if LineEls[0]:
                CurSuperCat=LineEls[0]
            SubSuperJ[LineEls[1]]=CurSuperCat

ConvTableFN='mecab_juman_pos_conv_table.txt'

ConvTableFP=os.path.join(MecabToolsDir,ConvTableFN)

def pos_table_m2j(TableFP):
    CurSuperCat=None;CurSubCat1=None;CurSubCat2=None
    Table={}
    with open(TableFP) as FSr:
        for LiNe in FSr:
            LineEls=LiNe.rstrip().split('|')
            if len(LineEls)<2:
                print('funny line')
                print(LineEls)
                continue
            MCats,JCat=LineEls[0].rstrip().split(),LineEls[1].split()[0]
            if MCats[0]:
                CurSuperCat=MCats[0]
            if len(MCats)>=2 and MCats[1]:
                CurSubCat1=MCats[1]
            else:
                CurSubCat1='*'
            if len(MCats)>=3:
                CurSubCat2=MCats[2]
            else:
                CurSubCat2='*'

            JSuperCat,JSubCat=(SubSuperJ[JCat],JCat) if JCat in SubSuperJ.keys() else (JCat,'*')
            
            Table[(CurSuperCat,CurSubCat1,CurSubCat2)]=(JSuperCat,JSubCat)
            
    return Table        

PoSTable=pos_table_m2j(ConvTableFP)
assert({Values[0] PoSTable.values()}

def mecabwd2jumanwd(MecabWd,PoSTable):
    JumanPoS=PoSTable[MecabWd.inherentatts]
    return MecabWd.change_fts(JumanPoS)

