import unittest
from decimal import Decimal

from project.parser.fixed_width import FieldSpec, RecordSpec, parse_line
from project.parser.registry import LayoutRegistry
from project.parser.dec_parser import DecParser
from project.utils.helpers import (
    parse_decimal,
    clean_string,
    extract_structured_asset_fields,
    format_cpf_cnpj,
    get_asset_description,
)

class TestParserHelpers(unittest.TestCase):
    """
    Test suite for parser utility helpers.
    """
    def test_parse_decimal(self) -> None:
        # Standard decimal with 2 decimals
        self.assertEqual(parse_decimal("0000000012345", 2), Decimal("123.45"))
        # Standard decimal with 0 decimals (integer)
        self.assertEqual(parse_decimal("0000000012345", 0), Decimal("12345"))
        # Negative decimal
        self.assertEqual(parse_decimal("-0000000012345", 2), Decimal("-123.45"))
        # Zero padded
        self.assertEqual(parse_decimal("00000", 2), Decimal("0.00"))
        # Already parsed float fallback
        self.assertEqual(parse_decimal("123.45", 2), Decimal("123.45"))
        # Sign +
        self.assertEqual(parse_decimal("+0000000012345", 2), Decimal("123.45"))
        # Empty/whitespace values
        self.assertEqual(parse_decimal("   "), Decimal("0.00"))

    def test_clean_string(self) -> None:
        self.assertEqual(clean_string("  texto com espaco  "), "texto com espaco")
        self.assertEqual(clean_string(""), "")

    def test_format_cpf_cnpj(self) -> None:
        # CPF formatting (11 characters)
        self.assertEqual(format_cpf_cnpj("12345678901"), "123.456.789-01")
        self.assertEqual(format_cpf_cnpj("  123.456.789-01  "), "123.456.789-01")
        # CNPJ formatting (14 characters)
        self.assertEqual(format_cpf_cnpj("12345678000199"), "12.345.678/0001-99")
        # Invalid format output
        self.assertEqual(format_cpf_cnpj("123"), "123")
        self.assertEqual(format_cpf_cnpj(""), "")

    def test_extract_structured_asset_fields(self) -> None:
        instituicao, nome_ativo, quantidade, preco_medio = extract_structured_asset_fields(
            "ITAU-ACOES-MDNE3-88-28,08-Posicao consolidada"
        )
        self.assertEqual(instituicao, "ITAU")
        self.assertEqual(nome_ativo, "MDNE3")
        self.assertEqual(quantidade, 88)
        self.assertEqual(preco_medio, Decimal("28.08"))

        instituicao2, nome_ativo2, quantidade2, preco_medio2 = extract_structured_asset_fields(
            "BB-ACOES-DIVO11-110-R$ 64,25-BB - ACOES VIA BB BANCO DE INVESTIMENTO S/A"
        )
        self.assertEqual(instituicao2, "BB")
        self.assertEqual(nome_ativo2, "DIVO11")
        self.assertEqual(quantidade2, 110)
        self.assertEqual(preco_medio2, Decimal("64.25"))


class TestFixedWidthParser(unittest.TestCase):
    """
    Test suite for fixed width posicional parser.
    """
    def test_parse_line(self) -> None:
        spec = RecordSpec(
            record_type="99",
            fields=[
                FieldSpec("TIPO", 1, 2, "N"),
                FieldSpec("CPF", 3, 13, "C"),
                FieldSpec("CODIGO", 14, 15, "N"),
                FieldSpec("TEXTO", 16, 25, "C"),
                FieldSpec("VALOR", 26, 35, "N", decimals=2),
            ],
            description="Registro de teste"
        )
        
        # Exact length line: TEXTO is 10 chars (TEST STRIN)
        line = "991234567890103TEST STRIN0000012345\n"
        parsed = parse_line(line, spec)
        self.assertEqual(parsed["TIPO"], "99")
        self.assertEqual(parsed["CPF"], "12345678901")
        self.assertEqual(parsed["CODIGO"], "03")
        self.assertEqual(parsed["TEXTO"], "TEST STRIN")
        self.assertEqual(parsed["VALOR"], "0000012345")
        
        # Shorter line handling (padding robust)
        short_line = "991234567890103"
        parsed_short = parse_line(short_line, spec)
        self.assertEqual(parsed_short["TIPO"], "99")
        self.assertEqual(parsed_short["CPF"], "12345678901")
        self.assertEqual(parsed_short["CODIGO"], "03")
        self.assertEqual(parsed_short["TEXTO"], "")
        self.assertEqual(parsed_short["VALOR"], "")


