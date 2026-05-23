from project.parser.fixed_width import FieldSpec, RecordSpec

# Register IR - Header do Arquivo
IR_SPEC = RecordSpec(
    record_type="IR",
    fields=[
        FieldSpec("SISTEMA", 1, 8, "C"),
        FieldSpec("EXERCICIO", 9, 12, "N"),
        FieldSpec("ANO_BASE", 13, 16, "N"),
        FieldSpec("CODIGO_RECNET", 17, 20, "N"),
        FieldSpec("IN_RETIFICADORA", 21, 21, "C"),
        FieldSpec("NR_CPF", 22, 32, "C"),
    ],
    description="Header da declaração"
)

# Register 16 - Identificação do Declarante
R16_SPEC = RecordSpec(
    record_type="16",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("NM_NOME", 14, 73, "C"),
    ],
    description="Identificação do declarante"
)

# Register 27 - Bens e Direitos
R27_SPEC = RecordSpec(
    record_type="27",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("CD_BEM", 14, 15, "N"),
        FieldSpec("IN_EXTERIOR", 16, 16, "N"),
        FieldSpec("CD_PAIS", 17, 19, "N"),
        FieldSpec("TX_BEM", 20, 531, "C"),
        FieldSpec("VR_ANTER", 532, 544, "N", decimals=2),
        FieldSpec("VR_ATUAL", 545, 557, "N", decimals=2),
        FieldSpec("NM_CPFCNPJ", 1042, 1055, "C"),
        FieldSpec("CD_GRUPO_BEM", 1101, 1102, "C"),
    ],
    description="Declaração de Bens e Direitos"
)

# Register 23 - Rendimentos Isentos (Consolidado/Direto)
R23_SPEC = RecordSpec(
    record_type="23",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("NR_COD_ISENTO", 14, 17, "N"),
        FieldSpec("VR_VALOR", 18, 30, "N", decimals=2),
    ],
    description="Rendimentos Isentos e Não Tributáveis (Sumário/Direto)"
)

# Register 83 - Rendimento Isento Detalhe 2
R83_SPEC = RecordSpec(
    record_type="83",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("IN_TIPO", 14, 14, "C"),
        FieldSpec("NR_CPF_BENEFIC", 15, 25, "C"),
        FieldSpec("NR_COD", 26, 29, "N"),
        FieldSpec("VR_VALOR", 30, 42, "N", decimals=2),
    ],
    description="Rendimento Isento Tipo de Informação 2"
)

# Register 84 - Rendimento Isento Detalhe 3
R84_SPEC = RecordSpec(
    record_type="84",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("IN_TIPO", 14, 14, "C"),
        FieldSpec("NR_CPF_BENEFIC", 15, 25, "C"),
        FieldSpec("NR_COD", 26, 29, "N"),
        FieldSpec("NR_PAGADORA", 30, 43, "C"),
        FieldSpec("NM_NOME", 44, 103, "C"),
        FieldSpec("VR_VALOR", 104, 116, "N", decimals=2),
    ],
    description="Rendimento Isento Tipo de Informação 3"
)

# Register 85 - Rendimento Isento Detalhe 4
R85_SPEC = RecordSpec(
    record_type="85",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("IN_TIPO", 14, 14, "C"),
        FieldSpec("NR_CPF_BENEFIC", 15, 25, "C"),
        FieldSpec("NR_COD", 26, 29, "N"),
        FieldSpec("NR_PAGADORA", 30, 43, "C"),
        FieldSpec("NM_NOME", 44, 103, "C"),
        FieldSpec("VR_RECEB", 104, 116, "N", decimals=2),
    ],
    description="Rendimento Isento Tipo de Informação 4"
)

# Register 86 - Rendimento Isento Detalhe 5
R86_SPEC = RecordSpec(
    record_type="86",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("IN_TIPO", 14, 14, "C"),
        FieldSpec("NR_CPF_BENEFIC", 15, 25, "C"),
        FieldSpec("NR_COD", 26, 29, "N"),
        FieldSpec("NR_PAGADORA", 30, 43, "C"),
        FieldSpec("NM_NOME", 44, 103, "C"),
        FieldSpec("VR_VALOR", 104, 116, "N", decimals=2),
        FieldSpec("NM_DESCRICAO", 117, 176, "C"),
    ],
    description="Rendimento Isento Tipo de Informação 5"
)

# Register 87 - Rendimento Isento Detalhe 6
R87_SPEC = RecordSpec(
    record_type="87",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("NR_COD", 14, 17, "N"),
        FieldSpec("VR_VALOR", 18, 30, "N", decimals=2),
        FieldSpec("VR_VALORGCAP", 31, 43, "N", decimals=2),
    ],
    description="Rendimento Isento Tipo de Informação 6"
)

# Register 24 - Rendimentos Sujeitos a Tributação Exclusiva (Consolidado)
R24_SPEC = RecordSpec(
    record_type="24",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("NR_COD_EXCLUSIVO", 14, 17, "N"),
        FieldSpec("VR_VALOR", 18, 30, "N", decimals=2),
    ],
    description="Rendimentos Sujeitos a Tributação Exclusiva (Sumário/Direto)"
)

# Register 88 - Rendimento Exclusivo Detalhe 2
R88_SPEC = RecordSpec(
    record_type="88",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("IN_TIPO", 14, 14, "C"),
        FieldSpec("NR_CPF_BENEFIC", 15, 25, "C"),
        FieldSpec("NR_COD", 26, 29, "N"),
        FieldSpec("NR_PAGADORA", 30, 43, "C"),
        FieldSpec("NM_NOME", 44, 103, "C"),
        FieldSpec("VR_VALOR", 104, 116, "N", decimals=2),
    ],
    description="Rendimento Exclusivo Tipo de Informação 2"
)

# Register 89 - Rendimento Exclusivo Detalhe 3
R89_SPEC = RecordSpec(
    record_type="89",
    fields=[
        FieldSpec("NR_REG", 1, 2, "N"),
        FieldSpec("NR_CPF", 3, 13, "C"),
        FieldSpec("IN_TIPO", 14, 14, "C"),
        FieldSpec("NR_CPF_BENEFIC", 15, 25, "C"),
        FieldSpec("NR_COD", 26, 29, "N"),
        FieldSpec("NR_PAGADORA", 30, 43, "C"),
        FieldSpec("NM_NOME", 44, 103, "C"),
        FieldSpec("VR_VALOR", 104, 116, "N", decimals=2),
        FieldSpec("NM_DESCRICAO", 117, 176, "C"),
    ],
    description="Rendimento Exclusivo Tipo de Informação 3"
)

# Dicionário mapeando tipo de registro para sua especificação
LAYOUTS = {
    "IR": IR_SPEC,
    "16": R16_SPEC,
    "27": R27_SPEC,
    "23": R23_SPEC,
    "83": R83_SPEC,
    "84": R84_SPEC,
    "85": R85_SPEC,
    "86": R86_SPEC,
    "87": R87_SPEC,
    "24": R24_SPEC,
    "88": R88_SPEC,
    "89": R89_SPEC,
}
