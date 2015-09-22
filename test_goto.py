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

def test_range_as_function():
	ns = {}
	exec('\n'.join(['def func():'] + ['\t' + x for x in CODE.splitlines() + ['return result']]), ns)
	assert with_goto(ns['func'])() == EXPECTED

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

def test_jump_out_of_nested_4_loops():
	@with_goto
	def func():
		for i in range(2):
			for j in range(2):
				for k in range(2):
					for m in range(2):
						goto .end
		label .end
		return (i, j, k, m)

	assert func() == (0, 0, 0, 0)

def test_jump_out_of_nested_5_loops():
	def func():
		for i in range(2):
			for j in range(2):
				for k in range(2):
					for m in range(2):
						for n in range(2):
							goto .end
		label .end
		return (i, j, k, m, n)

	pytest.raises(SyntaxError, with_goto, func)

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
		except:
			rv = 'except'
		finally:
			rv = 'finally'
		label .end
		return rv
	
	assert func() == None

def test_jump_into_try_block():
	def func():
		try:
			label .block
		except:
			pass
		goto .block

	pytest.raises(SyntaxError, with_goto, func)

def test_jump_to_unkown_label():
	def func():
		goto .unknown

	pytest.raises(SyntaxError, with_goto, func)

def test_function_is_copy():
	def func():
		pass

	func.foo = 'bar'
	newfunc = with_goto(func)

	assert newfunc is not func
	assert newfunc.foo == 'bar'
