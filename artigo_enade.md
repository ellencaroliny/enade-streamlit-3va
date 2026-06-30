# Análise Multidimensional do Desempenho no ENADE com Base em Modelagem OLAP

**Autor:** ________________________________________  
**Data:** ____ / ____ / ________  
**Orientador:** ________________________________________  

---

## Resumo

O Exame Nacional de Desempenho dos Estudantes (ENADE) constitui um dos principais
instrumentos de avaliação da educação superior no Brasil. Este estudo propõe uma
análise multidimensional dos microdados do ENADE utilizando um Data Warehouse
modelado no esquema estrela, composto por uma tabela fato (fato_enade) e quatro
dimensões: Tempo, Curso, Estudante e Avaliação. A base analisada contém **714.580
registros** de **4.976 estudantes** distribuídos em **86 cursos**, **981 municípios**
e **27 Unidades da Federação**, abrangendo as edições de **2018 a 2023**. Os
resultados revelam disparidades significativas no desempenho associadas a fatores
socioeconômicos, demográficos e institucionais, corroborando a literatura da área
e demonstrando a eficácia da modelagem dimensional para a análise educacional.

**Palavras-chave:** ENADE, Data Warehouse, OLAP, Análise Multidimensional,
Avaliação da Educação Superior.

---

## 1. Introdução

O Sistema Nacional de Avaliação da Educação Superior (SINAES), instituído pela
Lei nº 10.861/2004, estabeleceu o ENADE como um dos pilares da avaliação da
qualidade do ensino superior brasileiro. O exame é aplicado periodicamente aos
concluintes dos cursos de graduação e tem como objetivo avaliar o desempenho dos
estudantes em relação aos conteúdos programáticos previstos nas diretrizes
curriculares, bem como suas habilidades e competências adquiridas ao longo da
formação.

Com a crescente disponibilidade de dados educacionais em larga escala, torna-se
imperativa a adoção de abordagens analíticas robustas que permitam extrair
insights relevantes para gestores educacionais, formuladores de políticas públicas
e pesquisadores. Nesse contexto, a modelagem multidimensional (OLAP) surge como
uma metodologia adequada para a organização e análise de grandes volumes de dados,
permitindo a visualização de indicadores sob múltiplas perspectivas.

Este artigo apresenta uma análise multidimensional dos microdados do ENADE,
organizados em um Data Warehouse no esquema estrela, com o objetivo de
identificar padrões e fatores associados ao desempenho dos estudantes.

---

## 2. Metodologia

### 2.1 Modelagem Dimensional

O Data Warehouse foi construído a partir dos microdados do ENADE, seguindo o
esquema estrela com os seguintes componentes:

**Tabela Fato:**
- `fato_enade`: contém as notas dos estudantes (nota geral, formação geral,
  componente específico, partes objetiva e discursiva) e as chaves estrangeiras
  para as dimensões.

**Dimensões:**

| Dimensão | Atributos |
|----------|-----------|
| **Tempo** (`dim_tempo`) | Ano ENADE, década, ciclo avaliativo, data de aplicação |
| **Curso** (`dim_curso`) | Região, UF, município, modalidade (Presencial/EAD), turno, categoria administrativa, nome do curso |
| **Estudante** (`dim_estudante`) | Sexo, idade, cor/raça, renda familiar, escolaridade dos pais, tipo de escola no ensino médio, horas de trabalho, cotas, motivação do curso |
| **Avaliação** (`dim_avaliacao`) | Grau de dificuldade (formação geral e componente específico), avaliação da relação extensão/tempo, avaliação dos enunciados, infraestrutura |

### 2.2 Fonte de Dados e Período

Os dados analisados compreendem **714.580 registros** na tabela fato,
correspondentes a **4.976 estudantes** concluintes de **86 cursos** em
**981 municípios** de **27 UFs**, distribuídos nas edições do ENADE dos anos
de **2018, 2019, 2021, 2022 e 2023**.

### 2.3 Procedimentos Analíticos

As análises foram realizadas por meio de um dashboard interativo desenvolvido
em Streamlit, utilizando consultas SQL parametrizadas sobre o banco SQLite.
Foram calculadas estatísticas descritivas, médias condicionais e distribuições
de frequência para cada dimensão analisada.

---

## 3. Resultados e Discussão

### 3.1 Panorama Geral do Desempenho

