def validate_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if len(cleaned) < 4 or not cleaned.isalnum():
        raise ValueError("Invalid symbol. Use formats like BTCUSDT.")
    return cleaned

def validate_positive_float(value: str, field_name: str) -> float:
    try:
        val = float(value.strip())
        if val <= 0:
            raise ValueError
        return val
    except ValueError:
        raise ValueError(f"{field_name} must be a number greater than 0.")