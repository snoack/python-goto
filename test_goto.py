import pytest
from goto import with_goto

NonConstFalse = False

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


def test_jump_into_loop_iter_param():
    @with_goto
    def func():
        my_iter = iter(range(5))
        goto.param .loop = my_iter
        for i in range(10):
            label .loop
        return i, sum(1 for _ in my_iter)

    assert func() == (4, 0)


def test_jump_into_loop_iter_params():
    @with_goto
    def func():
        my_iter = iter(range(5))
        goto.params .loop = my_iter,
        for i in range(10):
            label .loop
        return i, sum(1 for _ in my_iter)

    assert func() == (4, 0)


def test_jump_into_loop_iterable_param():
    @with_goto
    def func():
        goto.param .loop = range(5)
        for i in range(10):
            label .loop
        return i

    assert func() == 4


def test_jump_into_loop_bad_params():
    @with_goto
    def func():
        goto.param .loop = 1
        for i in range(10):
            label .loop
        return i

    pytest.raises(TypeError, func)


def test_jump_into_loop_params_not_seq():
    @with_goto
    def func():
        goto.params .loop = iter(range(5))
        for i in range(10):
            label .loop
        return i

    pytest.raises(TypeError, func)


def test_jump_into_loop_param_with_index():
    @with_goto
    def func():
        lst = []
        i = -1
        goto.param .loop = iter(range(5))
        for i in range(10):
            label .loop
            lst.append(i)
        return lst

    assert func() == [-1, 0, 1, 2, 3, 4]


def test_jump_into_loop_param_without_index():
    @with_goto
    def func():
        lst = []
        goto.param .loop = iter(range(5))
        for i in range(10):
            label .loop
            lst.append(i)
        return lst

    pytest.raises(UnboundLocalError, func)


def test_jump_into_2_loops_and_live():
    @with_goto
    def func():
        for i in range(3):
            c = 0
            goto.params .loop = iter(range(3)), iter(range(10))
            for j in None:
                for k in range(2):
                    label .loop
                    c += 1
        return i, c

    assert func() == (2, 11 + 6)


def test_jump_out_then_back_in_for_loop_and_survive():
    @with_goto
    def func():
        it1 = iter(range(5))
        cc = 0
        for i in it1:
            it2 = iter(range(4))
            for j in it2:
                goto .out
                raise None
                label .back

        if NonConstFalse:
            label .out
            cc += 1
            goto.params .back = it1, it2
        return cc, i, j

    assert func() == (20, 4, 3)


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


def test_jump_across_loops_with_param():
    @with_goto
    def func():
        for i in range(10):
            goto.param .other_loop = iter(range(3))

        for i in range(10):
            label .other_loop

        return i

    assert func() == 2


def test_jump_across_loops_with_param_and_live():
    @with_goto
    def func():
        for i in range(5):
            for j in range(10):
                for k in range(10):
                    goto.param .other_loop = iter(range(3))

            for j in range(10):
                label .other_loop

        return (i, j)

    assert func() == (4, 2)


def test_jump_into_with_unneeded_params_and_live():
    @with_goto
    def func():
        for i in range(10):
            j = 0
            goto.params .not_loop = ()
            j = 1
            label .not_loop
        return (i, j)

    assert func() == (9, 0)


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


def test_jump_into_while_true_loop():
    @with_goto
    def func():
        x = 1
        goto .inside
        x += 1
        while True:
            x += 1
            label .inside
            if x == 1:
                break
        return x

    assert func() == 1


def test_jump_into_while_true_loop_and_survive():
    @with_goto
    def func():
        x = 0
        for i in range(10):
            goto .inside
            while True:
                x += 1
                label .inside
                break
        return i, x

    assert func() == (9, 0)


def test_jump_into_while_loop():
    @with_goto
    def func():
        c, x = 0, 0
        goto .inside
        while x < 10:
            x += 1
            label .inside
            c += 1
        return c, x

    assert func() == (11, 10)


def test_jump_into_while_loop_and_survive():
    @with_goto
    def func():
        c, x = 0, 0
        for i in range(5):
            goto .inside
            while x < 5:
                x += 1
                label .inside
                c += 1
        return i, c, x

    assert func() == (4, 10, 5)


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


def test_jump_into_with_block_without_params():
    def func():
        with Context() as c:
            label .block
        goto .block
        return c

    pytest.raises(SyntaxError, with_goto, func)


def test_jump_into_with_block_with_param():
    @with_goto
    def func():
        c = Context()
        goto.param .block = c
        with 123 as c:
            label .block
        return c.data()

    assert func() == (0, 1)


