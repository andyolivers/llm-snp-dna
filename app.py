import os
from transformers import pipeline
import plotly.express as px
import pandas as pd
import warnings
import streamlit as st
from snps import SNPs
warnings.filterwarnings("ignore", category=UserWarning)


st.set_page_config(
    page_title="SNiP",
    page_icon="🧬",
    # layout="wide",
)

from streamlit.components.v1 import html

button = """
<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="adof6qkj3h" data-color="#FFDD00" data-emoji=""  data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>
"""

html(button, height=70, width=220)

st.markdown(
    """
    <style>
        iframe[width="220"] {
            position: fixed;
            bottom: 60px;
            right: 40px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.warning(
        'This software is not meant to diagnose any disorders or diseases. SNP data is sourced from https://www.snpedia.com/ which publish genetic datasets. The process of diagnosis is complex and requires medical support.',
        icon="⚠️")



# Displaying chatbot interface title and description
st.title("🧬 SNiP - DNA Analyzer")
st.write(' ')
st.write('Leverage the power of LLM to get to know more about your DNA.')
st.write("The genome, essentially the full collection of genetic instructions in a cell, holds the blueprint for life. Genomics, a field in molecular biology, explores the structure, functions, variations, evolutionary aspects, and mapping of these genomes. In the case of the human genome, it contains both the coding sections that carry the blueprint for about 20,000 to 25,000 genes, as well as noncoding regions that don't directly encode these genes. Delving into someone's genome could unveil a wealth of biological insights—details like potential age indicators, skin characteristics, disease susceptibilities, and much more—essentially painting a comprehensive picture of an individual's biological traits.")
st.write("SNP stands for Single Nucleotide Polymorphism. It's a common type of genetic variation that occurs within a person's DNA sequence. Specifically, it refers to a variation at a single position in a DNA sequence among individuals. This variation arises when a single nucleotide (the building blocks of DNA) differs between members of a species or paired chromosomes in an individual. SNPs are the most frequent type of genetic variation among people and can impact various traits, including susceptibility to certain diseases, response to drugs, or other characteristics. They're crucial in genetics research and understanding the genetic basis of various traits and diseases.")
st.write(' ')
st.write(' ')
st.subheader("File Upload")
st.write('Upload a DNA file from MyHeritage, ancestry or 23andMe.')
cwd = os.getcwd()
df_base = pd.read_excel(os.path.join(cwd,'genotypes.xlsx'))
df_base.drop_duplicates(inplace=True)
df_base.reset_index(drop=True,inplace=True)

uploaded_file = st.file_uploader("Choose a file", type=['csv','txt'], accept_multiple_files=False,
                 help=None, disabled=False, label_visibility="visible")



if uploaded_file is not None:

    bytes_data = uploaded_file.getvalue()
    s = SNPs(bytes_data)
    #s = SNPs("resources/662.23andme.340.txt.gz")
    df = s.snps

    st.success('File uploaded!', icon="✅")

    ###--------------- ENGINEERING ---------------###

    df['rsid'] = df.index
    df['rsid'] = df['rsid'].str.lower()
    df.reset_index(inplace=True,drop=True)

    fet = ['rsID','Magnitude', 'Repute', 'Summary','geno']
    data = df.merge(df_base[fet], how='left',left_on=['rsid','genotype'], right_on=['rsID','geno'], indicator=False)
    data.loc[data['rsID'].isnull()==False,'match'] = 1
    data.drop(columns=['rsID','geno'],inplace=True)

    # Filter
    filter = data[data['match']==1]
    filter['Repute'] = filter['Repute'].fillna('Neutral')
    bad = filter[filter['Repute'] == 'Bad']
    good = filter[filter['Repute']=='Good']
    neutral = filter[filter['Repute']=='Neutral']
    father = data[data['chrom'] == 'Y']
    mother = data[data['chrom'] == 'X']


    def merge_text(df,stp,nm):
        df_ = df.copy()
        df_['Summary'] = df_['Summary'].astype('object')
        df_.dropna(subset=['Summary'],inplace=True)

        my_list = df_['Summary'].unique().tolist()

        if len(my_list) > 0:
            result_string = ';\n'.join(my_list)
        else:
            result_string = 'no traits found'

        if stp in ['mother','father']:
            add = f'The traits of your DNA from your {stp} are:\n' + result_string
        else:
            add = f'The {stp} traits of your DNA are:\n' + result_string

        df_add = pd.DataFrame({'Repute': nm, 'Condition': add},index=[0])

        return add, df_add


    add_bad, df_bad = merge_text(bad, 'bad (diseases, health problems, disorders, issues, defects)','negative')
    add_good, df_good = merge_text(good, 'good (healthy characteristics, qualities)','positive')
    add_neutral, df_neutral = merge_text(neutral, 'neutral (normal characteristics)','neutral')
    add_father, df_father = merge_text(father, 'father','father')
    add_mother, df_mother = merge_text(mother, 'mother','mother')

    df_text = pd.concat([df_bad,df_good,df_neutral, df_mother, df_father],ignore_index=True)

    ###--------------- ANALYSIS ---------------###
    st.write(' ')
    st.subheader("Summary")
    a1, a2, a3, a4 = st.columns(4)
    with a2:
        st.metric(label="Traits Found", value=len(filter.rsid.unique().tolist()))

    with a3:
        st.metric(label="% Traits Found", value=str(round((len(filter.rsid.unique().tolist())/len(data.rsid.unique().tolist()))*100,2))+'%')
    #delta= str((len(filter.rsid.unique().tolist())/len(data.rsid.unique().tolist()))*100)+'%',delta_color="off"


    # Aggregate counts based on unique values in 'Value' column
    df_agg = filter['Repute'].value_counts().reset_index()
    df_agg.columns = ['Repute', 'Count']

    # Create Donut Chart
    fig = px.pie(df_agg, names='Repute', values='Count', hole=0.5)
    fig.update_layout(title_text='Traits by Scope')

    st.write(fig)


    with st.spinner('Reading traits...'):
        ###--------------- CHAT ---------------###

        task = "text2text-generation"  # text-generation"
        #checkpoint = "./model/"
        #tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        #base_model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint,
        #                                                   device_map='auto',
        #                                                   torch_dtype=torch.float32, offload_folder="offload")

        # Use Hugging Face's Transformers for text summarization
        template = "Summarize the DNA traits: {context}."


        #summarizer = pipeline(model_id = "google/flan-t5-large",task=task,model=base_model, tokenizer=tokenizer)
        summarizer = pipeline(task=task,model="MBZUAI/LaMini-Flan-T5-248M")

        prompt = template.format(context=add_bad)
        sum_bad = summarizer(prompt, max_length=1000, do_sample=False)[0]['generated_text']
        st.text_area("Bad traits",sum_bad)

        prompt = template.format(context=add_good)
        sum_good = summarizer(prompt, max_length=1000, do_sample=False)[0]['generated_text']
        st.text_area("Good traits",sum_good)

        prompt = template.format(context=add_neutral)
        sum_neutral = summarizer(prompt, max_length=1000, do_sample=False)[0]['generated_text']
        st.text_area("Neutral traits",sum_neutral)


        prompt = template.format(context=add_mother)
        sum_mother = summarizer(prompt, max_length=1000, do_sample=False)[0]['generated_text']
        st.text_area("Traits from your mother:",sum_mother)

        prompt = template.format(context=add_father)
        sum_father = summarizer(prompt, max_length=1000, do_sample=False)[0]['generated_text']
        st.text_area("Traits from your father:",sum_father)


        #summary = sum_bad + '\n' + sum_good + '\n' + sum_neutral + '\n' + sum_mother + '\n' + sum_father

        #df_summary = pd.DataFrame({'Condition': summary},index=[0])






