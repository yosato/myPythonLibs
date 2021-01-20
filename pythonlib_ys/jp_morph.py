import copy,sys,imp,re,os,random,subprocess,inspect,functools,itertools
import romkan
import bidict
from pdb import set_trace
from collections import defaultdict
# some globals
if os.name=='nt':
    HomeDir=os.getenv('HOMEPATH')
else:
    HomeDir=os.getenv('HOME')

assert HomeDir is not None    

from pythonlib_ys import main as myModule
imp.reload(myModule)

CharSetsWithRelatives={'カキクケコ':'ガ|ギ|グ|ゲ|ゴ','サシスセソ':'ザ|ジ|ズ|ゼ|ゾ','タチツテト':'ダ|ヂ|ヅ|デ|ド','ハヒフヘホ':'パバ|ピビ|プブ|ペベ|ポボ'}
CharsWithRelatives={};VoicedHalfVoiced=[]
for CharSet,Relatives in CharSetsWithRelatives.items():
    for Char,Relative in zip(list(CharSet),list(Relatives.split('|'))):
        CharsWithRelatives[Char]=tuple(Relative)
        VoicedHalfVoiced.extend(Relative)

def preserved_order_sublist_p(ShorterList,LongerList):
    LongerListCopy=copy.copy(LongerList)
    for El in ShorterList:
        if El not in LongerListCopy:
            return False
        else:
            LongerListCopy=LongerList[LongerListCopy.index(El):]
    return True
        
def okurigana_variants_p(Str1,Str2):
    # if no kanji is involved at all, leave it
    if not any(myModule.at_least_one_of_chartypes_p(Str,['han']) for Str in (Str1,Str2)):
        return False
    # the kanji content (including the order) is identical between the two
    Kanjis1,Kanjis2=[[myModule.identify_chartype(Char) for Chars in Str] for Str in (Str1,Str2)]
    if Kanjis1!=Kanjis2:
        return False
    # shorter one is preserved-order char subset of longer one
    (Longer,Shorter)=(Str1,Str2) if Str1>Str2 else (Str2,Str1)
    if not preserved_order_sublist_p(Shorter,Longer):
        return False
    return True
    
        
def unvoice_char(Char,StrictP=False):
    CharType=myModule.identify_chartype(Char)
    assert(CharType in ['hiragana','katakana'])
    HiraganaP=myModule.identify_chartype(Char)=='hiragana'
    KataChar=myModule.kana2kana(Char) if  HiraganaP else Char
    Unvoiced=next((UV for (UV,Vs) in CharsWithRelatives.items() if KataChar in Vs),None)
    if Unvoiced and HiraganaP:
        Unvoiced=myModule.kana2kana(Unvoiced)
    return Unvoiced if Unvoiced else (None if StrictP else Char)
        
def pick_highest_charrate(Cands,CharTypes):
    return max([(Cand,chartype_rate(Cand.orth,CharTypes)) for Cand in Cands], key=lambda x:x[1])
        


def chartype_rate(Str,CharTypes):
    RightCharCnt=0
    for Cntr,Char in enumerate(Str):
        if myModule.identify_chartype(Char) in CharTypes:
            RightCharCnt+=1
    return RightCharCnt/(Cntr+1)

def contain_kanji_p(Str):
    return any(myModule.identify_chartype(Char) for Char in Str)


def orth_mixed_p(Str):
    Bool=False
    FstCharType=myModule.identify_chartype(Str[0])
    for Char in Str[1:]:
        Type=myModule.identify_chartype(Char)
        if Type != FstCharType:
            return True
    return Bool

