from decimal import Decimal, InvalidOperation
import re
from typing import Dict, Optional, Tuple

def parse_decimal(value: str, decimals: int = 2) -> Decimal:
    """
    Parses a zero-padded fixed-width numeric string into a Decimal.
    Handles negative signs if present at the beginning of the string.
    Example: '0000000012345' with decimals=2 -> Decimal('123.45')
             '-0000000012345' with decimals=2 -> Decimal('-123.45')
    """
    cleaned = value.strip()
    if not cleaned:
        return Decimal("0.00")
    
    # Check for sign
    sign = 1
    if cleaned.startswith("-"):
        sign = -1
        cleaned = cleaned[1:]
    elif cleaned.startswith("+"):
        cleaned = cleaned[1:]
        
    if not cleaned.isdigit():
        # Fallback for floats that might already have dot
        try:
            return Decimal(cleaned) * sign
        except Exception:
            return Decimal("0.00")
            
    num = int(cleaned)
    if decimals > 0:
        return Decimal(num) / Decimal(10 ** decimals) * sign
    return Decimal(num) * sign


def clean_string(value: str) -> str:
    """Trim whitespace and remove leading zeros from textual fields.
    Numeric strings (e.g., CPF/CNPJ) remain unchanged.
    """
    stripped = value.strip()
    if stripped and not stripped.isdigit():
        return stripped.lstrip('0')
    return stripped


def format_cpf_cnpj(value: str) -> str:
    """
    Cleans CPF or CNPJ. Removes formatting and spaces, preserving leading zeros.
    Returns cleaned raw numeric string or formatted string.
    """
    cleaned = re.sub(r"\D", "", value)
    if not cleaned:
        return ""
    
    if len(cleaned) == 11:
        # Format as CPF: 000.000.000-00
        return f"{cleaned[:3]}.{cleaned[3:6]}.{cleaned[6:9]}-{cleaned[9:]}"
    elif len(cleaned) == 14:
        # Format as CNPJ: 00.000.000/0000-00
        return f"{cleaned[:2]}.{cleaned[2:5]}.{cleaned[5:8]}/{cleaned[8:12]}-{cleaned[12:]}"
    
    return cleaned


def get_asset_description(group_code: str, asset_code: str) -> str:
    """
    Returns friendly description in Portuguese for Asset group + code.
    Based on official Receita Federal Bens e Direitos classification.
    """
    combined = f"{group_code.zfill(2)}-{asset_code.zfill(2)}"
    
    descriptions = {
        # Grupo 01 - Bens Imóveis
        "01-01": "Prédio residencial",
        "01-02": "Prédio comercial",
        "01-03": "Galpão industrial",
        "01-11": "Apartamento",
        "01-12": "Casa",
        "01-13": "Terreno",
        "01-14": "Imóvel rural",
        "01-15": "Sala ou escritório",
        "01-16": "Loja",
        "01-99": "Outros bens imóveis",
        # Grupo 02 - Bens Móveis
        "02-01": "Veículo automotor terrestre (carro, moto, etc.)",
        "02-02": "Aeronave",
        "02-03": "Embarcação",
        "02-99": "Outros bens móveis",
        # Grupo 03 - Participações Societárias
        "03-01": "Ações (inclusive as listadas em bolsa)",
        "03-02": "Quotas ou quinhões de capital",
        "03-99": "Outras participações societárias",
        # Grupo 04 - Aplicações e Investimentos
        "04-01": "Depósito em poupança",
        "04-02": "Títulos públicos e privados (CDB, RDB, Tesouro Direto, etc.)",
        "04-03": "Letras de Crédito (LCI, LCA, etc.)",
        "04-04": "Debêntures e outros títulos de dívida",
        "04-99": "Outras aplicações e investimentos",
        # Grupo 06 - Depósito à Vista e Dinheiro em Espécie
        "06-01": "Depósito em conta corrente no País",
        "06-02": "Depósito em conta corrente no Exterior",
        "06-99": "Dinheiro em espécie ou outros depósitos",
        # Grupo 07 - Fundos
        "07-01": "Fundo de Investimento em Renda Fixa",
        "07-02": "Fundo de Investimento em Ações",
        "07-03": "Fundo de Investimento Imobiliário (FII)",
        "07-04": "Fundo de Investimento em Índices (ETF)",
        "07-99": "Outros fundos de investimento",
        # Grupo 08 - Criptoativos
        "08-01": "Criptoativo Bitcoin (BTC)",
        "08-02": "Outros criptoativos (Altcoins, ex: ETH, SOL)",
        "08-03": "Stablecoins (ex: USDT, USDC)",
        "08-99": "Outros criptoativos",
        # Grupo 09 - Outros Bens e Direitos
        "09-99": "Outros bens e direitos",
    }
    
    if combined in descriptions:
        return descriptions[combined]
        
    # Group names backup
    group_names = {
        "01": "Bem Imóvel",
        "02": "Bem Móvel",
        "03": "Participação Societária",
        "04": "Aplicação e Investimento",
        "05": "Crédito",
        "06": "Depósito à Vista e Dinheiro",
        "07": "Fundo de Investimento",
        "08": "Criptoativo",
        "09": "Outro Bem e Direito",
    }
    g_code = group_code.zfill(2)
    if g_code in group_names:
        return f"{group_names[g_code]} (Código {asset_code})"
        
    return f"Outros Bens e Direitos (Grupo {group_code}, Código {asset_code})"


