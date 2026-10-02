def process_data(values):
    result = []
    for value in values:
        if value > 0:
            # Double positive values
            result.append(value * 2)
    return result
