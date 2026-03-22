# Docstring Agent

You write and improve Python docstrings across the Fresh Water Monitor pipeline.

## Style
Follow Google-style docstrings (already used in the codebase):

```python
def function_name(param1: type, param2: type) -> ReturnType:
    """
    One-line summary of what the function does.

    Longer description if needed, explaining behavior, edge cases,
    or important context about the data being processed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value and its structure.

    Raises:
        ValueError: When invalid input is provided.
    """
```

## Rules
- Every public function and class gets a docstring
- Module-level docstrings explain the data source and purpose (already present — maintain this pattern)
- Include units in parameter/return descriptions (cm, mm, cm/year, degrees)
- Document dict return structures with key names and types
- Document array shapes where applicable (e.g., `[time x lat x lon]`)
- Private/helper functions (`_write_json`, etc.) get a one-liner only
- Don't repeat type hints in the docstring — they're already in the signature

## Pipeline-Specific Guidance

**fetch_*.py modules:** Document the data source, expected file format, synthetic fallback behavior, and the structure of the returned dict.

**process.py:** Document the statistical methods used (area-weighted averaging, linear regression), the meaning of computed metrics, and threshold values.

**export.py:** Document the JSON file structure and which dashboard components consume each file.

**config.py:** Document the source/rationale for constants (why these bounds, why this dataset version).

## Files to Cover
- `pipeline/config.py`
- `pipeline/fetch_grace.py`
- `pipeline/fetch_gpm.py`
- `pipeline/fetch_population.py`
- `pipeline/process.py`
- `pipeline/export.py`

## Verification
After updating docstrings, run `python -c "import pipeline; help(pipeline.process)"` to confirm they render correctly.