def test_jump_into_with_block_with_params():
    @with_goto
    def func():
        c = Context()
        goto.params .block = c,
        with 123 as c:
            label .block
        return c.data()

    assert func() == (0, 1)


def test_jump_into_with_block_and_survive():
    @with_goto
    def func():
        c = Context()
        for i in range(10):
            goto.param .block = c
            with 123 as c:
                label .block
        return i, c.data()

    assert func() == (9, (0, 10))


def test_jump_into_with_block_with_bad_params():
    @with_goto
    def func():
        with Context() as c:
            label .block
        goto.param .block = 123
        return c

    pytest.raises(AttributeError, func)


def test_jump_into_with_block_with_bad_exit_params():
    class BadAttr:
        __exit__ = 123

    @with_goto
    def func():
        with Context() as c:
            label .block
        goto.param .block = BadAttr
        return c

    pytest.raises(TypeError, func)


def test_jump_out_then_in_with_block_and_survive():
    @with_goto
    def func():
        c = Context()
        cc = 0
        for i in range(10):
            with c:
                goto .out
                cc -= 100
                label .back

            if NonConstFalse:
                label .out
                cc += 1
                goto.param .back = c

        return i, cc, c.data()

    assert func() == (9, 10, (10, 10))


def test_jump_out_then_in_2_nested_with_blocks_and_survive():
    @with_goto
    def func():
        c1 = Context()
        c2 = Context()
        cc = 0
        for i in range(11):
            with c1:
                if i != 10:
                    with c2:
                        goto .out
                        cc -= 100
                        label .back

            if NonConstFalse:
                label .out
                cc += 1
                goto.params .back = c1, c2

        return i, cc, c1.data(), c2.data()

    assert func() == (10, 10, (11, 11), (10, 10))


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
    @with_goto
    def func():
        rv = 0
        goto .block
        try:
            rv = 1
            label .block
        except Exception:
            rv = 2
        finally:
            rv = 3
        return rv

    assert func() == 3


def test_jump_into_try_except_block_and_survive():
    @with_goto
    def func():
        for i in range(10):
            rv = 0
            goto .block
            try:
                rv = 1
                label .block
            except Exception:
                rv = 2
        return i, rv

    assert func() == (9, 0)


def test_jump_into_try_finally_block_and_survive():
    @with_goto
    def func():
        for i in range(10):
            rv, fv = 0, 0
            goto .block
            try:
                rv = 1
                label .block
            finally:
                fv = 1
        return i, rv, fv

    assert func() == (9, 0, 1)


def test_jump_into_try_block_and_survive():
    @with_goto
    def func():
        for i in range(10):
            rv, fv = 0, 0
            goto .block
            try:
                rv = 1
                label .block
            except Exception:
                rv = 2
            finally:
                fv = 1
        return i, rv, fv

    assert func() == (9, 0, 1)


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


def test_jump_into_except_block():
    @with_goto
    def func():
        i = 1
        goto .block
        try:
            i = 2
        except Exception:
            label .block
            i = 3
        return i

    assert func() == 3


def test_jump_into_except_block_and_live():
    @with_goto
    def func():
        for i in range(10):
            j = 1
            goto .block
            try:
                j = 2
            except Exception:
                label .block
                j = 3
        return i, j


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


def test_jump_into_finally_block():
    @with_goto
    def func():
        rv = 1
        goto .fin
        try:
            rv = 1 / 0
        finally:
            label .fin
            rv = 2
        return rv

    assert func() == 2


def test_jump_into_finally_block_and_live():
    @with_goto
    def func():
        for i in range(3):
            rv = 1
            goto .fin
            try:
                rv = 1 / 0
            finally:
                label .fin
                rv = 2
        return i, rv

    assert func() == (2, 2)


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


def test_jump_with_for_break():  # to see it doesn't confuse parser
    @with_goto
    def func():
        for i in range(4):
            goto .x
            break
        label .x
        return i

    assert func() == 0


def test_jump_with_for_continue():  # to see it doesn't confuse parser
    @with_goto
    def func():
        for i in range(4):
            goto .x
            continue
        label .x
        return i

    assert func() == 0


def test_jump_with_for_return():  # to see it doesn't confuse parser
    @with_goto
    def func():
        for i in range(4):
            goto .x
            return
        label .x
        return i

    assert func() == 0


def test_jump_with_while_true_break():  # to see it doesn't confuse parser
    @with_goto
    def func():
        i = 0
        while True:
            i += 1
            goto .x
            break
        label .x
        return i

    assert func() == 1


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
