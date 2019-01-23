import re, imp, os, sys, time, shutil,subprocess,collections, copy,bidict,glob
from difflib import SequenceMatcher
from collections import defaultdict,OrderedDict
from pythonlib_ys import main as myModule
import romkan
from pythonlib_ys import jp_morph
import correspondences
imp.reload(myModule)
imp.reload(jp_morph)
imp.reload(correspondences)

CharsWithRelatives={'カ':('ガ',),'キ':('ギ',),'ク':('グ',),'ケ':('ゲ',),'コ':('ゴ',),'サ':('ザ',),'シ':('ジ',),'ス':('ズ',),'セ':('ゼ',),'ソ':('ゾ',),'タ':('ダ',),'チ':('ヂ',),'ツ':('ヅ',),'テ':('デ',),'ト':('ド',),'ハ':('バ','パ',),'ヒ':('ピ','ビ',),'フ':('プ','ブ',),'ヘ':('ペ','ベ',),'ホ':('ポ','ボ',),'ア':('ァ',),'イ':('ィ',),'ウ':('ゥ','ヴ',),'エ':('ェ',),'オ':('ォ',),'ヤ':('ャ',),'ユ':('ュ',),'ヨ':('ョ',),'ツ':('ヅ','ッ',)}
RelativesToChars={Rels:Char for (Char,Rels) in CharsWithRelatives.items()}
RelativeToChar={}
for Rels,Char in RelativesToChars.items():
    for Rel in Rels:
        RelativeToChar[Rel]=Char
    
CharsWithoutRelatives=list('ナニヌネノマミムメモラリルレロワ')
EntryChars=list(CharsWithRelatives.keys())+CharsWithoutRelatives

try:
    from ipdb import set_trace
except:
    from pdb import set_trace
# Chunk:
# SentLine:

Debug=0
HomeDir=os.getenv('HOME')

DefFts=['orth','cat','subcat','subcat2','sem','infpat','infform','lemma','reading','pronunciation']
DefFtsSmall=DefFts[:8]
DefIndsFts={Ind:Ft for (Ind,Ft) in enumerate(DefFts)}
# the reverse list from ft to ind
DefFtsInds={ Ft:Ind for (Ind,Ft) in DefIndsFts.items() }
InfCats=('動詞','形容詞','助動詞')
IrregPats=('不変化型','サ変','カ変')
DinasourPats=('ラ変','文語','四段','下二','上二')

class Tree:
    def __init__(self,CompPaths):
        self.comppaths=CompPaths

    def is_path(self,PathCand):
        if not type(PathCand).__name__=='list':
            return False
        if not PathCand[0][0] is None:
            return False
        if not all((type(Node).__name__=='tuple') for Node in PathCand):
            return False
        return True
    
    def complete_path_p(self,Path):
        return Path[-1][-1] is None

    def next_nodes(self,CurNode):
        NextNodes=[]
        for Node in self.nodes:
            if CurNode[1]==Node[0]:
                NextNodes.append(Node)
        return NextNodes
    def classify_paths(self,Paths):
        Complete=[];Int=[]
        for Path in Paths:
            if self.complete_path_p(Path):
                Complete.append(Path)
            else:
                Int.append(Path)
        return Complete, Int

    def create_paths(self):
        def extend_path(Path):
            NextNodes=self.next_nodes(Path[-1])
            NewPaths=[Path+[NextNode] for NextNode in NextNodes]
            assert(all(self.is_path(NewPath) for NewPath in NewPaths))
            return NewPaths

        def extend_multipaths(Paths):
            NewPaths=[]
            for Path in Paths:
                NewPaths.extend(extend_path(Path))
            return NewPaths
        
        #(IntPaths,CompPaths)=next_nodes(self.startnodes)
        IntPaths=[ [Node] for Node in self.startnodes ]
        CompPaths=[]
        Fst=True
        while IntPaths:
            NewPaths=extend_multipaths(IntPaths)
            NewCompPaths,IntPaths=self.classify_paths(NewPaths)
            CompPaths.extend(NewCompPaths)

        return CompPaths
            