def align_han2reading(HanContWd,WdReading,Debug=False,NoAssim=False):
    def make_kanjichunks(HanCntWd):
        KanjiContChunks=[];Chunk=''
        for Char in HanContWd:
            if Char=='々' or myModule.identify_type_char(Char)!='han':
                Chunk+=Char
            else:
                if Chunk:
                    KanjiContChunks.append(Chunk)
                Chunk=Char
        if Chunk:
            KanjiContChunks.append(Chunk)
        return KanjiContChunks

    KanjiContChunks=make_kanjichunks(HanContWd)
    OrthReadPairs=[]
    WdReadingResidue=WdReading 
    for Chunk in KanjiContChunks:
        PossibleChunkReadings=possible_kanji_readings(Chunk)
        if not PossibleChunkReadings:
            if Debug:
                sys.stderr.write('alignment not possible for '+HanContWd+', kakasi returns nothing\n')
            return None
        ChunkReadings=[render_kana(Reading,WhichKana='katakana') for Reading in PossibleChunkReadings]
        # we use kakasi to do kanji chunk readings 
        PossibleReadings=[ ChunkReading for ChunkReading in ChunkReadings if WdReadingResidue.startswith(ChunkReading) ]
        # it may not return the right one, then it returns none
        if not PossibleReadings:
            if Debug:
                sys.stderr.write('alignment not possible for '+HanContWd+', kanji readings not found\n')
            return None
        # otherwise pick the longest
        ChunkReading=max(PossibleReadings)
        OrthReadPairs.append((Chunk,ChunkReading,))
        WdReadingResidue=WdReadingResidue[len(ChunkReading):]
    return OrthReadPairs


    
   # (Pairs1,(HanResidue,WdResidue))=align_firsts(HanContainingWd,WdReading)
    #(Pairs2,(HanResidue,WdResidue))=align_firsts(HanResidue,WdResidue,Rev=True)

    #Pairs=Pairs1#+Pairs2
    
    #if len(HanResidue)==1 and len(WdResidue)<=2:
     #   Pairs.append((HanResidue,WdResidue))
        
    #return Pairs,WdResidue

def align_firsts(HanContWd,WdReading,Rev=False):
    HanReadPairs=[]
    if not Rev:
        CurWdReading=WdReading
        CurHanContWd=HanContWd
    else:
        CurWdReading=WdReading[::-1]
        CurHanContWd=HanContWd[::-1]
    while CurWdReading:
        Char,CurHanContWd=myModule.string_pop(CurHanContWd,0)
        if not Char:
            break
        CType=myModule.identify_type_char(Char)
        if CType!='han':
            CurWdReading=CurWdReading[1:]
        else:
            HanReading=None
            CharReadings=possible_kanji_readings(Char)
            for CharReading in CharReadings:
                if Rev:
                    CharReading[::-1]
                if CurWdReading.startswith(CharReading):
                    HanReading=CharReading
                    HanReadPair=(Char,HanReading)
                    CurWdReading=CurWdReading.replace(HanReading,'')
                    HanReadPairs.append(HanReadPair)
                    break
            if not HanReading:
                return HanReadPairs,(CurHanContWd,CurWdReading)

    Residues=(CurHanContWd,CurWdReading)
                    
    return HanReadPairs,Residues

def differentiate_ambnonamb(Str):
    AmbNonamb=[];InAmb=False;Amb=[];NonAmb=[]
    for Char in Str:
        if Char=='{':
            InAmb=True
            if NonAmb:
                AmbNonamb.append([''.join(NonAmb)])
            Amb=[]
        elif Char=='}':
            InAmb=False
            if Amb:
                AmbNonamb.append(''.join(Amb).split('|'))
            NonAmb=[]
        elif InAmb:
            Amb.append(Char)
        else:
            NonAmb.append(Char)
    if NonAmb:
        AmbNonamb.append([''.join(NonAmb)])
    return AmbNonamb
        

def possible_kanji_readings(Kanji):
    Cmd='echo '+Kanji+'| kakasi -i utf8 -o utf8 -JK -HK -p'
    Proc=subprocess.Popen(Cmd,shell=True,stdout=subprocess.PIPE)
    Output=Proc.communicate()[0]
    Output=Output.decode().strip()
    if not Output:
        print('\njp_morph.possible kanji readings failed for '+Kanji+'\n\n')
        return None
    AmbNonambSeq=differentiate_ambnonamb(Output)
    Readings=[ ''.join(SegReading) for SegReading in expand_seqs(AmbNonambSeq) ]
        
    return Readings

def expand_seqs(LofLs):
    return functools.reduce(expand_product,LofLs)

def expand_product(L1,L2):
    return list(itertools.product(L1,L2))

InfCats=['助動詞','動詞','形容詞']

