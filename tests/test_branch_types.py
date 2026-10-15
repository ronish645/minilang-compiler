"""Type inference across if / else branches.

Only one branch of an if runs, so each branch is checked from the types
known *before* the if. Where the branches meet again, their results are
joined: agreement keeps the type, disagreement makes the variable dynamic
(unknown), the same as a function parameter.
"""

import pytest

from minilang.errors import MiniLangRuntimeError, SemanticError


def test_branches_may_give_an_untyped_variable_different_types(run):
    src = 'let flag = false; let x; if (flag) { x = 10; } else { x = "hello"; } print(x);'
    assert run(src) == ["hello"]


def test_branches_that_agree_keep_the_static_type(run):
    src = 'let x; if (true) { x = 1; } else { x = 2; } x = "text";'
    with pytest.raises(SemanticError, match="cannot assign string to 'x' of type int"):
        run(src)


def test_disagreeing_branches_make_the_variable_dynamic(run):
    # x may be an int or a string, so the mistake can only be caught at run time.
    src = 'let x; if (false) { x = 1; } else { x = "a"; } print(x - 1);'
    with pytest.raises(MiniLangRuntimeError, match="cannot apply .-. to string and int"):
        run(src)


def test_if_without_else_keeps_the_branch_type(run):
    src = 'let x; if (true) { x = 1; } x = "text";'
    with pytest.raises(SemanticError, match="cannot assign string to 'x' of type int"):
        run(src)


def test_else_if_chain_joins_every_branch(run):
    src = (
        "fn label(n) { let r;"
        ' if (n == 0) { r = "zero"; } else if (n == 1) { r = 1; } else { r = true; }'
        " return r; } print(label(0)); print(label(1)); print(label(2));"
    )
    assert run(src) == ["zero", "1", "true"]


def test_null_initialized_variable_is_inferred_per_branch(run):
    src = 'let x = null; if (false) { x = [1]; } else { x = "s"; } print(x);'
    assert run(src) == ["s"]


def test_typed_variables_are_still_checked_inside_branches(run):
    src = 'let x = 1; if (true) { x = "no"; }'
    with pytest.raises(SemanticError, match="cannot assign string to 'x' of type int"):
        run(src)


def test_errors_in_both_branches_are_reported(run):
    src = "let x = 1; if (true) { x = true; } else { x = [1]; }"
    with pytest.raises(SemanticError) as caught:
        run(src)
    messages = [e.message for e in [caught.value, *caught.value.additional]]
    assert messages == [
        "cannot assign bool to 'x' of type int",
        "cannot assign array to 'x' of type int",
    ]
