from __past__ import with_goto

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

def test_with_code():
	ns = {}
	exec(with_goto(compile(CODE, '', 'exec')), ns)
	assert ns['result'] == EXPECTED

def test_as_decorator():
	ns = {}
	exec('\n'.join(['def func():'] + ['\t' + x for x in CODE.splitlines() + ['return result']]), ns)
	assert with_goto(ns['func'])() == EXPECTED
