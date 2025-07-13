# Otimização da Distribuição de Água na Região Metropolitana do Recife

Este projeto implementa um modelo de programação linear para otimizar a distribuição de água na Região Metropolitana do Recife (RMR), Brasil. O objetivo é determinar a alocação de água de múltiplos sistemas de abastecimento para diversos municípios, minimizando os custos operacionais de energia elétrica e tratamento químico.

O modelo e os dados são baseados na tese de doutorado de Lidia Maria Alves Rodella, da Universidade Federal de Pernambuco (UFPE).

## Descrição do Problema

A Companhia Pernambucana de Saneamento (COMPESA) opera nove sistemas integrados de abastecimento que atendem dez municípios da RMR. A operação dessa complexa rede gera custos significativos, especialmente com energia elétrica (para bombeamento) e produtos químicos (para tratamento).

Este projeto busca fornecer uma ferramenta de apoio à decisão que encontre a estratégia de distribuição mais econômica, respeitando todas as restrições físicas e operacionais do sistema, como a capacidade de produção de cada usina, a capacidade de fluxo das tubulações e a garantia de um abastecimento mínimo para cada cidade.

## Modelo de Otimização

O problema é formulado como um modelo de Programação Linear, implementado em Python utilizando a biblioteca **Pyomo**.

* **Função Objetivo:** Minimizar o custo total anual, que é a soma dos custos de energia e tratamento em todos os sistemas e meses.

    `Minimizar Σ (Custo_Energia + Custo_Tratamento)`

* **Variáveis de Decisão:**
    * `x[i, j, t]`: Volume de água (m³) distribuído pelo sistema `i` para o município `j` no mês `t`.

* **Restrições Principais:**
    1.  **Capacidade de Produção:** O volume total de água distribuído por um sistema em um mês não pode exceder sua capacidade máxima de produção.
    2.  **Distribuição Mínima por Município:** A soma da água recebida por um município de todos os sistemas deve ser maior ou igual a uma demanda mínima mensal para aquele município.
    3.  **Fluxo Máximo na Rede:** O volume de água enviado de um sistema específico para um município específico é limitado pela capacidade da tubulação que os conecta.
    4.  **Volume Mínimo Total:** O volume total distribuído por todos os sistemas em um mês deve atender a uma meta mínima geral para toda a região.

## Estrutura do Diretório

Para que o código funcione corretamente, os arquivos devem seguir a seguinte estrutura:

```
/projeto-otimizacao-agua
|-- /dados
|   |-- dados.xlsx
|-- alocation_model.py
|-- requirements.txt
|-- README.md
```

## Requisitos e Instalação

Este projeto requer Python 3.x e as bibliotecas listadas no arquivo `requirements.txt`. Além disso, é necessário um solver de otimização, como o **Gurobi**, que deve ser instalado separadamente.

1.  **Instale o Gurobi Solver:**
    Siga as instruções de instalação no [site oficial do Gurobi](https://www.gurobi.com/downloads/gurobi-software/). Uma licença acadêmica gratuita está disponível.

2.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/projeto-otimizacao-agua.git](https://github.com/seu-usuario/projeto-otimizacao-agua.git)
    cd projeto-otimizacao-agua
    ```

3.  **Crie um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

4.  **Instale as dependências Python:**
    ```bash
    pip install -r requirements.txt
    ```

**Conteúdo do `requirements.txt`:**
```
pandas
pyomo
gurobipy
```

## Estrutura dos Dados

O modelo requer um arquivo Excel chamado `dados.xlsx` dentro da pasta `/dados`.

## Como Executar o Modelo

Certifique-se de que todos os requisitos estão instalados e que o arquivo `dados.xlsx` está corretamente formatado e localizado. Em seguida, execute o script a partir do terminal:

```bash

python alocation_model.py

````
O script irá carregar os dados, construir o modelo de otimização, resolver o problema usando o Gurobi e imprimir os resultados no console. Modificações podem ser feitas no final do script para salvar os resultados em um arquivo.
Se não tiver o Gurobi, utilize o Highs, que é open source. 

```
import highspy

solver = SolverFactory('highs')
solver.solve(model)
```

### Citação
Este trabalho é uma implementação computacional baseada na metodologia e nos dados apresentados na seguinte tese:

RODELLA, Lidia Maria Alves. Modelo de programação linear para apoio a decisão na distribuição de água de sistemas integrados de abastecimento. Tese (Doutorado em Economia) – Universidade Federal de Pernambuco, Recife, 2014. Disponível em: https://repositorio.ufpe.br/handle/123456789/12585.

### Licença:
Este projeto está licenciado sob a Licença MIT.
