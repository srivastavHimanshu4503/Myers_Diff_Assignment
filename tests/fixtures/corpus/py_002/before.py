def process_data(values):
    result = []
    for value in values:
        if value > 0:
            result.append(value * 2)
    return result
