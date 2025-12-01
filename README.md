# Analytics de POs - Diagnóstico de Prontidão Digital

Esta é minha solução para o case de People Analytics.
Com essa analise conseguimos observar de forma responsiva os gaps atuais e as oportunidades dentro do time para mitigar essas lacunas de skills.


## Link de Deploy

Você pode ver o resultado final da solução do case no link abaixo:


[[Link da solução](https://casepeople.streamlit.app/)]

## Tecnologias Utilizadas

O projeto foi construído utilizando Python e as seguintes bibliotecas principais:

* **Streamlit**: Framework para construção da interface web e dashboard interativo.
* **Pandas**: Manipulação, limpeza e agregação dos dados (ETL).
* **Plotly**: Criação de gráficos interativos e visualização de dados.

## Estrutura de Dados

Para a execução deste case, o conjunto de dados original foi processado e segmentado em dois ficheiros CSV distintos, permitindo uma análise relacional mais eficiente entre a performance atual e as expectativas do cargo:

1.  **Base_Avaliacao.csv**: Contém as notas atribuídas aos colaboradores (avaliações funcionais e matriciais) nas diversas competências.
2.  **Nivel_de_necessidade_po.csv**: Contém a régua de exigência (meta) para cada skill, variando conforme a especialidade do PO.

## Como Executar Localmente 

1.  Clone este repositório.
2.  Instale as dependências listadas no ficheiro `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3.  Certifique-se de que os ficheiros CSV dos dados estão na raiz do diretório.
4.  Execute a aplicação:
    ```bash
    streamlit run app.py
    ```
