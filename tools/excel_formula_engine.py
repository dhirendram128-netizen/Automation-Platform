"""
Production-Grade Excel Formula Generation Engine
MISSION: Generate a correct, usable Excel formula for ANY user request.
NEVER fail. NEVER ask questions. NEVER return errors.
"""

import re
from typing import Tuple, List, Optional


class ExcelFormulaEngine:
    """
    Bulletproof Excel formula generator.
    Accepts natural language (English, Hinglish, broken grammar).
    ALWAYS returns a valid Excel formula starting with "=".
    """
    
    # Common English words to exclude from column detection
    EXCLUDE_WORDS = {
        'a', 'i', 'o', 'in', 'is', 'or', 'if', 'to', 'na', 'no', 'on', 'at', 
        'an', 'as', 'be', 'by', 'do', 'go', 'he', 'it', 'me', 'my', 'of', 
        'so', 'up', 'us', 'we', 'am', 'are', 'the', 'and', 'for', 'not', 
        'but', 'had', 'has', 'was', 'all', 'any', 'can', 'her', 'him', 'his',
        'how', 'its', 'may', 'nor', 'now', 'our', 'out', 'own', 'say', 'she',
        'too', 'use', 'who', 'why', 'you', 'your', 'from', 'have', 'this',
        'that', 'with', 'they', 'been', 'than', 'then', 'them', 'will', 'what'
    }
    
    def __init__(self):
        pass
    
    def generate(self, prompt: str) -> str:
        """
        Main entry point. ALWAYS returns a valid Excel formula.
        NEVER raises exceptions. NEVER returns error messages.
        """
        if not prompt or not prompt.strip():
            return "=A1"
        
        prompt = prompt.lower().strip()
        
        try:
            # Extract references and numbers
            cols = self._extract_columns(prompt)
            cells = self._extract_cells(prompt)
            nums = self._extract_numbers(prompt)
            
            # Try to generate formula based on intent
            formula = self._detect_and_generate(prompt, cols, cells, nums)
            
            # Ensure formula starts with =
            if not formula.startswith("="):
                formula = "=" + formula
            
            return formula
            
        except Exception:
            # FAILSAFE: If anything goes wrong, return safe default
            return "=IFERROR(A1,\"\")"
    
    def _extract_columns(self, prompt: str) -> List[str]:
        """Extract column letters from prompt."""
        # First try explicit "column X" patterns
        cols = re.findall(r'column\s+([a-z])', prompt)
        
        if not cols:
            # Try standalone single letters (excluding common words)
            cols = re.findall(r'\b([a-z])\b', prompt)
            cols = [c for c in cols if c not in self.EXCLUDE_WORDS]
        
        return [c.upper() for c in cols]
    
    def _extract_cells(self, prompt: str) -> List[str]:
        """Extract cell references like A1, B2, etc."""
        cells = re.findall(r'\b([a-z]+)(\d+)\b', prompt)
        return [f"{c.upper()}{n}" for c, n in cells]
    
    def _extract_numbers(self, prompt: str) -> List[str]:
        """Extract all numbers from prompt."""
        return re.findall(r'\d+\.?\d*', prompt)
    
    def _get_primary_ref(self, cols: List[str], cells: List[str], default: str = "A1") -> str:
        """Get primary cell/column reference with smart defaults."""
        if cells:
            return cells[0]
        if cols:
            return f"{cols[0]}1"
        return default
    
    def _get_column_range(self, cols: List[str], cells: List[str], default: str = "A:A") -> str:
        """Get column range for aggregation functions."""
        if cells:
            # Extract column from cell reference
            col = re.match(r'([A-Z]+)', cells[0]).group(1)
            return f"{col}:{col}"
        if cols:
            return f"{cols[0]}:{cols[0]}"
        return default
    
    def _detect_and_generate(self, prompt: str, cols: List[str], cells: List[str], nums: List[str]) -> str:
        """
        Detect intent and generate appropriate formula.
        Uses cascading if-elif logic with smart defaults.
        ORDER MATTERS: Check specific patterns before general ones.
        """
        
        # ============ DATE & TIME ============
        if any(x in prompt for x in ["today", "current date", "today's date", "aaj ki date", "aaj ka date"]):
            return "=TODAY()"
        
        if any(x in prompt for x in ["now", "current time", "date and time", "abhi ka time"]):
            return "=NOW()"
        
        if "year" in prompt and (cols or cells):
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=IFERROR(YEAR({ref}),\"\")"
        
        if "month" in prompt and (cols or cells):
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=IFERROR(MONTH({ref}),\"\")"
        
        if "day" in prompt and (cols or cells):
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=IFERROR(DAY({ref}),\"\")"
        
        if "date difference" in prompt or "datedif" in prompt:
            if len(cells) >= 2:
                return f'=IFERROR(DATEDIF({cells[0]},{cells[1]},"D"),0)'
            elif len(cols) >= 2:
                return f'=IFERROR(DATEDIF({cols[0]}1,{cols[1]}1,"D"),0)'
            else:
                return '=IFERROR(DATEDIF(A1,B1,"D"),0)'
        
        # Check for age AFTER other date functions to avoid false matches
        if ("age" in prompt or "umar" in prompt) and not any(x in prompt for x in ["average", "percentage"]):
            ref = self._get_primary_ref(cols, cells, "A1")
            return f'=IFERROR(DATEDIF({ref},TODAY(),"Y"),0)'
        
        # ============ GRADING SYSTEMS ============
        if "grade" in prompt or ("90" in prompt and "75" in prompt):
            ref = self._get_primary_ref(cols, cells, "A1")
            return f'=IF({ref}>=90,"A",IF({ref}>=75,"B","C"))'
        
        # ============ MULTIPLE CONDITIONS (AND/OR) ============
        if " and " in prompt and "if" in prompt:
            ref1 = cells[0] if cells else (f"{cols[0]}1" if cols else "A1")
            ref2 = cells[1] if len(cells) > 1 else (f"{cols[1]}1" if len(cols) > 1 else "B1")
            
            threshold1 = nums[0] if nums else "50"
            threshold2 = nums[1] if len(nums) > 1 else threshold1
            
            op = ">" if any(x in prompt for x in ["greater", "more", "above", "zyada"]) else "<"
            
            true_val = '"Pass"' if "pass" in prompt else '"Yes"'
            false_val = '"Fail"' if "fail" in prompt else '"No"'
            
            return f'=IF(AND({ref1}{op}{threshold1},{ref2}{op}{threshold2}),{true_val},{false_val})'
        
        if " or " in prompt and "if" in prompt:
            ref1 = cells[0] if cells else (f"{cols[0]}1" if cols else "A1")
            ref2 = cells[1] if len(cells) > 1 else (f"{cols[1]}1" if len(cols) > 1 else "B1")
            
            threshold1 = nums[0] if nums else "50"
            threshold2 = nums[1] if len(nums) > 1 else threshold1
            
            op = ">" if any(x in prompt for x in ["greater", "more", "above", "zyada"]) else "<"
            
            true_val = '"Yes"'
            false_val = '"No"'
            
            return f'=IF(OR({ref1}{op}{threshold1},{ref2}{op}{threshold2}),{true_val},{false_val})'
        
        # ============ CONDITIONAL AGGREGATION (MUST BE BEFORE GENERAL IF) ============
        # Check for SUMIF before general IF detection
        if "sumif" in prompt or ("sum" in prompt and "if" in prompt):
            # Check if we have multiple columns (sum A if B > 100)
            if len(cols) >= 2:
                criteria_col = f"{cols[1]}:{cols[1]}"  # B column for criteria
                sum_col = f"{cols[0]}:{cols[0]}"  # A column to sum
                op = ">" if any(x in prompt for x in [">", "greater", "more"]) else "<"
                threshold = nums[0] if nums else "0"
                return f'=SUMIF({criteria_col},"{op}{threshold}",{sum_col})'
            else:
                ref = self._get_column_range(cols, cells, "A:A")
                op = ">" if any(x in prompt for x in [">", "greater", "more"]) else "<"
                threshold = nums[0] if nums else "0"
                return f'=SUMIF({ref},"{op}{threshold}")'
        
        # Check for AVERAGEIF before general IF
        if "averageif" in prompt or ("average" in prompt and "if" in prompt):
            ref = self._get_column_range(cols, cells, "A:A")
            op = ">" if any(x in prompt for x in [">", "greater", "more"]) else "<"
            threshold = nums[0] if nums else "0"
            return f'=AVERAGEIF({ref},"{op}{threshold}")'
        
        # Check for COUNTIF before general IF
        if "countif" in prompt or ("count" in prompt and "if" in prompt and "blank" not in prompt):
            ref = self._get_column_range(cols, cells, "A:A")
            op = ">" if any(x in prompt for x in [">", "greater", "more"]) else "<"
            threshold = nums[0] if nums else "0"
            return f'=COUNTIF({ref},"{op}{threshold}")'
        
        # ============ CONDITIONAL LOGIC (IF) ============
        # Check for Hinglish IF patterns (including standalone conditions)
        hinglish_condition = any(x in prompt for x in ["agar", "yadi", "hai"])
        explicit_if = "if" in prompt and not any(x in prompt for x in ["countif", "sumif", "averageif", "ifs"])
        
        if hinglish_condition or explicit_if:
            ref = self._get_primary_ref(cols, cells, "A1")
            
            # Detect condition type
            if any(x in prompt for x in ["blank", "khali", "empty"]):
                condition = f"ISBLANK({ref})"
            elif any(x in prompt for x in ["greater than", "more than", "zyada", ">"]):
                threshold = nums[0] if nums else "0"
                condition = f"{ref}>{threshold}"
            elif any(x in prompt for x in ["less than", "kam", "<"]):
                threshold = nums[0] if nums else "0"
                condition = f"{ref}<{threshold}"
            elif any(x in prompt for x in ["equal", "equals", "barabar", "="]):
                threshold = nums[0] if nums else "0"
                condition = f"{ref}={threshold}"
            elif any(x in prompt for x in ["not equal", "not blank"]):
                condition = f'{ref}<>""'
            else:
                # Default: check if not empty
                condition = f'{ref}<>""'
            
            # Detect true/false values
            true_val = '"Yes"'
            false_val = '"No"'
            
            if "pass" in prompt and "fail" in prompt:
                true_val = '"Pass"'
                false_val = '"Fail"'
            elif "na" in prompt or "n/a" in prompt:
                true_val = '"NA"'
                false_val = '""'
            
            return f"=IF({condition},{true_val},{false_val})"
        
        # ============ TEXT FORMULAS ============
        if any(x in prompt for x in ["concat", "combine", "join", "merge"]):
            if "comma" in prompt or "," in prompt:
                sep = '","'
            elif "space" in prompt:
                sep = '" "'
            else:
                sep = '""'
            
            if len(cells) >= 2:
                return f'=CONCAT({cells[0]},{sep},{cells[1]})'
            elif len(cols) >= 2:
                return f'=CONCAT({cols[0]}1,{sep},{cols[1]}1)'
            else:
                return f'=CONCAT(A1,{sep},B1)'
        
        if "textjoin" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            sep = '","' if "comma" in prompt else '" "'
            return f'=TEXTJOIN({sep},TRUE,{ref})'
        
        if "left" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            length = nums[0] if nums else "5"
            return f"=LEFT({ref},{length})"
        
        if "right" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            length = nums[0] if nums else "5"
            return f"=RIGHT({ref},{length})"
        
        if "mid" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            start = nums[0] if len(nums) > 0 else "1"
            length = nums[1] if len(nums) > 1 else "5"
            return f"=MID({ref},{start},{length})"
        
        if ("len" in prompt or "length" in prompt) and not "wavelength" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=LEN({ref})"
        
        if "trim" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=TRIM({ref})"
        
        if "upper" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=UPPER({ref})"
        
        if "lower" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=LOWER({ref})"
        
        # ============ LOOKUP & REFERENCE ============
        if "vlookup" in prompt:
            if len(cells) >= 1 and len(cols) >= 2:
                lookup_val = cells[0]
                table_range = f"{cols[0]}:{cols[1]}"
                col_index = nums[0] if nums else "2"
                return f'=IFERROR(VLOOKUP({lookup_val},{table_range},{col_index},FALSE),"")'
            elif len(cols) >= 2:
                return f'=IFERROR(VLOOKUP({cols[0]}1,{cols[0]}:{cols[1]},2,FALSE),"")'
            else:
                return '=IFERROR(VLOOKUP(A1,A:B,2,FALSE),"")'
        
        if "xlookup" in prompt:
            if len(cells) >= 1 and len(cols) >= 2:
                lookup_val = cells[0]
                lookup_array = f"{cols[0]}:{cols[0]}"
                return_array = f"{cols[1]}:{cols[1]}"
                return f'=IFERROR(XLOOKUP({lookup_val},{lookup_array},{return_array}),"")'
            elif len(cols) >= 2:
                return f'=IFERROR(XLOOKUP({cols[0]}1,{cols[0]}:{cols[0]},{cols[1]}:{cols[1]}),"")'
            else:
                return '=IFERROR(XLOOKUP(A1,A:A,B:B),"")'
        
        if "index" in prompt and "match" in prompt:
            if len(cols) >= 2:
                return f'=IFERROR(INDEX({cols[1]}:{cols[1]},MATCH({cols[0]}1,{cols[0]}:{cols[0]},0)),"")'
            else:
                return '=IFERROR(INDEX(B:B,MATCH(A1,A:A,0)),"")'
        
        # ============ LOGICAL / VALIDATION ============
        if "isblank" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=ISBLANK({ref})"
        
        if "isnumber" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=ISNUMBER({ref})"
        
        if "istext" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            return f"=ISTEXT({ref})"
        
        # ============ COUNTING ============
        if "not empty" in prompt or "non empty" in prompt or "counta" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=COUNTA({ref})"
        
        if "count" in prompt and "blank" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=COUNTBLANK({ref})"
        
        if "count" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=COUNT({ref})"
        
        # ============ AGGREGATION ============
        if "average" in prompt or "avg" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=AVERAGE({ref})"
        
        if "sum" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=SUM({ref})"
        
        if "max" in prompt or "maximum" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=MAX({ref})"
        
        if "min" in prompt or "minimum" in prompt:
            ref = self._get_column_range(cols, cells, "A:A")
            return f"=MIN({ref})"
        
        # ============ PERCENTAGE ============
        if "percentage" in prompt or "percent" in prompt:
            if "increase" in prompt or "decrease" in prompt:
                if len(cols) >= 2:
                    return f"=IFERROR(({cols[1]}1-{cols[0]}1)/{cols[0]}1*100,0)"
                elif len(cells) >= 2:
                    return f"=IFERROR(({cells[1]}-{cells[0]})/{cells[0]}*100,0)"
                else:
                    return "=IFERROR((B1-A1)/A1*100,0)"
            else:
                if len(cols) >= 2:
                    return f"=IFERROR({cols[0]}1/{cols[1]}1*100,0)"
                elif len(cells) >= 2:
                    return f"=IFERROR({cells[0]}/{cells[1]}*100,0)"
                else:
                    return "=IFERROR(A1/B1*100,0)"
        
        # ============ ROUNDING ============
        if "round" in prompt:
            ref = self._get_primary_ref(cols, cells, "A1")
            decimals = nums[0] if nums else "2"
            if "up" in prompt:
                return f"=ROUNDUP({ref},{decimals})"
            elif "down" in prompt:
                return f"=ROUNDDOWN({ref},{decimals})"
            else:
                return f"=ROUND({ref},{decimals})"
        
        # ============ DEFAULT FALLBACK ============
        # If we have cell references, return the first one
        if cells:
            return f"={cells[0]}"
        
        # If we have columns, assume SUM
        if cols:
            return f"=SUM({cols[0]}:{cols[0]})"
        
        # Ultimate fallback
        return "=A1"


# Singleton instance
_engine = ExcelFormulaEngine()


def generate_formula(prompt: str) -> str:
    """
    Public API: Generate Excel formula from natural language.
    ALWAYS returns a valid formula. NEVER fails.
    """
    return _engine.generate(prompt)