GojuonStrH='あいうえお\nかきくけこ\nさしすせそ\nたちつてと\nなにぬねの\nはひふへほ\nまみむめも\nやいゆえよ\nらりるれろ\nわいうえを\nがぎぐげご\nざじずぜぞ\nだぢづでど\nばびぶべぼ\nぱぴぷぺぽ\nゃぃゅぇょ\nぁぃぅぇぉ'
GojuonStrK='アイウエオ\nカキクケコ\nサシスセソ\nタチツテト\nナニヌネノ\nハヒフヘホ\nマミムメモ\nヤイユエヨ\nラリルレロ\nワイウエヲ\nガギグゲゴ\nザジズゼゾ\nダヂヅデド\nバビブベボ\nパピプペポ\nャィュェョ\nァィゥェォ'
GojuonStrR='aiueo\nkakikukeko\nsasisuseso\tatituteto\naninuneno\nhahihuheho\nmamimumemo\nyayiyuyeyo\nwawiwuwewo\ngagigugego\nzazizuzezo\ndadidudedo\nbabibubebo\npapipupepo\nyayiyuyeyo\naiueo'

GojuonDic={'んン':{'N':('ん','ン')},'っッ':{'t':('っ','ッ')}}

for GyoStrPair in zip(GojuonStrH.split('\n'),GojuonStrK.split('\n')):
    GyoDic={}

    GyoDic.update([('a',(GyoStrPair[0][0],GyoStrPair[1][0])),('i',(GyoStrPair[0][1],GyoStrPair[1][1])),('u',(GyoStrPair[0][2],GyoStrPair[1][2])),('e',(GyoStrPair[0][3],GyoStrPair[1][3])),('o',(GyoStrPair[0][4],GyoStrPair[1][4]))])

    GojuonDic[GyoStrPair[0]+GyoStrPair[1]]=GyoDic



def identify_dan(Char,InRomaji=False):
    if myModule.identify_type_char(Char)=='hiragana':
        Ind=0
    else:
        Ind=1
    for GyoChars,Dic in GojuonDic.items():
        if Char in GyoChars:
            for Dan,CandCharPair in Dic.items():
                if CandCharPair[Ind]==Char:
                    if not InRomaji:
                        return Dan
                    else:
                        return romkan.to_hiragana(Dan)

def change_dan(Char,Dan):
    if myModule.identify_type_char(Char)=='hiragana':
        Ind=0
    else:
        Ind=1
    for Chars in GojuonDic.keys():
        if Char in Chars:
            return GojuonDic[Chars][Dan][Ind]

                    

def identify_gyo(Kana,InRomaji=False):
    Dan=identify_dan(Kana)
    if Dan in ('N','t'):
        Gyo=Dan
    elif Dan=='a':
        Gyo=Kana
    else:
        Gyo=change_dan(Kana,'a')
    if InRomaji:
        Gyo=romkan.to_roma(Kana)[0]
        
    return Gyo


    
class Syllable:
    def __init__(self,Orth):
        self.orth=Orth
        self.dan=identify_dan(Orth) if len(Orth)==1 else identify_dan(Orth[-1])
        self.gyo=identify_gyo(Orth) if len(Orth)==1 else identify_gyo(Orth[0])
        self.voiced=True if self.gyo in ('ば','が','ざ','だ','ぱ') else False
        self.palatalised=True if len(Orth)==2 else False
    def feat_strs(self):
        return [str(self.dan),str(self.gyo),repr(self.voiced),repr(self.palatalised)]

GyoDicH=defaultdict(list)

for DanDic in GojuonDic.values():
    for (Gyo,HK) in DanDic.items():
        GyoDicH[Gyo].append(HK[0])

            
Pals=[]
for IDanChar in GyoDicH['i']:
    if identify_dan(IDanChar) not in ('y','a'):
        for V in ('ゃ','ゅ','ょ'):
            Pals.append(IDanChar+V)
    
    
Syllables=[Syllable(Orth) for Orth in list(GojuonStrH)]+[Syllable(Orth) for Orth in Pals]+[Syllable('ん'),Syllable('っ')]


