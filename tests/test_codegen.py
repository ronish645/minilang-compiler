"""Code generator unit tests: AST -> three-address code and pseudo-assembly."""

from minilang.codegen import CodeGenerator, op_to_instr
from minilang.lexer import Lexer
from minilang.parser import Parser


def generate(source: str) -> tuple[list[str], list[str]]:
    return CodeGenerator().generate(Parser(Lexer(source).tokenize()).parse())


def tac(source: str) -> list[str]:
    return generate(source)[0]


def test_nested_expression_uses_one_temp_per_operator():
    assert tac("let a = 1 + 2 * 3;") == ["t1 = 2 * 3", "t2 = 1 + t1", "a = t2"]


def test_string_literals_are_quoted():
    assert tac("print('42');") == ["print '42'"]


def test_declaration_without_initializer():
    assert generate("let a;") == (["declare a"], ["DECLARE a"])


def test_if_else_lowers_to_conditional_jump_and_labels():
    assert tac("let c = true; if (c) { print(1); } else { print(2); }") == [
        "c = true",
        "if_false c goto ELSE1",
        "print 1",
        "goto ENDIF2",
        "label ELSE1",
        "print 2",
        "label ENDIF2",
    ]


def test_while_loop_jumps_back_to_condition():
    assert tac("let i = 0; while (i < 2) { i++; }") == [
        "i = 0",
        "label WHILE1",
        "t1 = i < 2",
        "if_false t1 goto ENDWHILE2",
        "t2 = i",
        "i = i + 1",
        "goto WHILE1",
        "label ENDWHILE2",
    ]


def test_for_loop_without_condition_has_no_exit_jump():
    assert tac("for (;;) { print(1); }") == [
        "label FOR1",
        "print 1",
        "goto FOR1",
        "label ENDFOR2",
    ]


def test_function_and_call():
    assert tac("fn sq(x) { return x * x; } let r = sq(3);") == [
        "func sq(x)",
        "t1 = x * x",
        "return t1",
        "endfunc sq",
        "param 3",
        "t2 = call sq, 1",
        "r = t2",
    ]


def test_bare_return():
    assert tac("fn f() { return; }") == ["func f()", "return", "endfunc f"]


def test_compound_assignment_expands_to_operation_then_store():
    code, asm = generate("let a = 1; a += 2;")
    assert code == ["a = 1", "t1 = a + 2", "a = t1"]
    assert asm[-4:] == ["LOAD a", "LOAD 2", "ADD", "STORE a"]


def test_prefix_increment():
    code, asm = generate("let a = 1; --a;")
    assert code[-2:] == ["t1 = a - 1", "a = t1"]
    assert asm[-4:] == ["LOAD a", "PUSH 1", "SUB", "STORE a"]


def test_unary_not_and_negate():
    assert tac("let b = !true; let n = -5;") == ["t1 = !true", "b = t1", "t2 = -5", "n = t2"]


def test_pseudo_assembly_is_stack_style():
    assert generate("let a = 1 < 2;")[1] == ["LOAD 1", "LOAD 2", "LT", "STORE t1", "STORE a, t1"]


def test_unknown_operator_has_fallback_mnemonic():
    assert op_to_instr("+") == "ADD"
    assert op_to_instr("??") == "OP_??"
