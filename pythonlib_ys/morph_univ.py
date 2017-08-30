class Lexeme:
    def __init__(self,Lemma,PoS):
        self.lemma=Lemma
        self.pos=PoS

class Word:
    def __init__(self,Lemma,PoS,InfForm):
        super.__init__(Lemma,PoS)
        self.infform=InfForm

        