def get_country_description(code: str) -> str:
    """
    Returns a compact country/location description for common IRPF country codes.
    """
    normalized = code.strip().zfill(3) if code.strip().isdigit() else code.strip()
    descriptions = {
        "105": "Brasil",
        "840": "Estados Unidos",
    }
    return descriptions.get(normalized, f"Pais {normalized}" if normalized else "")


def extract_asset_name(text: str) -> str:
    """
    Tries to extract a compact market identifier from the asset description.
    """
    cleaned = clean_string(text)
    if not cleaned:
        return ""

    ticker_match = re.search(r"\b[A-Z]{4}\d{1,2}\b", cleaned)
    if ticker_match:
        return ticker_match.group(0)

    crypto_match = re.search(r"\b(BTC|ETH|SOL|USDT|USDC)\b", cleaned, re.IGNORECASE)
    if crypto_match:
        return crypto_match.group(1).upper()

    return ""


def extract_structured_asset_fields(text: str) -> Tuple[str, str, Optional[int], Optional[Decimal]]:
    """
    Extracts structured asset metadata from descriptions like:
      INSTITUICAO-ACOES-TICKER-QUANTIDADE-PRECO MEDIO-...
      BB-ACOES-DIVO11-110-64,25-...
    Returns: instituicao, nome_ativo, quantidade, preco_medio
    """
    cleaned = clean_string(text)
    if not cleaned:
        return "", "", None, None

    parts = [part.strip() for part in cleaned.split("-") if part.strip()]
    if not parts:
        return "", "", None, None

    instituicao = parts[0].upper()
    nome_ativo = ""
    quantidade: Optional[int] = None
    preco_medio: Optional[Decimal] = None

    if len(parts) >= 5 and parts[1].upper() == "ACOES":
        nome_ativo = parts[2].upper()
        if parts[3].isdigit():
            quantidade = int(parts[3])
        try:
            preco_bruto = re.sub(r"(?i)r\$\s*", "", parts[4]).strip()
            preco_medio = Decimal(preco_bruto.replace(".", "").replace(",", "."))
        except (InvalidOperation, AttributeError):
            preco_medio = None
    else:
        nome_ativo = extract_asset_name(cleaned)

    return instituicao, nome_ativo, quantidade, preco_medio


def get_exempt_income_description(code: str) -> str:
    """
    Returns friendly description for Exempt Income codes.
    """
    descriptions = {
        "01": "Bolsas de estudo e de pesquisa caracterizadas como doação",
        "02": "Bolsas de médico-residente ou de participante do Pronatec",
        "03": "Capital das apólices de seguro ou pecúlio pago por morte",
        "04": "Indenizações por rescisão de contrato de trabalho, PDV e FGTS",
        "05": "Ganho de capital na alienação de bens de pequeno valor",
        "06": "Ganho de capital na alienação do único imóvel",
        "07": "Ganho de capital na alienação de outros bens imóveis",
        "08": "Indenização por acidente de trabalho e depósitos do FGTS",
        "09": "Lucros e dividendos recebidos",
        "10": "Parcela isenta de proventos de aposentadoria (65 anos ou mais)",
        "11": "Pensão, proventos de aposentadoria por doença grave",
        "12": "Rendimentos de cadernetas de poupança, letras hipotecárias, etc.",
        "13": "Rendimentos de sócio ou titular de microempresa ou Simples Nacional",
        "14": "Transferências patrimoniais - doações e heranças",
        "16": "Imposto de anos anteriores compensado judicialmente",
        "18": "Incorporação de reservas de capital",
        "19": "Transferências patrimoniais - meação e divórcio",
        "20": "Ganhos líquidos em operações de ações até R$ 40.000,00",
        "21": "Ganhos líquidos com ouro até R$ 40.000,00",
        "23": "Rendimentos de poupança, letras hipotecárias, etc. (Outros)",
        "24": "Demais rendimentos isentos dos dependentes",
        "25": "Pensão, aposentadoria ou reforma dos dependentes",
        "26": "Outros rendimentos isentos e não tributáveis",
        "28": "Pensão alimentícia judicial",
    }
    c = code.zfill(2)
    return descriptions.get(c, f"Outros Rendimentos Isentos (Código {code})")


def get_exclusive_income_description(code: str) -> str:
    """
    Returns friendly description for Exclusive Income codes.
    """
    descriptions = {
        "01": "Décimo terceiro salário",
        "02": "Ganhos de capital na alienação de bens e direitos",
        "03": "Ganhos de capital na alienação de moeda estrangeira",
        "04": "Ganhos de capital em moeda estrangeira (espécie)",
        "05": "Ganhos líquidos em renda variável (bolsa, FII, etc.)",
        "06": "Rendimentos de aplicações financeiras",
        "07": "Rendimentos de participações societárias",
        "08": "Décimo terceiro salário de dependentes",
        "09": "Outros rendimentos sujeitos a tributação exclusiva de dependentes",
        "10": "Juros sobre capital próprio (JCP)",
        "11": "Participação nos lucros ou resultados (PLR)",
        "12": "Outros rendimentos sujeitos à tributação exclusiva/definitiva",
    }
    c = code.zfill(2)
    return descriptions.get(c, f"Outros Rendimentos de Trib. Exclusiva (Código {code})")
