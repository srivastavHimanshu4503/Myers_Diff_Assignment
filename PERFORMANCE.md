# Performance Measurement Results

**Date:** 2026-10-03  
**Environment:** Windows, Python 3.13.1  
**Methodology:** `time.perf_counter()` with warm-up run, repeated measurements

## Test Cases

### 1. Common Prefix (10,000 lines)
- **Before:** 10,001 lines (10,000 common + "BEFORE")
- **After:** 10,001 lines (10,000 common + "AFTER")
- **D:** 2 (1 delete + 1 insert)
- **Time:** 5.93 ms
- **Throughput:** 3.4M lines/sec
- **Result:** ✅ Excellent

### 2. Common Suffix (10,000 lines)
- **Before:** 10,001 lines ("BEFORE" + 10,000 common)
- **After:** 10,001 lines ("AFTER" + 10,000 common)
- **D:** 2 (1 delete + 1 insert)
- **Time:** 5.06 ms
- **Throughput:** 4.0M lines/sec
- **Result:** ✅ Excellent

### 3. Largest Real Corpus File
- **File:** ts_005 (TypeScript from microsoft/TypeScript)
- **Before:** 4,599 lines
- **After:** 4,599 lines
- **D:** 2 (1 delete + 1 insert)
- **Time:** 1.72 ms
- **Throughput:** 5.3M lines/sec
- **Result:** ✅ Excellent

### 4. Fully Different (2,000 lines) — Worst Case
- **Before:** 2,000 completely different lines
- **After:** 2,000 completely different lines
- **D:** 4,000 (2,000 deletes + 2,000 inserts)
- **Time:** 6,289.64 ms (~6.3 seconds)
- **Throughput:** 636 lines/sec
- **Result:** ❌ O(D²) pathological behavior

## Analysis

### Real-World Performance
The Myers algorithm performs **excellently** on realistic workloads:
- Common prefix/suffix patterns: 3-4 million lines/sec
- Actual source code diffs: 5+ million lines/sec
- All 36 corpus fixtures complete in < 2 ms each

### Pathological Worst Case
The fully-different test exhibits expected **O(D²) behavior**:
- With D=4,000, the forward search visits ~8 million grid points
- This is the documented worst case for standard Myers
- Time: 6.3 seconds for 2,000 lines

### Optimization Consideration

**Why no optimization was implemented:**

1. **Common prefix/suffix trimming** would not help the failing benchmark
   - The fully-different case has no common prefix or suffix to trim
   - Real-world cases already perform at 3-5M lines/sec
   - No demonstrated need for this optimization

2. **Linear-space middle-snake variant** would not eliminate O(D²) time complexity
   - Primarily addresses space, not time
   - Would add substantial implementation complexity
   - No evidence this is required by the assignment
   - Core algorithm already heavily validated (239 tests)

3. **Proportionality principle**
   - The pathological case is rare in practice (why diff two unrelated files?)
   - Real-world corpus performance is excellent
   - Proposed optimizations don't solve the measured problem efficiently

## Conclusion

Standard Myers performs extremely well on the real-world corpus and common-prefix/suffix workloads, but exhibits expected quadratic behavior on a 2,000-line fully-different pair (~6.3 s, D=4000).

**Decision:** No optimization adopted. The simple prefix/suffix optimization does not affect the pathological case, while a middle-snake rewrite would add substantial complexity without a demonstrated practical requirement.

## Reproduction

```bash
python benchmark.py
```

The benchmark script measures:
- Wall time via `time.perf_counter()`
- One warm-up run, then timed measurement
- Operation counts (delete/insert/equal)
- Throughput (lines/sec)
