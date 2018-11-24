import imp,sys,os,glob
import mecabtools
imp.reload(mecabtools)

def main0(Dir):
    mecabtools.create_indexed_dic(Dir)

def main():
    DicDir=sys.argv[1]
   # if not mecabtools.validate_corpora_indir(DicDir):
    #    sys.exit('corpora not found')
    main0(DicDir)
    
if __name__=='__main__':
    main()
