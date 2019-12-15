import pytest
from goto import with_goto

CODE = '''\
i = 0
result = []

label .start
if i == 10:
    goto .end

result.append(i)
i += 1
goto .start

label .end
'''

EXPECTED = list(range(10))


def test_range_as_code():
    ns = {}
    exec(with_goto(compile(CODE, '', 'exec')), ns)
    assert ns['result'] == EXPECTED


def make_function(code):
    lines = ['def func():']
    for line in code:
        lines.append('    ' + line)
    lines.append('    return result')

    ns = {}
    exec('\n'.join(lines), ns)
    return ns['func']


def test_range_as_function():
    assert with_goto(make_function(CODE.splitlines()))() == EXPECTED


def test_EXTENDED_ARG():
    code = []
    code.append('result = True')
    code.append('goto .foo')
    for i in range(2**16):
        code.append('label .l{0}'.format(i))
    code.append('result = "dead code"')
    code.append('label .foo')
    assert with_goto(make_function(code))() is True


def test_jump_out_of_loop():
    @with_goto
    def func():
        for i in range(10):
            goto .end
        label .end
        return i

    assert func() == 0


def test_jump_into_loop():
    def func():
        for i in range(10):
            label .loop
        goto .loop

    pytest.raises(SyntaxError, with_goto, func)


def test_jump_out_of_nested_2_loops():
    @with_goto
    def func():
        x = 1
        for i in range(2):
            for j in range(2):
                # These are more than 256 bytes of bytecode
                x += x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x
                x += x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x
                x += x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x+x

                goto .end
        label .end
        return (i, j)

    assert func() == (0, 0)


def test_jump_out_of_nested_11_loops():
    @with_goto
    def func():
        x = 1
        for i1 in range(2):
            for i2 in range(2):
                for i3 in range(2):
                    for i4 in range(2):
                        for i5 in range(2):
                            for i6 in range(2):
                                for i7 in range(2):
                                    for i8 in range(2):
                                        for i9 in range(2):
                                            for i10 in range(2):
                                                for i11 in range(2):
                                                    # These are more than
                                                    # 256 bytes of bytecode
                                                    x += x+x+x+x+x+x+x+x+x+x+x
                                                    x += x+x+x+x+x+x+x+x+x+x+x
                                                    x += x+x+x+x+x+x+x+x+x+x+x
                                                    x += x+x+x+x+x+x+x+x+x+x+x
                                                    x += x+x+x+x+x+x+x+x+x+x+x

                                                    goto .end
        label .end
        return (i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11)

    assert func() == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def test_jump_across_loops():
    def func():
        for i in range(10):
            goto .other_loop

        for i in range(10):
            label .other_loop

    pytest.raises(SyntaxError, with_goto, func)


def test_jump_out_of_try_block():
    @with_goto
    def func():
        try:
            rv = None
            goto .end
        except Exception:
            rv = 'except'
        finally:
            rv = 'finally'
        label .end
        return rv

    assert func() is None


def test_jump_into_try_block():
    def func():
        try:
            label .block
        except Exception:
            pass
        goto .block

    pytest.raises(SyntaxError, with_goto, func)


def test_jump_to_unknown_label():
    def func():
        goto .unknown

    pytest.raises(SyntaxError, with_goto, func)


def test_jump_to_ambiguous_label():
    def func():
        label .ambiguous
        goto .ambiguous
        label .ambiguous

    pytest.raises(SyntaxError, with_goto, func)


def test_function_is_copy():
    def func():
        pass

    func.foo = 'bar'
    newfunc = with_goto(func)

    assert newfunc is not func
    assert newfunc.foo == 'bar'
