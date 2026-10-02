def calculate_average(numbers: list[int]) -> float:
    """Calculate arithmetic mean of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
