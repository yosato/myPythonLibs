import imp,sys,os,re,glob,copy,time,shutil
from collections import defaultdict
#import mecab2juman as m2j
from pythonlib_ys import jp_morph
from pythonlib_ys import main as myModule
import mecabtools as mtools
imp.reload(mtools)
#imp.reload(m2j)
imp.reload(jp_morph)


def convtable_check(ConvTable):
    for MecabCat,TgtCats in ConvTable.items():
        sys.stderr.write(repr(MecabCat)+': ')
        for TgtCat in TgtCats:
            sys.stderr.write(repr(TgtCat)+'\n')

def main0(OrgResDir,TgtScheme,DicOutDir=None,IdioDic=None,CorpusDir=None, RedoIfExist=True,MakeTextDicToo=False,Strict=False,Debug=False):
    TagDir=os.path.join(os.getcwd(),'tagsets')
    (TgtCatFP,Mapping)= (os.path.join(TagDir,'juman_cats.txt'),mtools.MecabJumanMapping) if TgtScheme=='juman' else (os.path.join(TagDir,'csj_cats.txt'),mtools.MecabCSJMapping)

    if DicOutDir is None:
        DicOutDir=re.sub('/$','',OrgResDir)+'_trans_'+TgtScheme
        if not os.path.isdir(DicOutDir):
            os.makedirs(DicOutDir)

    translate_dic(OrgResDir,TgtCatFP,Mapping,DicOutDir,TgtSpec='csj',Debug=Debug,MakeTextDicToo=MakeTextDicToo,RedoIfExist=RedoIfExist)

    if CorpusDir:
        translate_corpora(CorpusDir,DicOutDir,TgtScheme,Debug=Debug)


def translate_dic(OrgResDir,TgtCatFP,SrcTgtMap,OutDir,TgtSpec,MakeTextDicToo=False,Debug=False,RedoIfExist=True):
    def clean_old_files(OutDir,Backup=True):
        OldOutFiles=glob.glob(OutDir+'/*.pickle')
        if OldOutFiles:
            if not RedoIfExist:
                return False
            if Backup:
                BackupDir=os.path.join(OutDir,'bak')
            for File in OldOutFiles:
                if Backup:
                    shutil.copy2(File,BackupDir)
                os.remove(File)
        return True

        TDicOutDir=os.path.join(OutDir,'textdics')
        if os.path.isdir(TDicOutDir):
            shutil.removetree(TDicOutDir)
#    def prepare_new_dirs(OrgResDir,MakeTextDicToo):

            
    if not OrgResDir:
        if not os.path.join(OrgResDir,'alphdics'):
            sys.exit('alphdic dir does not exist')
        else:
            mtools.create_indexing_dic(OrgResDir)
            
    TgtCats=mtools.construct_tree_from_file(TgtCatFP)
    ConvTable=mtools.create_conversion_table(mtools.MecabIPACats,TgtCats,SrcTgtMap)

    if Debug:
        convtable_check(ConvTable)
    
    RedoP=clean_old_files(OutDir)
    if not RedoP:
        return None

    if MakeTextDicToo:
        TDicOutDir=os.path.join(OutDir,'textdics')
        if not os.path.isdir(TDicOutDir):
            os.makedirs(TDicOutDir)
    ODictFPs=glob.glob(os.path.join(OrgResDir,'*.objdic.pickle'))
    SrcODictNames=set(['.'.join(os.path.basename(FP).split('.')[:-3]) for FP in ODictFPs])
    
    if len(SrcODictNames)!=1:
        sys.exit('there are too many or no objdic stems')
    SrcODictName=SrcODictNames.pop()
            
    for Cntr,FP in enumerate(ODictFPs):
        Alph=FP.split('.')[-3]
        AlphObjDic=myModule.load_pickle(FP)

        Errors=defaultdict(list)
        NewWds=defaultdict(list);Dups=defaultdict(list);ECnt=0
        for WdCntr,(EssentialEls,Wd) in enumerate(AlphObjDic.items()):
            NewWd,ErrorCode=translate_word(Wd,ConvTable,TgtSpec,Debug=Debug)
            if ErrorCode:
                Errors[ErrorCode].append(Wd)
#                ECnt+=1
 #               LostCnt=sum(len(List) for ErrCat,List in Errors.items())
  #              assert(ECnt==LostCnt)
            else:
