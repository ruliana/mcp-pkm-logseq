# Assistant TODO List

## Current Context

## Example

```markdown
# 2025-02-20 Thursday

- Delete [[BigQuery/Snapshots]] that are duplicated in a day. #query
  - {{embed ((67b8b8d7-b9c5-4b86-bc97-bc06fea24ee5))}}
```

## Testing guidelines
- Start with the happy path first. Add more tests after the happy path works.
- Keep all tests for the same function together. Add a comment banner with the name of the function.
- Test can be executed with `uv run pytest ...`
   - After the first failure, make it more verbose with `-vv`
   - Focus on the first function with error by using `uv run pytest <filename> -v -k "test_<function_name>"`
   - After the function at focus finishes successfully, run all tests with `uv run pytest <filename> -v`

## Goals
1. Separate concerns into individual functions
2. Make code more testable
3. Use functional programming principles
4. Maintain existing functionality
5. Keep the code readable and maintainable

## TODO Steps


## Success Criteria
1. All tests pass
2. No nested functions
3. Each function has a single responsibility
4. Code is more maintainable and testable
5. Existing functionality is preserved
6. Performance is maintained or improved 