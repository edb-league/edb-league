"""Inspecione uma demo local sem precisar abrir o painel."""
import argparse
from pathlib import Path
from demo_importer import parse_demo,prepare_upload
import io
import pandas as pd

class Upload:
    def __init__(self,p):
        self.p=Path(p)
        self.name=self.p.name
        self.file=open(p,'rb')
    def seek(self,n):return self.file.seek(n)
    def read(self,n=-1):return self.file.read(n)
    def close(self):self.file.close()

p=argparse.ArgumentParser(description='XINXAS: extrair estatísticas de uma demo CS2')
p.add_argument('arquivo',help='Arquivo .dem ou .dem.gz da xplay')
args=p.parse_args()
upload=Upload(args.arquivo)
folder=None
try:
    folder,path,fingerprint=prepare_upload(upload)
    result=parse_demo(path,fingerprint)
    print('Mapa:',result.map_name,'\nRounds (verificar):',result.rounds_total,
          '\nSHA256:',result.fingerprint)
    print(pd.DataFrame(result.players).to_string(index=False))
    print('\nATENÇÃO:',*result.warnings,sep='\n • ')
finally:
    if folder:folder.cleanup()
    upload.close()