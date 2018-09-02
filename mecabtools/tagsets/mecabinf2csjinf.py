def mecabinfpat2csj(MecabInfPat,Lemma):
    Els=MecabInfPat.split('・')
    if Els[0]=='五段':
        Gyo=Els[1][:2]
        GyoPat= Gyo+Els[0]
    elif Els[0]=='一段':
        Gyo,Dan=jp_morph(Lemma[-2])
        if Dan=='e':
            Pat='下一段'
        elif Dan=='i':
            Pat='上一段'
        GyoPat=Gyo+Pat
    elif Els[0]=='サ変':
        if Els[1]=='−ズル':
            GyoPat='ザ行変格'
        else:
            GyoPat='サ行変格'
    elif Els[0]=='カ変':
        GyoPat='カ行変格'
    return GyoPat

def mecabinfform2csjx2(MecabInfForm):
    if MecabInfForm.endswith('形'):
        FormAssim(MecabInfForm[:3],*)
    elif MecabInfForm.startswith():
        未然形
    elif


        
