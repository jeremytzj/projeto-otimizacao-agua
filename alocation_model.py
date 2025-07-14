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

# model.volume_minimo = ConstraintList()
# for t in model.T:    
#     model.volume_minimo.add(expr=sum(model.x[i,j,t] for i in model.I for j in model.J) >= model.d[t])


#resolvendo o modelo

import gurobipy

model.dual = Suffix(direction=Suffix.IMPORT)
solver = SolverFactory('gurobi')
results = solver.solve(model)


status = results.solver.termination_condition
if status not in (TerminationCondition.optimal,
                  TerminationCondition.feasible):
    raise RuntimeError(f'Modelo ainda inviável: {status}')

print(f'Custo ótimo: R$ {value(model.obj):,.2f}')


custo_tratamento = 0
custo_energia = 0

with pd.ExcelWriter('./dados/distribuicao.xlsx', engine='openpyxl') as writer:
    x_list = []
    for i in model.I:
        for j in model.J:
            for t in model.T:
                if (i, j, t) in model.x:
                    value = model.x[i, j, t].value
                    custo_tratamento += value*model.pt[i, t]
                    custo_energia += value*model.pe[i, t]
                    x_list.append({
                        'Sistema': i,
                        'Municipio': j,
                        'Mes': t,
                        'Fluxo': value
                    })
                    

    df_x = pd.DataFrame(x_list)
    df_x.to_excel(writer, sheet_name='Distribuicao de agua', index=False)


print(f"Custo total com produtos químicos para tratamento: R${custo_tratamento:.2f}")
print(f"Custo total com energia elétrica: R${custo_energia:.2f}")

custo_real = 47213697.77

print(f"Redução de {(custo_real - custo_otimizado)*100/custo_real :.2f}% (R${custo_real - custo_otimizado :.2f}) nos custos")




print("="*60)
print("ANÁLISE DE SENSIBILIDADE")
print("="*60)

# 1. VARIÁVEIS DUAIS (Shadow Prices) das Restrições
print("\n1. VARIÁVEIS DUAIS (Shadow Prices):")
print("-" * 40)

duais_producao = []
duais_distribuicao = []
duais_fluxo_maximo = []

# Duais das restrições de produção
for i, constraint in enumerate(model.producao.values()):
    if constraint.active:
        dual_value = model.dual[constraint]
        # Identificar sistema e mês baseado no índice
        sistema_idx = i // len(model.T)
        mes_idx = i % len(model.T)
        sistema = list(model.I)[sistema_idx]
        mes = list(model.T)[mes_idx]
        
        duais_producao.append({
            'Sistema': sistema,
            'Mes': mes,
            'Dual_Producao': dual_value,
            'Interpretacao': f'Redução de R$ {dual_value:.4f} no custo por unidade adicional de capacidade produtiva'
        })

# Duais das restrições de distribuição (demanda)
for i, constraint in enumerate(model.distribuicao.values()):
    if constraint.active:
        dual_value = model.dual[constraint]
        # Identificar município e mês baseado no índice
        municipio_idx = i // len(model.T)
        mes_idx = i % len(model.T)
        municipio = list(model.J)[municipio_idx]
        mes = list(model.T)[mes_idx]
        
        duais_distribuicao.append({
            'Municipio': municipio,
            'Mes': mes,
            'Dual_Demanda': dual_value,
            'Interpretacao': f'Aumento de R$ {dual_value:.4f} no custo por unidade adicional de demanda'
        })

# Duais das restrições de fluxo máximo
for i, constraint in enumerate(model.fluxo_maximo.values()):
    if constraint.active:
        dual_value = model.dual[constraint]
        if abs(dual_value) > 1e-6:  # Apenas duais significativos
            # Identificar sistema, município e mês baseado no índice
            total_combinations = len(model.I) * len(model.J) * len(model.T)
            ij_combinations = len(model.I) * len(model.J)
            
            mes_idx = i // ij_combinations
            remaining = i % ij_combinations
            sistema_idx = remaining // len(model.J)
            municipio_idx = remaining % len(model.J)
            
            sistema = list(model.I)[sistema_idx]
            municipio = list(model.J)[municipio_idx]
            mes = list(model.T)[mes_idx]
            
            duais_fluxo_maximo.append({
                'Sistema': sistema,
                'Municipio': municipio,
                'Mes': mes,
                'Dual_Fluxo_Max': dual_value,
                'Interpretacao': f'Redução de R$ {-dual_value:.4f} no custo por unidade adicional de capacidade de fluxo'
            })

