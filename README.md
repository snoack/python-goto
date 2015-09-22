# goto

A function decorator to use `goto` in Python.
Tested on Python 2.6 through 3.5 and PyPy.

[![Build Status](https://travis-ci.org/snoack/python-goto.svg?branch=master)](https://travis-ci.org/snoack/python-goto)

[![](https://imgs.xkcd.com/comics/goto.png)](https://xkcd.com/292/)

## Usage

```python
from goto import with_goto

@with_goto
def range(start, stop):
	i = start
	result = []

	label .begin
	if i == stop:
		goto .end

	result.append(i)
	i += 1
	goto .begin

	label .end
	return result
```

## Implementation

Note that `label .begin` and `goto .begin` is regular Python syntax to retrieve
the attribute `begin` from the objects with the variable names `label` and
`goto`. However, in the example above these variables aren't defined.
So this code would usually cause a `NameError`. But since it's valid
syntax the function can be parsed, and results in following bytecode:


```
  2           0 LOAD_FAST                0 (start)
              3 STORE_FAST               2 (i)

  3           6 BUILD_LIST               0
              9 STORE_FAST               3 (result)

  5          12 LOAD_GLOBAL              0 (label)
             15 LOAD_ATTR                1 (begin)
             18 POP_TOP

  6          19 LOAD_FAST                2 (i)
             22 LOAD_FAST                1 (stop)
             25 COMPARE_OP               2 (==)
             28 POP_JUMP_IF_FALSE       41

  7          31 LOAD_GLOBAL              2 (goto)
             34 LOAD_ATTR                3 (end)
             37 POP_TOP
             38 JUMP_FORWARD             0 (to 41)

  9     >>   41 LOAD_FAST                3 (result)
             44 LOAD_ATTR                4 (append)
             47 LOAD_FAST                2 (i)
             50 CALL_FUNCTION            1
             53 POP_TOP

 10          54 LOAD_FAST                2 (i)
             57 LOAD_CONST               1 (1)
             60 INPLACE_ADD
             61 STORE_FAST               2 (i)

 11          64 LOAD_GLOBAL              2 (goto)
             67 LOAD_ATTR                1 (begin)
             70 POP_TOP

 13          71 LOAD_GLOBAL              0 (label)
             74 LOAD_ATTR                3 (end)
             77 POP_TOP

 14          78 LOAD_FAST                3 (result)
             81 RETURN_VALUE
```

The `with_goto` decorator then removes the respective bytecode that has been
generated for the attribute lookups of the `label` and `goto` variables, and
injects a `JUMP_ABSOLUTE` instruction for each `goto`:

```
  2           0 LOAD_FAST                0 (start)
              3 STORE_FAST               2 (i)

  3           6 BUILD_LIST               0
              9 STORE_FAST               3 (result)

  5          12 NOP
             13 NOP
             14 NOP
             15 NOP
             16 NOP
             17 NOP
             18 NOP

  6     >>   19 LOAD_FAST                2 (i)
             22 LOAD_FAST                1 (stop)
             25 COMPARE_OP               2 (==)
             28 POP_JUMP_IF_FALSE       41

  7          31 JUMP_ABSOLUTE           78
             34 NOP
             35 NOP
             36 NOP
             37 NOP
             38 JUMP_FORWARD             0 (to 41)

  9     >>   41 LOAD_FAST                3 (result)
             44 LOAD_ATTR                4 (append)
             47 LOAD_FAST                2 (i)
             50 CALL_FUNCTION            1
             53 POP_TOP

 10          54 LOAD_FAST                2 (i)
             57 LOAD_CONST               1 (1)
             60 INPLACE_ADD
             61 STORE_FAST               2 (i)

 11          64 JUMP_ABSOLUTE           19
             67 NOP
             68 NOP
             69 NOP
             70 NOP

 13          71 NOP
             72 NOP
             73 NOP
             74 NOP
             75 NOP
             76 NOP
             77 NOP

 14     >>   78 LOAD_FAST                3 (result)
             81 RETURN_VALUE
```

## Alternative implementation

The idea of `goto` in Python isn't new.
There is [another module](http://entrian.com/goto/) that has been released
as April Fool's joke in 2004. That implementation doesn't touch the bytecode,
but uses a trace function, similar to how debuggers are written.

While this eliminates the need for a decorator, it comes with significant
runtime overhead and a more elaborate implementation. Modifying the bytecode,
on the other hand, is fairly simple and doesn't add overhead at function
execution.