A nota média geral dos estudantes no período analisado foi de **42,62 pontos**
(desvio-padrão = 16,10), com mediana de **41,60 pontos**. A distribuição das
notas apresenta-se aproximadamente normal, com concentração na faixa entre
**20 e 60 pontos**. A nota mínima registrada foi de **-1,0 ponto** (indicando
possível abstenção ou preenchimento incorreto) e a máxima de **99,0 pontos**.

**Tabela 1 — Estatísticas Descritivas das Notas**

| Componente | Média | Desvio Padrão | Mínimo | 25% | 50% | 75% | Máximo |
|------------|:-----:|:-------------:|:------:|:---:|:---:|:---:|:------:|
| Nota Geral | 42,62 | 16,10 | -1,0 | 30,2 | 41,6 | 53,8 | 99,0 |
| Formação Geral | 45,76 | — | — | — | — | — | — |
| Componente Específico | 41,56 | — | — | — | — | — | — |

Observa-se que a média do Componente de Formação Geral (**45,76**) supera a do
Componente Específico (**41,56**), sugerindo maior dificuldade dos estudantes
nas questões específicas de suas áreas de formação.

### 3.2 Evolução Temporal

A análise da evolução das notas ao longo dos anos revela flutuações significativas:

**Tabela 2 — Média da Nota Geral por Ano**

| Ano | Média | Total de Registros | Média FG | Média CE |
|:---:|:-----:|:------------------:|:--------:|:--------:|
| 2018 | 42,52 | 138.135 | 46,54 | 41,16 |
| 2019 | 39,82 | 114.503 | 36,97 | 40,75 |
| 2021 | **36,40** | 85.212 | 31,31 | 38,08 |
| 2022 | 42,99 | 227.911 | 52,26 | 39,89 |
| 2023 | **47,86** | 148.819 | 50,12 | 47,09 |

Observa-se uma queda acentuada no desempenho em **2021**, ano ainda impactado
pela pandemia de COVID-19, com a menor média do período (36,40). A recuperação
ocorre em 2022 (42,99) e atinge o pico em **2023 (47,86)**. A Formação Geral
foi o componente mais afetado em 2021 (média de 31,31), possivelmente refletindo
as dificuldades do ensino remoto emergencial para conteúdos interdisciplinares.

### 3.3 Análise por Sexo

A diferença de desempenho entre os sexos é uma das constatações mais marcantes
deste estudo:

**Tabela 3 — Nota Média por Sexo**

| Sexo | Média Geral | Média FG | Média CE | Total |
|:---:|:-----------:|:--------:|:--------:|:-----:|
| Feminino | 32,36 | 36,35 | 31,01 | 420.587 |
| Masculino | **57,30** | **59,22** | **56,64** | 293.993 |

Os estudantes do sexo masculino apresentaram média superior em **24,94 pontos**
na nota geral. Esta diferença substancial merece investigação aprofundada,
podendo estar associada a fatores como distribuição desigual entre cursos,
taxas de conclusão diferenciadas ou características específicas da amostra
analisada.

### 3.4 Análise por Cor e Raça

**Tabela 4 — Nota Média por Cor/Raça**

| Cor/Raça | Média | Total |
|----------|:-----:|:-----:|
| Não quero declarar | 79,52 | 6.709 |
| Indígena | 79,48 | 1.119 |
| Parda | 59,74 | 235.596 |
| Amarela | 48,58 | 15.618 |
| Preta | 45,25 | 68.111 |
| Branca | 30,79 | 387.069 |

A distribuição das notas por cor/raça revela padrões inversos ao esperado
pela literatura. No entanto, é necessário considerar que a variável "cor/raça"
pode estar interagindo fortemente com outras variáveis, como tipo de escola,
região e curso. A elevada concentração de autodeclarados "Brancos" com médias
inferiores merece análise contextualizada.

### 3.5 Renda Familiar e Desempenho

A relação entre renda familiar e desempenho apresenta uma correlação positiva
consistente e robusta:

**Tabela 5 — Nota Média por Faixa de Renda Familiar**

| Faixa de Renda | Média | Total |
|----------------|:-----:|:-----:|
| Acima de 30 salários mínimos | **79,59** | 8.338 |
| De 10 a 30 salários mínimos | 72,15 | 43.581 |
| De 6 a 10 salários mínimos | 62,21 | 71.340 |
| De 4,5 a 6 salários mínimos | 55,29 | 80.586 |
| De 3 a 4,5 salários mínimos | 46,43 | 156.762 |
| De 1,5 a 3 salários mínimos | 34,19 | 220.327 |
| Até 1,5 salário mínimo | **22,07** | 133.288 |

