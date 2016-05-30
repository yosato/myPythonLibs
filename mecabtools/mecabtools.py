import re, imp, os, sys, time, shutil,subprocess,collections
from difflib import SequenceMatcher
sys.path.append('./../myPythonLibs')
from collections import defaultdict,OrderedDict
from pythonlib_ys import main as myModule
imp.reload(myModule)
try:
    from ipdb import set_trace
except:
    from pdb import set_trace
# Chunk:
# SentLine:

Debug=0
HomeDir=os.getenv('HOME')

def mecabline2avpairs(MecabLine):
    Wd,Fts=line2wdfts()
    if len(Fts)>=8:
        Cat=Fts[0]
        MecabWd=MecabWdParse(orth=Wd,cat=Cat,subcat=Fts[1],subcat2=Fts[2],sem=Fts[3],lemma=Fts[6],infpat=Fts[4],infform=Fts[5],reading=Fts[7])
    else:
        MecabWd=MecabWdParse(orth=Wd,cat=Fts[0],subcat=Fts[1],subcat2=Fts[2],sem=Fts[3],lemma='*',infpat=Fts[4],infform='*')

class MecabWdCluster:
    def __init__(self,MecabWdParse,CoreFtNames):
        self.wd=MecabWdParse
        self.core_fts=[ MecabWdParse ]
        
class MecabWdParse:
    def __init__(self,**AVPairs):
#Lexeme='',Feats={},Variants=[],SoundRules=[],CtxtB='',CtxtA='',Cat='*',Subcat='*',Subcat2='*',Sem='*',Lemma='*',InfPat='*',InfForm='*',Reading='*'):
        Fts=AVPairs.keys()
        if not ('orth' in Fts or 'lemma' in Fts):
            sys.exit('you must have orth and lemma)')
        else:
            for Ft,Val in AVPairs.items():
                self.__dict__[Ft]=Val
#            self.lemma=AVPairs['lemma']
 #       # just populating in case 
  #      self.subcat='*'; self.subcat2='*'; self.reading='*';self.pronunciation='*'
   #     self.sem='*'; self.infpat='*'; self.infform='*'
        self.soundrules=[]; self.variants=[]
        self.count=None
        self.poss=None
        self.lexpos=None

    def set_poss(self,Poss):
        self.poss=Poss
        self.count=len(Poss)
#        if 'lexeme' in AVPairs.keys():
 #           self.initialise_features_fromlexeme(AVPairs)
  #      else:
   #         self.initialise_features_withoutlexeme(AVPairs)

    def set_count(self,Cnt):
        self.count=Cnt
        
    def add_count(self,By=1):
        self.count=self.count+By
   
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
    def get_mecabline(self):
        Str=''
        Orth=self.orth
        if Orth:
            Str=Orth
            Fts=[self.cat,self.subcat,self.subcat2,self.sem,self.inftype,self.infform,self.lemma,self.reading,self.pronunciation]
            FtsNonEmpty=[ Ft for Ft in Fts if Ft ]
            Rest=','.join(FtsNonEmpty)
            Str=Str+'\t'+Rest
        return Str
    def get_mecabdicline(self):
        Str=''
        Orth=self.orth
        if Orth:
            Str=Orth
            Fts=[self.cat,self.subcat,self.subcat2,self.sem,self.infpat,self.infform,self.lemma,self.reading,self.pronunciation]
            FtsNonEmpty=[ Ft for Ft in Fts if Ft ]
            Rest=','.join(FtsNonEmpty)
            Str=Str+',0,0,0,'+Rest
        return Str


def line2wdfts(Line,CorpusOrDic):
    if CorpusOrDic=='corpus':
        Wd,FtStr=Line.strip().split('\t')
        Fts=tuple(FtStr.split(','))
    elif CorpusOrDic=='dic':
        WdFts=Line.strip().split(',')
        Wd=WdFts[0]
        Fts=tuple(WdFts[4:])
    return Wd,Fts

def eos_p(Line):
    return Line.strip()=='EOS'

def unknown_p(Line):
    return Line.strip().endswith('*')

def not_proper_jp_p(Line):
    return (eos_p(Line) or unknown_p(Line) )

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
    ContentsLines=OrderedDict()
    with open(FP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            Line=LiNe.strip()
            FtEls=Line.split(',')
            if FtEls[4] not in Exclude:
                RelvEls=tuple([ FtEls[Ind-1] for Ind in Colnums ])
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


