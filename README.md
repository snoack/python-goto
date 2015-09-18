This module implements a decorator to use `goto` in Python, by rewriting bytecode.

Usage:

```python
from goto import with_goto

@with_goto
def range(start, stop):
	i = start
	result = []

	label .start
	if i == stop:
		goto  .end

	result.append(i)
	i += 1
	goto .start

	label .end
	return result
```