class MecabSentParse:
    def __init__(self,Wds2Add):
        self.words=[]
        self.wdcnt=len(self.words)
        self.add_words(Wds2Add)
        self.orth=self.get_orths()

    def append_word(self,Wd2Add,SoundChange=True,Deb=0):
        if self.wdcnt==0:
            Wd2Add.contextbefore=None
        else:
            PrvWd=self.words[-1]
            Wd2Add.contextbefore=PrvWd
            if SoundChange:
                Wd2Add=self.check_apply_soundchange(Wd2Add,Deb=Deb)
                if Wd2Add.contextbefore.orth!=PrvWd.orth:
                    self.words[-1]=Wd2Add.contextbefore

        self.words.append(Wd2Add)
        self.wdcnt=self.wdcnt+1
        self.set_orths()

    def check_apply_soundchange(self,Wd2Add,Deb=0):
        VariantP=Wd2Add.variants; SoundChangeP=Wd2Add.soundrules
        if all([not VariantP and not SoundChangeP ]):
            pass
#            if Deb:  print('no sound rule for this word')
        elif VariantP:
            VariantSnd=Wd2Add.pick_applicable_variant()
            if VariantSnd:
                if Deb:   print('a phonetic variant found, changing to '+VariantSnd)
                Wd2Add.change_sound(VariantSnd)
        elif SoundChangeP:
            Wd2Add=Wd2Add.apply_soundchange(Deb=Deb)
        return Wd2Add 

        
    def add_words(self,Wds2Add):
        for Wd2Add in Wds2Add:
            self.append_word(Wd2Add)

    def set_orths(self):
        self.orth=self.get_orths()

    def get_orths(self):
        Orth=''
        for Wd in self.words:
            Orth=Orth+Wd.orth
        return Orth

    def get_wakati_str(self):
        Str=''
        for Wd in self.words:
            Str=Str+' '+Wd.orth
        return Str.strip()
    def get_mecaboutput(self):
        Str=''
        for Wd in self.words:
            Str=Str+'\n'+Wd.get_mecabline()
        return Str
    def unify_changes(self,Preced='cxt'):
        PrvWd=''
        for Ind,Wd in enumerate(self.words):
            if PrvWd:
                if not feature_identity(PrvWd,Wd.contextbefore):
                    self.words[Ind-1]=Wd.contextbefore

            PrvWd=Wd

def identify_kana_boundary(Str):
    Cntr=0
    while Str:
        Cntr=Cntr-1
        if not myModule.is_kana(Str[-1]):
            return Cntr
        Str=Str[:-1]

    return Cntr

'''
class MecabWdParse:
    def __init__(self,**AVPairs):
#Lexeme='',Feats={},Variants=[],SoundRules=[],CtxtB='',CtxtA='',Cat='*',Subcat='*',Subcat2='*',Sem='*',Lemma='*',InfPat='*',InfForm='*',Reading='*'):
        Fts=AVPairs.keys()
        if ('orth' in Fts and 'lexeme' in Fts) or ('orth' not in Fts and 'lexeme' not in Fts):
            sys.exit('you must have either orth or lexeme for word (and not both)')
        # just populating in case 
        self.subcat='*'; self.subcat2='*'; self.reading='*';self.pronunciation='*'
        self.sem='*'; self.infpat='*'; self.infform='*'
        self.soundrules=[]; self.variants=[]

        if 'lexeme' in AVPairs.keys():
            self.initialise_features_fromlexeme(AVPairs)
        else:
            self.initialise_features_withoutlexeme(AVPairs)

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
            Fts=[self.cat,self.subcat,self.subcat2,self.sem,self.infpat,self.infform,self.lemma,self.reading,self.pronunciation]
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
'''
class Lexeme:
    def __init__(self,Cat,Lemma,subcat='*',subcat2='*',sem='*',soundrules=[],variants=[]):
        self.cat=Cat
        self.lemma=Lemma
        self.subcat=subcat
        self.subcat2=subcat2
        self.sem=sem
        self.variants=variants
        self.soundrules=soundrules
    def add_features(self,FeatDic):
        for Feat,Val in FeatDic:
            if Feat not in self.__dict__.keys():
                sys.exit('Feature '+Feat+ 'does not exist')
            else:
                self.__dict__[Feat]=Val
    def summary(self):
        for Feat in self.__dict__.keys():
            print(self.__dict__[Feat])


