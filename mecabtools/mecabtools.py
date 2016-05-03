import re, imp, os, sys, time, shutil,subprocess
from difflib import SequenceMatcher
sys.path.append('./../myPythonLibs')
from collections import defaultdict
from pythonlib_ys import main as myModule
imp.reload(myModule)
try:
    from ipdb import set_trace
except:
    from pdb import set_trace
# Chunk:
# SentLine:

Debug=0

def pick_lines(FP,OrderedLineNums):
    with open(FP) as FSw:
        for Cntr,LiNe in enumerate(FSw):
            if OrderedLineNums and Cntr+1 == OrderedLineNums[0]:
                OrderedLineNums.pop(0)
                sys.stdout.write(LiNe)

def extract_samefeat_lines(FP,Colnums):
    SeenInf=set()
    ContentsLinums=defaultdict(list)
    with open(FP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            FtEls=LiNe.strip().split(',')
            RelvEls=tuple([ FtEls[Ind-1] for Ind in Colnums ])
            InfEls=tuple([ FtEls[Ind-1] for Ind in (5,6,7,8,9,11) ])
            #print(InfEls)
#            if InfEls[0]=='動詞' or InfEls[0]=='形容詞':
                #print(InfEls[0]+InfEls[5])
            ContentsLinums[RelvEls].append(LiNe.strip())
            SeenInf.add(InfEls)
    ContentsLinums={ Fts:Lines for (Fts,Lines) in ContentsLinums.items() if len(Lines)>=2 }
    #ContentsLinums=sorted(ContentsLinums.items(),key=lambda x:len(x[1]),reverse=True)

    for Content,Lines in ContentsLinums.items():
        sys.stderr.write('candidate\n')
        sys.stderr.write('\n'.join(Lines)+'\n')
        Clusters=cluster_homonyms([Line.split(',')[0] for Line in Lines])
        for Cntr,ClusterPair in enumerate(Clusters):
            #RelvLines=[]
            for KanaCluster,KanjiCluster in ClusterPair:
                sys.stderr.write('\nresults'+str(Cntr+1)+'\n')
                cluster_process(KanjiCluster)
                def cluster_process(Cluster):
                    for Group in Cluster:
                        if len(Cluster)>=2:
                            RelvLines=[ Line for Line in Lines if Line.split(',')[0] in Cluster ]
            
                        sys.stdout.write('\n'.join(RelvLines)+'\n\n')
            if 
            
                
    return ContentsLinums

def homonympair_identical_p(Homonym1,Homonym2):
    # trivial case
    if Homonym1==Homonym2:
        Bool=True
    else:
        # default is true
        Bool=True
        # but don't accept kanji-only pairs as synonyms
        if all(myModule.all_of_chartypes_p(Homonym,['han']) for Homonym in (Homonym1,Homonym2)):
            Bool=False
        Kanjis1={ Char for Char in Homonym1 if myModule.identify_type_char(Char)=='han'}
        if Kanjis1:
            Kanjis2={ Char for Char in Homonym2 if myModule.identify_type_char(Char)=='han'}
            if Kanjis2:
                if not Kanjis1.intersection(Kanjis2):
                    Bool=False
            
    return Bool

def cluster_homonyms(Homs):
    #print(Homs)
    #print()
    KanaOnlys=[ Hom  for Hom in Homs if myModule.all_of_chartypes_p(Hom,['hiragana','katakana']) ]
    Prv=None;Clusters=[set()]
    for Cntr,Hom in enumerate(set(Homs)-set(KanaOnlys)):
        if Cntr==0:
            Clusters[-1].add(Hom)
        else:
            if homonympair_identical_p(Prv,Hom):
                Clusters[-1].add(Hom)
            else:
                Clusters.append({Hom})
        Prv=Hom
    return ([KanaOnlys],Clusters) 


        


HomeDir=os.getenv('HOME')
extract_samefeat_lines(os.path.join(HomeDir,'links/mecabKansaiModels/original/standard/model/allpos.csv'),[5,6,7,8,9,10,13])
    
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