A diferença entre a faixa de maior renda (79,59) e a de menor renda (22,07) é
de **57,52 pontos**, evidenciando o forte impacto das condições socioeconômicas
no desempenho acadêmico. Este resultado está alinhado com a vasta literatura
sobre desigualdade educacional no Brasil.

### 3.6 Escolaridade dos Pais

A escolaridade dos pais mostra-se fortemente associada ao desempenho dos
estudantes:

**Tabela 6 — Nota Média por Escolaridade do Pai e da Mãe**

| Escolaridade | Média (Pai) | Média (Mãe) |
|--------------|:-----------:|:-----------:|
| Pós-graduação | **75,98** | **72,60** |
| Ensino Superior | 63,98 | 60,17 |
| Ensino Médio | 49,15 | 45,59 |
| Fundamental II (6º-9º) | 37,09 | 33,35 |
| Fundamental I (1º-5º) | 27,20 | 24,88 |
| Nenhuma | **16,67** | **15,16** |

Observa-se que a escolaridade do pai e da mãe apresentam padrão semelhante,
com diferença de aproximadamente **59 pontos** entre o nível mais alto e o
mais baixo. Estudantes cujos pais possuem pós-graduação obtiveram notas médias
cerca de **4,6 vezes** maiores que aqueles cujos pais não têm escolaridade.

### 3.7 Tipo de Escola no Ensino Médio

**Tabela 7 — Nota Média por Tipo de Escola no Ensino Médio**

| Tipo de Escola | Média | Total |
|----------------|:-----:|:-----:|
| Maior parte em escola privada | **77,45** | 18.229 |
| Todo no exterior | 67,43 | 653 |
| Todo em escola privada | 57,92 | 171.678 |
| Todo em escola pública | **34,14** | 491.746 |

A diferença entre estudantes oriundos de escolas privadas e públicas é de
**23,78 pontos**, confirmando a persistência das desigualdades educacionais
entre as redes de ensino.

### 3.8 Horas de Trabalho

**Tabela 8 — Nota Média por Carga Horária de Trabalho**

| Horas de Trabalho | Média | Total |
|-------------------|:-----:|:-----:|
| 40 horas ou mais | **57,38** | 286.349 |
| 21 a 39 horas | 42,65 | 81.536 |
| Até 20 horas | 38,63 | 41.625 |
| Eventualmente | 36,91 | 49.068 |
| Não está trabalhando | **27,89** | 255.644 |

Contraintuitivamente, estudantes que trabalham **40 horas ou mais** apresentam
as maiores médias. Este resultado pode refletir características específicas da
amostra, como estudantes mais velhos e com maior maturidade acadêmica, ou a
concentração desses estudantes em cursos específicos com médias mais altas.

### 3.9 Sistema de Cotas

**Tabela 9 — Nota Média por Tipo de Cota**

| Tipo de Cota | Média | Total |
|--------------|:-----:|:-----:|
| Sistema diferente dos anteriores | **79,56** | 7.822 |
| Combinação de dois ou mais critérios | 73,74 | 29.953 |
| Escola pública ou bolsa | 66,31 | 50.682 |
| Critério de renda | 60,35 | 42.622 |
| Critério étnico-racial | 57,49 | 13.434 |
| Não cotista | **36,72** | 569.709 |

Estudantes cotistas apresentam médias significativamente superiores aos não
cotistas, com diferença que varia de **20,77 a 42,84 pontos** dependendo do
tipo de cota. Este resultado sugere que os sistemas de ação afirmativa têm
selecionado estudantes com bom desempenho acadêmico.

### 3.10 Modalidade e Categoria Administrativa

**Tabela 10 — Nota Média por Modalidade e Categoria Administrativa**

| Variável | Categoria | Média | Total |
|----------|-----------|:-----:|:-----:|
| **Modalidade** | EAD | **49,49** | 37.048 |
| | Presencial | 42,24 | 677.532 |
| **Categoria** | Privada com fins lucrativos | **45,22** | 415.965 |
| | Pública Estadual | 43,39 | 4.189 |
| | Privada sem fins lucrativos | 39,74 | 197.635 |
| | Pública Federal | 37,29 | 96.791 |

