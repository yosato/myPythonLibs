from pdb import set_trace

import imp,sys,os,re,glob

import unittest
import transducer
imp.reload(transducer)

def flatten(L):
    if L==[]:
        return L
    if isinstance(L[0],list):
        return flatten(L[0])+flatten(L[1:])
    return [L[0]]+flatten(L[1:])

class TestTransducerStemming(unittest.TestCase):
    def setUp(self):
        def get_fps(Dir,FGlobs):
            FPs=[]
            for FGlob in FGlobs:
                Glob=os.path.join(Dir,FGlob)
                FPs.extend(glob.glob(Glob))
            return FPs
        #set_trace()
        Lang='kr'
        TransDir=os.getcwd()
        ExampleDir=os.getcwd()
        TransFPs=get_fps(TransDir,['transducer_'+Lang+'*','inflection_mapping_'+Lang+'*'])
        assert len(TransFPs)==2,'at least one of the required files missing'
        ExampleFPs=get_fps(ExampleDir,['examples_'+Lang+'*'])
        assert len(ExampleFPs)==1,'at least one of the required files missing'
        self.examplefp=ExampleFPs[0]
        self.transfp=TransFPs[0]
        self.inflfp=TransFPs[1]
        Pairs=[]
        with open(self.examplefp) as FSr:
            for Cntr,Line in enumerate(FSr):
                if not Line.strip() or Line.lstrip().startswith('//'):
                    continue
                Els=Line.split('\t')
                assert len(Els)==2,'the file format wrong, line '+str(Cntr)+': '+Line
                OrgStr,StemmedRefBlock=Els
                StemmedRefs={}
                for StemmedRefStr in StemmedRefBlock.split(','):
                    StemmedRefEls=re.split('[()]',StemmedRefStr)
                    assert len(StemmedRefEls)==3 and (StemmedRefEls[-1]=='' or StemmedRefEls[-1]=='\n'),'the file format wrong, line '+str(Cntr)+': '+Line
                    StemmedRefs[StemmedRefEls[1].decode('utf8')]=StemmedRefEls[0].decode('utf8')
                Pairs.append((OrgStr.decode('utf8'),StemmedRefs))
        self.sentpairs=Pairs
    def test_examples(self):
        #set_trace()
        Trans,InfWds=transducer.make_transducer_fromjsons(self.transfp,self.inflfp)
        VLexs=flatten(list(InfWds.values()))
        set_trace()
        Refs=[];Hyps=[]
        for (Org,StemmedRefs) in self.sentpairs:
            for InfForm,StemmedRef in StemmedRefs.items():
                Hyp=transducer.parse_with_transducer(Org,Trans,InfForm,VLexs)
                if Hyp is None:
                    StemmedHyp=None
                else:
                    (Stemmed,OrgSeg,Consumed)=Hyp
                    StemmedHyp=Org[:-(len(OrgSeg)+len(Consumed))]+Stemmed
                Refs.append(StemmedRef)
                Hyps.append(StemmedHyp)
                print(StemmedRef)
                print(StemmedHyp)
        self.assertListEqual(Refs,Hyps)
 #       set_trace()

if __name__=='__main__':
    unittest.main()
