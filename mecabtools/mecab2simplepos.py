import sys,os,imp
sys.path.append('/home/yosato/myProjects/myPythonLibs/mecabtools')
import mecabtools

imp.reload(mecabtools)


def main(MecabFP):
        for SentChunk in mecabtools.generate_sentchunks(MecabFP):
            SentStrs=[]
            for Line in SentChunk:
                Orth,RestStr=Line.split('\t')
                if not Orth.strip():
                    continue
                Orth='colon' if Orth==':' else Orth
                Rest=RestStr.split(',')
                SentStrs.append((Orth,Rest[0],Rest[-1]))
            OutStr=' '.join([':'.join(WdStr) for WdStr in SentStrs])
            sys.stdout.write(OutStr+'\n')

            
if __name__=='__main__':
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('input_file')
    Args=Psr.parse_args()
    #InFPs=glob.glob(os.path.join(Args.input_dir,'*.mecab'))
    main(Args.input_file)
    
    
