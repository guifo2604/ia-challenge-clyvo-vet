# CLYVO VET — Serviço de Inteligência Artificial

Serviço de IA da plataforma **CLYVO VET**, desenvolvido para estimar o nível de risco clínico de cães e gatos a partir de informações cadastrais e do histórico do pet. A solução disponibiliza uma API REST, persiste os resultados das predições e oferece interfaces web para tutor e veterinário.

> **Importante:** a classificação gerada pelo modelo é um recurso de apoio à triagem e ao acompanhamento. Ela não substitui avaliação, diagnóstico ou orientação de um médico-veterinário.

## Objetivo

Apoiar o acompanhamento da saúde dos pets por meio de uma classificação preditiva de risco (**baixo risco** ou **alto risco**), apresentando a probabilidade estimada e uma recomendação de acompanhamento.

## Como funciona a IA

O serviço utiliza um modelo de classificação **XGBoost**, treinado previamente e carregado pela aplicação na inicialização. O modelo recebe características do pet e retorna:

- classificação: `Baixo risco` ou `Alto risco`;
- probabilidade estimada de alto risco;
- pontuação percentual;
- recomendação de acompanhamento.

As características utilizadas na inferência são:

- espécie;
- sexo;
- tipo sanguíneo;
- peso;
- idade;
- situação de castração;
- presença de alergia;
- presença de doença crônica;
- quantidade de vacinas registradas.

O pré-processamento organiza essas informações no mesmo formato e na mesma ordem de atributos esperados pelo modelo. A classificação considera o limiar de probabilidade de `0,5` (50%). As recomendações são definidas conforme a probabilidade calculada.

### Faixas de recomendação

- **Abaixo de 50%:** manter a rotina de check-ups e o calendário vacinal em dia.
- **De 50% a menos de 75%:** acompanhamento preventivo, retorno e monitoramento de sintomas.
- **A partir de 75%:** prioridade alta na triagem, com retorno preventivo em curto prazo e revisão do histórico clínico.

Essas faixas representam regras implementadas no serviço e não devem ser interpretadas como diagnóstico médico.

## Arquitetura e integração

O fluxo principal da aplicação é:

1. O tutor e/ou veterinário acessa a interface web.
2. A aplicação consulta e envia informações por meio da API FastAPI.
3. No registro de uma consulta, o backend recupera os dados do pet e as informações da consulta.
4. O serviço transforma os dados para o formato esperado pelo XGBoost e executa a predição.
5. O resultado é armazenado junto à consulta no banco de dados.
6. A interface pode apresentar a classificação, a probabilidade, a recomendação e o histórico de risco.

**Tecnologias e componentes:**

| Componente | Tecnologia |
|---|---|
| API/backend | Python e FastAPI |
| Servidor ASGI | Uvicorn |
| Modelo de IA | XGBoost |
| Manipulação de dados | Pandas e NumPy |
| Validação dos dados | Pydantic |
| Persistência e ORM | SQLAlchemy |
| Banco de dados | Oracle ou SQLite para desenvolvimento/testes |
| Interface web | HTML, CSS e JavaScript |
| Serialização do modelo | Arquivo nativo XGBoost (`.json`) e alternativa com Joblib (`.pkl`) |

## Estrutura do projeto

```text
ia-service/
├── app/
│   ├── db/                 # Conexão, entidades e configuração do banco
│   ├── routers/             # Rotas de cadastro e consultas
│   ├── services/            # Regras de negócio e integração da predição
│   ├── static/              # Interfaces web do tutor e veterinário
│   ├── main.py              # Inicialização da API e rotas principais
│   ├── predictor.py         # Carregamento do XGBoost e inferência
│   ├── schemas.py           # Dados de entrada e saída da IA
│   └── schemas_api.py       # Contratos da API
├── data/                    # Dataset utilizado no projeto
├── model/                   # Modelo treinado e lista de atributos
├── scripts/                 # Scripts de carga e verificação do banco
├── sql/                     # Script de criação do esquema Oracle
├── .env.example             # Exemplo de variáveis de ambiente
└── requirements.txt         # Dependências Python
```

## Requisitos

- Python 3.10 ou superior;
- pip;
- Oracle acessível e credenciais válidas, caso utilize o banco Oracle;
- SQLite pode ser utilizado para desenvolvimento e testes locais.

## Instalação e execução

Os comandos abaixo devem ser executados a partir da pasta `ia-service/`.

### 1. Clonar o repositório e acessar a pasta

```bash
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_REPOSITORIO>/ia-service
```

Se o repositório já contiver diretamente os arquivos deste serviço, entre apenas na pasta correspondente.

### 2. Criar e ativar o ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o banco de dados

Por padrão, se nenhuma configuração for informada, a aplicação utiliza SQLite local no arquivo `clyvo_dev.db`.

Para utilizar Oracle, configure as variáveis de ambiente antes de iniciar a aplicação. Os valores de exemplo estão em `.env.example`; esse arquivo é apenas um modelo e não é carregado automaticamente.

**Windows (PowerShell):**

```powershell
$env:ORACLE_USER="SEU_USUARIO"
$env:ORACLE_PASSWORD="SUA_SENHA"
$env:ORACLE_HOST="oracle.fiap.com.br"
$env:ORACLE_PORT="1521"
$env:ORACLE_SID="orcl"
```

**Linux/macOS:**

```bash
export ORACLE_USER="SEU_USUARIO"
export ORACLE_PASSWORD="SUA_SENHA"
export ORACLE_HOST="oracle.fiap.com.br"
export ORACLE_PORT="1521"
export ORACLE_SID="orcl"
```

