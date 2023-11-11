import pandas as pd
import os
import json
from scrap import get_snp_data
import glob

cwd = os.getcwd()
data_dir = os.path.join(cwd,'data/')


def get_df(json_files):

    # Open and read the JSON file
    with open(json_files, 'r') as json_file:
        # Load the JSON data into a list of dictionaries
        data_list = json.load(json_file)

    df = pd.DataFrame(data_list['results'])
    df = df.transpose()
    df['genotype'] = df.index
    df.reset_index(drop=True,inplace=True)

    df_ = pd.json_normalize(df['printouts'])

    #df_ = df_.explode(df_.columns.tolist())
    df_ = df_.explode(['Summary'])
    df_ = df_.explode(['Magnitude','Repute'])
    df_.to_excel('df_.xlsx')



    df_final = df.merge(df_, how='left',  left_index=True, right_index=True, indicator=False)
    df_final.drop(columns=['printouts'],inplace=True)

    df_final['geno'] = df_final['fulltext'].str.extract(r'\((\w;\w)\)').fillna('')
    df_final['geno'] = df_final['geno'].str.replace(';', '')

    df_final['rsID'] = df_final['fulltext'].str.extract(r'(Rs\d+)')
    df_final['rsID'] = df_final['rsID'].str.lower()

    return df_final


json_files = glob.glob(data_dir + '*')
#print(json_files)

ft = []
for i in json_files:
    print(i)
    df_final = get_df(i)
    ft.append(df_final)

df = pd.concat(ft,ignore_index=True)

#print(df)
print(df)
df.to_excel('genotypes.xlsx')