# 📊 ENADE Streamlit - Análise Multidimensional

Dashboard interativo para análise dos dados do ENADE (Exame Nacional de Desempenho dos Estudantes) utilizando modelagem dimensional (Data Warehouse em esquema estrela).

## 🎯 Características

- **Modelagem Dimensional**: Esquema estrela com tabela fato e 4 dimensões
- **Análises Interativas**: Filtros dinâmicos por ano, região, curso, perfil de estudante
- **Visualizações**: Gráficos interativos com Plotly
- **Performance**: Cache de queries para melhor desempenho

## 📁 Estrutura do Projeto

```
enade-streamlit-3va/
├── app.py                  # Aplicação Streamlit principal
├── requirements.txt        # Dependências Python
├── prepare_data.py         # Script de preparação de dados
├── Create_DW.sql          # SQL de criação do Data Warehouse
├── enade_dw.db            # Banco SQLite (não incluído no Git - 88 MB)
└── README.md              # Este arquivo
```

## ⚙️ Instalação e Execução Local

### 1. Clone o repositório

```bash
git clone https://github.com/ellencaroliny/enade-streamlit-3va.git
cd enade-streamlit-3va
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. **IMPORTANTE**: Obtenha o banco de dados

O arquivo `enade_dw.db` (~88 MB) não está incluído no repositório Git devido ao seu tamanho.

**Opções:**
- Solicite o arquivo diretamente aos mantenedores do projeto
- Se você tem os dumps SQL originais, execute `prepare_data.py` para gerar o banco

### 4. Execute a aplicação

```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

## 📊 Dados

- **Total de registros**: 714.580
- **Anos disponíveis**: 2018, 2019, 2021, 2022, 2023
- **Dimensões**:
  - `dim_tempo`: Ano ENADE, década, ciclo
  - `dim_curso`: Região, UF, município, modalidade, categoria
  - `dim_estudante`: Sexo, idade, cor/raça, renda, escolaridade
  - `dim_avaliacao`: Dificuldade da prova, tempo, avaliação

## 🚀 Deploy no Streamlit Cloud

⚠️ **Atenção**: O banco de dados SQLite precisa estar disponível para a aplicação funcionar.

**Opções para deploy:**

1. **Incluir o banco no Git** (se < 100 MB):
   ```bash
   # Remover do .gitignore
   git add enade_dw.db
   git commit -m "Add database for deployment"
   git push
   ```

2. **Usar armazenamento externo**:
   - AWS S3
   - Google Drive com acesso público
   - GitHub LFS (Large File Storage)

3. **Gerar banco dinamicamente** (mais lento no primeiro acesso):
   - Incluir os dumps SQL no repositório
   - Executar `prepare_data.py` na inicialização

## 🛠️ Tecnologias

- **Python 3.8+**
- **Streamlit**: Framework web para data apps
- **Pandas**: Manipulação de dados
- **Plotly**: Visualizações interativas
- **SQLite**: Banco de dados

## 📝 Licença

Este projeto foi desenvolvido para fins acadêmicos.

