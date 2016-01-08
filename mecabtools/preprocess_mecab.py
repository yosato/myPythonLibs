import imp,sys,os,subprocess
import mecabtools
imp.reload(mecabtools)

def main0(FP,CleanDir,NotCleanDir,OrgTestFP):
    # remove unwanted stuff and normalise
    print('first we normalise the file')
    CleanFP=CleanDir+'/'+os.path.basename(FP)
    ReducedFP='.'.join(CleanFP.split('.')[:-1])+'.reduced.mecab'
    Cmd=' '.join([CleanDir+'/clean_mecab.sh',FP,'>',CleanFP])
    Proc=subprocess.Popen(Cmd,shell=True)
    Return=Proc.wait()
    if Return !=0:
        sys.exit('clean shellscript failed')
    else:
        print('normalisation done')
    # clean mecab file
    print('now doing cleaning')
    MkdSents=mecabtools.mark_sents(CleanFP,[7,9])
    ErrorFreeP=mecabtools.markedsents2outputs(MkdSents,CleanFP,StrictP=True,MoveTo=NotCleanDir)
    # splitting
    print('finally doing splitting')
    if ErrorFreeP:
        mecabtools.produce_traintest(CleanFP,(80,5,True),CheckAgainst=OrgTestFP)
    else:
        mecabtools.produce_traintest(ReducedFP,(80,5,True),CheckAgainst=OrgTestFP)
    print('all done')

def main():
    '''
      this script does three things
      1 remove annotations and normalise
      2 error checking of mecab format
      3 only on clean files do splitting
    '''
    Inputs=sys.argv
    if len(Inputs)<2 or not os.path.isfile(Inputs[1]):
        sys.exit('requires an existing input file')

    HomeDir=os.getenv('HOME')
    RtDir=os.path.join(HomeDir,'mecabKansaiModels')
    #RtDir='/mecabKansaiModels'
    DataDir=os.path.join(RtDir,'data')
    TestDir=os.path.join(RtDir,'testfiles')
                        
    CleanDir=os.path.join(DataDir,'corpora/clean')
    NotCleanDir=os.path.join(DataDir,'corpora/not_clean')
    OrgTestFP=os.path.join(TestDir,'test_sentences_kansai.txt')

    for Path in (CleanDir,NotCleanDir,OrgTestFP):
        if not os.path.exists(Path):
            print(Path+ ' does not exist')
            
    main0(Inputs[1],CleanDir=CleanDir,NotCleanDir=NotCleanDir,OrgTestFP=OrgTestFP)
    
if __name__=='__main__':
    main()
