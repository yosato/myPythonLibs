import imp,sys,os
import mecabtools
imp.reload(mecabtools)

def main0(Dir):
    mecabtools.create_indexed_dic(Dir)

if __name__=='__main__':
    main0('/processedData/mecabStdJp/models/standard_reduced')
