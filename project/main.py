import argparse
import logging
import sys
import os
from pathlib import Path

# Garante que o diretório raiz do projeto esteja no sys.path,
# permitindo execução tanto via 'python3 project/main.py' quanto 'python3 -m project.main'
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from project.parser.registry import LayoutRegistry
from project.parser.dec_parser import DecParser
from project.exporters.excel_exporter import export_to_excel


def setup_logging(debug: bool) -> None:
    """
    Sets up structured logging.
    If debug is True, sets logging level to DEBUG. Otherwise INFO.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=log_format, stream=sys.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="IRPF Positional Parser - Lê arquivos .DEC/.DBK e gera planilha Excel padronizada."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Caminho para o arquivo .DEC ou .DBK de entrada.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Caminho para o arquivo .xlsx de saída.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Habilita modo debug (mostra logs detalhados e estatísticas de registros).",
    )
    
    args = parser.parse_args()
    
    setup_logging(args.debug)
    logger = logging.getLogger("main")
    
    if not os.path.exists(args.input):
        logger.error(f"Arquivo de entrada não encontrado: {args.input}")
        return 1
        
    try:
        # 1. Initialize layout registry
        registry = LayoutRegistry()
        logger.debug(f"Registrados layouts para os seguintes registros: {registry.list_registered_types()}")
        
        # 2. Parse DIRPF file
        dec_parser = DecParser(registry)
        assets, exempts, exclusives = dec_parser.parse_file(args.input)
        
        # 3. Export to Excel
        logger.info(f"Iniciando exportação dos dados para: {args.output}")
        export_to_excel(assets, exempts, exclusives, args.output)
        logger.info("Exportação concluída com sucesso!")
        
        # 4. Debug statistics reporting
        if args.debug or True: # Always show summary of execution
            stats = dec_parser.report_stats()
            print("\n" + "=" * 50)
            print("ESTATÍSTICAS DA EXECUÇÃO (MODO RESUMO)")
            print("=" * 50)
            print(f"Total de linhas lidas: {stats['total_lines']}")
            print(f"Linhas parseadas com sucesso: {stats['parsed_lines']}")
            
            print("\nREGISTROS PROCESSADOS:")
            for r_type, count in sorted(stats["processed_counts"].items()):
                spec = registry.get(r_type)
                desc = spec.description if spec else ""
                print(f"  Registro [{r_type}] ({desc}): {count} ocorrentes")
                
            print("\nREGISTROS IGNORADOS/PULADOS:")
            ignored = stats["ignored_counts"]
            if ignored:
                for r_type, count in sorted(ignored.items()):
                    print(f"  Registro [{r_type}]: {count} ocorrentes")
            else:
                print("  Nenhum registro ignorado.")
            print("=" * 50 + "\n")
            
        return 0
        
    except Exception as e:
        logger.exception(f"Erro inesperado durante a execução do pipeline: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
