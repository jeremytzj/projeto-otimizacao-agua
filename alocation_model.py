import pandas as pd

energia = pd.read_excel("./dados/dados.xlsx", sheet_name= "custo_energia")
tratamento = pd.read_excel("./dados/dados.xlsx", sheet_name="custo_tratamento")
producao = pd.read_excel("./dados/dados.xlsx", sheet_name="producao_maxima")
demanda = pd.read_excel("./dados/dados.xlsx", sheet_name="demanda_minima")
distribuicao = pd.read_excel("./dados/dados.xlsx", sheet_name="distribuicao_maxima")
demanda_municipio = pd.read_excel('./dados/dados.xlsx', sheet_name="demanda_municipios")

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

D = {
    (row['Municipio'], col) : row[col]
    for _, row in demanda_municipio.iterrows()
    for col in demanda_municipio.columns if col != 'Municipio' 
}

d = {}
for _,i in demanda.iterrows():
    d[i["Mes"]] = i["Volume Minimo"]
d


v = {}
for _, i in distribuicao.iterrows():
    sys, mun, vol = i['Sistema Integrado'], i['Municipio'], i['Volume Maximo'] 
    v[(sys,mun)] = vol

v

# inicializa o modelo

from pyomo.environ import *

model = ConcreteModel()

#conjuntos
model.T = Set(initialize=meses)
model.I = Set(initialize=sistemas)
model.J = Set(initialize=municipio)

#parametros
model.pe = Param(model.I, model.T, initialize=pe)
model.pt = Param(model.I, model.T, initialize=pt)
model.S = Param(model.I, initialize=S)
model.D = Param(model.J, model.T, initialize=D, default = 0)
model.v = Param(model.I, model.J, initialize=v, default = 0)
model.d = Param(model.T, initialize=d)

#variaveis de decisao
model.x = Var(model.I, model.J, model.T, domain=NonNegativeReals)



# funcao objetiva
def obj(model):
    return sum(model.x[i,j,t]*(model.pe[i,t] + model.pt[i,t])for i in model.I for j in model.J for t in model.T)

model.obj = Objective(rule=obj, sense=minimize)

#restricoes
model.producao = ConstraintList()
for i in model.I:
    for t in model.T:
        model.producao.add(expr=sum(model.x[i,j,t] for j in model.J) <= model.S[i])

model.distribuicao = ConstraintList()
for j in model.J:
    for t in model.T:
        model.distribuicao.add(expr=sum(model.x[i,j,t] for i in model.I) >= model.D[j,t]) 

model.fluxo_maximo = ConstraintList()
for i in model.I:
    for j in model.J:
        for t in model.T:
            model.fluxo_maximo.add(expr=model.x[i,j,t] <= model.v[i,j])

model.volume_minimo = ConstraintList()
for t in model.T:    
    model.volume_minimo.add(expr=sum(model.x[i,j,t] for i in model.I for j in model.J) >= model.d[t])


#resolvendo o modelo

import gurobipy

solver = SolverFactory('gurobi')
results = solver.solve(model)


# --- 4. RESOLUÇÃO DO MODELO ---
results = solver.solve(model)

status = results.solver.termination_condition
if status == TerminationCondition.optimal or status == TerminationCondition.feasible:
    print(f"Custo Total Mínimo: R$ {value(model.obj):,.2f}")
else:
    print("Modelo inviável — pulando impressão do objetivo.")




with pd.ExcelWriter('./dados/distribuicao.xlsx', engine='openpyxl') as writer:
    x_list = []
    for i in model.I:
        for j in model.J:
            for t in model.T:
                if (i, j, t) in model.x:
                    x_list.append({
                        'Sistema': i,
                        'Municipio': j,
                        'Mes': t,
                        'Fluxo': model.x[i, j, t].value
                    })
    df_x = pd.DataFrame(x_list)
    df_x.to_excel(writer, sheet_name='Distribuicao de agua', index=False)