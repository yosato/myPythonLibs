
def remove_bad_strings_fromfile(FP,StrongBans,WeakBans,StrongBanRanges=None,WeakBanRanges=None,SpecificColumn=None):
    with open(FP+'.badremoved','wt') as FSw:
        for Cntr,LiNe in enumerate(open(FP)):
            if Cntr%10000==0:   print(Cntr)
            Line=(LiNe.strip().split('\t')[SpecificColumn] if SpecificColumn else LiNe.strip())
            if string_bad_p(Line,StrongBans,WeakBans,StrongBanRanges=StrongBanRanges,WeakBanRanges=WeakBanRanges,MaxLength=20):
                continue
            else:
                FSw.write(LiNe)
            

def string_bad_p(Str,StrongBans,WeakBans,StrongBanRanges=[(0,float('inf'))],WeakBanRanges=[(0,float('inf'))],MaxLength=2000):
    '''
    given two sets, strongly prohibited chars and weakly prohibited chars,
    check, for a str, if it is bad, in the sense that:
    it contains a strongly prohibited char (even one) or
    it consists wholly of bad weakly prohinited char
    >>> string_bad_p('adef',['a','b'],['x','y','z'])
    True
    >>> string_bad_p('xyzf',['a','b'],['x','y','z'])
    False
    >>> string_bad_p('xyyz',['a','b'],['x','y','z'])
    True
    >>> string_bad_p('def',['a','b'],['x','y','z'])
    False
    '''
    if len(Str)>MaxLength:
        return True
    WkCnt=0
    for Cntr,Char in enumerate(Str):
        CodeP=ord(Char)
        if Char in StrongBans or in_ranges(CodeP,StrongBanRanges):
            return True
        elif Char in WeakBans or in_ranges(CodeP,WeakBanRanges):
            if WkCnt<Cntr:
            #this means there has been at least one legitimate char
                return True
            else:
                WkCnt+=1
    if Cntr==WkCnt-1:
     # meaning everything was a weekly banned char 
        return True
    return False



def str2hexes(Str):
    return [hex(ord(Chr)) for Chr in list(Str)]

def hexes2str(Hexes):
    return ''.join([chr(int(Hex,16)) for Hex in Hexes])
    




