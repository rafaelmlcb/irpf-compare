from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class FieldSpec:
    name: str
    start: int   # 1-based initial column (inclusive)
    end: int     # 1-based final column (inclusive)
    type: str    # 'C' (Char), 'N' (Num), 'NN' (Num Negativo), 'I' (Bool)
    decimals: int = 0

@dataclass
class RecordSpec:
    record_type: str
    fields: List[FieldSpec]
    description: str


def parse_line(line: str, spec: RecordSpec) -> Dict[str, str]:
    """
    Parses a single line of text according to a RecordSpec using positional slicing.
    Returns a dictionary mapping field names to raw string values.
    
    Robustness:
    - Strips record endings like CRLF.
    - If the line is shorter than the spec's end index, it pads the missing characters with spaces.
    """
    # Remove any trailing newlines (CRLF or LF)
    clean_line = line.rstrip("\r\n")
    
    parsed_fields = {}
    for field in spec.fields:
        start_idx = field.start - 1
        end_idx = field.end
        
        # Safe slicing
        line_len = len(clean_line)
        if start_idx >= line_len:
            raw_val = ""
        elif end_idx > line_len:
            raw_val = clean_line[start_idx:]
        else:
            raw_val = clean_line[start_idx:end_idx]
            
        parsed_fields[field.name] = raw_val
        
    return parsed_fields
