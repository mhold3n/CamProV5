class TomlDecodeError(ValueError):
    """Exception raised for TOML decoding errors."""
    pass


def dumps(data):
    """Serialize a simple dict to a TOML string.

    Only handles flat dictionaries with primitive types.
    """
    lines = []
    for key, value in data.items():
        if isinstance(value, str):
            value_repr = f'"{value}"'
        elif isinstance(value, bool):
            value_repr = 'true' if value else 'false'
        else:
            value_repr = str(value)
        lines.append(f"{key} = {value_repr}")
    return "\n".join(lines)


def loads(toml_str):
    """Parse a very small subset of TOML into a dictionary.

    Supports only flat key-value pairs where values are numbers, booleans, or
    quoted strings. Raises :class:`TomlDecodeError` for unsupported syntax.
    """
    result = {}
    for line in toml_str.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise TomlDecodeError(f"Invalid line: {line}")
        key, value = [part.strip() for part in line.split('=', 1)]
        if value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]
        elif value.lower() in {'true', 'false'}:
            result[key] = value.lower() == 'true'
        else:
            try:
                if '.' in value or 'e' in value.lower():
                    result[key] = float(value)
                else:
                    result[key] = int(value)
            except ValueError as e:
                raise TomlDecodeError(str(e))
    return result
