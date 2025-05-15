def calculate_bcc(data: str|bytes) -> bytes:
    """Calculate Block Check Character (BCC) for error detection."""
    if type(data) is bytes:
        pass
    elif type(data) is str:
        data = data.encode('ascii')
    else:    
        raise ValueError(f"Unsupported data type: {type(data)}")
    
    bcc = 0
    for char in data:
        bcc ^= char
    return bytes([bcc])
