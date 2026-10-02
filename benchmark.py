"""Performance measurement for Myers diff engine.

Measures runtime on specific workloads to identify any performance issues
before considering optimization.

Test cases:
1. 10,000-line common prefix with 1 diff at end
2. 10,000-line common suffix with 1 diff at start
3. Largest real corpus file
4. Fully different 2,000-line files (worst case for O(D²) memory)
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")

from diff_engine.line_diff import diff_lines, read_file, split_lines
from diff_engine.myers import myers_diff


def measure_diff(name, before_lines, after_lines):
    """Measure diff performance and return metrics."""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    print(f"Before: {len(before_lines):,} lines")
    print(f"After:  {len(after_lines):,} lines")
    
    # Warm-up run
    _ = diff_lines(before_lines, after_lines)
    
    # Timed run
    start_time = time.perf_counter()
    edits = diff_lines(before_lines, after_lines)
    elapsed = time.perf_counter() - start_time
    
    # Count operations
    operations = {
        "equal": 0,
        "delete": 0,
        "insert": 0,
    }
    
    for edit in edits:
        operations[edit.operation] += 1
    
    D = operations["delete"] + operations["insert"]
    
    print(f"D (edits): {D:,}")
    print(f"  Deletes: {operations['delete']:,}")
    print(f"  Inserts: {operations['insert']:,}")
    print(f"  Equal:   {operations['equal']:,}")
    print(f"Time: {elapsed*1000:.2f} ms")
    print(f"Throughput: {(len(before_lines) + len(after_lines)) / elapsed:,.0f} lines/sec")
    
    return {
        "name": name,
        "before_lines": len(before_lines),
        "after_lines": len(after_lines),
        "D": D,
        "time_ms": elapsed * 1000,
        "operations": operations,
    }


def generate_common_prefix_test():
    """10,000-line common prefix, 1 diff at end."""
    common = [f"Line {i}\n" for i in range(10000)]
    before = common + ["BEFORE\n"]
    after = common + ["AFTER\n"]
    return "10k common prefix + 1 diff", before, after


def generate_common_suffix_test():
    """10,000-line common suffix, 1 diff at start."""
    common = [f"Line {i}\n" for i in range(10000)]
    before = ["BEFORE\n"] + common
    after = ["AFTER\n"] + common
    return "1 diff + 10k common suffix", before, after


def generate_fully_different_test():
    """2,000 fully different lines (worst case for O(D²) memory)."""
    before = [f"Before line {i}\n" for i in range(2000)]
    after = [f"After line {i}\n" for i in range(2000)]
    return "2k fully different lines", before, after


def find_largest_corpus_file():
    """Find and load the largest corpus file."""
    corpus_dir = Path("tests/fixtures/corpus")
    largest_size = 0
    largest_fixture = None
    
    for fixture_dir in corpus_dir.iterdir():
        if not fixture_dir.is_dir():
            continue
        
        for file in fixture_dir.glob("before.*"):
            size = file.stat().st_size
            if size > largest_size:
                largest_size = size
                largest_fixture = (fixture_dir, file)
    
    if not largest_fixture:
        return None
    
    fixture_dir, before_file = largest_fixture
    after_file = fixture_dir / before_file.name.replace("before", "after")
    
    before_text = read_file(str(before_file))
    after_text = read_file(str(after_file))
    
    before_lines, _ = split_lines(before_text)
    after_lines, _ = split_lines(after_text)
    
    return f"Largest corpus file ({fixture_dir.name})", before_lines, after_lines


def main():
    """Run all performance measurements."""
    print("Myers Diff Engine - Performance Measurement")
    print("=" * 60)
    print("\nMeasuring performance on specific workloads to identify")
    print("any bottlenecks before considering optimization.\n")
    
    results = []
    
    # Test 1: Common prefix
    name, before, after = generate_common_prefix_test()
    result = measure_diff(name, before, after)
    results.append(result)
    
    # Test 2: Common suffix
    name, before, after = generate_common_suffix_test()
    result = measure_diff(name, before, after)
    results.append(result)
    
    # Test 3: Largest corpus file
    corpus_test = find_largest_corpus_file()
    if corpus_test:
        name, before, after = corpus_test
        result = measure_diff(name, before, after)
        results.append(result)
    
    # Test 4: Fully different
    name, before, after = generate_fully_different_test()
    result = measure_diff(name, before, after)
    results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")
    
    for result in results:
        print(f"{result['name']:40s} {result['time_ms']:8.2f} ms")
    
    print(f"\n{'='*60}")
    print("ANALYSIS")
    print(f"{'='*60}\n")
    
    # Identify any performance issues
    issues = []
    
    for result in results:
        # Flag if > 1 second
        if result['time_ms'] > 1000:
            issues.append(f"  - {result['name']}: {result['time_ms']:.0f} ms (slow)")
        
        # Flag if throughput < 10k lines/sec
        total_lines = result['before_lines'] + result['after_lines']
        throughput = total_lines / (result['time_ms'] / 1000)
        if throughput < 10000:
            issues.append(f"  - {result['name']}: {throughput:,.0f} lines/sec (low throughput)")
    
    if issues:
        print("Performance issues detected:\n")
        for issue in issues:
            print(issue)
        print("\nOptimization may be warranted.")
    else:
        print("All measurements completed in acceptable time.")
        print("No optimization needed.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
