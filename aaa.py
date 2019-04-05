Strs=['aaa','bbb','ccc','ddd','eee']
Suffixes=[('d',' eee'),('e','e'),('e','ee'),('dd','d eee')]

def do_stuff(Strs,S1,S2):
    def find_spot(Strs,Suffix):
        Cntr=-1;EndStr=Strs[Cntr];ConsumedSuffix=Suffix
        while True:
            if Strs[Cntr]==ConsumedSuffix:
                Cntr-=1
                ConsumedSuffix=CoonsumedSuffix[-len(Strs[Cntr])]
                continue
            elif Strs[Cntr].endswith(ConsumedSuffix):
                return Cntr,Strs[Cntr][-len(ConsumedSuffix)]

    Glued=' '.join(Strs)
    Suffix=S1+S2
    assert Glued.endswith(Suffix)
    Spot,Remnant=find_spot(Strs,Suffix) 
    return Str[:Spot]+[Remnant]
    

for (S1,S2) in Suffixes:
    do_stuff(Strs,S1,S2)