class InfLexeme(Lexeme):
    def __init__(self,Cat,Lemma,InfForms,InfPat,subcat='*',subcat2='*',sem='*',variants=[],soundrules=[]):
        self.__name__='InfLexeme'
        super().__init__(Cat,Lemma,subcat=subcat,subcat2=subcat2,sem=sem,variants=variants,soundrules=soundrules)
        InfFormType=type(InfForms).__name__
        if InfFormType!='dict':
            print('infforms need to be a dict. '+InfFormType+' given.')
            sys.exit()
        else:
            self.infforms=InfForms
        self.infpat=InfPat
    def set_infforms(self,InfFormPairs):
        import subprocess
        NewInfFormPairs=[]
        for InfFormName,InfForm in InfFormPairs:
            Reading=InfForm
#subprocess.check_output(['/home/yosato/myProgs/scripts/kakasi_utf8.sh',InfForm,'-HK -JK']).decode().strip()
            NewInfFormPairs.append((InfFormName,(InfForm,Reading)))

        self.infforms.update(NewInfFormPairs)


class NonInfLexeme(Lexeme):
    def __init__(self,Cat,Lemma,subcat='*',subcat2='*',sem='*',variants=[],protos={},soundrules=[]):
        import subprocess
        super().__init__(Cat,Lemma,subcat=subcat,subcat2=subcat2,sem=sem,variants=variants,soundrules=soundrules)
        self.__name__='NonInfLexeme'
        ShellCmd=' '.join([HomeDir+'/myProgs/scripts/kakasi_katakana.sh','"'+Lemma+'"'])
        Reading=subprocess.Popen(ShellCmd,shell=True,stdout=subprocess.PIPE).communicate()[0].decode().strip()
        #[0].decode().strip()
        
      #  self.infform=(Lemma,Reading)
#self.create_variants(VariantProtos)
#    def create_variants(self,VariantProtos):
#        Variants=[]
#        for (Orth,(Feat,Vals)) in VariantProtos.items():
#            Variants.append(Variant(Orth,Feat,Vals))
#        return Variants

class Word:
    def __init__(self,Lexeme,InfFormN=''):
        self.lexeme=Lexeme
        if Lexeme.__name__=='InfLexeme':
            self.orth=Lexeme[InfFormN]
        else:
            self.orth=Lexeme.lemma



class Variant:
    def __init__(self,Orth,RelFeat,RelVals):
        self.orth=Orth
        self.relfeat=RelFeat
        self.relvals=RelVals

def construct_lexemes_from_mecabdic(MecabFP):
    LineCnt=myModule.get_linecount(MecabFP)
    LexemeDic={}
    Milestones=myModule.create_percentage_milestones(20)
    for Cntr,Line in enumerate(open(MecabDicFP)):
        Milestones=myModule.progress_counter(Milestones,Cntr,LineCnt)
        LineEls=Line.split(',')
        (Orth,_,_,_,Cat,Subcat,Sem,_,InfPat,InfForm,Lemma,Reading,Pronunciation)=LineEls
        if (Lemma,Cat) not in LexemeDic.keys():
            if Cat in InfCats:
                Lexeme=InfLexeme(Cat,Lemma,{InfForm:Orth})
            else:
                Lexeme=NonInfLexeme(Cat,Lemma)
            Lexeme.add_features()
            LexemeDic[(Lemma,Cat)]=Lexeme
        else:
            Lexeme=LexemeDic[(Lemma,Cat)]
            Lexeme.set_infforms([(InfForm,Orth)])

#Dir='/home/yosato/myWork/myvo/mecab/ja_JP/seeds/'
#MecabDicFN='Verb.csv'
#MecabDicFP=Dir+MecabDicFN

#Lexemes=construct_lexemes_from_mecabdic(MecabDicFP)

def kana2kana(Str,Strict=False):
    NewStr=''
    for Char in Str:
        if myModule.is_kana(Char):
            NewStr+=myModule.kana2kana(Char)
        else:
            if Strict:
                sys.exit('jp_morph.kana2kana: this is not kana: '+Char)
            else:
                NewStr+=Char
    return NewStr

