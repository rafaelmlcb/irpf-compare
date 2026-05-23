# IRPF – Parser e Gerador de Excel

## Contexto

Este repositório contém um **parser Python** para os arquivos de declaração do Imposto de Renda da Pessoa Física (IRPF) da Receita Federal, especificamente os formatos **`.DEC`** e **`.DBK`**.  Os arquivos são texto de largura fixa (fixed‑width) semelhantes aos layouts CNAB/SPED.

O objetivo da primeira versão é:

- Ler registros de **Bens e Direitos** (registro 27), **Rendimentos Isentos** (registro 23) e **Rendimentos Sujeitos a Tributação Exclusiva** (registro 24).
- Converter esses dados em objetos canônicos (`AssetRecord`, `ExemptIncomeRecord`, `ExclusiveIncomeRecord`).
- Exportar tudo para um **arquivo Excel** bem formatado, pronto para reconciliação tributária futura.

A arquitetura está preparada para extensões (novo registros, reconciliação, validações avançadas).

---

## Estrutura do Projeto

```
irpf-compare/
├─ project/
│  ├─ exporters/           # exportador para Excel
│  │   └─ excel_exporter.py
│  ├─ models/              # dataclasses canônicas
│  │   └─ canonical.py
│  ├─ parser/              # parser genérico e registradores de layout
│  │   ├─ dec_parser.py
│  │   ├─ fixed_width.py
│  │   ├─ registry.py
│  │   └─ layouts/specs.py
│  └─ utils/               # utilitários de auxílio
│      └─ helpers.py
├─ example.DEC            # arquivo de teste minimalista
├─ README.md              # **este documento**
└─ requirements.txt       # dependências (opcional)
```

---

## Pré‑requisitos

- **Python 3.10+**
- `pip` para instalar as bibliotecas
- (Opcional) Ambiente virtual (`python -m venv .venv`)

---

## Instalação

```bash
# Clone ou entre no diretório já existente
cd /home/rafael/projetos/irpf-compare

# (Recomendado) criar ambiente virtual
python -m venv .venv
source .venv/bin/activate   # no Windows use .venv\Scripts\activate

# Instalar dependências
pip install pandas openpyxl
```

> **Nota:** O `requirements.txt` não está incluído neste commit, mas as duas bibliotecas acima são suficientes para a execução.

---

## Como executar

```bash
# Executar o ponto de entrada oficial
python3 -m project.main --input dados_exemplo/entrada_exemplo.DEC --output dados_exemplo/saida_exemplo.xlsx --debug

```

- `--input` – caminho para o arquivo `.DEC` ou `.DBK` que será analisado.
- `--output` – caminho onde o Excel será gravado.
- `--debug` – ativa logging em nível `DEBUG` (útil para depuração).

Após a execução, abra `saida.xlsx` em qualquer visualizador de planilhas. O workbook contém quatro abas:

- `Resumo`, como primeira aba, consolidando cada bem em uma única linha.
- `Bens e Direitos`, com os detalhes completos de cada ativo.
- `Rendimentos Isentos`, com o nome do bem associado em formato de link interno.
- `Rendimentos Exclusivos`, também com navegação interna para o bem correspondente.

Todas as abas possuem uma primeira coluna `Item`, que enumera as linhas de dados. O exportador cria hyperlinks internos para facilitar a navegação entre resumo, bens e rendimentos, e o texto de cada link inclui o item relacionado.

---

## Atualizações Recentes

- Removido o ponto de entrada legado `project/cli/`; a execução oficial agora passa por `project/main.py`.
- O parser ficou centralizado em `DecParser`, sem funções procedurais antigas para leitura de arquivo.
- A exportação Excel foi refatorada para incluir a aba `Resumo` como primeira planilha.
- A planilha `Bens e Direitos` passou a exportar grupo, código, código do bem, localização, país, indicador de exterior, CNPJ fonte e nome do ativo quando identificável.
- A planilha `Bens e Direitos` também passou a extrair `Instituicao`, `Quantidade` e `Preco Medio` quando a discriminação segue um padrão estruturado.
- As abas de rendimentos agora usam hyperlinks internos para voltar ao bem correspondente.
- As colunas de vínculos em `Bens e Direitos` agora são hyperlinks para as abas de rendimentos, em vez de apenas contagens.
- Todas as abas receberam a coluna `Item` para padronizar navegação e referência cruzada.

---

## Teste rápido

O arquivo [dados_exemplo/entrada_exemplo.DEC](/home/rafael/projetos/irpf-compare/dados_exemplo/entrada_exemplo.DEC) foi enriquecido para servir como base de testes e comparações futuras. Ele agora inclui:

- múltiplos bens com grupos e códigos distintos, como imóvel, ações, CDB, conta no exterior e criptoativo;
- valores de ano anterior e ano atual preenchidos;
- indicador de exterior e código de país para cenários de localização;
- fontes pagadoras variadas para vincular rendimentos aos bens;
- rendimentos isentos e exclusivos, tanto diretos quanto detalhados.

Isso ajuda a validar comparações por tipo de ativo, local, fonte pagadora e evolução patrimonial.

Campos especialmente úteis para comparações futuras:

- grupo e código do bem separados do código composto;
- localização e código do país;
- identificação da fonte pagadora por CNPJ;
- nome do ativo quando reconhecido na discriminação, como ticker de ação ou sigla de criptoativo;
- instituição, quantidade e preço médio para ativos descritos em formato estruturado;
- vínculos navegáveis entre bem e rendimentos nas duas direções.

### Formato estruturado da discriminação

Para bens do tipo ações, o parser pode aproveitar uma convenção textual para extrair campos adicionais automaticamente:

```text
INSTITUICAO-ACOES-TICKER-QUANTIDADE-PRECO MEDIO-DETALHES LIVRES
```

Exemplos:

- `ITAU-ACOES-MDNE3-88-28,08-...`
- `BB-ACOES-DIVO11-110-64,25-...`

Nesses casos, a exportação tenta preencher:

- `Instituicao`
- `Nome do Ativo`
- `Quantidade`
- `Preco Medio`

---

## Próximos passos

- Adicionar testes unitários sob `project/tests/` (ainda a ser implementado).
- Implementar reconciliação automática entre diferentes declarações.
- Documentar cada registro adicional conforme necessidade.

---

**© 2026 Rafael – Projeto IRPF‑Compare**
