"""
Modelos canônicos para os dados extraídos do IRPF (.DEC / .DBK).

Hierarquia de relacionamento:
    AssetRecord (Bem ou Direito)
        └── rendimentos_isentos:   List[ExemptIncomeRecord]   (vinculados por CNPJ)
        └── rendimentos_exclusivos: List[ExclusiveIncomeRecord] (vinculados por CNPJ)
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List


@dataclass
class ExemptIncomeRecord:
    """Rendimento Isento e Não Tributável (registros 23, 83, 84, 85, 86, 87)."""

    cpf: str
    tipo_rendimento: str       # código normalizado ex: "09"
    descricao: str             # descrição em PT-BR enriquecida
    valor: Decimal
    cnpj_fonte: str = ""       # CNPJ da fonte pagadora (chave para reconciliação)
    nome_fonte: str = ""       # Nome da fonte pagadora
    origem: str = "direto"     # "direto" (reg 23) | "detalhe" (reg 84/85/86/87)


@dataclass
class ExclusiveIncomeRecord:
    """Rendimento Sujeito a Tributação Exclusiva/Definitiva (registros 24, 88, 89)."""

    cpf: str
    tipo_rendimento: str       # código normalizado ex: "10"
    descricao: str             # descrição em PT-BR enriquecida
    valor: Decimal
    cnpj_fonte: str = ""       # CNPJ da fonte pagadora (chave para reconciliação)
    nome_fonte: str = ""       # Nome da fonte pagadora
    origem: str = "direto"     # "direto" (reg 24) | "detalhe" (reg 88/89)


@dataclass
class AssetRecord:
    """Bem ou Direito declarado (registro 27)."""

    cpf: str
    codigo_bem: str            # ex: "03-01" (grupo-código formatado)
    descricao: str             # descrição enriquecida em PT-BR
    valor_anterior: Decimal    # valor na declaração anterior (VR_ANTER)
    valor_2025: Decimal        # valor na declaração atual    (VR_ATUAL)
    cnpj_fonte: str = ""       # CNPJ vinculado ao bem (chave para reconciliação)
    discriminacao: str = ""    # texto livre discriminativo do bem (TX_BEM)

    # Relacionamentos preenchidos na etapa de reconciliação pós-parsing
    rendimentos_isentos: List[ExemptIncomeRecord] = field(default_factory=list)
    rendimentos_exclusivos: List[ExclusiveIncomeRecord] = field(default_factory=list)
