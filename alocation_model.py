import pandas as pd

energia = pd.read_excel("./dados/dados.xlsx", sheet_name= "custo_energia")
tratamento = pd.read_excel("./dados/dados.xlsx", sheet_name="custo_tratamento")
producao = pd.read_excel("./dados/dados.xlsx", sheet_name="producao_maxima")
demanda = pd.read_excel("./dados/dados.xlsx", sheet_name="demanda_minima")
distribuicao = pd.read_excel("./dados/dados.xlsx", sheet_name="distribuicao_maxima")

#conjuntos
meses = energia['Mes'].tolist()
sistemas = producao['Sistema Integrado'].tolist()
municipio = distribuicao['Municipio'].unique().tolist()

# parametros 

pe = {
    (col.strip(), row['Mes']): row[col]
    for _, row in energia.iterrows()
    for col in energia.columns if col != 'Mes' 
}

pt = {
    (col.strip(), row['Mes']): row[col]
    for _, row in tratamento.iterrows()
    for col in tratamento.columns if col != 'Mes' 
}

S = {}
for _, i in producao.iterrows():
    sys, vol = i['Sistema Integrado'], i['Volume Maximo']   
    S[sys] = vol

D = {}
for _, i in demanda.iterrows():
    mes, vol = i['Mes'], i['Volume Minimo']   
    D[mes] = vol

v = {}
for _, i in distribuicao.iterrows():
    sys, mun, vol = i['Sistema Integrado'], i['Municipio'], i['Volume Maximo'] 
    v[(sys,mun)] = vol







