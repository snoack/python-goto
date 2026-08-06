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


def test_jump_out_of_loop_and_survive():
    @with_goto
    def func():
        for i in range(10):
            for j in range(10):
                goto .end
            label .end
        return (i, j)

    assert func() == (9, 0)


def test_jump_out_of_loop_and_live():
    @with_goto
    def func():
        for i in range(10):
            for j in range(10):
                for k in range(10):
                    goto .end
            label .end
        return (i, j, k)

    assert func() == (9, 0, 0)


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


def test_jump_out_of_nested_4_loops_and_survive():
    @with_goto
    def func():
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    for m in range(2):
                        for n in range(2):
                            goto .end
            label .end
        return (i, j, k, m, n)

    assert func() == (1, 0, 0, 0, 0)


def test_large_jumps_in_diff_orders():
    @with_goto
    def func():
        goto .start

        if NonConstFalse:
            label .finalle
            return (i, j, k, m, n, i1, j1, k1, m1, n1, i2, j2, k2, m2, n2)

        label .start
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    for m in range(2):
                        for n in range(2):
                            goto .end
        label .end
        for i1 in range(2):
            for j1 in range(2):
                for k1 in range(2):
                    for m1 in range(2):
                        for n1 in range(2):
                            goto .end2
        label .end2
        for i2 in range(2):
            for j2 in range(2):
                for k2 in range(2):
                    for m2 in range(2):
                        for n2 in range(2):
                            goto .finalle

    assert func() == (0,) * 15


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


def test_jump_out_of_while_true_loop():
    @with_goto
    def func():
        i = 0
        while True:
            i += 1
            goto .out
        label .out
        return i

    assert func() == 1


def test_jump_out_of_while_true_loop_and_survive():
    @with_goto
    def func():
        j = 0
        for i in range(10):
            while True:
                j += 1
                goto .out
            label .out
        return i, j

    assert func() == (9, 10)


def test_jump_out_of_while_true_loop_and_live():
    @with_goto
    def func():
        k = 0
        for i in range(10):
            for j in range(10):
                while True:
                    k += 1
                    goto .out
            label .out
        return i, j, k

    assert func() == (9, 0, 10)


def test_jump_out_of_while_loop_and_live():
    @with_goto
    def func():
        k = 0
        for i in range(10):
            for j in range(4):
                while k < 5:
                    k += 1
                    goto .out
            label .out
        return i, j, k

    assert func() == (9, 3, 5)


class Context:
    def __init__(self):
        self.enters = 0
        self.exits = 0

    def __enter__(self):
        self.enters += 1
        return self

    def __exit__(self, a, b, c):
        self.exits += 1
        return self

    def data(self):
        return (self.enters, self.exits)


def test_jump_out_of_with_block():
    @with_goto
    def func():
        with Context() as c:
            goto .out
        label .out
        return c.data()

    assert func() == (1, 0)


def test_jump_out_of_with_block_and_survive():
    @with_goto
    def func():
        c = Context()
        for i in range(3):
            with c:
                goto .out
            label .out
        return (i, c.data())

    assert func() == (2, (3, 0))


def test_jump_out_of_with_block_and_live():
    @with_goto
    def func():
        c = Context()
        for i in range(3):
            for j in range(3):
                with c:
                    goto .out
            label .out
        return (i, j, c.data())

    assert func() == (2, 0, (3, 0))


def test_jump_into_with_block():
    def func():
        with Context() as c:
            label .block
        goto .block
        return c

    pytest.raises(SyntaxError, with_goto, func)


def test_generator():
    @with_goto
    def func():
        yield 0
        yield 1
        goto .x
        yield 2
        yield 3
        label .x
        yield 4
        yield 5

    assert tuple(func()) == (0, 1, 4, 5)


def test_jump_out_of_try_except_block():
    @with_goto
    def func():
        try:
            rv = None
            goto .end
        except Exception:
            rv = 'except'
        label .end
        return rv

    assert func() is None


def test_jump_out_of_try_except_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = None
                    goto .end
                except Exception:
                    rv = 'except'
                label .end
        return (i, j, rv)

    assert func() == (2, 2, None)