#                NewEssentialVals=tuple([ NewWd.__dict__[Att] for Att in NewWd.identityatts ])
                NewWds[EssentialEls].append(NewWd)

        OrgWdCnt=WdCntr+1
        LostCnt=sum(len(List) for ErrCat,List in Errors.items())
        assert(OrgWdCnt==len(NewWds)+LostCnt+len(Dups))
        sys.stderr.write('\nDic for "'+Alph+'", '+str(OrgWdCnt)+' wds processed, ('+str(len(Dups))+' dups) '+str(LostCnt)+' wds lost\n')
        FNStem=SrcODictName+'_'+Alph
        OutDicFP=os.path.join(OutDir,FNStem+'.objdic')
        myModule.dump_pickle(NewWds,OutDicFP)
        if MakeTextDicToo:
            output_textdic(NewWds,os.path.join(TDicOutDir,FNStem+'.textdic'))
        
#        if DoCorpus and Cntr==0:
#            check_corpus(SampleCorpusFP)

def output_textdic(Dict,FP):
    with open(FP,'wt') as FSw:
        for Wd in Dict.values():
            FSw.write(Wd.get_mecabline()+'\n')



    
        
    
def translate_word(Wd,CatConvTable,TgtSpec,MaxLevel=4,Debug=False):
    InhAttsTable={'csj':[('orth','cat','subcat','phoneassim','infform','infpat','lemma','reading'),(3,)],'juman':[('orth','cat','subcat','phonassim','infform','infpat','lemma','reading'),(3,)]}
    InfCats=['動詞','形容詞','助動詞']
    Feats=Wd.populated_catfeats()
    if Feats not in CatConvTable.keys():
        if Debug:
            sys.stderr.write(repr(Feats)+' not found in table\n')
            sys.stderr.write(repr(Wd.__dict__)+'\n')
            time.sleep(5)
        return None,'convtable'
    TgtCats=CatConvTable[Feats][0]
    OrgCats=('cat','subcat','subcat2','sem')
    if Wd.cat in InfCats:
        (NewInfPat,NewInfForm,PhoneAssim)=process_yogen(Wd,TgtSpec)
        if any(Var is None for Var in (NewInfPat,NewInfForm)):
            if NewInfPat is None and NewInfForm is None:
                ErrorCode='infboth'
            elif NewInfPat is None:
                ErrorCode='infpat'
            else:
                ErrorCode='infform'
            return None,ErrorCode
    else:
        assert(Wd.infform=='*' and Wd.infpat=='*')
        NewInfForm='*';NewInfPat='*';PhoneAssim='*'
        
    NewAttsVals={}
    NewAttsVals['infform']=NewInfForm
    NewAttsVals['infpat']=NewInfPat
    NewWd=copy.deepcopy(Wd)
    NewWd.change_feats(NewAttsVals)

    InhAttsValsToAdd={'hello':'hello'} if TgtSpec=='juman' else {'phoneassim':PhoneAssim}
    NewWd.change_feats(InhAttsValsToAdd)
    NewWd.replace_inherentatts(InhAttsTable[TgtSpec][0])
    
    for Ind,Cat in enumerate(OrgCats):
        if Ind+1>MaxLevel:
            break
        else:
            if Ind+1<=len(TgtCats):
                NewAttsVals[Cat]=TgtCats[Ind]
            else:
                NewAttsVals[Cat]='*'
    return NewWd,None

def process_yogen(Wd,TgtSpec):
    NewInfF=translate_infform(Wd.infform,TgtSpec)
    NewPat,SNote=translate_infpat(Wd.infpat,Wd.lemma,TgtSpec)
    PhoneAssim=identify_phoneassim(Wd) if (NewInfF=='連用形' and NewPat=='五段') else None 
    return NewPat,NewInfF,PhoneAssim

def identify_phoneassim(Wd):
    OnbinsGyos={'イ音便':{'k','g'},'撥音便':{'m','n'},'促音便':{'t','r','w'}}
    return next((Onbin for Onbin in OnbinsGyos.keys() if jp_morph.identify_gyo(Wd.lemma) in OnbingGyos[Onbin]),None)

def translate_infform(MInfF,TgtSpec='csj'):
    FstTwo=MInfF[:2]
    if FstTwo in ('連用','仮定','命令','基本'):
        NewMInf=('終止' if FstTwo=='基本' else FstTwo)+'形'
    elif FstTwo=='未然':
        NewMInf='未然形' if MInfF=='未然形' else '未然形４'
    elif FstTwo=='体言':
        NewMInf='連体形'
    else:
        NewMInf=None
    return NewMInf