class TestDecParser(unittest.TestCase):
    """
    Test suite for DecParser high-level file parser and anti-duplicity rules.
    """
    def setUp(self) -> None:
        self.registry = LayoutRegistry()
        self.parser = DecParser(self.registry)

    def test_dec_parser_filtering(self) -> None:
        # Build 27 record using exact offsets
        buf_27 = [" "] * 1174
        def write_27(val: str, start: int):
            for idx, char in enumerate(val):
                buf_27[start - 1 + idx] = char
                
        write_27("27", 1)
        write_27("12345678901", 3)
        write_27("01", 14)
        write_27("0", 16)
        write_27("105", 17)
        write_27("Descricao do ativo", 20)
        write_27("0000000000000", 532) # VR_ANTER
        write_27("0000000010000", 545) # VR_ATUAL (100.00)
        write_27("12345678000199", 1042)
        write_27("03", 1101) # CD_GRUPO_BEM
        write_27("0000000000", 1165)
        line_27 = "".join(buf_27) + "\n"

        # Build 84 record (exempt income detailed) using exact offsets
        buf_84 = [" "] * 144
        def write_84(val: str, start: int):
            for idx, char in enumerate(val):
                buf_84[start - 1 + idx] = char
                
        write_84("84", 1)
        write_84("12345678901", 3)
        write_84("T", 14)
        write_84("12345678901", 15)
        write_84("0009", 26)
        write_84("98765432000100", 30)
        write_84("Fonte Pagadora Ltda.", 44)
        write_84("0000000500000", 104) # VR_VALOR (5000.00 with decimals=2)
        write_84("00000", 130)
        write_84("0000000000", 135)
        line_84 = "".join(buf_84) + "\n"

        # Build 88 record (taxable income detailed) using exact offsets
        buf_88 = [" "] * 131
        def write_88(val: str, start: int):
            for idx, char in enumerate(val):
                buf_88[start - 1 + idx] = char
                
        write_88("88", 1)
        write_88("12345678901", 3)
        write_88("0010", 26)
        write_88("12345678000199", 11)
        write_88("Fonte Pagadora Tributavel", 30)
        write_88("0000000300000", 90) # VR_VALOR (3000.00 with decimals=2)
        write_88("00000", 117)
        write_88("0000000000", 122)
        line_88 = "".join(buf_88) + "\n"

        lines = [
            "IRPessoaFi202520243300012345678901   1000Contribuinte Teste                    PR0000000000\n",
            line_27,
            # Direct code 03 (Exempt)
            "231234567890100030000000150000\n",
            # Summary code 09 (Exempt, should be ignored)
            "231234567890100090000000500000\n",
            # Detailed code 09 (Exempt, detail 84)
            line_84,
            # Direct code 01 (Exclusive)
            "241234567890100010000000085000\n",
            # Summary code 10 (Exclusive, should be ignored)
            "241234567890100100000000300000\n",
            # Detailed code 10 (Exclusive, detail 88)
            line_88,
        ]
        
        # Create a temp file to parse
        import tempfile
        import os
        
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.writelines(lines)
                
            assets, exempts, exclusives, taxables = self.parser.parse_file(path)
            
            # Check Assets
            self.assertEqual(len(assets), 1)
            self.assertEqual(assets[0].cpf, "12345678901")
            self.assertEqual(assets[0].codigo_bem, "03-01")
            self.assertEqual(assets[0].valor_2025, Decimal("100.00"))
            self.assertEqual(assets[0].localizacao, "Brasil")
            
            # Check Exempt Incomes (Direct 03 + Detailed 09)
            self.assertEqual(len(exempts), 2)
            exempt_codes = {e.tipo_rendimento for e in exempts}
            self.assertIn("03", exempt_codes)
            self.assertIn("09", exempt_codes)
            # Ensure the summary 09 was ignored (meaning we only have 2 exempts, not 3)
            self.assertEqual(sum(e.valor for e in exempts), Decimal("1500.00") + Decimal("5000.00"))
            
            # Check Exclusive Incomes (Direct 01 + Detailed 10)
            self.assertEqual(len(exclusives), 2)
            exclusive_codes = {e.tipo_rendimento for e in exclusives}
            self.assertIn("01", exclusive_codes)
            self.assertIn("10", exclusive_codes)
            # Ensure the summary 10 was ignored
            self.assertEqual(sum(e.valor for e in exclusives), Decimal("850.00") + Decimal("3000.00"))

            # Check Taxable Incomes (Registro 88)
            self.assertEqual(len(taxables), 1)
            self.assertEqual(taxables[0].cnpj_fonte, "12345678000199")
            self.assertEqual(taxables[0].valor, Decimal("3000.00"))
            self.assertEqual(len(assets[0].rendimentos_tributaveis), 1)
            
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