# 2. VARIÁVEIS DE FOLGA (Slack Variables)
print("\n2. VARIÁVEIS DE FOLGA:")
print("-" * 40)

folgas_producao = []
folgas_distribuicao = []
folgas_fluxo_maximo = []

# Folgas das restrições de produção
for i, constraint in enumerate(model.producao.values()):
    if constraint.active:
        # Calcular folga: RHS - LHS
        sistema_idx = i // len(model.T)
        mes_idx = i % len(model.T)
        sistema = list(model.I)[sistema_idx]
        mes = list(model.T)[mes_idx]
        
        capacidade_total = model.S[sistema]
        uso_atual = sum(model.x[sistema, j, mes].value for j in model.J if (sistema, j, mes) in model.x)
        folga = capacidade_total - uso_atual
        
        folgas_producao.append({
            'Sistema': sistema,
            'Mes': mes,
            'Capacidade_Total': capacidade_total,
            'Uso_Atual': uso_atual,
            'Folga_Producao': folga,
            'Utilizacao_%': (uso_atual/capacidade_total)*100 if capacidade_total > 0 else 0
        })

# Folgas das restrições de distribuição (demanda)
for i, constraint in enumerate(model.distribuicao.values()):
    if constraint.active:
        municipio_idx = i // len(model.T)
        mes_idx = i % len(model.T)
        municipio = list(model.J)[municipio_idx]
        mes = list(model.T)[mes_idx]
        
        demanda_minima = model.D[municipio, mes]
        fornecimento_atual = sum(model.x[i, municipio, mes].value for i in model.I if (i, municipio, mes) in model.x)
        folga = fornecimento_atual - demanda_minima
        
        folgas_distribuicao.append({
            'Municipio': municipio,
            'Mes': mes,
            'Demanda_Minima': demanda_minima,
            'Fornecimento_Atual': fornecimento_atual,
            'Folga_Demanda': folga,
            'Atendimento_%': (fornecimento_atual/demanda_minima)*100 if demanda_minima > 0 else 0
        })

# Folgas das restrições de fluxo máximo
for i in model.I:
    for j in model.J:
        for t in model.T:
            if (i, j, t) in model.x:
                fluxo_atual = model.x[i, j, t].value
                capacidade_max = model.v[i, j]
                folga = capacidade_max - fluxo_atual
                
                if capacidade_max > 0:  # Apenas para conexões válidas
                    folgas_fluxo_maximo.append({
                        'Sistema': i,
                        'Municipio': j,
                        'Mes': t,
                        'Capacidade_Max': capacidade_max,
                        'Fluxo_Atual': fluxo_atual,
                        'Folga_Fluxo': folga,
                        'Utilizacao_%': (fluxo_atual/capacidade_max)*100
                    })

# 3. EXPORTAR RESULTADOS PARA EXCEL
print("\n3. EXPORTANDO RESULTADOS PARA ANÁLISE...")
print("-" * 40)