def extract_diffs_withinresource(ResFP,EssFtNames,OrderedFtNames,PrvDiffDic={},Debug=False,DicOrCorpus=None,ResLineCnt=None):
    DiffEls=PrvDiffDic
    CorD=DicOrCorpus if DicOrCorpus is not None else dic_or_corpus(ResFP,FullCheckP=False)
    if CorD is None:
        sys.exit(ResFP+' not identified either as corpus or dic\n')
    PConsts=myModule.prepare_progressconsts(ResFP,KnownCnt=ResLineCnt)
    MSs=None
    with open(ResFP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            Linum=Cntr+1
            if Cntr!=0 and Cntr%100000==0:
                MSs=myModule.progress_counter(MSs,PConsts,Cntr)
            if CorD=='corpus' and LiNe=='EOS\n':
                continue
            Line=LiNe.strip()
            try:
                EssFts=pick_feats_fromline(Line,EssFtNames,InhFtNames=OrderedFtNames,DicOrCorpus=CorD,ValueOnlyP=True)
            except:
                pick_feats_fromline(Line,EssFtNames,InhFtNames=OrderedFtNames,DicOrCorpus=CorD)
            if EssFts not in DiffEls.keys():
                DiffEls[EssFts]={Line:{ResFN:[Linum]}}
            elif Line not in DiffEls[EssFts].keys():
                DiffEls[EssFts][Line].update({Line:{ResFN:[Linum]}})
            else:
                DiffEls[EssFts][Line][ResFN].append(Linum)

    return DiffEls
    
def extract_resdiffs(ResFPs,EssFtNames,OrderedFtNames,ResLineCnts=None,ResTypes=None):
    assert all(EssFt in OrderedFtNames for EssFt in EssFtNames)
    
    ResLineCnts=[myModule.get_linecount(ResFP) for ResFP in ResFPs] if ResLineCnts is None else ResLineCnts
    ResLineCnts=tuple(ResLineCnts)
    assert (len(ResLineCnts)==len(ResFPs))

    CorDs=[mtools.dic_or_corpus(ResFP) for ResFP in ResFPs] if CorDs is None else CorDs
    CorDs=tuple(CorDs)
    assert (len(CorDs)==len(ResFPs))

    ResFPsTypes=list(zip(ResFPs,CorDs))

    DiffDic={}
    for ResFP in ResFPs:
        DiffDic=extract_diffs_withinresource(ResFP,EssFtNames,OrderedFtNames,PrvDiffDic=DiffDic)
    return DiffDic


def normalise_unify_ftsets(FtSets):
    SoFar=FtSets[0]
    for FtSet in FtSets[1:]:
        SoFar=normalise_unify_twoftsets(SoFar,FtSet)
        if SoFar is None:
            break
    return SoFar

def normalise_unify_twoftsets(Fts1,Fts2):
    DiffInds=diffinds_two_ftsets(Fts1,Fts2)
    (UnifiableDiffInds,NonUnifiableDiffInds)=DiffInds
    Which=None
    PronInd=len(Fts1)-1
    if PronInd in NonUnifiableDiffInds:
        Which=choose_pronunciation(Fts1[-1],Fts2[-1])
        if Which==0:
            Normed=Fts2[:-1]+(Fts1[-1],)
        elif Which==1:
            Normed=Fts1[:-1]+(Fts2[-1],)

    if NonUnifiableDiffInds==[PronInd] and Which is not None:
        Unified=Normed
    else:
        if NonUnifiableDiffInds:
            Unified=None 
        elif Which==0:
            Unified=unify_two_ftsets(Normed,Fts2)
        elif Which==1:
            Unified=unify_two_ftsets(Fts1,Normed)
        elif Which is None:
            Unified=unify_two_ftsets(Fts1,Fts2)
    if Unified is None and NonUnifiableDiffInds==[PronInd-1]:
        NormedLemma=normalise_twolemmata(Fts1[PronInd-1],Fts2[PronInd-1])
        if NormedLemma:
            Which=0 if NormedLemma==Fts1[PronInd-1] else 1
            if Which==0:
                Unified=unify_two_ftsets(Fts1,Fts2[:PronInd-1]+(NormedLemma,)+Fts2[-1:])
            else:
                Unified=unify_two_ftsets(Fts1[:PronInd-1]+(NormedLemma,)+Fts1[-1:],Fts2)
    return Unified

def normalise_twolemmata(Lemma1,Lemma2):
    Lemmata=(Lemma1,Lemma2)
    # pick the kanji version if only one of them is
    if all(myModule.all_of_chartypes_p(Lemma,['hiragana']) for Lemma in Lemmata):
        return normalise_hiragana_twolemmata(Lemma1,Lemma2)
    else:
        HanInds=[Ind for (Ind,Lemma) in enumerate(Lemmata) if myModule.at_least_one_of_chartypes_p(Lemma,['han'])]
        if any(len(HanInds)==Len for Len in (0,2)):
            return None
        else:
            HanInd=HanInds[0]
            NonHanInd=1 if HanInd==0 else 0
            if not myModule.all_of_chartypes_p(Lemmata[NonHanInd],['hiragana']):
                return None
            else:
                HanLemma=Lemmata[HanInd];KanaLemma=Lemmata[NonHanInd]
                RenderedKanaLemma=myModule.render_kana(HanLemma)
                if KanaLemma==RenderedKanaLemma:
                    return HanLemma
                else:
                    return None

ContractionMap=[('じゃ','では')]              
def normalise_hiragana_twolemmata(HiraganaLemma1,HiraganaLemma2):
    Lemmata=(HiraganaLemma1,HiraganaLemma2)
    if len(HiraganaLemma1)!=len(HiraganaLemma2):
        return None
    else:
    #CharsWithRelatives=jp_morph.CharsWithRelatives
        VoicedCnts=[sum([myModule.kana2kana(Char) in jp_morph.VoicedHalfVoiced for Char in list(Lemma)]) for Lemma in Lemmata]
        VoicedInd=VoicedCnts.index(max(VoicedCnts))
        TgtInd=1 if VoicedInd==0 else 0
        VoicedLemma=Lemmata[VoicedInd];TgtLemma=Lemmata[TgtInd]
        for Cntr,Char in enumerate(VoicedLemma):
            UnvoicedChar=jp_morph.unvoice_char(Char,StrictP=True)
            if UnvoicedChar:
                L=list(VoicedLemma)
                L[Cntr]=UnvoicedChar
                UnvoicedCand=''.join(L)
                if UnvoicedCand==TgtLemma:
                    return TgtLemma
        return None       
    

def choose_pronunciation(Str1,Str2):
    if 'ー' in Str1:
        return 0
    elif 'ー' in Str2:
        return 1
    elif 'ヲ' in Str1:
        return 1
    elif 'ヲ' in Str2:
        return 0
    elif Str1=='ワ' and Str2=='ハ':
        return 0
    elif Str2=='ワ' and Str1=='ハ':
        return 1
    else:
        return None
    
    

def unify_two_ftsets(FtSet1,FtSet2):
    Unified=[]
    for Ind,(Ft1,Ft2) in enumerate(zip(FtSet1,FtSet2)):
        if Ft1==Ft2:
            Unified.append(Ft1)
        elif Ft1=='*' and Ft2!='*':
            Unified.append(Ft2)
        elif Ft1!='*' and Ft2=='*':
            Unified.append(Ft1)
        else:
            return None

    return tuple(Unified)

def diffinds_two_ftsets(FtSet1,FtSet2):
    Inds=[[],[]]
    for Ind,(Ft1,Ft2) in enumerate(zip(FtSet1,FtSet2)):
        if Ft1!=Ft2:
            if any(Ft=='*' for Ft in (Ft1,Ft2)):
                Inds[0].append(Ind)
            else:
                Inds[1].append(Ind)
    return Inds
    
def count_head_charrep(TgtChar,Str):
    Cnt=0
    for Char in Str:
        if Char==TgtChar:
            Cnt+=1
        else:
            break
    return Cnt

def construct_tree_from_file(FP):
    Nodes=[];PrvLevel=0;FullPaths=[]
    with open(FP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            LineR=re.sub(r'#.+$','',LiNe).rstrip()
            if not LineR.lstrip():
                continue
            LineEls=LineR.split('\t')
            Level=count_head_charrep('',LineEls)
            if Level==0:
                CurSuperCats=LineEls
            elif Level>=PrvLevel:
                if len(CurSuperCats)<=Level:
                    CurSuperCats.append(LineEls[Level])
                else:
                    CurSuperCats[Level]=LineEls[Level]
            elif Level<PrvLevel:
                CurSuperCats=CurSuperCats[:Level]+LineEls[Level:]
            FullPaths.append(tuple(CurSuperCats[:Level]+[LineEl for LineEl in LineEls if LineEl]))
#            print(FullPaths)
            PrvLevel=Level
            
    return Tree(FullPaths)

MecabCatFN='mecabipa_cats.txt'
CatDir=os.path.join(os.getenv('HOME'),'myProjects/myPythonLibs/mecabtools/tagsets')
MecabCatFP=os.path.join(CatDir,MecabCatFN)
MecabIPACats=construct_tree_from_file(MecabCatFP)
CatCnt=len(MecabIPACats.comppaths)
Mappings=correspondences.MecabCSJ,correspondences.MecabJuman

def continuous_p(Ints):
    Bool=True
    for Cntr,Int in enumerate(Ints):
        if Cntr!=0 and abs(PrvInt-Int)!=1:
            Bool=False
            break
        PrvInt=Int
    return Bool
    

for Mapping in [Mappings[0]]:
    OrderedKeyList=sorted(myModule.flatten_list(Mapping.keys()))
    assert(continuous_p(OrderedKeyList))
    assert(OrderedKeyList[-1]==CatCnt)
    
MecabCSJMapping=Mappings[0]
MecabJumanMapping=Mappings[1]

def create_conversion_table(OrgTree,TgtTree,Mapping,IdioDic=None,Depth='max'):
    assert ('0id' not in Mapping.values() or IdioDic)
    Table={}
    for Cntr,Path in enumerate(OrgTree.comppaths):
        TgtLinums=next(Nums2 for (Nums1,Nums2) in Mapping.items() if Cntr+1 in Nums1)
        TgtIndices=[Num-1 for Num in TgtLinums]
        Table[Path]=[TgtTree.comppaths[TgtIndices[0]]]
    return Table
        
def validate_corpora_dics_indir(Dir,Strict=False):
        CDFPs={'corpus':glob.glob(os.path.join(Dir,'*.mecab')),'dic':glob.glob(os.path.join(Dir,'*.csv'))}
        ProbFiles={'corpus':[],'dic':[]}
        for CorD,FPs in CDFPs.items():
            for FP in FPs:
                if dic_or_corpus(FP)!=CorD:
                    ProbFiles[CorD].append(FP)
        for CorD,FPs in ProbFiles.items():
            if FPs:
                sys.stderr.write('problem '+CorD+' files '+repr(ProbFiles)+'\n')
            if Strict:
                sys.exit()
            else:
                CDFPs[CorD]=list(set(CDFPs[CorD])-set(FPs))
        return CDFPs

def sort_dic(DicFP,ColNum,OutFP=None,InLineP=False):
    NumStr=str(ColNum)+','+str(ColNum)
    if not os.path.isfile(DicFP) or not os.path.isdir(os.path.dirname(OutFP)):
        sys.exit('file does not exist')
    TmpOutFP=DicFP+'.tmp'
#    TmpFPForNoReading=DicFP+'.noread'
 #   ShellCmd=' '.join(["sed -i '/\* *$/p'",DicFP,'>',TmpFPForNoReading])
  #  subprocess.Popen(ShellCmd,shell=True).communicate()
    ShellCmd=' '.join(['sed',"'/\* *$/d'",DicFP,'|','LANG=C','sort','-t,','-k',NumStr,'>',TmpOutFP])
    subprocess.Popen(ShellCmd,shell=True).communicate()
    if InLineP:
        OutFP=DicFP
    elif OutFP is None:
        OutFP=DicFP+'.out'

    if InLineP:
        shutil.copy(TmpOutFP,OutFP)
    os.remove(TmpOutFP)

 #   StartChar=dict(pick_feats_fromline(Line,['reading'],DicOrCorpus='dic'))['reading'][0][0]

def deduplicate_list(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def divide_dic_into_alphdics(DicFPWhole,FPsPerChar,RelToChar):
    OrgTotal=myModule.get_linecount(DicFPWhole)
    CharsFSws={EntryChar:open(FP,'wt') for (EntryChar,FP) in FPsPerChar.items() }
    
    with open(DicFPWhole) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if Cntr!=0 and Cntr%10000==0:
                print(str(Cntr)+' '+str(OrgTotal))
            StartChar=pick_feats_fromline(LiNe.strip(),['reading'],DicOrCorpus='dic')[0][1][0]
            if StartChar in EntryChars:
                myFSw=CharsFSws[StartChar]
            elif StartChar in RelToChar.keys():
                myFSw=CharsFSws[RelToChar[StartChar]]
            else:
                myFSw=CharsFSws['outsiders']
            myFSw.write(LiNe)
    for FSw in CharsFSws.values():
        FSw.close()
    ResTotal=0
    for FP in FPsPerChar.values():
        ResTotal+=myModule.get_linecount(FP)
    
    assert(OrgTotal==ResTotal)    
 
def create_alph_objdics(DicDir,Lang='jp',RedoSrc=False):
    DicFPs=glob.glob(os.path.join(DicDir,'*.csv'))
    assert DicFPs
    assert all(dic_or_corpus(DicFP,FullCheckP=False)=='dic' for DicFP in DicFPs)
    SandboxOutputDir=os.path.join(DicDir,'objdics')
    SandboxSrcDir=os.path.join(DicDir,'srcdics')
    if not os.path.isdir(SandboxOutputDir):
        os.makedirs(SandboxOutputDir)
    if not os.path.isdir(SandboxSrcDir):
        os.makedirs(SandboxSrcDir)
    else:
        Files=glob.glob(SandboxOutputDir+'/*.objdic')
        if Files:
            for File in Files:
                os.remove(File)
    # these are the original files, to be copied with '.tmp' ext        
    DicFNs=[os.path.basename(DicFP) for DicFP in DicFPs]
    #RestFPs=[];DicFNs=[os.path.basename(RestFP) for RestFP in RestFPs]
    MgdFNStem=myModule.get_stem_ext(myModule.merge_filenames(DicFNs,UpperBound=10))[0]
    MgdFPSrcStem=os.path.join(SandboxSrcDir,MgdFNStem)
    MgdDicTmpFP=MgdFPSrcStem+'.rest'

    # merging all the dics
    FSw=open(MgdDicTmpFP,'wt')
    for DicFP in DicFPs:
        with open(DicFP) as FSr:
            FSw.write(FSr.read())
    FSw.close()
    shutil.copy(MgdDicTmpFP,MgdDicTmpFP+'.org')

    FPsPerChar={EntryChar:MgdFPSrcStem+'.'+EntryChar+'.csv' for EntryChar in EntryChars }
    FPsPerChar['outsiders']=MgdFPSrcStem+'.outsiders.csv'

    if RedoSrc:
        divide_dic_into_alphdics(MgdDicTmpFP,FPsPerChar,RelativeToChar)
        

    #if Lang=='jp':
        # excluding rare stuff (separate file) and dakuten stuff (included in the nonvoiced ctrprt)

    for FPPerChar in FPsPerChar.values():
        MecabWdsPerChar={}
        with open(FPPerChar) as FSr:
            for LiNe in FSr:
                MecabWd=mecabline2mecabwd(LiNe.strip(),'dic')
                MecabWdsPerChar[tuple(MecabWd.identityattsvals.values())]=MecabWd

            if MecabWdsPerChar:
                FPEls=FPPerChar.split('.')
                SrcFPStem='.'.join(FPEls[:-1])
                NewFPStem=change_dir_infp(SrcFPStem,5,'objdics')
                Char=FPEls[-2]
                sys.stderr.write('Alphabet dic for '+Char+' done, '+str(len(MecabWdsPerChar))+' entries\n')
                myModule.dump_pickle(MecabWdsPerChar,NewFPStem+'.objdic')
            else:
                sys.stderr.write('nothing found for '+Char+'\n')

def change_dir_infp(FP,Num,Repl):
    New=FP.strip().split('/')
    New[Num]=Repl
    return '/'.join(New)
                
def get_alphwords_fromdic(Chars,RestFP):
    MecabWdsPerChar={}
    TmpFP=RestFP+'.tmp'
    FSw=open(TmpFP,'wt')
#    CharsWithRelatives=jp_morph.CharsWithRelatives
    with open(RestFP) as FSr:
                Fnd=False
                for LiNe in FSr:
                    Line=LiNe.strip()
                    StartChar=dict(pick_feats_fromline(Line,['pronunciation'],DicOrCorpus='dic'))['pronunciation'][0][0]

                    if StartChar in Chars:
                        if not Fnd:
                            Fnd=True
                        MecabWd=mecabline2mecabwd(Line,'dic')
                        MecabWdsPerChar[tuple(MecabWd.identityattsvals.values())]=MecabWd
                    else:
                        if Fnd:
                            FSw.write(FSr.read())
                            FSw.close()
                            shutil.copy(TmpFP,RestFP)
                            os.remove(TmpFP)
                            return MecabWdsPerChar
                        FSw.write(LiNe)
    FSw.close()
    shutil.copy(TmpFP,RestFP)
    os.remove(TmpFP)
    return MecabWdsPerChar

def mecabline_p(Line):
    return ',' in Line or Line=='EOS'
    
def corpusline_p(Line):
    if not mecabline_p(Line):
        return False
    return Line=='EOS' or '\t' in Line

def dicline_p(Line):
    if not mecabline_p(Line):
        return False
    else:
        return ',' in Line and '\t' not in Line
def corpus_or_dic(FP,FullCheckP):
    return dic_or_corpus(FP,FullCheckP)
    
def get_line(FP,LiNum):
    with open(FP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if Cntr+1==LiNum:
                return LiNe.strip()
        return None

def dic_or_corpus(FP,FullCheckP=True):
    if FullCheckP:
        CheckUpTo=float('inf')
        if sys.getsizeof(FP)>100:
            sys.stderr.write('[dic_or_corpus] full check is being made. this may take time\n')
    else:
        CheckUpTo=5000
    if valid_mecabfile_p(FP,'corpus',CheckUpTo=CheckUpTo):
        return 'corpus'
    elif valid_mecabfile_p(FP,'dic',CheckUpTo=CheckUpTo):
        return 'dic'
    else:
        return None

def feat_count_line(Line,DicOrCorpus):
    _,Fts,_=decompose_mecabline(Line,DicOrCorpus)
    return len(Fts)
    
def valid_mecabfile_p(FP,DicOrCorpus,CheckUpTo=float('inf')):
    assert any(DicOrCorpus==Type for Type in ('dic','corpus'))
    valid_p=valid_corpusline_p if DicOrCorpus=='corpus' else valid_dicline_p
    LengthCntd=False
    with open(FP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if Cntr>CheckUpTo:
                break
            if DicOrCorpus=='corpus' and LiNe=='EOS\n':
                continue
            if not valid_p(LiNe):
                sys.stderr.write(' '.join(['Offending line:',str(Cntr+1),LiNe]))
                return False
            if not LengthCntd:
                FtLen=feat_count_line(LiNe.strip(),DicOrCorpus)
                LengthCntd=True
            else:
                if FtLen!=feat_count_line(LiNe.strip(),DicOrCorpus):
                    sys.stderr.write(' '.join(['Offending line:',str(Cntr+1),LiNe]))
                    return False



    return True

def valid_dicline_p(LiNe):
    Line=LiNe.strip()
    if ' ' in Line or '\t' in Line:
        return False
    elif ',' not in Line:
        return False
    else:
        LineEls=Line.split(',')
        if len(LineEls)<5:
            return False
        elif any(not re.sub(r'^-','',LineEl).isdigit() for LineEl in LineEls[1:4]):
            return False
        else:
            return True

def valid_corpusline_p(LiNe):
    Line=LiNe.strip()
    if Line=='EOS':
        return True
    elif ' ' in Line or '\t' not in Line:
        return False
    elif len(Line.split('\t')[1].split(','))<=2:
        return False
    else:
        return True    
    
def decompose_mecabline(Line,DicOrCorpus='corpus'):
    assert DicOrCorpus=='dic' or DicOrCorpus=='corpus'
    Line=Line.strip()
    if DicOrCorpus=='corpus':
        Orth,Rest=Line.strip().split('\t')
        Fts=Rest.split(',')
        Costs=None
    else:
        LineEls=Line.split(',')
        Orth=LineEls[0]
        Costs=tuple(LineEls[1:4])
        Fts=LineEls[4:]
    return (Orth,tuple(Fts),Costs)

def simpletranslate_resources(SrcRes,SrcType,SrcFts,TgtDics,TgtType,TgtFts,IdentityAtts={'orth','cat','infform'}):
    SrcFtSet,TgtFtSet=set(SrcFts),set(TgtFts)
    if SrcFtSet==TgtFtSet:
        SubsumptionType='identical'
    
    elif SrcFtSet.issubset(TgtFtSet):
        SubsumptionType='reduction'
    elif TgtFtSet.issubset(SrcFtSet):
        SubsumptionType='enlarge'
    else:
        SubsumptionType='idiosyncratic'
    
    SrcIAValsInds=extract_identityattvals([SrcRes],SrcType,SrcFts,IdentityAtts)
    TranslatedDicFP=os.path.join(os.path.dirname(TgtDics[0]),'translation.csv')
    SrcTransMappings,NearMisses=create_newdic_mapping(SrcIAValsInds,SrcFts,SubsumptionType,TgtDics,IdentityAtts,TranslatedDicFP)
    LineIndsWithTrans=SrcTransMappings.keys()
    FstIndsOthers={Inds[0]:Inds[1:] for Inds in LineIndsWithTrans}
    SrcTransMappings={SrcInds[0]:TgtInd for (SrcInds,TgtInd) in SrcTransMappings.items()}
    IndTrans={}
    with open(SrcRes) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if LiNe=='EOS\n':
                Output=LiNe

            elif Cntr in SrcTransMappings.keys():
                Output=get_line(TranslatedDicFP,SrcTransMappings[Cntr]+1)+'\n'
                OtherInds=FstIndsOthers[Cntr]
                IndTrans[OtherInds]=Output
#                AllOtherInds.extends[OtherInds]
    #        elif Cntr in AllOtherInds:
     #           for IndSet in IndTrans.keys():
      #              if Cntr in IndSet:
       #                 Output=IndTrans[IndSet]
        #                break                
            else:
                Orth,Fts=decompose_corpusline(LiNe)
                Output=Orth+'\t'+','.join(Fts[:len(SrcFts)-1])+'\n'
            sys.stdout.write(Output)
                

def create_newdic_mapping(SrcIAValsInds,SrcFts,SubsumptionType,TgtDics,IdentityAtts,OutFP):
    # creating new translated dic in file
    # while mapping is created as a dict
    SrcIAVals=SrcIAValsInds.keys()
    SrcIAValsR=[SrcIAVal[:-1] for SrcIAVal in SrcIAVals]

    Mappings={}
    OutFSr=open(OutFP,'wt')
    NearMisses=defaultdict(set)
    TransCnt=0
    if SubsumptionType in ['reduction','identical']:
        for TgtDic in TgtDics:
            with open(TgtDic) as FSr:
                for LiNe in FSr:
                    Line=LiNe.strip()
                    LineEls=Line.split(',')
                    TgtWdFts=line2wdfts(Line,CorpusOrDic='dic')
                    TgtIAVals=tuple([Val for (Att,Val) in TgtWdFts if Att in IdentityAtts])
                    Costs=LineEls[1:3]
                    if TgtIAVals in SrcIAVals:
                        TransCnt+=1
                        RedFts=[V for (A,V) in TgtWdFts if A in SrcFts]
                        OutputLine=','.join([RedFts[0]]+Costs+RedFts[1:])
                        Mappings[tuple(SrcIAValsInds[TgtIAVals])]=TransCnt-1
                        OutFSr.write(OutputLine+'\n')
                        
                    elif TgtIAVals[:-1] in SrcIAValsR:
                        NearlyMissed=tuple([Val for Val in SrcIAVals if TgtIAVals[:-1]==Val[:-1]])
                        NearMisses[TgtIAVals].add(NearlyMissed)
    OutFSr.close()                
    return Mappings,NearMisses
     

 
def extract_identityattvals(ResFP,Type,IdentityAtts,SrcFts=None):
    IdentityAtts=tuple(IdentityAtts)
    assert Type=='dic' or Type=='corpus'
    #SrcFts=DefFts if SrcFts is None else SrcFts
    IAttsInds=defaultdict(list)
    if Type=='corpus':
        Seen=set()
    with open(ResFP) as FSr:
        for Ind,LiNe in enumerate(FSr):
            if Type=='corpus' and LiNe=='EOS\n':
                continue
            WdFts=line2wdfts(LiNe.strip(),CorpusOrDic=Type,Fts=SrcFts)
            IdentityAttVals=[]
            for IdAtt in IdentityAtts:
                IdentityAttVals.append(WdFts[IdAtt])
            IdentityAttVals=tuple(IdentityAttVals)
            if Type=='corpus':
                if IdentityAtts not in Seen:
                    Seen.add(IdentityAttVals)
                    Reading='*' if 'reading' not in WdFts.keys() else WdFts['reading']
                    IAttsInds[(IdentityAttVals,Reading)].append(Ind)
            else:
                IAttsInds[IdentityAttVals].append(Ind)
    return {IAtt:tuple(Inds) for (IAtt,Inds) in IAttsInds.items()}
    



def radicalise_mecabline(MecabCorpusLiNe):
    Line=MecabCorpusLiNe.strip()
    MWd=mecabline2mecabwd(Line,CorpusOrDic='corpus')
    if MWd.cat=='助動詞' and (MWd.infpat=='特殊・ナイ' or MWd.infpat=='特殊・タイ'):
        MWd.infpat='形容詞・イ段'
    if not radicalisable_p(MWd):
        return MecabCorpusLiNe
    else:
        return radicalise_mecabwd(MWd)

def generate_sentchunks(MecabFP):
    FSr=open(MecabFP)
    Chunk=[]
    for LiNe in FSr:
        if LiNe=='EOS\n':
            yield Chunk
            Chunk=[]
        else:
            Chunk.append(LiNe.rstrip())

def get_mecablines_wds(MWds):
    Strs=''
    for MWd in MWds:
        Strs.append(MWd.get_mecabline())
    return '\n'.join(MWds)+'\n'

def radicalisable_p(MWd):
    if MWd.cat not in InfCats:
        return False
    elif any(MWd.infpat.startswith(Pat) for Pat in IrregPats):
        return False
    elif MWd.infform=='連用テ接続' and MWd.cat=='形容詞' or (MWd.cat=='助動詞' and MWd.infpat.startswith('形容詞')):
        return True

    elif not MWd.infform.endswith('形') or MWd.infpat.startswith('特殊'):
        return False
    elif MWd.infpat=='一段' and any(MWd.infform==Form for Form in ('未然形','連用形')):
        return False

    elif any(MWd.infpat.startswith(Pat) for Pat in DinasourPats):
        return False
    return True

def make_suffixline(Orth,InfForm,Cat,InfPat):
    KatakanaOrth=jp_morph.render_kana(Orth,WhichKana='katakana')
    return Orth+'\t'+Cat+'活用語尾,*,*,*,'+','.join([InfPat,InfForm,Orth]+[KatakanaOrth]*2)

def radicalise_mecabwd(MWd):
    def org2new(Stuff,Stem,Suffix,GodanP):
        SuffixLen=len(Suffix)
        if GodanP:
            return Stuff[:-SuffixLen]+Stem[-1]
        else:
            return Stuff[:-SuffixLen]
            
    Stem,Suffix=MWd.divide_stem_suffix_radical()
    GodanP=True if MWd.infpat.startswith('五段') else False
    FtValPairs=[('orth',Stem),('infform','語幹'),('reading',org2new(MWd.reading,Stem,Suffix,GodanP)),('pronunciation',org2new(MWd.pronunciation,Stem,Suffix,GodanP))]
    Var1LiNe=MWd.get_variant(FtValPairs).get_mecabline()

    Var2LiNe=make_suffixline(Suffix,MWd.infform,MWd.cat,MWd.majorinfpat)+'\n'

    return Var1LiNe+'\n'+Var2LiNe
    
def fts2inds(Fts,CorpusOrDic='dic'):
    Mapping=DefLexIndsFts if CorpusOrDic=='dic' else DefIndsFts
        
    return sorted([Ind for (Ind,Ft) in Mapping.items() if Ft in Fts])

def add_costs(IndsFtsOrFts):
    ToAdd=[(1,'right'),(2,'left'),(3,'cost')]
    if type(IndsFtsOrFts).__name__=='dict':
        NewDic={}
        for (Ind,Val) in IndsFtsOrFts.items():
            NewInd=Ind if Ind==0 else Ind+3
            NewDic[NewInd]=Val
        NewDic.update(ToAdd)
        return NewDic
    elif type(IndsFtsOrFts).__name__=='list':
        CopyList=copy.copy(IndsFtsOrFts)
        CopyList=CopyList[:1]+[AddPair[1] for AddPair in ToAdd]+CopyList[2:]
        return CopyList
    else:
        sys.stderr.write('Fts must be either list or dic\n')
        return None

def pick_feats_fromline(Line,TgtFtNames,InhFtNames=None,DicOrCorpus='corpus',ValueOnlyP=False,Debug=False):
    assert (DicOrCorpus=='dic' or DicOrCorpus=='corpus')
    from bidict import bidict
    if not Line.strip():
        print('empty line encountered')
        return None
    InhFtIndsNames={Ind:Ft for (Ind,Ft) in enumerate(InhFtNames)} if InhFtNames else DefIndsFts
    FullIndsFts=InhFtIndsNames if DicOrCorpus=='corpus' else add_costs(InhFtIndsNames)
    FullIndsFts=bidict(FullIndsFts)

    Line=Line.rstrip()
    if Line.startswith(','):
        Line=Line.replace(',','、',1)
    LineEls=Line.replace('\t',',').split(',')
    LineElCnt=len(LineEls)
    LineInhFtEls=LineEls[:1]+LineEls[4:] if DicOrCorpus=='dic' else LineEls
    LineInhFtCnt=len(LineInhFtEls)
    #checking line has the specified number of feats and costs
    assert(LineInhFtCnt==len(InhFtNames) and len(LineEls)==len(FullIndsFts))

    TgtInds=[ Ind for (Ind,FtName) in FullIndsFts.items() if FtName in TgtFtNames ]

    Pairs=[]
    for Ind in TgtInds:
        Pairs.append((FullIndsFts[Ind],LineEls[Ind]))
    if not ValueOnlyP:
        return Pairs
    else:
        return tuple([Pair[1] for Pair in Pairs])

def file2delimchunks(FP,Delim):
    FSr=open(FP)
    
    Lines=[]
    for LiNe in FSr:
        Line=LiNe.strip()
        if Line==Delim:
            yield Lines
            Lines=[]
        else:
            Lines.append(Line)

def search_feat(MWds,Ft,Val,FstOnly=False):
    Fnd=[]
    for MWd in MWds:
        if MWd.__dict__[Ft]==Val:
            Fnd.append(MWd)
            if FstOnly:
                return Fnd
    return Fnd


class MecabWdCluster:
    def __init__(self,MecabWdParse,CoreFtNames):
        self.wd=MecabWdParse
        self.core_fts=[ MecabWdParse ]

class MecabSentParse:
    def __init__(self,MecabWds):
        self.wds=MecabWds
    def stringify_orths(self,WithSpace=True):
        Str=''
        for Wd in self.wds:
            Str+=Wd.orth
            if WithSpace:
                Str+=' '
        if WithSpace:
            Str=Str.strip()
        return Str
    
class Word:
    def __init__(self,AVPairs,InhAtts=[]):
        assert AVPairs.keys()
        assert all(InhAtt in AVPairs.keys() for InhAtt in InhAtts)
        self.metaatts={'inherentatts','metaatts'}
        self.inherentatts={A for (A,V) in AVPairs.items() if A in InhAtts}
        for Ft,Val in AVPairs.items():
            self.__dict__[Ft]=Val
        
        if not all(OblCat in self.__dict__.keys() for OblCat in self.inherentatts):
            sys.exit('all obligatory categories must be present')

    def change_feats(self,AVPairs,CopyP=False):
        Self=copy.deepcopy(self) if CopyP else self
        for (Ft,Val) in AVPairs.items():
            Self.__dict__[Ft]=Val
        if CopyP:
            return Self
    def delete_feats(self,Atts,InhAsWell=False):
        for Att in Atts:
             if Att in self.inherentatts:
                 if InhAsWell:
                     self.inherentatts.remove(Att)
                     del self.__dict__[Att]
                 else:
                     sys.stderr.write('cannot delete inherent att: '+Att+'\n')
             else:
                 del self.__dict__[Att]
            
class WordParse(Word):
    def __init__(self,AVPairs,Costs=None,InhAtts={'orth','cat','lemma','reading'}):
        super().__init__(AVPairs)
        self.inherentatts=self.inherentatts.union(InhAtts)
        self.costs=Costs

        self.orthtypes=self.get_orthtypes()
    def get_orthtypes(self):
        Types=[];PrvType=''
        for Char in self.orth:
            CurType=myModule.identify_chartype(Char)
            if CurType!=PrvType:
                Types.append(CurType)
            PrvType=CurType
        return Types
    def get_feature_strs(self,OrderedKeys=None,InhOnly=True):
        RestrictedSet=self.inherentatts if InhOnly else {A for A in self.__dict__.keys() if A not in self.metaatts}
        Dict={Att:Val for (Att,Val) in self.__dict__.items() if Att in RestrictedSet}
        Pairs=reorder_dict(Dict,OrderedKeys) if OrderedKeys else Dict.items()
        return [str(Val) for (Att,Val) in Pairs]
            
    
    def get_jumanline(self,CorpusOrDic='corpus'):
        
        Orth=self.orth
        FtStrs=self.get_feature_strs(OrderedKeys=['orth','reading','lemma','cat','subcat','subcat2','infform'])
        FtStr=' '.join(FtStrs)
        return FtStr

class MecabWdParse(WordParse):        
    def __init__(self,AVPairs,Costs=None,InhAtts=('orth','cat','subcat','subcat2','sem','lemma','reading','infpat','infform'),IdentityAtts=('orth','cat','subcat','infform','infpat','pronunciation')):
        super().__init__(AVPairs)
        self.inherentatts=InhAtts
        self.identityatts=IdentityAtts
        self.identityattsvals=self.get_identityattsvals()
        if self.cat=='動詞' or self.cat=='形容詞':
            self.divide_stem_suffix()
         
        self.soundrules=[]; self.variants=[]
        self.count=None
        self.poss=None
        self.lexpos=None
        if 'infpat' in self.__dict__.keys():
            self.majorinfpat=self.infpat.split('・')[0] if self.infpat else self.infpat

    def replace_inherentatts(self,NewInhAtts):
        if type(NewInhAtts).__name__!='tuple':
            sys.exit('new inh atts need to be a tuple')
        for Att in self.inherentatts:
            if Att not in NewInhAtts:
                delattr(self,Att)
        self.inherentatts=NewInhAtts
#        NewAtts=[NewInhAtt for NewInhAtt in self.inherentatts if NewInhAtt not in NewInhAtts]
#        if NewAtts:
 #           sys.stderr.write('[WARNING] new inhatt, '+repr(NewAtts))
 

        
        

    def get_identityattsvals(self):     
        return {K:self.__dict__[K] for K in self.identityatts}
    def same_type(self,AnotherWd):
        return self.identityattsvals==AnotherWd.identityattsvals
    
    def set_poss(self,Poss):
        self.poss=Poss
        self.count=len(Poss)

    def set_count(self,Cnt):
        self.count=Cnt
        
    def add_count(self,By=1):
        self.count=self.count+By

    def feature_identical(self,AnotherWd,Excepts=[]):
        DefBool=True
        for Ft in self.__dict__.keys():
            if Ft not in Excepts and not self.__dict__[Ft]==AnotherWd.__dict__[Ft]:
                return not DefBool
        return DefBool

    def divide_stem_suffix_radical(self,OutputObject=True,StrictP=False):
        IrregTable= {
            'サ変':('s',{'未然ヌ接続':'e','体言接続特殊':'ん','仮定縮約１':'ur','未然レル接続':'a','未然形':'i','未然ウ接続':'iよ','連用形':'i','基本形':'uる','仮定形':'uれ','命令ｒｏ':'iろ','命令ｙｏ':'eよ','命令ｉ':'eい','未然形・長音化':'eえ','未然形・長音化i':'iい','基本形・撥音便':'uん','未然形・ヤ挿入':'iや'}),
            'カ変':('k',{'体言接続特殊':'ん','仮定縮約１':'ur','未然ウ接続':'oよ','未然形':'o','連用形':'i','基本形':'uる','仮定形':'uれ','命令ｉ':'oい','基本形・撥音便':'uん','未然形・長音化':'eえ','未然形・長音化o':'oお','未然形・長音化i':'iい','未然形・ヤ挿入':'iや'}),
            '特殊・タ':('た',{'未然形':'ろ','連用タ接続':'t','基本形':'','仮定形':'ら'}),
            '特殊・ヤ':('や',{'未然形':'ろ','連用タ接続':'t','基本形':'','体言接続':'な','仮定形':'ら'}),
            '特殊・ダ':('だ',{'未然形':'ろ','連用タ接続':'t','連用形':'で','基本形':'','仮定形':'ら','体言接続':'な'}),
                        '特殊・ジャ':('だ',{'未然形':'ろ','連用タ接続':'t','連用形':'で','基本形':'','仮定形':'ら','体言接続':'な'}),
            '特殊・マス':('まs',{'連用形':'i','未然ウ接続':'iy','未然形':'e','基本形':'u','基本形・撥音便':'n'}),
            '特殊・デス':('でs',{'連用形':'i','未然ウ接続':'iy','未然形':'iy','基本形':'u','基本形・撥音便':'n'}),
            '五段・特殊':('ちゃw',{'基本形':'u','連用形':'uく','未然形':'a','連用タ接続':'uかっ'})
            }
        Irregulars=set(IrregTable.keys())
        def determine_inftype(self):
            Pats=[ Pat for Pat in Irregulars if self.infpat.startswith(Pat) ]

            if self.infpat == '特殊・タんや' or self.infpat == '特殊・タ＋んや' or self.infpat == '文語・ベシ':
                InfType='fixed'
                InfGyo=None

            elif self.cat=='形容詞' or (self.cat=='助動詞' and (self.infpat.startswith('形容詞') or self.infpat.startswith('特殊・ナイ') or self.infpat.startswith('特殊・タイ'))):
                InfType='adj'
                InfGyo=None
            elif Pats:
                InfType=Pats[0]
                InfGyo=None
            
            elif self.infpat.startswith('五段'):
                InfType='godan'
                InfGyo=jp_morph.identify_gyo(self.infpat.split('・')[1][0],InRomaji=True)
            elif self.infpat.startswith('一段') or (self.cat=='助動詞' and any(self.lemma==Lemma for Lemma in ('れる','られる','せる','させる'))):
                InfType='ichidan'
                InfGyo=None
            else:
                InfType=None
                InfGyo=None
            return InfType,InfGyo
        
        def handle_irregulars(self,Type):
            Stem,Suffixes=IrregTable[Type]
            if self.infform not in Suffixes.keys():
                print('\n'+self.infform+' not found for '+Type+'\n')
                Suffix=None
            else:
                Suffix=Suffixes[self.infform] if Type!='サ変' else Suffixes[self.infform]
            return Stem,Suffix
           
        InfType,InfGyo=determine_inftype(self)

        if any(InfType==Type for Type in Irregulars):
            Stem,Suffix=handle_irregulars(self,InfType)
        elif InfType=='fixed':
            Stem=self.orth
            Suffix=''
        elif InfType is None and not StrictP:
            print('\nCategorisation of\n'+repr(self.__dict__)+'\nfailed\n')
            return self
        
        elif InfType=='adj':
            PossibleSuffixes=('から','かろ','かっ','きゃ','く','くっ','い','けれ','ゅう','ゅぅ','う','ぅ','き','かれ','けりゃ')
            try:
                Suffix=next(Suffix for Suffix in PossibleSuffixes if self.orth.endswith(Suffix) )
                Stem=re.sub(r'%s$'%Suffix,'',self.orth)
            except:
                Suffix=''
                Stem=self.orth
            
        elif InfType=='godan':
            if self.infform.startswith('仮定縮約'):
                self.orth=self.orth[:-1]
            Stem=self.orth[:-1]+InfGyo
            
            if self.infform.startswith('連用タ接続'):
                if any(InfGyo==Dan for Dan in ('k', 'g')):
                    Suffix='i'
                elif any(InfGyo==Dan for Dan in ('t','d','r','w')):
                    Suffix='t'
                elif any(InfGyo==Dan for Dan in ('m','n','b',)):
                    Suffix='n'

            elif any(self.infform.startswith(Type) for Type in ('未然特殊','体言接続特殊','基本形・撥音便')):
                Stem=self.orth[:-1]+InfGyo
                Suffix='n'
            elif self.infform.startswith('仮定縮約'):
                Suffix='ey'

            else:
                SuffixPlus=self.orth[len(Stem)-1:]
                Suffix=jp_morph.identify_dan(SuffixPlus[0])
                
        elif InfType=='ichidan':
            if self.lemma=='る':
                Stem=''
            else:    
                Stem=self.lemma[:-1]
            Suffix=self.orth[len(Stem):]
        else:
            sys.stderr.write('\nERROR for'+self.get_mecabline()+'\n')
            sys.exit('ERROR: no category to classify, aborting\n')
        
        self.stem=Stem
        self.suffix=Suffix

        if not Suffix:
            StemReading=self.reading
        else:
            StemReading=self.reading[:-len(self.suffix)]
            if re.match(r'^.*[a-z]$',self.stem):
                StemReading=StemReading+self.stem[-1]
        if OutputObject:
            Stem=self.get_variant([('orth',Stem),('infform','語幹'),('reading',StemReading),('pronunciation',StemReading)])
            

        if OutputObject:
            KatakanaSuffix=romkan.to_katakana(Suffix)
            Suffix=self.get_prototype(FtsVals=[('orth',Suffix),('lemma',Suffix), ('infform',self.infform), ('cat','活用語尾'), ('pronunciation',KatakanaSuffix)])
        
        return Stem,Suffix
    def populated_catfeats(self):
        PopulatedCatFeats=[self.cat]
        for Feat in (self.subcat,self.subcat2,self.sem):
            if Feat!='*':
                PopulatedCatFeats.append(Feat)
        return tuple(PopulatedCatFeats)
    
    def divide_stem_suffix(self):
        if self.cat=='動詞':
            if self.infpat=='一段':
                if any(Pat in self.infform for Pat in ('未然','連用','命令')):
                    Stem=self.orth[:-1]
                    Suffix=self.orth[-1]
                else:
                    Stem=self.orth[:-2]
                    Suffix=self.orth[-2:]
            else:
                Stem=self.orth[:-1]
                Suffix=self.orth[-1]
        elif self.cat=='形容詞':
            PossibleSuffixes=('から','かろ','かっ','きゃ','く','くっ','い','けれ','けりゃ','し')
            WhichEnding=[ Suffix for Suffix in PossibleSuffixes if self.orth.endswith(Suffix) ]
            if WhichEnding:
                Ending=WhichEnding[0]
                BoundInd=-len(Ending)
                BoundIndAlt=BoundInd-1
                if len(self.orth)> -(BoundIndAlt):
                    PrvChar=self.orth[BoundIndAlt]
                    if PrvChar in ('し','た','ぽ'):
                        BoundInd=BoundIndAlt
                Stem=self.orth[:BoundInd]
                Suffix=self.orth[BoundInd:]
            else:
                Stem=self.orth[:-1]
                Suffix=self.orth[-1:]
        self.stem=Stem
        self.suffix=Suffix
        return Stem,Suffix
                
    def initialise_features_withoutlexeme(self,AVDic):
        self.construct_lexeme(AVDic)
        self.initialise_features(AVDic)

    def initialise_features_fromlexeme(self,AVDic):
        self.set_lexeme(AVDic['lexeme'],AVDic['infform'])
        self.initialise_features(AVDic)

    def initialise_features(self,AVDic):
        DoSound=False
        if 'orth' in AVDic.keys() and ('reading' not in AVDic.keys() or AVDic['reading']=='*'):
            Orth=AVDic['orth']
            if not myModule.textproc.all_of_chartypes_p(Orth,['katakana']) and myModule.textproc.at_least_one_of_chartypes_p(Orth,['han','hiragana']):
                DoSound=True

        self.set_features(AVDic,dosoundorth=DoSound,dosoundreading=DoSound)

        if not self.orth:
            if self.lexeme.__name__=='InfLexeme':
                self.orth=self.lexeme.infforms[self.infform]
            else:
                self.orth=self.lexeme.lemma
    def set_features(self,AVDic,dosoundorth=False,dosoundreading=False):
        for Ft,Val in AVDic.items():
            self.set_feature(Ft,Val,dosoundorth=dosoundorth,dosoundreading=dosoundreading)

    def set_feature(self,Ft,Val,dosoundorth=False,dosoundreading=False):
        if Ft=='reading':
            self.set_reading(Val,dosound=dosoundreading)
        elif Ft=='orth':
            self.set_orth(Val,dosound=dosoundorth)
        elif Ft=='infform' and Val=='仮定形':
            self.infform='連用形'
        else:
            self.__dict__[Ft]=Val

    def get_variant(self,FtsVals):
        FtsVals=dict(FtsVals)
        SelfCopy=copy.deepcopy(self)
        for Ft,Val in FtsVals.items():
            SelfCopy.__dict__[Ft]=Val
        return SelfCopy

    def get_prototype(self,FtsVals={}):
        FtsVals=dict(FtsVals)
        AVPairs=[(Att,'*') for Att in self.inherentatts]
        ProtoType=MecabWdParse(*AVPairs)
        for Ft,Val in FtsVals.items():
            ProtoType.__dict__[Ft]=Val
        return ProtoType
            
    def construct_lexeme(self,AVDic):
        Cat=AVDic['cat'];Lemma=AVDic['lemma']
        CommonFts=['subcat','subcat2','sem']
        AVSubDic={}
        if AVDic['infform']!='*':
            for Ft in CommonFts:
                AVSubDic[Ft]=AVDic[Ft]
            Lexeme=InfLexeme(Cat,Lemma,{},AVDic['infpat'],**AVSubDic)
        else:
            for Ft in CommonFts:
                AVSubDic[Ft]=AVDic[Ft]
            Lexeme=NonInfLexeme(Cat,Lemma,**AVSubDic)
#Cat,Lemma,Subcat=Subcat,Subcat2=Subcat2,Sem=Sem,SoundRules=SoundRules,Variants=Variants)
            
        return Lexeme

    def set_lexeme(self,Lexeme,InfForm): 
#        if Lexeme.__name__=='InfLexeme':
#            self.orth=Lexeme.infforms[InfForm]
#        elif Lexeme.__name__=='NonInfLexeme':
#            self.orth=Lexeme.lemma

        self.lexeme=Lexeme
        self.transfer_feats_fromlex(InfForm)


    def set_orth(self,Orth,dosound=False):
        self.orth=Orth
        if dosound:
            if myModule.all_of_chartypes_p(Orth,['katakana']):
                self.reading=Orth
            elif myModule.all_of_chartypes_p(Orth,['hiragana']):
                self.reading=myModule.kana2kana_wd(Orth)
            elif myModule.all_of_chartypes_p(Orth,['han','hiragana','katakana']):
                ShellCmd=' '.join([HomeDir+'/myProgs/scripts/kakasi_katakana.sh','"'+Orth+'"'])
                self.reading=subprocess.Popen(ShellCmd,shell=True,stdout=subprocess.PIPE).communicate()[0].strip().decode()

    def set_reading(self,Reading,dosound=False):
        if not myModule.textproc.all_of_chartypes_p(Reading,['katakana']):
            pass
            #if not myModule.all_of_types_p(Reading,['sym','cjksym']):
            #    print('\n'+Reading+' '+inspect.stack()[1][3]+' reading not in katakana')
#                sys.excepthook()
        else:
            self.reading=Reading
            self.pronunciation=Reading
        if dosound:
            self.synchronise_sound()

    def change_sound(self,ChangeToWhat):
        self.set_reading(ChangeToWhat)
        self.synchronise_sound()

    def synchronise_sound(self):
        OrgOrth=self.orth
        if myModule.all_of_chartypes_p(OrgOrth,['katakana']):
            self.orth=self.reading
        elif myModule.all_of_chartypes_p(OrgOrth,['hiragana']):
            self.orth=myModule.kana2kana_wd(self.reading)
        elif myModule.all_of_chartypes_p(OrgOrth,['han','hiragana']):
            EndSubstr=''
            Boundary=identify_kana_boundary(OrgOrth)
            EndSubstr=myModule.kana2kana_wd(self.reading[Boundary:])
            TopSubstr=OrgOrth[:Boundary]
            self.orth=TopSubstr+EndSubstr
                
        else:
            self.orth=self.reading

    def transfer_feats_fromlex(self,InfForm):
        if self.lexeme:
            self.lemma=self.lexeme.lemma
            self.cat=self.lexeme.cat
            self.subcat=self.lexeme.subcat
            self.subcat2=self.lexeme.subcat2
            self.sem=self.lexeme.sem
            self.variants=self.lexeme.variants
            self.soundrules=self.lexeme.soundrules
            if self.lexeme.__name__=='InfLexeme':
                self.set_feature('infpat',self.lexeme.infpat)
                self.set_orth(self.lexeme.infforms[InfForm],dosound=True)
            else:
                self.set_orth(self.lexeme.lemma,dosound=True)

    def pick_applicable_variant(self):
        for Variant,FtDic in self.variants:
#            for Variant,FtDic in VarDic:
                if all([ self.contextbefore.__dict__[Ft]==Val for (Ft,Val) in FtDic.items()] ):
                   return Variant
    def apply_soundchange(self,Deb=0):
        if not self.soundrules:
            if Deb:    print('no sound change rule found')
        else:
            NewMe=self
            for (SoundRule,Probability) in self.soundrules:
                if Probability>=random.randint(1,100):
                    OldSoundB=NewMe.contextbefore.reading
                    OldSoundC=NewMe.reading

                    NewMe=SoundRule(NewMe)

                    NewSoundB=NewMe.contextbefore.reading
                    NewSoundC=NewMe.reading
                    ChangedPairs=[]
                    if OldSoundB!=NewSoundB:
                        ChangedPairs=[(OldSoundB,NewSoundB,)]
                    if OldSoundC!=OldSoundC:
                        ChangedPairs.append((OldSoundC,NewSoundC,))

                    if ChangedPairs:
                        for (OldSound,NewSound) in ChangedPairs:
                            if Deb:    print('posthoc rule '+SoundRule.__name__+' changed '+OldSound+' to '+NewSound)
            
            return NewMe

    def summary(self):
        for FtName,Val in self.__dict__.items():
            print(FtName,Val)
    def get_mecabline(self,CorpusOrDic='corpus'):
        FtStrs=[]
        for Ft in self.inherentatts:
            FtStr='*' if not self.__dict__[Ft] else str(self.__dict__[Ft]) 
            FtStrs.append(FtStr)
        Orth=FtStrs[0]
        Rest=FtStrs[1:]
        if CorpusOrDic=='dic':
            if not self.costs:
                Costs=['0','0','0']
            else:
                Costs=[str(Cost) for Cost in self.costs]
            FinalStr=','.join([Orth]+Costs+Rest)
        else:
            FinalStr=Orth+'\t'+','.join(Rest)

        return FinalStr

def reorder_dict(Dict,OrderedKeys):
    if any(OrderedKey not in Dict.keys() for OrderedKey in OrderedKeys):
        sys.exit('key in orderedkeys does not exist')
    PairsHead=[];PairsTail=[]
    for Key in Dict.keys():
        PairsToAppend=PairsHead if Key in OrderedKeys else PairsTail
        PairsToAppend.append((Key,Dict[Key]))
    return PairsHead+PairsTail
    
# utility functions to render lines to objects
def mecabfile2mecabsents(MecabFP):
    ChunksG=file2delimchunks(MecabFP,'EOS')
    for Chunk in ChunksG:
        MecabWds=[mecabline2mecabwd(Line,'corpus') for Line in Chunk]
        yield MecabSentParse(MecabWds)
    
    

    
def mecabline2mecabwd(MecabLine,CorpusOrDic,Fts=None,WithCost=True):
    WithCost=True if WithCost else False
    WithCost=False if CorpusOrDic=='corpus' else WithCost
    FtsVals,Costs=line2wdfts(MecabLine,CorpusOrDic=CorpusOrDic,WithCost=WithCost,Fts=Fts)
    return MecabWdParse(dict(FtsVals),Costs=Costs)

def line2wdfts(Line,CorpusOrDic='corpus',TupleOrDict='dict',Fts=None,WithCost=False):
    assert Fts is None or type(Fts).__name__=='list'
    assert CorpusOrDic in ['dic','corpus']
    assert TupleOrDict in ['dict','tuple']
    if CorpusOrDic=='corpus': 
        assert '\t' in Line
    if CorpusOrDic=='dic': 
        assert '\t' not in Line
    
    if CorpusOrDic=='corpus':
        WdFtStrPlusNote=Line.strip().split('\t')
        Wd=WdFtStrPlusNote[0]
        Vals=tuple([Wd]+WdFtStrPlusNote[1].split(','))
        Costs=None
    elif CorpusOrDic=='dic':
        WdFts=Line.strip().split(',')
        Wd=WdFts[0]
        Vals=tuple([Wd]+WdFts[4:])
        if WithCost:
            Costs=tuple([int(Str) for Str in WdFts[1:4]])
        else:
            Costs=None

    if Fts is None:
        Fts=(DefFtsSmall if len(Vals)==8 else DefFts)
            
    assert(len(Fts)==len(Vals))
    FtsVals=list(zip(Fts,Vals))
    if TupleOrDict=='dict':
        FtsVals=dict(FtsVals)
    if WithCost:
        FtsVals=(FtsVals,Costs)

    return FtsVals

def eos_p(Line):
    return Line.strip()=='EOS'

def unknown_p(Line):
    return Line.strip().endswith('*')

def symbol_p(Line):
    import string
    Bads=tuple(string.punctuation+string.whitespace)
    if Line.startswith(Bads):
        return True
    elif re.match(r'..*\t記号',Line):
        return True
    return False
    
def not_proper_jp_p(Line):
    return (eos_p(Line) or unknown_p(Line) or symbol_p(Line))

def count_words(MecabCorpusFP):
    CountDict=collections.defaultdict(int)
    FSr=open(MecabCorpusFP)
    for Cntr,LiNe in enumerate(FSr):
        if not (not_proper_jp_p(LiNe)):
            CountDict[line2wdfts(LiNe,'corpus')]+=1
    FSr.close()
    return CountDict

#count_words(HomeDir+'/Dropbox/testFiles/corpora/test.mecab')


def pick_lines(FP,OrderedLineNums):
    with open(FP) as FSw:
        for Cntr,LiNe in enumerate(FSw):
            if OrderedLineNums and Cntr+1 == OrderedLineNums[0]:
                OrderedLineNums.pop(0)
                sys.stdout.write(LiNe)

def cluster_samefeat_lines(FP,Colnums,Exclude=[]):
#    import pdb
 #   if os.path.basename(FP)=='names.csv':
  #      pdb.set_trace()
    ContentsLines=OrderedDict()
    MSs,Consts=None,myModule.prepare_progressconsts(FP)
    with open(FP,encoding='utf8',errors='replace') as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if Cntr+1%500==0:

                MSs=myModule.progress_counter(MSs,Cntr,Consts)
            Line=LiNe.strip()
            if not Line:
                continue
            FtEls=Line.split(',')
            if FtEls[4] not in Exclude:
                try:
                    RelvEls=tuple([ FtEls[Ind] for Ind in Colnums ])
                except:
                    print('\ncluster_samefeat_lines: Column number invalid for \n')
                    print(LiNe+'\n')
                    sys.exit()
                if RelvEls in ContentsLines.keys():
                    ContentsLines[RelvEls].append(Line)
                else:
                    ContentsLines[RelvEls]=[Line]

    return ContentsLines

    
def count_sentences(FP):
    Cntr=0
    for LiNe in open(FP):
        if LiNe.strip()=='EOS':
            Cntr+=1
    return Cntr

def extract_sentences(FileP,LineNums='all',ReturnRaw=False,Print=False):
    def chunkprocess(Chunk,ReturnRaw):
        if not ReturnRaw:
            return Chunk.strip().split('\n')
    FSr=open(FileP,'rt',encoding='utf-8')
    extract_chunk=lambda FSr: myModule.pop_chunk_from_stream(FSr,Pattern='EOS')
    FSr,Chunk,_,NxtLine=extract_chunk(FSr)
    Sentl=False
    Cntr=0
    while not Sentl:
        Cntr+=1
        if LineNums=='all':
            yield chunkprocess(Chunk,ReturnRaw)
        else:
            if Cntr in LineNums:
                LineNums.remove(Cntr)
                yield chunkprocess(Chunk,ReturnRaw)

        FSr,Chunk,_,NxtLine=extract_chunk(FSr)
        if not LineNums or not NxtLine:
            Sentl=True


def already_in_anothersentlist_p(TestSent,Sents):
    TestSentLen=len(TestSent)
    for Sent in Sents:
        SentLen=len(Sent)
        (Longer,LongerLen),(Shorter,ShorterLen)=(((TestSent,TestSentLen),(Sent,SentLen)) if TestSentLen>=SentLen else ((Sent,SentLen),(TestSent,TestSentLen)))
        if ShorterLen>8 and Shorter in Longer:
            if Debug:  print('Sentence '+TestSent+' found in list: '+Sent)
            return True
        else:
            if ShorterLen>10 and LongerLen-ShorterLen<5:
                Similarity=SequenceMatcher(a=TestSent,b=Sent).ratio()
                if Similarity>0.9:
                    if Debug:  print('Very similar sentence '+TestSent+' found in list: '+Sent)
                    return True

    return False


def produce_traintest(OrgFP,TestSpec,CheckAgainst=None):
    (WhereFrom,TestNum,PercentP)=TestSpec
    SentCnt=count_sentences(OrgFP)
    if PercentP:
        WhereFrom=int(SentCnt//(100/WhereFrom))
        TestNum=int(SentCnt//(100/TestNum))
    if CheckAgainst:
        SentsAlreadyInTest=open(CheckAgainst).read().strip().split('\n')
    FSwTest=open(myModule.get_stem_ext(OrgFP)[0]+'_test.mecab','wt')
    FSwTrain=open(myModule.get_stem_ext(OrgFP)[0]+'_train.mecab','wt')
    TestCntr=0    
    for Cntr,Sent in enumerate(extract_sentences(OrgFP)):
        #AlreadyInTestP=False
        if CheckAgainst:
            SentStr=''.join([ Line.split('\t')[0] for Line in Sent ])
            if already_in_anothersentlist_p(SentStr,SentsAlreadyInTest):
                TestCntr+=1
                continue
        if Cntr+1>=WhereFrom and TestCntr<TestNum:
            TestCntr+=1
            FSwToWrite=FSwTest
        else:
            FSwToWrite=FSwTrain
        FSwToWrite.write('\n'.join(Sent)+'\nEOS\n')
    FSwTest.close()
    FSwTrain.close()

def sentence_list(FP,IncludeEOS=True):
    if IncludeEOS:
        return re.split(r'\nEOS',open(FP,'rt',encoding='utf-8').read())
    else:
        return open(FP,'rt',encoding='utf-8').read().split('EOS')
    
    
def mark_sents(FP,FtCnts,Recover=True,Output=None):
    #set_trace()
    '''
    def find_eof_errors(FP):
  
        FSr=open(FP)
        LstLiNe=myModule.readline_reverse(FSr)
        TrailEmptyLineCnt=0
        while LstLiNe.strip()=='':
            LstLine=myModule.readline_reverse(FSr)
            TrailEmptyLineCnt+=1
        
        if LstLine!='EOS':
            LstEOSP=False
        return (TrailEmptyCnt,LstEOSP)    
            
    '''        
  #      return MkdLines

    
    with open(FP,'rt',encoding='utf-8') as FSr:
       # (TrailEmptyCnt,LstEOSP)=find_eof_errors(FP)
       # if not Recover and not (TrailEmptyCnt and LstEOSP):
       #     sys.exit('there is an EOF error, either empty trailing lines or no EOS')
            
        extract_chunk=lambda FSr: myModule.pop_chunk_from_stream(FSr,Pattern='EOS')

        MkdSents=[]; SentCnt=LineCnt=0; NextLine=True
        while NextLine:
            FSr,Sent,LineCntPerSent,NextLine=extract_chunk(FSr)
            if NextLine:
                LineCnt+=LineCntPerSent;SentCnt+=1
                if Sent.strip()=='':
                    if Recover:
                        #MkdSents.append([(Sent,None,'empty sent')])
                        yield [(Sent,None,'empty sent')]
                else:
                    if Debug:
                        print('Now at '+str(LineCnt))
                    MkdLines=mark_sentlines(Sent.strip().split('\n'),FtCnts,Recover=Recover)
                    #MkdSents.append(MkdLines)
                    yield MkdLines
#    return MkdSents


def mark_sentlines(SentLines,FtCnts,Recover=True):
        MkdLines=[]
        for (Cntr,Line) in enumerate(SentLines):
            Wrong=something_wrong_insideline(Line,FtCnts)
            if not Wrong:
                ToAppend=(Line,Line,'original')
                
            # below is when there is something wrong!!!
            else:
                if Recover:
                    ErrorMsgPrefix='error found ('+Wrong+', "'+Line[:10]+'"), attempting to recover..'
                    # attempt to recover
                    Attempted=try_and_recover(Line,Wrong)
                    # it could return none, this is failure
                    if Attempted is None:
                        SuccessP=False
                        ToAppend=(Line,None,Wrong)
                
                    # it could return something where there still are errors
                    elif something_wrong_insideline(Attempted,FtCnts):
                        SuccessP=False
                        ToAppend=(Line,None,Wrong)
                    # otherwise it's success
                    else:
                        SuccessP=True
                        ToAppend=(Line,Attempted,'recovered')
                    if Debug:
                        ErrorMsgSuffix=('successful' if SuccessP else 'failed')
                        sys.stderr.write('\n'+ErrorMsgPrefix+' '+ErrorMsgSuffix)
                        
                else:
                    ToAppend=(Line,None,Wrong)
            MkdLines.append(ToAppend)
        return MkdLines
                    

def markedsent2output(MkdSent):
    MecabSent=[ MkdLine[1] for MkdLine in MkdSent ]
    return '\n'.join(MecabSent)+'\nEOS\n'
    
def markedsents2outputs(MkdSents,OrgFP,StrictP=True,MoveTo=None):
    ErrorOutput=OrgFP+'.errors'
    ReducedOutput=myModule.get_stem_ext(OrgFP)[0]+'.reduced.mecab'
    FSwE=open(ErrorOutput,'wt')
    FSwR=open(ReducedOutput,'wt')
    ErrorCnt=0; LineCntr=0
    for Cntr,MkdSent in enumerate(MkdSents):
        LineCntr+=len(MkdSent)+1
        if not all(Line[-1]=='original' for Line in MkdSent):
            if StrictP or any(Line[-2] is None for Line in  MkdSent):
                ErrorCnt+=1
                FSwE.write(str(Cntr+1)+'; '+str(LineCntr)+'\n'+'\n'.join([ MkdLine[0]+'\t'+MkdLine[-1] for MkdLine in MkdSent])+'\n')
            else:
                FSwR.write(markedsent2output(MkdSent))
        else:
            MkdSentM=markedsent2output(MkdSent)
            FSwR.write(MkdSentM)
    FSwE.close()
    FSwR.close()
    if ErrorCnt==0:
        os.remove(ReducedOutput)
        os.remove(ErrorOutput)
        print('No error found for file '+OrgFP)
        time.sleep(2)
        return True
    else:
        print(str(ErrorCnt)+' error(s) found for file '+OrgFP)
        if not MoveTo:
            MoveTo=os.getcwd
        subprocess.call(['cp',OrgFP,MoveTo])
        subprocess.call(['cp',ErrorOutput,MoveTo])
        os.remove(OrgFP)
        os.remove(ErrorOutput)
        print('Original file moved to '+MoveTo)
        time.sleep(2)
        return False
            
    
def remove_badsents(FP,FtCnts,RemoveAgainst=None):
    if RemoveAgainst:
        SentsToRemove=open(RemoveAgainst,'rt').read().strip().split('\n')
    MkdSents=mark_sents(FP,FtCnts)
    BadCnts=0
    with open(FP+'.reduced','wt') as FSw:
        for MkdSent in MkdSents:
            if any(not MkdLine[1] for MkdLine in MkdSent):
                print('problem!')
                BadCnts+=1
            else:
                if RemoveAgainst:
                    OrgSent=''.join([MkdLine[0].split('\t')[0] for MkdLine in MkdSent])
#                    print(OrgSent)
                    if already_in_anothersentlist_p(OrgSent,SentsToRemove):
                        print('test sentence found!')
                        BadCnts+=1
                        continue
                MkdLines='\n'.join([MkdLine[0] for MkdLine in MkdSent])
                ToWrite=MkdLines+'\nEOS\n'
                #sys.stdout.write(ToWrite)
                FSw.write(ToWrite)
        print(str(BadCnts)+' bad sentences found')

def something_wrong_insideline(Line,FtCnts):
    if Line.strip()=='':
        return 'empty line'
    elif Line=='====' or re.match(r'@[1-9]',Line):
        return None
    else:
        if len(re.findall(r'\s',Line))>1:
            return 'redundant whitespaces'
        elif Line.strip()[-1] == ',':
            return 'ending with comma'
        elif  '\t' not in Line:
            return 'no tab in line'
        elif Line!='EOS':
            CurFtCnt=len(Line.split('\t')[-1].split(','))
            if CurFtCnt not in FtCnts:
                return 'wrong num of features'
    return None

def stringify_filteredsents(Sents):
    WrongStrs=[]
    CorrectStrs=[]
    for Sent in Sents:
        for Line in Sent:
            if type(Line).__name__=='tuple':
                WrongStrs.append(stringify_wrongline(Line))
            else:
                CorrectStrs.append(Line)
    return WrongStrs,CorrectStrs
                

def stringify_wrongline(WrongLineTup):
    SentCnt,LineNum,Line,Comment=WrongLineTup
    return ' '.join(['Line',str(LineNum)+', Sent',str(SentCnt)+':',Comment,"'"+Line+"'"])


def get_el(List,Ind):
    try:
        return List[Ind]
    except IndexError:
        return None

def try_and_recover(Line,Wrong):
    if Wrong=='redundant whitespaces':
        WdFeatsR=re.split(r'\t+',Line.strip())
        if len(WdFeatsR)==2:
            Wd,FeatsR=WdFeatsR
            Feats=[ Ft.strip() for Ft in FeatsR.split(',') ]
            Attempt='\t'.join([Wd.strip(),','.join(Feats)])
            return Attempt
    elif Wrong=='wrong num of features':
        return Line
    elif Wrong=='empty line':
        return None



def split_file_into_n(FP,N):
    Sents=sentence_list(FP)
    SplitIntvl=len(Sents)//N
    with open(FP,'rt',encoding='utf-8') as FSr:
        Chunk=[];ChunkCnt=1
        for (Cntr,LiNe) in enumerate(FSr):
            Chunk.append(LiNe)
            if Cntr!=0 and Cntr % SplitIntvl==0:
                open(FP+str(ChunkCnt),'wt',encoding='utf-8').write(''.join(Chunk)+'EOS\n')
                Chunk=[];ChunkCnt=ChunkCnt+1
                if ChunkCnt==N:
                    open(FP+str(ChunkCnt),'wt',encoding='utf-8').write(FSr.read())


def extract_sentences_fromsolfile(SolFileP):
    Sents=extract_sentences(SolFileP)
    return [ extract_string_fromsentlines(Sent,SolP=True) for Sent in Sents  ]


def extract_string_fromsentlines(SentLines,SolP=False):
    extract_string_normal=lambda SentLines: ''.join([Line.split('\t')[0] for Line in SentLines])
    if SolP:
        return re.sub(r'====@1([^@]+)@.+?====',r'\1',extract_string_normal(SentLines))
    else:
        return extract_string_normal(SentLines)


def files_corresponding_p(FPR,FPS,Strict=True,OutputFP=None):

    def write_errors(FPR,FPS):
        Dir=os.path.dirname(FPR)
        FNR=os.path.basename(FPR)
        FNS=os.path.basename(FPS)
        
        with open(os.path.join(Dir,FNR+'.'+FNS+'.errors'),'wt',encoding='utf-8') as FSwErr:
            for SentNum,SentR,SentS in Errors:
                FSwErr.write('Sent '+str(SentNum)+': '+SentR+'\t'+SentS+'\n')

    Bool=True

    SentLinesR=[SentL for SentL in extract_sentences(FPR)]
    SentLinesS=[SentL for SentL in extract_sentences(FPS)]

    LenR=len(SentLinesR)
    LenS=len(SentLinesS)
    
    Thresh=LenR//15
    
    LenDiff=LenR-LenS
    if LenDiff!=0:
        if LenDiff>0:
            Larger='results'
        else:
            Larger='solutions'

        if Strict:
            print('Sentence counts do not match')
            print('there are '+str(abs(LenDiff))+' more sentenes in '+Larger+' file')
            return False
        elif abs(LenDiff)>Thresh:
            print('Too much difference in sentence counts')
            return False
        else:
            print('Warning: difference in sentence count, there will be errors')
            print('there are '+str(abs(LenDiff))+' more sentenes in '+Larger+' file')

    Errors=[]; Corrects=[]
    for Cntr,(SentR,SentS) in enumerate(zip(SentLinesR,SentLinesS)):
        StringR=extract_string_fromsentlines(SentR)
        StringS=extract_string_fromsentlines(SentS,SolP=True)
        if StringR==StringS:
            Corrects.append((str(Cntr),SentR,SentS))
        else:
            Errors.append((str(Cntr),StringR,StringS))
            if Strict:
                print('error, aborting')
                print(Errors)
                return False
            else:
                if len(Errors)>Thresh:
                    print('too many errors, at '+', '.join([ Error[0] for Error in Errors])+'. For details see [combinedfilenames].errors')
                    write_errors(FPR,FPS)
                    return False

    if not Strict:
        FSwR=open(FPR+'.reduced','wt',encoding='utf-8')
        FSwS=open(FPS+'.reduced','wt',encoding='utf-8')
        for _,SentR,SentS in Corrects:
            FSwR.write('\n'.join(SentR)+'\nEOS\n')
            FSwS.write('\n'.join(SentS)+'\nEOS\n')
        FSwR.close();FSwS.close()
        write_errors(FPR,FPS)
        
    return Bool


