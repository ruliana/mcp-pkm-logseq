# Markdown Converter Refactoring Plan

Refactor the file `markdown_converter.py` using `test_markdown_converter.py` to make sure the refactoring is safe.

Keep everything in a single new file `to_markdown.py` and the new tests in `test_to_markdown.py`.

Keep this file in sync. Ask the user if the code is good enough before checking a task as done.

## Current Context
- The code currently uses nested functions which makes testing and maintenance harder
- The main function `page_to_markdown` contains all the logic
- The code mixes different responsibilities:
  1. Data cleaning/preparation
  2. Property handling
  3. Block hierarchy building
  4. Markdown formatting

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

- [x] Create data models/types:
   - Define Block and Page types using dataclasses

- [ ] Create pure functions for each responsibility:
   - `clean_response(response: List[dict]) -> Tuple[Page, Dict[int, Block]]`
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes
   - `extract_properties(blocks: Dict[int, Block]) -> Tuple[List[str], Dict[int, Block]]`
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes
   - `reorganize_blocks(blocks: Dict[int, Block], parent_id: int) -> Dict[Block]`
     - Reorganize blocks in a dictionary of dictionaries and arrays (a tree) that mimics hierarchy and order of the final Markdown
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes
   - `format_blocks(Dict[Block]) -> str`
     - Format all blocks from `reorganize_blocks` to markdown
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes
   - `format_block(block: Block, level: int) -> str`
     - Format a single block to markdown
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes
   - `format_code_block(content: str, level: int) -> str`
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes
   - `build_markdown(page: Page, blocks: Dict[int, Block]) -> str`
     - [x] Create the test for the function
     - [x] Create the function
     - [x] Test it and make sure the test passes

- [ ] Reorganize the test code, grouping all tests from the same function together.
   - Add a comment banner to each section
   - Make sure all tests passes

- [ ] Create an end to end test using `example_response` and `example_output`
   - Make sure all tests passes

- [ ] Clean up
   - Make sure all new tests passes
   - Delete old code

- [ ] Documentation:
   - [ ] Add docstrings to all functions
   - [ ] Add type hints
   - [ ] Add examples in docstrings
   - [ ] Add comment headers to the test file to visually separate the functions


## Success Criteria
1. All tests pass
2. No nested functions
3. Each function has a single responsibility
4. Code is more maintainable and testable
5. Existing functionality is preserved
6. Performance is maintained or improved 