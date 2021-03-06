import unittest,imp,os,sys
from pdb import set_trace

import work_utils
imp.reload(work_utils)

HomeDir=os.getenv('HOME')
TGRootDir=os.path.join(HomeDir,'links/myLMBEexps')

class TestWorkUtils(unittest.TestCase):
    def setUp(self):
        Lang='ar'
        LangSuffix=os.path.join(Lang,'lingo_'+Lang,'sources',Lang)
        DialectDirN='arabic_twitteronly'
        TGFN=Lang+'-lk-text.lex.3gram.txt'
        #self.TGFP=os.path.join(TGRootDir,DialectDirN,LangSuffix,TGFN)
        self.TGFP=os.path.join(HomeDir,TGFN)
        if not os.path.isfile(self.TGFP):
            sys.exit('file does not exist')
        
    def test_collect_bigrams_from3gramtxt(self):
        set_trace()
        TGs=work_utils.collect_trigrams_from3gramtxt(self.TGFP)
        for TG in TGs:
            print(TG)

if __name__=='__main__':
    unittest.main()
