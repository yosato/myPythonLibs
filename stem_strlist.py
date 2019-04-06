Strs=['aaa','bbb','ccc','ddd','eee']
Suffixes=[('d','eee'),('e','e'),('e','ee'),('dd','deee')]

def stem_strlist(Strs,S1,S2):
    Suffix=S1+S2
    Cntr=-1;RemSuffix=Suffix
    while True:
        LenStr=len(Strs[Cntr])
        LenSuffix=len(RemSuffix)
        if LenSuffix>LenStr:
            assert(RemSuffix.endswith(Strs[Cntr]))
            RemSuffix=RemSuffix[:-LenStr]
            Cntr-=1
            continue
        else:
            break
    Remnant=Strs[Cntr][:-LenSuffix]
    Remnants=[] if not Remnant else [Remnant]
    return Strs[:Cntr]+Remnants
for (S1,S2) in Suffixes:
    Result=do_stuff(Strs,S1,S2)
    print(Result)