def mecab_sentstr(MecabSentStr):
    MecabWds=[];RelvP=False;FstRelvInd=-1;PrvWd=None
    WdLines=MecabSentStr.strip().split('\n')
    WdCnt=len(WdLines)
    SentToBuild=MecabSentParse([])
    for Cntr,MecabLine in enumerate(WdLines):
        if MecabLine:
            Wd,FtsStr=MecabLine.split('\t')
            Fts=FtsStr.split(',')
            if len(Fts)>=8:
                Cat=Fts[0]
                MecabWd=MecabWdParse(orth=Wd,cat=Cat,subcat=Fts[1],subcat2=Fts[2],sem=Fts[3],lemma=Fts[6],infpat=Fts[4],infform=Fts[5],reading=Fts[7])
            else:
                MecabWd=MecabWdParse(orth=Wd,cat=Fts[0],subcat=Fts[1],subcat2=Fts[2],sem=Fts[3],lemma='*',infpat=Fts[4],infform='*')

            SentToBuild.append_word(MecabWd,SoundChange=False)
        
    return SentToBuild

def at_least_one_kanji(Wd):
    Bool=False
    for Char in Wd:
        if myModule.identify_type_char(Char)=='han':
            return True
    return False

def all_kana(Wd):
    Bool=True
    for Char in Wd:
        if not myModule.is_kana(Char):
            return False
    return Bool

def render_kana(Wd,WhichKana='hiragana',Strict=False):
    import subprocess
    assert (WhichKana in ['hiragana','katakana'],'output should be either hiragana or katakana')
    OutCharFlag='H' if WhichKana=='hiragana' else 'K'
    if any(myModule.identify_chartype(Char)=='han' for Char in Wd):
        Cmd=' '.join(['echo', Wd.strip(), '| nkf -eW | kakasi -J'+OutCharFlag,'| nkf -Ew'])
        Proc=subprocess.Popen(Cmd,shell=True,stdout=subprocess.PIPE)
        Wd=Proc.communicate()[0].decode().strip()

    Str=''
    for Char in Wd:
        CharT=myModule.identify_type_char(Char)
        if CharT not in ('han','katakana','hiragana'):
            if Strict:
                sys.exit('jp_morph.render_katakana: disallowed char: '+Char+' in '+Wd)
            else:
                Str+=Char
        elif (CharT=='hiragana' and WhichKana=='katakana') or (CharT=='katakana' and WhichKana=='hiragana'):
            Str+=myModule.kana2kana(Char)
        else:
            Str+=Char
    return Str



def voice_first_char(Wd):
    if ' ' in Wd:
        exit('there should not be a space in the str')
    FstCharVoiced=voicethevoiceable(Wd[0])
    if not FstCharVoiced:
        exit('the first char is not voiceable')
    else:
        return FstCharVoiced[0]+Wd[1:]
        
    
def voicethevoiceable(Kana):
    UVPairs={ 'か':'が', 'さ':'ざ', 'た':'だ', 'は':'ば', 'カ':'ガ', 'サ':'ザ', 'タ':'ダ', 'ハ':'バ' }
    Gyo=identify_gyo(Kana)
    if Gyo in UVPairs.keys():
        Dan=identify_dan(Kana)
        return change_dan(UVPairs[Gyo],Dan)
    else:
        return None
        
        

def all_kana_p(Str):
    return all(myModule.is_kana(Char) for Char in Str)

def kana_fuzzy_match(Char1,Char2):
    if Char1==Char2 or myModule.kana2kana(Char1)==Char2:
        return True
    else:
        return False

def palatalise_twokanastr(KanaStr):
    PalDic={'あ':'ゃ','う':'ゅ','お':'ょ','ア':'ャ','ウ':'ュ','オ':'ョ'}
    Conds=[
        (len(KanaStr)==2),
        (identify_dan(KanaStr[0])=='i'),
        (KanaStr[1] in ['あ','う','お','ア','ウ','オ'])
        ]

    if not all(Conds):
        print('Not the case for palatalisation')
        return None
    else:
        return KanaStr[0]+PalDic[KanaStr[1]]
        
    
def ai_u_rule(Str):
    StrLen=len(Str)
    NewStr=''
    for Ind,Char in enumerate(Str):
        if Ind+1 == StrLen:
            NewStr=NewStr+Char
        else:
            if identify_dan(Char)=='a' and kana_fuzzy_match(Str[Ind+1],'う'):
                NewStr=NewStr+change_dan(Char,'o')
            elif identify_dan(Char)=='i' and kana_fuzzy_match(Str[Ind+1],'う'):
                NewStr=NewStr+palatalise_twokanastr(Char+Str[Ind+1])
            else:
                NewStr=NewStr+Char
    return NewStr