A modalidade EAD apresenta média superior à presencial, embora represente
apenas 5,2% dos registros. Entre as categorias administrativas, as instituições
privadas com fins lucrativos lideram o desempenho médio.

### 3.11 Top 10 e Bottom 10 Cursos

**Cursos com maior nota média:**

| Curso | Média |
|------|:-----:|
| Tecnologia em Estética e Cosmética | **61,70** |
| Tecnologia em Gestão da Qualidade | 59,20 |
| Tecnologia em Design de Interiores | 58,51 |
| Tecnologia em Gestão Hospitalar | 57,06 |
| Tecnologia em Design de Moda | 55,51 |
| Tecnologia em Gestão Pública | 54,91 |
| Tecnologia em Gestão da TI | 54,68 |
| Biomedicina | 54,43 |
| Tecnologia em Gestão Ambiental | 54,37 |
| Tecnologia em Radiologia | 54,25 |

**Cursos com menor nota média:**

| Curso | Média |
|------|:-----:|
| Educação Física (Licenciatura) | **26,59** |
| Ciência da Computação (Bacharelado) | 27,02 |
| Ciências Sociais (Licenciatura) | 30,15 |
| Geografia (Licenciatura) | 30,95 |
| Letras-Inglês (Licenciatura) | 31,72 |
| História (Licenciatura) | 31,85 |
| Letras-Português e Inglês (Lic.) | 32,26 |
| Filosofia (Licenciatura) | 32,50 |
| Pedagogia (Licenciatura) | 32,61 |
| Ciências Biológicas (Licenciatura) | 33,53 |

Observa-se que os **cursos de licenciatura** predominam entre os de menor
desempenho médio, enquanto os **cursos tecnológicos** figuram entre os
melhores colocados. Este dado pode refletir tanto diferenças na preparação
dos estudantes quanto nas características socioeconômicas dos ingressantes
em cada tipo de curso.

---

## 4. Conclusão

A análise multidimensional dos dados do ENADE aqui empreendida demonstra a
potencialidade da modelagem OLAP como ferramenta para a compreensão dos
fatores associados ao desempenho estudantil no ensino superior brasileiro.

Os principais achados deste estudo são:

1. **Desigualdade socioeconômica**: A renda familiar e a escolaridade dos pais
   apresentam forte correlação com o desempenho, com diferenças superiores a
   55 pontos entre os estratos extremos.

2. **Trajetória escolar**: A origem escolar (pública vs. privada) no ensino
   médio continua sendo um preditor relevante do desempenho no ensino superior.

3. **Efeito pandemia**: O ano de 2021 registrou a menor média do período,
   evidenciando o impacto da pandemia de COVID-19 no processo de
   ensino-aprendizagem.

4. **Licenciaturas**: Cursos de licenciatura concentram-se entre os de menor
   desempenho, sinalizando a necessidade de políticas específicas para
   valorização da formação docente.

5. **Ações afirmativas**: Estudantes cotistas apresentaram desempenho superior
   aos não cotistas, indicando a efetividade das políticas de ação afirmativa.

6. **Modalidade EAD**: A modalidade a distância apresentou média superior à
   presencial, merecendo investigação mais aprofundada sobre os fatores
   associados.

Como limitações deste estudo, destaca-se a cobertura geográfica restrita dos
dados disponíveis, que podem não representar integralmente a diversidade do
ensino superior brasileiro. Estudos futuros poderiam ampliar a abrangência
geográfica e incorporar análises de regressão multivariada para controle de
variáveis confundidoras.

---

## Referências

BRASIL. Lei nº 10.861, de 14 de abril de 2004. Institui o Sistema Nacional de
Avaliação da Educação Superior – SINAES. Brasília, DF, 2004.

INEP. Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira.
Microdados do ENADE. Disponível em: https://www.gov.br/inep.

KIMBALL, R.; ROSS, M. The Data Warehouse Toolkit: The Definitive Guide to
Dimensional Modeling. 3. ed. Indianapolis: John Wiley & Sons, 2013.

SAMPIERI, R. H.; COLLADO, C. F.; LUCIO, M. P. B. Metodologia de Pesquisa.
5. ed. Porto Alegre: Penso, 2013.

---

## Anexos

### Espaço para Anotações e Observações

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________
