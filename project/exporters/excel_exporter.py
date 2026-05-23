"""
Exportador de dados do IRPF para planilha Excel (.xlsx) em PT-BR.

Abas geradas:
  - "Resumo"
  - "Bens e Direitos"
  - "Rendimentos Isentos"
  - "Rendimentos Exclusivos"

O arquivo é construído com navegação interna via fórmulas HYPERLINK.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Sequence

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from project.models.canonical import AssetRecord, ExemptIncomeRecord, ExclusiveIncomeRecord

logger = logging.getLogger(__name__)

SUMMARY_SHEET = "Resumo"
ASSETS_SHEET = "Bens e Direitos"
EXEMPTS_SHEET = "Rendimentos Isentos"
EXCLUSIVES_SHEET = "Rendimentos Exclusivos"


def _money(value: Decimal) -> float:
    return float(value or Decimal("0"))


def _auto_width(ws) -> None:
    for column_cells in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        col_letter = get_column_letter(column_cells[0].column)
        ws.column_dimensions[col_letter].width = min(max_len + 4, 60)


def _style_header_row(ws) -> None:
    fill = PatternFill("solid", fgColor="1F4E78")
    font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _make_table(ws, display_name: str) -> None:
    if ws.max_row < 2:
        return
    tab = Table(displayName=display_name, ref=ws.dimensions)
    tab.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(tab)
    ws.freeze_panes = ws["A2"]


def _hyperlink_formula(target_sheet: str, cell_ref: str, label: str) -> str:
    return f'=HYPERLINK("#\'{target_sheet}\'!{cell_ref}","{label}")'


def _build_asset_index(assets: Sequence[AssetRecord]) -> dict[str, AssetRecord]:
    index: dict[str, AssetRecord] = {}
    for asset in assets:
        if asset.cnpj_fonte:
            index[asset.cnpj_fonte] = asset
    return index


def _write_summary(ws, assets: Sequence[AssetRecord], asset_rows: dict[int, int]) -> dict[int, int]:
    headers = [
        "Código do Bem",
        "Descrição do Bem",
        "Valor Ano Anterior (R$)",
        "Valor Ano Atual (R$)",
        "Total Rend. Isentos (R$)",
        "Total Rend. Exclusivos (R$)",
        "Ver Detalhes",
    ]
    ws.append(headers)

    summary_rows: dict[int, int] = {}
    for idx, asset in enumerate(assets, start=2):
        asset_row = asset_rows[id(asset)]
        summary_rows[id(asset)] = idx
        ws.append([
            asset.codigo_bem,
            asset.descricao,
            _money(asset.valor_anterior),
            _money(asset.valor_2025),
            _money(sum((r.valor for r in asset.rendimentos_isentos), Decimal("0"))),
            _money(sum((r.valor for r in asset.rendimentos_exclusivos), Decimal("0"))),
            _hyperlink_formula(ASSETS_SHEET, f"A{asset_row}", "Abrir"),
        ])
        ws.cell(row=idx, column=7).style = "Hyperlink"

    _style_header_row(ws)
    _auto_width(ws)
    _make_table(ws, "TabelaResumo")
    ws.freeze_panes = "A2"
    return summary_rows


def _write_assets(ws, assets: Sequence[AssetRecord]) -> dict[int, int]:
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

    asset_rows: dict[int, int] = {}
    for asset in assets:
        row_idx = ws.max_row + 1
        asset_rows[id(asset)] = row_idx
        ws.append([
            asset.cpf,
            asset.codigo_bem,
            asset.descricao,
            asset.discriminacao,
            _money(asset.valor_anterior),
            _money(asset.valor_2025),
            asset.cnpj_fonte,
            len(asset.rendimentos_isentos),
            len(asset.rendimentos_exclusivos),
        ])

    _style_header_row(ws)
    _auto_width(ws)
    _make_table(ws, "TabelaBens")
    return asset_rows


def _write_income_sheet(
    ws,
    records: Sequence[ExemptIncomeRecord | ExclusiveIncomeRecord],
    assets_by_cnpj: dict[str, AssetRecord],
    summary_rows: dict[int, int],
    *,
    summary_sheet: str,
    sheet_name: str,
) -> None:
    headers = [
        "CPF",
        "Código",
        "Descrição",
        "Valor (R$)",
        "CNPJ Fonte Pagadora",
        "Nome Fonte Pagadora",
        "Bem Associado",
        "Origem",
    ]
    ws.append(headers)

    for record in records:
        asset = assets_by_cnpj.get(record.cnpj_fonte, None) if record.cnpj_fonte else None
        bem_label = asset.descricao if asset else (record.bem_associado or "")
        if asset and id(asset) in summary_rows:
            bem_cell = _hyperlink_formula(summary_sheet, f"A{summary_rows[id(asset)]}", bem_label)
        else:
            bem_cell = bem_label

        ws.append([
            record.cpf,
            record.tipo_rendimento,
            record.descricao,
            _money(record.valor),
            record.cnpj_fonte,
            record.nome_fonte,
            bem_cell,
            "Detalhe" if record.origem == "detalhe" else "Direto",
        ])

    # Hyperlink formulas need to be explicitly kept as formulas.
    for row in range(2, ws.max_row + 1):
        cell = ws.cell(row=row, column=7)
        if isinstance(cell.value, str) and cell.value.startswith("=HYPERLINK("):
            cell.style = "Hyperlink"

    _style_header_row(ws)
    _auto_width(ws)
    _make_table(ws, f"Tabela{sheet_name.replace(' ', '')}")
    ws.freeze_panes = "A2"


def export_to_excel(
    assets: List[AssetRecord],
    exempts: List[ExemptIncomeRecord],
    exclusives: List[ExclusiveIncomeRecord],
    output_path,
) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    ws_assets = wb.create_sheet(ASSETS_SHEET)
    asset_rows = _write_assets(ws_assets, assets)
    assets_by_cnpj = _build_asset_index(assets)

    ws_summary = wb.create_sheet(SUMMARY_SHEET, 0)
    summary_rows = _write_summary(ws_summary, assets, asset_rows)

    ws_exempts = wb.create_sheet(EXEMPTS_SHEET)
    _write_income_sheet(
        ws_exempts,
        exempts,
        assets_by_cnpj,
        summary_rows,
        summary_sheet=SUMMARY_SHEET,
        sheet_name=EXEMPTS_SHEET,
    )

    ws_exclusives = wb.create_sheet(EXCLUSIVES_SHEET)
    _write_income_sheet(
        ws_exclusives,
        exclusives,
        assets_by_cnpj,
        summary_rows,
        summary_sheet=SUMMARY_SHEET,
        sheet_name=EXCLUSIVES_SHEET,
    )

    if not wb.sheetnames:
        wb.create_sheet("Sem Dados")

    try:
        wb.save(str(output_path))
        logger.info("Arquivo Excel gravado em: %s", output_path)
    except Exception as exc:
        logger.error("Falha ao gravar arquivo Excel: %s", exc)
        raise
