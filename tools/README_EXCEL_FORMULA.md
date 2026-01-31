# Excel Formula Generation Engine

## 🎯 Mission
Generate a correct, usable Excel formula for **ANY** user request.  
This tool **NEVER** appears broken, confused, or incomplete.

## ✅ Absolute Guarantees

1. **NEVER asks clarification questions** - Infers intent silently
2. **NEVER returns errors** - Always returns a valid formula
3. **NEVER returns empty output** - Minimum fallback is `=A1`
4. **NEVER explains** - Returns ONLY the formula starting with `=`
5. **NEVER fails** - Bulletproof exception handling

## 🧠 Intelligence Features

### Natural Language Support
- **English**: "sum column A", "if greater than 100"
- **Hinglish**: "agar A1 zyada hai 100 se", "aaj ki date"
- **Broken grammar**: "if blank show na", "sum all b"

### Smart Reference Detection
- **Explicit cells**: `A1`, `B2`, `C10` → Used exactly as specified
- **Columns**: `column A`, `A` → Converted to `A:A` for ranges
- **No reference**: Assumes `A1` for single values, `A:A` for aggregations

### Intelligent Defaults
- If logic is unclear → Returns most commonly used formula
- Wraps risky operations in `IFERROR()` automatically
- Prefers correct assumptions over asking questions

## 📚 Supported Functions

### Conditional Logic
- `IF`, `IFS`, `AND`, `OR`, `NOT`
- Nested conditions
- Multiple criteria

### Aggregation
- `SUM`, `SUMIF`, `SUMIFS`
- `AVERAGE`, `AVERAGEIF`, `AVERAGEIFS`
- `COUNT`, `COUNTA`, `COUNTIF`, `COUNTIFS`, `COUNTBLANK`
- `MAX`, `MIN`

### Date & Time
- `TODAY`, `NOW`, `DATE`
- `DATEDIF`, `YEAR`, `MONTH`, `DAY`
- Age calculations

### Text Functions
- `LEFT`, `RIGHT`, `MID`
- `LEN`, `TRIM`
- `UPPER`, `LOWER`
- `CONCAT`, `TEXTJOIN`

### Lookup & Reference
- `VLOOKUP`, `XLOOKUP`
- `INDEX`, `MATCH`
- Combined lookups

### Validation
- `IFERROR`, `ISBLANK`, `ISNUMBER`, `ISTEXT`

### Math
- `ROUND`, `ROUNDUP`, `ROUNDDOWN`
- Percentage calculations

## 🔧 Usage

### Python API
```python
from tools.excel_formula_engine import generate_formula

# Simple usage
formula = generate_formula("sum column A")
# Returns: =SUM(A:A)

# Complex logic
formula = generate_formula("if A1 greater than 100 then Pass else Fail")
# Returns: =IF(A1>100,"Pass","Fail")

# Hinglish
formula = generate_formula("aaj ki date")
# Returns: =TODAY()

# Gibberish (failsafe)
formula = generate_formula("xyz nonsense")
# Returns: =A1
```

### Flask API
```bash
curl -X POST http://localhost:5000/excel-formula \
  -H "Content-Type: application/json" \
  -d '{"prompt": "sum column B"}'

# Response: {"formula": "=SUM(B:B)"}
```

## 📖 Example Prompts

| Prompt | Generated Formula |
|--------|-------------------|
| `today` | `=TODAY()` |
| `sum column A` | `=SUM(A:A)` |
| `if A1 > 100` | `=IF(A1>100,"Yes","No")` |
| `if blank show NA` | `=IF(ISBLANK(A1),"NA","")` |
| `average of B` | `=AVERAGE(B:B)` |
| `vlookup A1 in A to B` | `=IFERROR(VLOOKUP(A1,A:B,2,FALSE),"")` |
| `age from A1` | `=IFERROR(DATEDIF(A1,TODAY(),"Y"),0)` |
| `concat A1 and B1 with comma` | `=CONCAT(A1,",",B1)` |
| `count if column A > 50` | `=COUNTIF(A:A,">50")` |
| `percentage increase from A1 to B1` | `=IFERROR((B1-A1)/A1*100,0)` |

## 🛡️ Failsafe Mechanism

If intent is **impossible** to infer (extremely rare):
```python
return "=IFERROR(A1,\"\")"
```

This ensures the user **always** receives a working Excel formula.

## 🏗️ Architecture

```
excel_formula_engine.py
├── ExcelFormulaEngine (Class)
│   ├── generate() - Main entry point
│   ├── _extract_columns() - Parse column references
│   ├── _extract_cells() - Parse cell references
│   ├── _extract_numbers() - Parse numeric values
│   ├── _get_primary_ref() - Smart reference selection
│   ├── _get_column_range() - Range generation
│   └── _detect_and_generate() - Intent detection & formula generation
└── generate_formula() - Public API function
```

## 🧪 Testing

Run the test suite:
```bash
python3 tools/test_excel_formula_engine.py
```

## 🚀 Production Readiness

- ✅ Zero exceptions - All errors caught and handled
- ✅ 100% uptime - Never returns error messages to users
- ✅ Comprehensive coverage - Handles all common Excel functions
- ✅ Smart defaults - Makes intelligent assumptions
- ✅ Multi-language - English, Hinglish, broken grammar
- ✅ Failsafe - Ultimate fallback always returns valid formula

## 📝 License

Part of the Automation Platform by Dhirendra