def translate_infpat(MInfP,Lemma,TgtSpec='csj'):
    SpecialNote=None
    DanGyo=MInfP.split('・')
    assert(len(DanGyo)<=2)
    Dan=DanGyo[0]
    Gyo=None if not DanGyo[1:] else DanGyo[1]
    if Gyo is None:
        NewGyo=''
        if Dan=='一段':
            if len(Lemma)<2:
                return None, None
            NewDan='下一段' if jp_morph.identify_dan(Lemma[-2])=='e' else '上一段'
        else:
            NewDan=Dan
    elif Dan=='カ変' or Dan=='サ変':
        NewGyo='';NewDan=Dan
    else:
        NewGyo=Gyo[:2]
        NewDan=Dan
        if len(Gyo)>=3:
            SpecialNote=Dan[2:]
    NewDanGyo=NewGyo+NewDan
    return NewDanGyo,SpecialNote

def translate_corpora(CorpusDir,ObjDicDir,TgtScheme,OutFP=None,Debug=False):
        DicCorpusFPs=mtools.validate_corpora_dics_indir(CorpusDir)
        CorpusOutDir=re.sub('/$','', CorpusDir)+'_trans_'+TgtScheme
        
        for CorpusFP in DicCorpusFPs['corpus']:
            OutFP=myModule.change_ext(os.path.join(CorpusOutDir,CorpusFP),TgtScheme)
            translate_corpus(CorpusFP,ObjDicDir,OutFP=CorpusFP+'.out',Debug=Debug)

def translate_corpus(MecabCorpusFP,ObjDicDir,OutFP=None,Debug=False):
    
    # collect all essentialels from the corpus, with line numbers
    CorpusEssAttsLines=mtools.extract_identityattvals(MecabCorpusFP,'corpus',['cat','orth','infform'])
    LineCnt=myModule.get_linecount(MecabCorpusFP)
    # objdic, with mecab keys but translated contents
    AlphObjDicFPs=glob.glob(ObjDicDir+'/*.pickle')
    if not AlphObjDicFPs:
        sys.exit('Objdics not found in '+ObjDicDir)
    # we're now identifying lines with existent keys in objedic
    FndWds={}
    for AlphObjDicFP in AlphObjDicFPs:
        sys.stderr.write(AlphObjDicFP+'\n'),
        AlphObjDic=myModule.load_pickle(AlphObjDicFP)
        Alph=myModule.get_stem_ext(myModule.get_stem_ext(AlphObjDicFP)[0])[0][-1]
        for (CorpusEssAtt,Reading),Lines in CorpusEssAttsLines.items():
            if CorpusEssAtt in AlphObjDic.keys():
                for Line in Lines:
                    FndWds[Line]=AlphObjDic[CorpusEssAtt][0]
            else:
                if Debug:
                    CharsWithRelatives=jp_morph.CharsWithRelatives
                    if Reading.startswith(Alph) or (Alph in CharsWithRelatives.keys() and any(Reading.startswith(Relative) for Relative in CharsWithRelatives[Alph])):
                        sys.stderr.write(repr(CorpusEssAtt)+' not found')
                        sys.stderr.write('\n')
                        
    
    sys.stderr.write('you have '+str(LineCnt-len(FndWds.keys()))+' missing entries out of '+str(LineCnt)+'\n')

    Out=sys.stdout if OutFP is None else open(OutFP,'wt')
    with open(MecabCorpusFP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if LiNe=='EOS\n':
                TransWdStr=LiNe.strip()
            else:
                if Cntr in FndWds.keys():
                    TransWdStr=FndWds[Cntr].get_mecabline()
#                WdIfFnd=next((Wd for (Inds,Wd) in FndWds.items() if Cntr in Inds), None)
 #               if WdIfFnd is None:
                else:
                    TransWdStr=fallback_trans('FALLBACK\t'+LiNe.strip())

            sys.stdout.write(TransWdStr+'\n')        
            Out.write(TransWdStr+'\n')
    Out.close()
    
def fallback_trans(Line):
    return Line
    



def main():
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('resdir')
    Psr.add_argument('target_scheme')
    Psr.add_argument('--out-dir',default=None)
    Psr.add_argument('--not-redo-if-exist',action='store_true')
    Psr.add_argument('--idiodic',default=None)
    Psr.add_argument('--corpus-dir',default=None)
    Psr.add_argument('--textdic-too',action='store_true')
    Psr.add_argument('--debug',action='store_true')

    Args=Psr.parse_args()

    assert(Args.target_scheme in ('csj','juman'))

    if not os.path.isdir(Args.resdir) or (Args.out_dir and not os.path.isdir(Args.out_dir)) or (Args.corpus_dir and not os.path.isdir(Args.corpus_dir)):
        sys.exit('non dir specified for a dir')
    
    main0(Args.resdir, Args.target_scheme, Args.out_dir, Args.idiodic, CorpusDir=Args.corpus_dir, RedoIfExist=not Args.not_redo_if_exist,MakeTextDicToo=Args.textdic_too,Debug=Args.debug)

if __name__=='__main__':
    main()
