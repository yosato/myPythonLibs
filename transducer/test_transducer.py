from pdb import set_trace

import imp,sys,os

import unittest
import transducer
imp.reload(transducer)



class TestKorean(unittest.TestCase):
    def setUp(self):
        CurDir=os.getcwd()
        FPs=[os.path.join(CurDir,FN) for FN in ('stemming_examples_kr.txt','transducer_kr.json','inflection_mapping_kr.json')]
        assert(all(os.path.isfile(FP) for FP in FPs),'at least one of the required files missing')
        self.examplefp=FPs[0]
        self.transfp=FPs[1]
        self.inflfp=FPs[2]
        Pairs=[]
        with open(self.examplefp) as FSr:
            for Line in FSr.readlines():
                Els=Line.split('\t')
                assert(len(Els)==2,'the file format wrong')
                Pairs.append(Els)

        self.sentpairs=Pairs
    def test_korean(self):
        set_trace()
        Trans=transducer.make_transducer(self.transfp,self.inflfp)
        for (Org,StemmedRef) in self.sentpairs:
            set_trace()
            StemmedHyp=transducer.stem_inflect_verb(Str,Trans,SpaceP=True)
            self.assertEqual(StemmedRef==StemmedHyp)
 #       set_trace()

if __name__=='__main__':
    unittest.main()
