import itertools,sys,os,imp
import align_jpseqs
from pythonlib_ys import main as myModule
from pythonlib_ys import jp_morph

from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner

# Create sequences to be aligned.
def align_jpseqs(Str1,Str2):
    a = Sequence(list(Str1))
    b = Sequence(list(Str2))

    # Create a vocabulary and encode the sequences.
    v = Vocabulary()
    aEncoded = v.encodeSequence(a)
    bEncoded = v.encodeSequence(b)

    # Create a scoring and align the sequences using global aligner.
    scoring = SimpleScoring(2, -1)
    aligner = GlobalSequenceAligner(scoring, -2)
    score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

    # Iterate over optimal alignments and print them.
    for encoded in encodeds:
        alignment = v.decodeSequenceAlignment(encoded)
        CurChunk1='';CurChunk2='';Chunks1=[];Chunks2=[]
        for Cntr,(Char1,Char2) in enumerate(zip(alignment.first,alignment.second)):
            if Char1==Char2:
                InId=True
                if Cntr!=0 and PrvInId!=InId:
                    Chunks1.append(CurChunk1);Chunks2.append(CurChunk2)
                    CurChunk1='';CurChunk2=''
                CurChunk1+=Char1;CurChunk2+=Char2

            else:
                InId=False
                if Cntr!=0 and PrvInId!=InId:
                    Chunks1.append(CurChunk1);Chunks2.append(CurChunk2)
                    CurChunk1='';CurChunk2=''
                if Char1=='-':
                    CurChunk2+=Char2
                elif Char2=='-':
                    CurChunk1+=Char1
                else:
                    CurChunk1+=Char1;CurChunk2+=Char2
            

            PrvInId=InId
        Chunks1.append(CurChunk1);Chunks2.append(CurChunk2)
        print()
        print('Alignment score: '+ str(alignment.score))
        print('Percent identity: '+str( alignment.percentIdentity()))
        print

        return Chunks1,Chunks2



def jp_orthvar(StrPairs):
    return list(filter(lambda SP:orth_variant_p(SP), StrPairs))
    

def chartypes_uniform_and_different(TopBit1,TopBit2,CharSets=['han','roman','katakana','hiragana']):
    CharPair=None
    for (CharSet1,CharSet2) in itertools.combinations(CharSets,2):
        if myModule.all_of_chartypes_p(TopBit1,[CharSet1]) and myModule.all_of_chartypes_p(TopBit2,[CharSet2]) or myModule.all_of_chartypes_p(TopBit1,[CharSet2]) and myModule.all_of_chartypes_p(TopBit2,[CharSet1]):
           
            CharPair=set((CharSet1,CharSet2))
            break
    return CharPair

def orth_variant_p(Str1,Str2):
    assert Str1!=Str2, "we don't do identical cases!!!"
    assert all(Str!='' for Str in (Str1,Str2)), "we don't do empty strings!!!"
    
    AlignedSeq1,AlignedSeq2=align_jpseqs(Str1,Str2)
    if AlignedSeq1==[''] and AlignedSeq2==['']:
        return False

    if not AlignedSeq1:
        return False
    
    for Chunk1,Chunk2 in zip(AlignedSeq1,AlignedSeq2):
        if Chunk1==Chunk2:
            continue
        else:
            EmptyInds=[Cntr for (Cntr,Chunk) in enumerate((Chunk1,Chunk2)) if Chunk=='']
            if EmptyInds:
                if len(EmptyInds)==2:
                    return False
                else:
                    NonEmptyInd=1 if EmptyInds[0]==0 else 0
                    NonEmptyChunk=[Chunk1,Chunk2][NonEmptyInd]
                    if len(NonEmptyChunk)==1 and myModule.all_of_chartypes_p(NonEmptyChunk,['hiragana','katakana']):
                        return True
                    else:
                        return False
                    
            Pair=chartypes_uniform_and_different(Chunk1,Chunk2)
            if Pair=={'han','katakana'}:
                return False
            if Pair:
                if any(any(Type==TgtType for TgtType in ('katakana','hiragana')) for Type in Pair):
                    KanaChunk,NonKanaChunk=(Chunk1,Chunk2) if myModule.all_of_chartypes_p(Chunk1,['hiragana','katakana']) else (Chunk2,Chunk1)
                    if len(NonKanaChunk)>len(KanaChunk):
                        return False
                if Pair=={'hiragana','katakana'}:
                    listified=list(Pair)
                    if jp_morph.kana2kana(listified[0])!=listified[1]:
                        return False
                    else:
                        continue
                else:
                    continue
            else:
                return False

    print(AlignedSeq1)
    print(AlignedSeq2)
    
          
    return True
        
        
