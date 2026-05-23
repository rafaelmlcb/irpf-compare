"""
Parser orientado a objetos para arquivos .DEC / .DBK do IRPF.

Responsabilidades:
  - Leitura posicional via LayoutRegistry / parse_line
  - Enriquecimento de dados usando helpers (parse_decimal, format_cpf_cnpj, get_*_description)
  - Anti-duplicidade: registros de detalhe (84-89) substituem sumários (23/24)
  - Reconciliação pós-parsing: vincula rendimentos a bens pelo CNPJ da fonte
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from project.models.canonical import AssetRecord, ExemptIncomeRecord, ExclusiveIncomeRecord
from project.parser.fixed_width import parse_line
from project.parser.registry import LayoutRegistry
from project.utils.helpers import (
    clean_string,
    extract_asset_name,
    format_cpf_cnpj,
    get_asset_description,
    get_country_description,
    get_exempt_income_description,
    get_exclusive_income_description,
    parse_decimal,
)

logger = logging.getLogger(__name__)

# ── Tipos de registro ──────────────────────────────────────────────────────────
ASSET_TYPE = "27"                              # Bens e Direitos
EXEMPT_SUMMARY_TYPE = "23"                     # Rendimentos Isentos – sumário
EXCLUSIVE_SUMMARY_TYPE = "24"                  # Rendimentos Exclusivos – sumário
EXEMPT_DETAIL_TYPES: Set[str] = {"84", "85", "86", "87"}
EXCLUSIVE_DETAIL_TYPES: Set[str] = {"88", "89"}


def _normalize_code(raw: str) -> str:
    """Normaliza um código numérico para string de 2 dígitos. Ex: '0009' → '09'."""
    cleaned = raw.strip()
    if cleaned.isdigit():
        return str(int(cleaned)).zfill(2)
    return cleaned


class DecParser:
    """
    Parser para arquivos IRPF no formato posicional (.DEC / .DBK).

    Usage::

        registry = LayoutRegistry()
        parser = DecParser(registry)
        assets, exempts, exclusives = parser.parse_file("declaracao.DEC")
        stats = parser.report_stats()
    """

    def __init__(self, registry: LayoutRegistry) -> None:
        self._registry = registry
        # Estatísticas redefinidas a cada chamada de parse_file
        self._total_lines: int = 0
        self._parsed_lines: int = 0
        self._processed_counts: Dict[str, int] = {}
        self._ignored_counts: Dict[str, int] = {}

    # ── API pública ────────────────────────────────────────────────────────────

    def parse_file(
        self,
        file_path: Any,
    ) -> Tuple[List[AssetRecord], List[ExemptIncomeRecord], List[ExclusiveIncomeRecord]]:
        """
        Lê um arquivo .DEC / .DBK e retorna as três listas canônicas.

        Etapas:
          1. Primeira passagem: detecta quais códigos possuem registros de detalhe
             (84-89) para aplicar a regra de anti-duplicidade.
          2. Segunda passagem: extrai e constrói os registros canônicos,
             ignorando sumários (23/24) cujo código já possui um detalhe.
          3. Reconciliação: vincula rendimentos a bens pelo CNPJ da fonte pagadora.
        """
        path = Path(file_path)
        self._reset_stats()

        # ── 1ª passagem: descobrir códigos com detalhe ─────────────────────────
        exempt_detail_codes: Set[str] = set()
        exclusive_detail_codes: Set[str] = set()

        with path.open("r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue
                rtype = line[:2]
                spec = self._registry.get(rtype)
                if spec is None:
                    continue
                if rtype in EXEMPT_DETAIL_TYPES:
                    fields = parse_line(line, spec)
                    code = _normalize_code(fields.get("NR_COD", ""))
                    if code:
                        exempt_detail_codes.add(code)
                elif rtype in EXCLUSIVE_DETAIL_TYPES:
                    fields = parse_line(line, spec)
                    code = _normalize_code(fields.get("NR_COD", ""))
                    if code:
                        exclusive_detail_codes.add(code)

        logger.debug("Códigos isentos com detalhe: %s", exempt_detail_codes)
        logger.debug("Códigos exclusivos com detalhe: %s", exclusive_detail_codes)

        # ── 2ª passagem: extração dos registros ────────────────────────────────
        assets: List[AssetRecord] = []
        exempts: List[ExemptIncomeRecord] = []
        exclusives: List[ExclusiveIncomeRecord] = []

        with path.open("r", encoding="utf-8") as fh:
            for line_number, raw_line in enumerate(fh, start=1):
                self._total_lines += 1
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue

                rtype = line[:2]
                spec = self._registry.get(rtype)

                if spec is None:
                    self._ignored_counts[rtype] = self._ignored_counts.get(rtype, 0) + 1
                    logger.debug("Sem spec para tipo '%s' na linha %d", rtype, line_number)
                    continue

                fields = parse_line(line, spec)

                # ── Bens e Direitos ────────────────────────────────────────────
                if rtype == ASSET_TYPE:
                    record = self._build_asset(fields)
                    if record:
                        assets.append(record)
                        self._inc_processed(rtype)

                # ── Rendimentos Isentos – Sumário ──────────────────────────────
                elif rtype == EXEMPT_SUMMARY_TYPE:
                    code = _normalize_code(fields.get("NR_COD_ISENTO", ""))
                    if code in exempt_detail_codes:
                        self._inc_ignored(rtype)
                        logger.debug("Sumário isento cód.%s ignorado (existe detalhe)", code)
                        continue
                    record = self._build_exempt_summary(fields, code)
                    if record:
                        exempts.append(record)
                        self._inc_processed(rtype)

                # ── Rendimentos Exclusivos – Sumário ───────────────────────────
                elif rtype == EXCLUSIVE_SUMMARY_TYPE:
                    code = _normalize_code(fields.get("NR_COD_EXCLUSIVO", ""))
                    if code in exclusive_detail_codes:
                        self._inc_ignored(rtype)
                        logger.debug("Sumário exclusivo cód.%s ignorado (existe detalhe)", code)
                        continue
                    record = self._build_exclusive_summary(fields, code)
                    if record:
                        exclusives.append(record)
                        self._inc_processed(rtype)

                # ── Rendimentos Isentos – Detalhe ──────────────────────────────
                elif rtype in EXEMPT_DETAIL_TYPES:
                    record = self._build_exempt_detail(fields, rtype)
                    if record:
                        exempts.append(record)
                        self._inc_processed(rtype)

                # ── Rendimentos Exclusivos – Detalhe ───────────────────────────
                elif rtype in EXCLUSIVE_DETAIL_TYPES:
                    record = self._build_exclusive_detail(fields, rtype)
                    if record:
                        exclusives.append(record)
                        self._inc_processed(rtype)

                # ── Demais registros (header, identificação, etc.) ─────────────
                else:
                    self._inc_processed(rtype)

                self._parsed_lines += 1

        # ── 3ª etapa: Reconciliação CNPJ ──────────────────────────────────────
        self._reconcile(assets, exempts, exclusives)

        return assets, exempts, exclusives

    def report_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da última execução de parse_file."""
        return {
            "total_lines": self._total_lines,
            "parsed_lines": self._parsed_lines,
            "processed_counts": dict(self._processed_counts),
            "ignored_counts": dict(self._ignored_counts),
        }

    # ── Construtores privados ──────────────────────────────────────────────────

    def _build_asset(self, fields: Dict[str, str]):
        try:
            cpf = clean_string(fields.get("NR_CPF", ""))
            cd_bem = fields.get("CD_BEM", "").strip()
            cd_grupo = fields.get("CD_GRUPO_BEM", "").strip()

            grupo_str = cd_grupo.zfill(2) if cd_grupo.isdigit() else cd_grupo
            bem_str = str(int(cd_bem)).zfill(2) if cd_bem.isdigit() else cd_bem
            codigo_bem = f"{grupo_str}-{bem_str}"

            descricao = get_asset_description(grupo_str, bem_str)
            discriminacao = clean_string(fields.get("TX_BEM", ""))
            valor_anterior = parse_decimal(fields.get("VR_ANTER", "0"), decimals=2)
            valor_atual = parse_decimal(fields.get("VR_ATUAL", "0"), decimals=2)
            cnpj_fonte = format_cpf_cnpj(fields.get("NM_CPFCNPJ", ""))
            indicador_exterior = fields.get("IN_EXTERIOR", "").strip()
            codigo_pais = fields.get("CD_PAIS", "").strip().zfill(3)
            nome_ativo = extract_asset_name(discriminacao)
            localizacao = get_country_description(codigo_pais)
            if indicador_exterior == "1" and localizacao:
                localizacao = f"Exterior - {localizacao}"

            return AssetRecord(
                cpf=cpf,
                grupo_bem=grupo_str,
                codigo_item=bem_str,
                codigo_bem=codigo_bem,
                descricao=descricao,
                discriminacao=discriminacao,
                valor_anterior=valor_anterior,
                valor_2025=valor_atual,
                cnpj_fonte=cnpj_fonte,
                indicador_exterior=indicador_exterior,
                codigo_pais=codigo_pais,
                localizacao=localizacao,
                nome_ativo=nome_ativo,
            )
        except Exception as exc:
            logger.warning("Erro ao construir AssetRecord: %s", exc)
            return None

    def _build_exempt_summary(self, fields: Dict[str, str], code: str):
        try:
            cpf = clean_string(fields.get("NR_CPF", ""))
            valor = parse_decimal(fields.get("VR_VALOR", "0"), decimals=2)
            descricao = get_exempt_income_description(code)
            return ExemptIncomeRecord(
                cpf=cpf,
                tipo_rendimento=code,
                descricao=descricao,
                valor=valor,
                origem="direto",
            )
        except Exception as exc:
            logger.warning("Erro ao construir ExemptIncomeRecord (sumário): %s", exc)
            return None

    def _build_exempt_detail(self, fields: Dict[str, str], rtype: str):
        try:
            cpf = clean_string(fields.get("NR_CPF", ""))
            code = _normalize_code(fields.get("NR_COD", ""))
            descricao = get_exempt_income_description(code)
            cnpj_fonte = format_cpf_cnpj(fields.get("NR_PAGADORA", ""))
            nome_fonte = clean_string(fields.get("NM_NOME", ""))
            # Reg 85 usa VR_RECEB; demais usam VR_VALOR
            vr_key = "VR_RECEB" if rtype == "85" else "VR_VALOR"
            valor = parse_decimal(fields.get(vr_key, "0"), decimals=2)
            return ExemptIncomeRecord(
                cpf=cpf,
                tipo_rendimento=code,
                descricao=descricao,
                valor=valor,
                cnpj_fonte=cnpj_fonte,
                nome_fonte=nome_fonte,
                origem="detalhe",
            )
        except Exception as exc:
            logger.warning("Erro ao construir ExemptIncomeRecord (detalhe %s): %s", rtype, exc)
            return None

    def _build_exclusive_summary(self, fields: Dict[str, str], code: str):
        try:
            cpf = clean_string(fields.get("NR_CPF", ""))
            valor = parse_decimal(fields.get("VR_VALOR", "0"), decimals=2)
            descricao = get_exclusive_income_description(code)
            return ExclusiveIncomeRecord(
                cpf=cpf,
                tipo_rendimento=code,
                descricao=descricao,
                valor=valor,
                origem="direto",
            )
        except Exception as exc:
            logger.warning("Erro ao construir ExclusiveIncomeRecord (sumário): %s", exc)
            return None

    def _build_exclusive_detail(self, fields: Dict[str, str], rtype: str):
        try:
            cpf = clean_string(fields.get("NR_CPF", ""))
            code = _normalize_code(fields.get("NR_COD", ""))
            descricao = get_exclusive_income_description(code)
            cnpj_fonte = format_cpf_cnpj(fields.get("NR_PAGADORA", ""))
            nome_fonte = clean_string(fields.get("NM_NOME", ""))
            valor = parse_decimal(fields.get("VR_VALOR", "0"), decimals=2)
            return ExclusiveIncomeRecord(
                cpf=cpf,
                tipo_rendimento=code,
                descricao=descricao,
                valor=valor,
                cnpj_fonte=cnpj_fonte,
                nome_fonte=nome_fonte,
                origem="detalhe",
            )
        except Exception as exc:
            logger.warning("Erro ao construir ExclusiveIncomeRecord (detalhe %s): %s", rtype, exc)
            return None

    # ── Reconciliação ─────────────────────────────────────────────────────────

    def _reconcile(
        self,
        assets: List[AssetRecord],
        exempts: List[ExemptIncomeRecord],
        exclusives: List[ExclusiveIncomeRecord],
    ) -> None:
        """
        Vincula ExemptIncomeRecord e ExclusiveIncomeRecord aos seus AssetRecord
        utilizando o CNPJ da fonte pagadora como chave estrangeira.
        """
        asset_index: Dict[str, AssetRecord] = {
            a.cnpj_fonte: a for a in assets if a.cnpj_fonte
        }

        for rec in exempts:
            if rec.cnpj_fonte and rec.cnpj_fonte in asset_index:
                asset = asset_index[rec.cnpj_fonte]
                asset.rendimentos_isentos.append(rec)
                rec.bem_associado = asset.descricao
                logger.debug(
                    "Isento cód.%s vinculado ao bem %s via CNPJ %s",
                    rec.tipo_rendimento, asset.codigo_bem, rec.cnpj_fonte,
                )

        for rec in exclusives:
            if rec.cnpj_fonte and rec.cnpj_fonte in asset_index:
                asset = asset_index[rec.cnpj_fonte]
                asset.rendimentos_exclusivos.append(rec)
                rec.bem_associado = asset.descricao
                logger.debug(
                    "Exclusivo cód.%s vinculado ao bem %s via CNPJ %s",
                    rec.tipo_rendimento, asset.codigo_bem, rec.cnpj_fonte,
                )

    # ── Utilidades de estatística ──────────────────────────────────────────────

    def _reset_stats(self) -> None:
        self._total_lines = 0
        self._parsed_lines = 0
        self._processed_counts = {}
        self._ignored_counts = {}

    def _inc_processed(self, rtype: str) -> None:
        self._processed_counts[rtype] = self._processed_counts.get(rtype, 0) + 1

    def _inc_ignored(self, rtype: str) -> None:
        self._ignored_counts[rtype] = self._ignored_counts.get(rtype, 0) + 1
