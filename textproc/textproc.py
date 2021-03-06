import sys,os
import bidict

FullWidthRange=('ff00','ff5e')
HalfWidthRange=('0020','007e')

FullWidthRangeDec=tuple([ int(Hex,16) for Hex in FullWidthRange ])
HalfWidthRangeDec=tuple([ int(Hex,16) for Hex in HalfWidthRange ])

FullHalfDiff=FullWidthRangeDec[0]-HalfWidthRangeDec[0]

FullWidthChars=tuple([ chr(Int) for Int in range(FullWidthRangeDec[0],FullWidthRangeDec[1])  ])
HalfWidthChars=tuple([ chr(Int) for Int in range(HalfWidthRangeDec[0],HalfWidthRangeDec[1])  ])

NormBidict=bidict.bidict({Full:Half for (Full,Half) in zip(FullWidthChars,HalfWidthChars)})

SentDelimsHalf=('!','?')
SentDelimsBoth=('。')
OpenQuotes=('"',"'",'「','『')
CloseQuotes=('"',"'",'」','』')

def normalise_fullwidth_file(FP,OutFP=None):
    Out=open(OutFP,'wt') if OutFP else sys.stdout
    for LiNe in open(FP):
        Out.write(normalise_fullwidth(LiNe))
    if OutFP:
        Out.close()

def normalise_fullwidth(Str,Reverse=False):
    NewStr=''
    for Char in Str:
        if not Reverse and Char in FullWidthChars:
            NewStr+=NormBidict[Char]
        if Reverse and Char in HalfWidthChars:
            NewStr+=NormBidict.inv[Char]
        else:
            NewStr+=Char
    return NewStr

SentDelimsFull=tuple(list(normalise_fullwidth(''.join(SentDelimsHalf))))
SentDelims=SentDelimsFull+SentDelimsHalf+SentDelimsBoth

                    
def segment_into_sents(Str):
    NewStr=''
    while len(Str)>=2:
        Char1,Char2=Str[:2]
        Str=Str[1:]
        if Char1 in SentDelims and Char2 not in CloseQuotes:  
            NewStr+=Char1+'\n'
        else:
            NewStr+=Char1
    NewStr+=Char2
    return NewStr


