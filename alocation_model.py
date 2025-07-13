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

