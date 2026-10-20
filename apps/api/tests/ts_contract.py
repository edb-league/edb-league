"""Valida respostas JSON contra os tipos declarados em web/src/lib/types.ts.

Lê o arquivo TypeScript real (subconjunto usado pelo contrato) e confere formato, nulos,
literais e chaves, inclusive chaves a mais ou a menos.
"""
from __future__ import annotations

import re
from pathlib import Path

TYPES_FILE = Path(__file__).resolve().parents[2] / "web" / "src" / "lib" / "types.ts"
TOKEN = re.compile(r'\s*("(?:[^"\\]|\\.)*"|[A-Za-z_][A-Za-z0-9_]*|\d+|[{}\[\]()<>|&;:,?=])')


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _tokenize(text: str) -> list[str]:
    tokens, pos = [], 0
    text = text.rstrip()
    while pos < len(text):
        match = TOKEN.match(text, pos)
        if not match:
            raise SyntaxError("Token inesperado perto de: " + text[pos:pos + 40])
        tokens.append(match.group(1))
        pos = match.end()
    return tokens


class Parser:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def next(self):
        token = self.t[self.i]
        self.i += 1
        return token

    def expect(self, token):
        got = self.next()
        assert got == token, f"esperava {token!r}, veio {got!r}"

    def declarations(self):
        out = {}
        while self.peek() is not None:
            self.expect("export")
            self.expect("type")
            name = self.next()
            self.expect("=")
            out[name] = self.type()
            if self.peek() == ";":
                self.next()
        return out

    def type(self):
        if self.peek() == "|":
            self.next()
        parts = [self.intersection()]
        while self.peek() == "|":
            self.next()
            parts.append(self.intersection())
        return parts[0] if len(parts) == 1 else ("union", parts)

    def intersection(self):
        parts = [self.postfix()]
        while self.peek() == "&":
            self.next()
            parts.append(self.postfix())
        return parts[0] if len(parts) == 1 else ("inter", parts)

    def postfix(self):
        node = self.primary()
        while self.peek() == "[" and self.t[self.i + 1] == "]":
            self.i += 2
            node = ("array", node)
        return node

    def primary(self):
        token = self.next()
        if token == "(":
            node = self.type()
            self.expect(")")
            return node
        if token == "{":
            fields = {}
            while self.peek() != "}":
                name = self.next()
                optional = self.peek() == "?"
                if optional:
                    self.next()
                self.expect(":")
                fields[name] = (self.type(), optional)
                if self.peek() in (";", ","):
                    self.next()
            self.expect("}")
            return ("obj", fields)
        if token == "[":
            items = [self.type()]
            while self.peek() == ",":
                self.next()
                items.append(self.type())
            self.expect("]")
            return ("tuple", items)
        if token.startswith('"'):
            return ("lit", token[1:-1])
        if token in ("string", "number", "boolean", "null"):
            return (token,)
        if token in ("Omit", "Record"):
            self.expect("<")
            first = self.type()
            self.expect(",")
            second = self.type()
            self.expect(">")
            return (token.lower(), first, second)
        return ("ref", token)


def load_types():
    return Parser(_tokenize(_strip_comments(TYPES_FILE.read_text(encoding="utf-8")))).declarations()


TYPES = load_types()


class Mismatch(AssertionError):
    pass


def _fields(node):
    """Resolve um tipo de objeto para {campo: (tipo, opcional)}."""
    kind = node[0]
    if kind == "ref":
        return _fields(TYPES[node[1]])
    if kind == "obj":
        return node[1]
    if kind == "inter":
        merged = {}
        for part in node[1]:
            merged.update(_fields(part))
        return merged
    if kind == "omit":
        dropped = {n[1] for n in (node[2][1] if node[2][0] == "union" else [node[2]])}
        return {k: v for k, v in _fields(node[1]).items() if k not in dropped}
    raise Mismatch("tipo de objeto inesperado: " + repr(node))


def validate(value, node, path="$"):
    kind = node[0]
    if kind == "ref":
        return validate(value, TYPES[node[1]], path)
    if kind == "union":
        errors = []
        for alt in node[1]:
            try:
                return validate(value, alt, path)
            except Mismatch as exc:
                errors.append(str(exc))
        raise Mismatch(f"{path}: nenhuma alternativa serve ({'; '.join(errors)[:300]})")
    if kind == "null":
        if value is not None:
            raise Mismatch(f"{path}: esperava null, veio {value!r}")
        return
    if kind == "string":
        if not isinstance(value, str):
            raise Mismatch(f"{path}: esperava string, veio {value!r}")
        return
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise Mismatch(f"{path}: esperava número, veio {value!r}")
        return
    if kind == "boolean":
        if not isinstance(value, bool):
            raise Mismatch(f"{path}: esperava booleano, veio {value!r}")
        return
    if kind == "lit":
        if value != node[1]:
            raise Mismatch(f"{path}: esperava {node[1]!r}, veio {value!r}")
        return
    if kind == "array":
        if not isinstance(value, list):
            raise Mismatch(f"{path}: esperava lista, veio {type(value).__name__}")
        for index, item in enumerate(value):
            validate(item, node[1], f"{path}[{index}]")
        return
    if kind == "tuple":
        if not isinstance(value, list) or len(value) != len(node[1]):
            raise Mismatch(f"{path}: esperava tupla de {len(node[1])}")
        for index, (item, sub) in enumerate(zip(value, node[1])):
            validate(item, sub, f"{path}[{index}]")
        return
    if kind == "record":
        if not isinstance(value, dict):
            raise Mismatch(f"{path}: esperava dicionário")
        for key, item in value.items():
            validate(item, node[2], f"{path}.{key}")
        return
    if kind in ("obj", "inter", "omit"):
        fields = _fields(node)
        if not isinstance(value, dict):
            raise Mismatch(f"{path}: esperava objeto, veio {type(value).__name__}")
        required = {k for k, (_, optional) in fields.items() if not optional}
        missing = required - set(value)
        extra = set(value) - set(fields)
        if missing:
            raise Mismatch(f"{path}: faltam chaves {sorted(missing)}")
        if extra:
            raise Mismatch(f"{path}: chaves fora do contrato {sorted(extra)}")
        for key, item in value.items():
            validate(item, fields[key][0], f"{path}.{key}")
        return
    raise Mismatch(f"{path}: tipo não suportado {node!r}")


def check(value, type_name: str, array: bool = False):
    node = ("array", ("ref", type_name)) if array else ("ref", type_name)
    validate(value, node)
