# Benchmark suite

Development data results do not establish independent test performance.

| Method | TP | FP | TN | FN | Abstained | Failed/partial | Requests | Input | Output |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| keyword | 4 | 1 | 4 | 7 | 10 | 0 | 0 | 0 | 0 |
| rules | 11 | 0 | 5 | 0 | 4 | 0 | 0 | 0 | 0 |
| llm | 10 | 1 | 4 | 1 | 3 | 0 | 20 | 12147 | 3031 |
| full | 11 | 0 | 5 | 0 | 4 | 0 | 15 | 15563 | 2299 |
| no_alignment | 10 | 0 | 5 | 1 | 5 | 0 | 15 | 15766 | 2367 |
| no_verifier | 10 | 0 | 5 | 1 | 4 | 0 | 15 | 15563 | 2435 |
| no_static | 11 | 0 | 5 | 0 | 4 | 0 | 20 | 12147 | 2983 |
