"""
Exportador de dados do IRPF para planilha Excel (.xlsx) em PT-BR.

Abas geradas:
  - "Bens e Direitos"      → AssetRecord
  - "Rendimentos Isentos"  → ExemptIncomeRecord
  - "Rendimentos Exclusivos" → ExclusiveIncomeRecord
"""
import logging
from pathlib import Path
from typing import List

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from project.models.canonical import AssetRecord, ExemptIncomeRecord, ExclusiveIncomeRecord

logger = logging.getLogger(__name__)


# ── Helpers de formatação ──────────────────────────────────────────────────────

def _auto_width(ws) -> None:
    """Ajusta a largura das colunas ao conteúdo (máx. 60 caracteres)."""
    for column_cells in ws.columns:
        max_len = max(
            len(str(cell.value)) if cell.value is not None else 0
            for cell in column_cells
        )
        col_letter = get_column_letter(column_cells[0].column)
        ws.column_dimensions[col_letter].width = min(max_len + 4, 60)


def _make_table(ws, display_name: str) -> None:
    """Aplica formatação de Tabela Excel com estilo ao worksheet."""
    if ws.max_row < 2:
        return
    tab = Table(displayName=display_name, ref=ws.dimensions)
    style = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    tab.tableStyleInfo = style
    ws.add_table(tab)
    ws.freeze_panes = ws["A2"]


# ── Writers por entidade ───────────────────────────────────────────────────────

def _write_assets(ws, assets: List[AssetRecord]) -> None:
    headers = [
        "CPF",
        "Código do Bem",
        "Descrição",
        "Discriminação",
        "Situação Anterior (R$)",
        "Valor Atual (R$)",
        "CNPJ Fonte",
        "Rend. Isentos Vinculados",
        "Rend. Exclusivos Vinculados",
    ]
    ws.append(headers)
    for a in assets:
        ws.append([
            a.cpf,
            a.codigo_bem,
            a.descricao,
            a.discriminacao,
            float(a.valor_anterior),
            float(a.valor_2025),
            a.cnpj_fonte,
            len(a.rendimentos_isentos),
            len(a.rendimentos_exclusivos),
        ])
    _auto_width(ws)
    _make_table(ws, "TabelaBens")


def _write_exempts(ws, exempts: List[ExemptIncomeRecord]) -> None:
    headers = [
        "CPF",
        "Código",
        "Descrição",
        "Valor (R$)",
        "CNPJ Fonte Pagadora",
        "Nome Fonte Pagadora",
        "Origem",
    ]
    ws.append(headers)
    for e in exempts:
        ws.append([
            e.cpf,
            e.tipo_rendimento,
            e.descricao,
            float(e.valor),
            e.cnpj_fonte,
            e.nome_fonte,
            "Detalhe" if e.origem == "detalhe" else "Direto",
        ])
    _auto_width(ws)
    _make_table(ws, "TabelaRendIsentos")


def _write_exclusives(ws, exclusives: List[ExclusiveIncomeRecord]) -> None:
    headers = [
        "CPF",
        "Código",
        "Descrição",
        "Valor (R$)",
        "CNPJ Fonte Pagadora",
        "Nome Fonte Pagadora",
        "Origem",
    ]
    ws.append(headers)
    for e in exclusives:
        ws.append([
            e.cpf,
            e.tipo_rendimento,
            e.descricao,
            float(e.valor),
            e.cnpj_fonte,
            e.nome_fonte,
            "Detalhe" if e.origem == "detalhe" else "Direto",
        ])
    _auto_width(ws)
    _make_table(ws, "TabelaRendExclusivos")


# ── Ponto de entrada ───────────────────────────────────────────────────────────

def export_to_excel(
    assets: List[AssetRecord],
    exempts: List[ExemptIncomeRecord],
    exclusives: List[ExclusiveIncomeRecord],
    output_path,
) -> None:
    """
    Exporta os registros do IRPF para um arquivo Excel formatado em PT-BR.

    Args:
        assets:      Lista de AssetRecord (Bens e Direitos).
        exempts:     Lista de ExemptIncomeRecord (Rendimentos Isentos).
        exclusives:  Lista de ExclusiveIncomeRecord (Rendimentos Exclusivos).
        output_path: Caminho de saída do arquivo .xlsx.
    """
    wb = Workbook()
    # Remove aba padrão criada automaticamente
    wb.remove(wb.active)

    if assets:
        _write_assets(wb.create_sheet("Bens e Direitos"), assets)

    if exempts:
        _write_exempts(wb.create_sheet("Rendimentos Isentos"), exempts)

    if exclusives:
        _write_exclusives(wb.create_sheet("Rendimentos Exclusivos"), exclusives)

    if not wb.sheetnames:
        wb.create_sheet("Sem Dados")

    try:
        wb.save(str(output_path))
        logger.info("Arquivo Excel gravado em: %s", output_path)
    except Exception as exc:
        logger.error("Falha ao gravar arquivo Excel: %s", exc)
        raise