Também é possível informar uma URL de conexão por `DATABASE_URL`. Quando definida, ela tem prioridade sobre as variáveis Oracle. Não versione senhas ou credenciais reais no GitHub.

### 5. Criar as tabelas e carregar os dados de exemplo (opcional)

O script abaixo cria as tabelas mapeadas pelo projeto e carrega os registros do arquivo `data/dataset-prontpet.csv`, caso as tabelas ainda estejam vazias:

```bash
python -m scripts.seed_from_csv
```

Para recriar as tabelas e carregar os dados novamente:

```bash
python -m scripts.seed_from_csv --reset
```

**Atenção:** a opção `--reset` apaga e recria as tabelas `CV_*` do projeto no banco configurado. Não a execute em um banco com dados que precisem ser preservados.

O script SQL equivalente para o esquema Oracle está disponível em `sql/oracle_schema.sql`.

### 6. Iniciar a aplicação

```bash
uvicorn app.main:app --reload
```

Após a inicialização, acesse:

- Aplicação principal: http://127.0.0.1:8000/
- Interface do tutor: http://127.0.0.1:8000/tutor
- Interface do veterinário: http://127.0.0.1:8000/vet
- Documentação interativa da API: http://127.0.0.1:8000/docs
- Verificação de saúde da API: http://127.0.0.1:8000/health

## Principais endpoints

| Método | Endpoint | Finalidade |
|---|---|---|
| `GET` | `/health` | Verifica o status da API e informa o modelo carregado e a quantidade de atributos. |
| `POST` | `/predict` | Executa uma predição avulsa, sem persistir uma consulta. |
| `GET` / `POST` | `/tutores` | Lista e cadastra tutores. |
| `GET` | `/tutores/{tutor_id}` | Consulta um tutor. |
| `GET` / `POST` | `/clinicas` | Lista e cadastra clínicas. |
| `GET` / `POST` | `/pets` | Lista e cadastra pets. |
| `GET` | `/pets/{pet_id}` | Consulta um pet. |
| `GET` / `POST` | `/pets/{pet_id}/vacinas` | Lista e registra vacinas de um pet. |
| `POST` | `/consultas` | Registra uma consulta e calcula o risco automaticamente. |
| `GET` | `/consultas/{consulta_id}` | Consulta uma consulta e sua predição. |
| `POST` | `/consultas/{consulta_id}/prever` | Recalcula a predição de uma consulta. |
| `POST` | `/consultas/prever-pendentes` | Calcula predições para consultas ainda sem resultado. |
| `GET` | `/pets/{pet_id}/consultas` | Consulta o histórico de consultas e predições de um pet. |
| `GET` | `/clinicas/{clinica_id}/consultas` | Lista as consultas de uma clínica. |
| `GET` | `/clinicas/{clinica_id}/alto-risco` | Lista os pets classificados como alto risco pela consulta mais recente. |

Os contratos completos de entrada e saída podem ser consultados em `/docs`.

## Verificação e testes

Para verificar a conexão com o banco, as tabelas esperadas e a execução da IA sobre consultas existentes, execute:

```bash
python -m scripts.check_db
```

O endpoint `POST /predict`, disponível na documentação interativa `/docs`, permite testar a inferência diretamente com os dados de entrada definidos pelo serviço. O endpoint `POST /consultas` permite validar o fluxo integrado, no qual a consulta é registrada e a predição é gerada e persistida automaticamente.

## Persistência dos resultados

Os principais dados são armazenados nas tabelas:

- `CV_TUTOR`: tutores;
- `CV_CLINICA`: clínicas;
- `CV_PET`: pets;
- `CV_VACINA_APLICADA`: vacinas aplicadas;
- `CV_CONSULTA`: consultas;
- `CV_PREDICAO_RISCO`: resultados de risco, probabilidade, recomendação, versão do modelo e data de criação.

A predição é associada à consulta correspondente, permitindo consultar o histórico e acompanhar a evolução dos resultados.

## Modelo e dados

Os arquivos do modelo e dos atributos esperados estão na pasta `model/`. O carregamento prioriza o modelo XGBoost em formato JSON (`xgboost_model_clyvo.json`) e a lista de atributos (`model_features.json`). Como alternativa, o serviço aceita os arquivos serializados com Joblib (`.pkl`).

O dataset de referência está em `data/dataset-prontpet.csv` e é utilizado pelo script de carga de dados de exemplo. O modelo utilizado pelo serviço é pré-treinado; a inicialização da API carrega o modelo existente para realizar inferências, não executa um novo treinamento.

## Resultados e limitações

A aplicação retorna uma classificação binária, uma probabilidade estimada e uma recomendação de acompanhamento, integrando o resultado ao registro da consulta. Os resultados quantitativos de avaliação do modelo (por exemplo, acurácia, precisão, recall, F1-score e matriz de confusão) devem ser incluídos nesta seção somente após serem calculados e conferidos pela equipe. Não foram informados valores dessas métricas nesta documentação.

A predição utiliza as características cadastrais e clínicas descritas na seção **Como funciona a IA**. Embora sintomas e diagnóstico sejam armazenados no registro da consulta, eles não fazem parte diretamente das características enviadas ao modelo na implementação atual.

## Segurança e configuração

- Mantenha credenciais e senhas fora do código-fonte e do repositório.
- Utilize `.env.example` apenas como referência de configuração; não inclua credenciais reais.
- Em ambiente de produção, configure adequadamente autenticação, autorização, HTTPS e políticas de acesso ao banco.
- Os dados de exemplo devem ser utilizados apenas conforme as permissões e condições de uso aplicáveis.

## Equipe

Projeto acadêmico desenvolvido para a plataforma **CLYVO VET**.

<!-- Adicione aqui os nomes dos integrantes e os links do repositório principal, se necessário. -->