with pd.ExcelWriter('./dados/analise_sensibilidade.xlsx', engine='openpyxl') as writer:
    # Variáveis Duais
    if duais_producao:
        df_duais_prod = pd.DataFrame(duais_producao)
        df_duais_prod.to_excel(writer, sheet_name='Duais_Producao', index=False)
    
    if duais_distribuicao:
        df_duais_dist = pd.DataFrame(duais_distribuicao)
        df_duais_dist.to_excel(writer, sheet_name='Duais_Demanda', index=False)
    
    if duais_fluxo_maximo:
        df_duais_fluxo = pd.DataFrame(duais_fluxo_maximo)
        df_duais_fluxo.to_excel(writer, sheet_name='Duais_Fluxo_Max', index=False)
    
    # Variáveis de Folga
    if folgas_producao:
        df_folgas_prod = pd.DataFrame(folgas_producao)
        df_folgas_prod.to_excel(writer, sheet_name='Folgas_Producao', index=False)
    
    if folgas_distribuicao:
        df_folgas_dist = pd.DataFrame(folgas_distribuicao)
        df_folgas_dist.to_excel(writer, sheet_name='Folgas_Demanda', index=False)
    
    if folgas_fluxo_maximo:
        df_folgas_fluxo = pd.DataFrame(folgas_fluxo_maximo)
        df_folgas_fluxo.to_excel(writer, sheet_name='Folgas_Fluxo_Max', index=False)

# 4. RELATÓRIO RESUMIDO
print("\n4. RELATÓRIO RESUMIDO:")
print("-" * 40)

# Recursos mais críticos (menor folga)
print("RECURSOS MAIS CRÍTICOS (menor folga):")
if folgas_producao:
    df_prod = pd.DataFrame(folgas_producao)
    criticos_prod = df_prod.nsmallest(5, 'Folga_Producao')[['Sistema', 'Mes', 'Folga_Producao', 'Utilizacao_%']]
    print("Produção:")
    print(criticos_prod.to_string(index=False))

if folgas_distribuicao:
    df_dist = pd.DataFrame(folgas_distribuicao)
    criticos_dist = df_dist.nsmallest(5, 'Folga_Demanda')[['Municipio', 'Mes', 'Folga_Demanda', 'Atendimento_%']]
    print("\nDemanda:")
    print(criticos_dist.to_string(index=False))

# Duais mais significativos
print("\nDUAIS MAIS SIGNIFICATIVOS (maior impacto no custo):")
if duais_producao:
    df_duais_p = pd.DataFrame(duais_producao)
    df_duais_p['Dual_Abs'] = abs(df_duais_p['Dual_Producao'])
    top_duais_p = df_duais_p.nlargest(5, 'Dual_Abs')[['Sistema', 'Mes', 'Dual_Producao']]
    print("Produção:")
    print(top_duais_p.to_string(index=False))

if duais_distribuicao:
    df_duais_d = pd.DataFrame(duais_distribuicao)
    df_duais_d['Dual_Abs'] = abs(df_duais_d['Dual_Demanda'])
    top_duais_d = df_duais_d.nlargest(5, 'Dual_Abs')[['Municipio', 'Mes', 'Dual_Demanda']]
    print("\nDemanda:")
    print(top_duais_d.to_string(index=False))

print("\n" + "="*60)
print("ANÁLISE COMPLETA! Verifique o arquivo: './dados/analise_sensibilidade.xlsx'")
print("="*60)

# 5. FUNÇÃO PARA ANÁLISE DE CENÁRIOS
def analise_cenario(parametro, variacao_percentual, tipo='capacidade'):
    """
    Analisa o impacto de mudanças percentuais nos parâmetros
    
    Args:
        parametro: Nome do parâmetro a ser alterado
        variacao_percentual: Percentual de mudança (ex: 10 para +10%)
        tipo: 'capacidade', 'demanda', 'custo_energia', 'custo_tratamento'
    """
    print(f"\nANÁLISE DE CENÁRIO: {tipo} - {parametro} ({variacao_percentual:+.1f}%)")
    print("-" * 50)
    
    # Aqui você pode implementar a lógica para alterar os parâmetros
    # e resolver novamente o modelo para comparar os resultados
    
    # Exemplo básico de estrutura:
    # 1. Salvar valores originais
    # 2. Alterar parâmetros
    # 3. Resolver modelo novamente
    # 4. Comparar resultados
    # 5. Restaurar valores originais
    
    print("Funcionalidade para implementar conforme necessidade específica")

print("\nPara usar a análise de cenários, chame:")
print("analise_cenario('Sistema_A', 10, 'capacidade')")