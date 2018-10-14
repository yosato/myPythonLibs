import functools,sys
import pdb

def contiguous_p(List):
    Bool=True
    Prv=List[0]
    for El in List[1:]:
        if El-Prv==1:
            Prv=El
        else:
            sys.stderr.write(str(El)+ ' follows '+str(Prv))
            Bool=False
            break
    return Bool

#def ambiguous_p(Dict):
    

MecabCSJ={
    (1,):	(22,),
    (2,3,4,5):	(20,),
    (6,7,8,10,12,14,33,34,36):	(11,),
    (9,):	(17,),
(11,):	(11,1),
    (13,):(14,),
(15,16,17,18,19,20,21,):	(12,),
(22,23,24,25,26,27,28,29,30,):	(13,),
    (31,32,):(10,),
(38,39,40,):	(9,),
(41,42,43,):	(16,),
(44,45,):	(1,),
(35,37,59,):	(2,),
    (46,): (19,),
(47,48,49,57,):	(6,),
    (50,):(3,),
    (58,):(7,),
    (55,):	(4,),
(51,53,56,):	(8,),
(52,54,):	(5,),
(60,69,):	(18,),
    (61,62,63,64,65,66,67,):	(15,),
        (68,):(21,),

}

#assert(ambiguous_p(MecabCSJ))

AllNumsM=sorted(set(functools.reduce(tuple.__add__,MecabCSJ.keys())))
AllNumsC=sorted(set(functools.reduce(tuple.__add__,MecabCSJ.values())))

#pdb.set_trace()

assert(contiguous_p(AllNumsM))
assert(contiguous_p(AllNumsC))

MecabJuman={
    (1,):(2,),
    
}