def test_jump_out_of_try_finally_block():
    @with_goto
    def func():
        try:
            rv = None
            goto .end
        finally:
            rv = 'finally'
        label .end
        return rv

    assert func() is None


def test_jump_out_of_try_finally_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = None
                    goto .end
                finally:
                    rv = 'finally'
                label .end
        return (i, j, rv)

    assert func() == (2, 2, None)


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


def test_jump_out_of_try_block_and_survive():
    @with_goto
    def func():
        for i in range(10):
            try:
                rv = None
                goto .end
            except Exception:
                rv = 'except'
            finally:
                rv = 'finally'
            label .end
        return (i, rv)

    assert func() == (9, None)


def test_jump_out_of_try_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = None
                    goto .end
                except Exception:
                    rv = 'except'
                finally:
                    rv = 'finally'
                label .end
        return (i, j, rv)

    assert func() == (2, 2, None)


def test_jump_into_try_block():
    def func():
        try:
            label .block
        except Exception:
            pass
        goto .block

    pytest.raises(SyntaxError, with_goto, func)


def test_jump_out_of_except_block_wo_finally():
    @with_goto
    def func():
        try:
            rv = 1 / 0
        except Exception:
            rv = 'except'
            goto .end
        label .end
        return rv

    assert func() == 'except'


def test_jump_out_of_except_block_wo_finally_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = 1 / 0
                except Exception:
                    rv = 'except'
                    goto .end
            label .end
        return (i, j, rv)

    assert func() == (2, 0, 'except')


def test_jump_out_of_except_block():
    @with_goto
    def func():
        try:
            rv = 1 / 0
        except Exception:
            rv = 'except'
            goto .end
        finally:
            rv = 'finally'
        label .end
        return rv

    assert func() == 'except'


def test_jump_out_of_except_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = 1 / 0
                except Exception:
                    rv = 'except'
                    goto .end
                finally:
                    rv = 'finally'
            label .end
        return (i, j, rv)

    assert func() == (2, 0, 'except')


def test_jump_out_of_bare_except_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = 1 / 0
                except:  # noqa: E722
                    rv = 'except'
                    goto .end
                finally:
                    rv = 'finally'
            label .end
        return (i, j, rv)

    assert func() == (2, 0, 'except')


"""def test_jump_into_except_block():
    def func():
        try:
            pass
        except:
            label .block
            pass
        goto .block

    pytest.raises(SyntaxError, with_goto, func)"""


def test_jump_out_of_finally_block_w_except():
    @with_goto
    def func():
        try:
            rv = None
        except Exception:
            rv = 'except'
        finally:
            rv = 'finally'
            goto .end
            rv = 'end'
        label .end
        return rv

    assert func() == 'finally'


def test_jump_out_of_finally_block_w_except_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = None
                except Exception:
                    rv = 'except'
                finally:
                    rv = 'finally'
                    goto .end
                    rv = 'end'
            label .end
        return i, j, rv

    assert func() == (2, 0, 'finally')


def test_jump_out_of_finally_block():
    @with_goto
    def func():
        try:
            rv = None
        finally:
            rv = 'finally'
            goto .end
            rv = 'end'
        label .end
        return rv

    assert func() == 'finally'


def test_jump_out_of_finally_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = None
                finally:
                    rv = 'finally'
                    goto .end
                    rv = 'end'
            label .end
        return i, j, rv

    assert func() == (2, 0, 'finally')


def test_jump_out_of_try_in_except_in_finally_and_live():
    @with_goto
    def func():
        for i in range(3):
            for j in range(3):
                try:
                    rv = None
                finally:
                    rv = 'finally'
                    try:
                        rv = 1 / 0
                    except Exception:
                        rv = 'except'
                        try:
                            rv = 'try'
                            goto .end
                        except Exception:
                            rv = 'except2'
                        finally:
                            rv = 'finally2'
                    rv = 'end'
            label .end
        return i, j, rv

    assert func() == (2, 0, 'try')


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


def test_code_is_not_copy():
    def outer_func():
        @with_goto
        def inner_func():
            goto .test
            label .test
        return inner_func

    assert outer_func() is not outer_func()
    assert outer_func().__code__ is outer_func().__code__
