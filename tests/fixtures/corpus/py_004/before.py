def calculate_average(numbers: list[int]) -> float:
    """Calculate arithmetic mean of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