def apply_vharmony(InputWd,RPreced=True):
    #TransWd=copy.deepcopy(InputWd)
    TransWd=InputWd
    CurWd=TransWd
    PrvWd=TransWd.contextbefore

    if not PrvWd.infpat.startswith('一段'):
        
        if RPreced:
            Preced=CurWd; PrecedPos=0; NonPreced=PrvWd; NonPrecedPos=-1
        else:
            Preced=PrvWd; PrecedPos=-1; NonPreced=CurWd; NonPrecedPos=0

        Dan2ChangeTo=identify_dan(Preced.reading[PrecedPos])
        NonPreced.change_sound(NonPreced.reading[:-1]+change_dan(NonPreced.reading[NonPrecedPos],Dan2ChangeTo))

    return TransWd

def apply_uonbin(InputWd,OnlyOne=True):
    Sokuonbin=InputWd.orth
    SyllableCnt=len(InputWd.reading)
    OutputWd1=copy.copy(InputWd)
    OutputWd1.reading=ai_u_rule(re.sub(r'[クッ]','ウ',InputWd.reading))
    OutputWd1.orth=ai_u_rule(re.sub(r'[くっ]','う',InputWd.orth))
    OutputWds=[OutputWd1]
    StdRead=OutputWd1.reading

    if len(StdRead)>=3:
        OutputWd2=copy.copy(OutputWd1)
        OutputWd2.reading=re.sub(r'ュ?ウ$','',OutputWd1.reading)
        OutputWd2.orth=re.sub(r'ゅ?う$','',OutputWd1.orth)
        OutputWds.append(OutputWd2)

#        if myModule.identify_type_char(OutputWd2.orth[-1])=='han':
#            OutputWd2.orth=OutputWd2.orth+change_dan(myModule.kana2kana(OutputWd1.reading[-2]),'o')

    if OnlyOne:
        return myModule.choose_randomly(OutputWds)
    else:
        return OutputWds





def construct_transmap(InfProtos,NonInfProtos):
    import subprocess
    TransMapInf={}
    for (Cat,Subcat,Excepts,Pairs1,AddPairs,InfFormPairsW) in InfProtos:
        InfForms=[Pairs1[0], Pairs1[1], Pairs1[2], Pairs1[3], Pairs1[4], Pairs1[5]]
        InfFormNames=['未然形','連用形','基本形','連体形','仮定形','命令形']
        InfFormPairsE=list(zip(InfFormNames,InfForms))+AddPairs
        InfFormPairsEDic={}
        for InfFormName,InfForm in InfFormPairsE:
            Reading=subprocess.check_output([HomeDir+'/myProgs/scripts/kakasi_katakana.sh',InfForm]).decode().strip()
            InfFormPairsEDic[InfFormName]=(InfForm,Reading)
        LexE=InfLexeme(Cat,Pairs1[2],InfFormPairsEDic,Subcat=Subcat)
        #we use copy and then change where necessary
        LexW=copy.deepcopy(LexE)
        LexW.set_infforms(InfFormPairsW)
        TransMapInf.update([((Cat,Subcat,LexE.lemma),(LexE,LexW,Excepts))])

    TransMapNonInf={}

    for (Cat,Subcat,Excepts,KantoOrth,[KansaiOrth,Variants]) in NonInfProtos:
#        Reading=subprocess.check_output(['/home/yosato/links/myProgs/scripts/kakasi_utf8.sh',KansaiOrth,'-HK -JK']).decode().strip()
        LexE=NonInfLexeme(Cat,KantoOrth,Subcat=Subcat)
        LexW=NonInfLexeme(Cat,KansaiOrth,Subcat=Subcat,VariantProtos=Variants)
        TransMapNonInf.update([((Cat,Subcat,LexE.lemma),(LexE,LexW,Excepts))])

    return (TransMapInf,TransMapNonInf)

    
def match_lexeme_p(Lexeme,Cat,Orth):
    if Lexeme.cat!=Cat:
        return False
    else:
        if Orth in Lexeme.infforms.values():
            return True
        else:
            return False

def find_matched_lexeme(Lexemes,Cat,Orth,FirstOnly=False):
    Matched=[]
    for Lexeme in Lexemes:
        if match_lexeme_p(Lexeme,Cat,Orth):
            if FirstOnly:
                return [Lexeme]
            else:
                Matched.append(Lexeme)
    return Matched
