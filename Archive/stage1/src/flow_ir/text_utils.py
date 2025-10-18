from __future__ import annotations

import re

_CAMEL_CASE_PATTERN = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_UNDERSCORE_PATTERN = re.compile(r"_+")
_ARG_SPLIT_PATTERN = re.compile(r"\s*,\s*")


def _humanize_identifier(identifier: str) -> str:
    identifier = identifier.strip()
    if not identifier:
        return identifier
    identifier = _CAMEL_CASE_PATTERN.sub(" ", identifier)
    identifier = _UNDERSCORE_PATTERN.sub(" ", identifier)
    identifier = identifier.replace(".", " ").replace("->", " to ")
    identifier = identifier.replace("::", " ")
    identifier = identifier.replace("[", " ").replace("]", " ")
    identifier = identifier.replace("(", "").replace(")", "")
    identifier = re.sub(r"\s+", " ", identifier)
    return identifier.strip()


def summarize_expression(expr: str) -> str:
    expr = expr.strip()
    if not expr:
        return ""
    if expr.startswith("return "):
        return summarize_statement(expr)
    if expr.startswith("if "):
        cond = expr[3:].strip()
        return f"Check whether {summarize_condition(cond)}."
    if expr.startswith("elif "):
        cond = expr[5:].strip()
        return f"Otherwise, check whether {summarize_condition(cond)}."
    if expr.startswith("else"):
        return "Handle the alternative branch."
    return summarize_statement(expr)


def summarize_condition(cond: str) -> str:
    cond = cond.strip()
    if not cond:
        return "the condition holds"
    tokens = cond.replace("==", " equals ").replace("!=", " does not equal ")
    tokens = tokens.replace(">=", " is at least ").replace("<=", " is at most ")
    tokens = tokens.replace(">", " is greater than ").replace("<", " is less than ")
    tokens = tokens.replace(" and ", " and ").replace(" or ", " or ")
    tokens = tokens.replace(" not ", " not ")
    tokens = tokens.replace(" in ", " in ")
    tokens = tokens.replace(" is ", " is ")
    tokens = re.sub(r"\s+", " ", tokens)
    return tokens.strip()


def summarize_loop(header: str) -> str:
    header = header.strip()
    if header.startswith("for "):
        loop_header = header[4:].strip()
        if " in " in loop_header:
            target, iterable = loop_header.split(" in ", 1)
            return f"Repeat for each { _humanize_identifier(target) } in { _humanize_identifier(iterable) }."
    if header.startswith("while "):
        cond = header[6:].strip()
        return f"Loop while {summarize_condition(cond)}."
    if header.startswith("async for "):
        loop_header = header[10:].strip()
        if " in " in loop_header:
            target, iterable = loop_header.split(" in ", 1)
            return f"Asynchronously iterate for each { _humanize_identifier(target) } in { _humanize_identifier(iterable) }."
    if header.startswith("do-while "):
        cond = header[9:].strip()
        return f"Repeat until {summarize_condition(cond)} becomes false."
    return f"Repeat according to {header}."


def summarize_statement(statement: str) -> str:
    statement = statement.strip("; ").strip()
    if not statement:
        return "Perform the next action."

    if statement.startswith("return"):
        expr = statement[6:].strip()
        if expr:
            return f"Return {summarize_value(expr)}."
        return "Return from the function."

    if statement.startswith("raise"):
        expr = statement[5:].strip()
        if expr:
            return f"Raise {summarize_value(expr)}."
        return "Raise an exception."

    if "=" in statement and not statement.startswith("if "):
        left, right = statement.split("=", 1)
        if "==" not in statement:
            return f"Set {summarize_value(left)} to {summarize_value(right)}."

    if statement.endswith(")"):
        name, _, args = statement.partition("(")
        args = args[:-1]  # remove trailing ')'
        readable_name = _humanize_identifier(name)
        if args.strip():
            args_list = [_humanize_identifier(arg) for arg in _ARG_SPLIT_PATTERN.split(args)]
            args_str = ", ".join(args_list)
            return f"Call {readable_name} with {args_str}."
        return f"Call {readable_name}."

    readable = _humanize_identifier(statement)
    return readable if readable else "Execute the next step."


def summarize_value(expr: str) -> str:
    expr = expr.strip()
    if not expr:
        return "the value"

    if expr.startswith(("\"", "'")) and expr.endswith(("\"", "'")):
        return expr.strip("\"'")

    expr = expr.replace("**", " to the power of ")
    expr = expr.replace("*", " multiplied by ")
    expr = expr.replace("/", " divided by ")
    expr = expr.replace("+", " plus ")
    expr = expr.replace("-", " minus ")
    expr = expr.replace("%", " modulo ")
    expr = re.sub(r"\s+", " ", expr)
    return expr.strip()
