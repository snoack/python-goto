import dis
import struct
import ctypes
import types
import itertools

_STRUCT1 = struct.Struct('<BHBHB')
_STRUCT2 = struct.Struct('<BH')
_NOP = struct.pack('B', dis.opmap['NOP'])

if hasattr(lambda: 0, '__code__'):
	_FUNC_CODE_ATTRIBUTE = '__code__'  # PY3
else:
	_FUNC_CODE_ATTRIBUTE = 'func_code' # PY2

def _make_code(code, codestring):
	args = [
		code.co_argcount,  code.co_nlocals,     code.co_stacksize,
		code.co_flags,     codestring,          code.co_consts,
		code.co_names,     code.co_varnames,    code.co_filename,
		code.co_name,      code.co_firstlineno, code.co_lnotab,
		code.co_freevars,  code.co_cellvars
	]

	try:
		args.insert(1, code.co_kwonlyargcount)  # PY3
	except AttributeError:
		pass

	return types.CodeType(*args)

def _find_instructions(code, name):
	for pos in itertools.count():
		try:
			op1, arg1, op2, arg2, op3 = _STRUCT1.unpack_from(code.co_code, pos)
		except struct.error:
			break

		if dis.opname[op1] not in ('LOAD_GLOBAL', 'LOAD_NAME'):
			continue
		if code.co_names[arg1] != name:
			continue
		if dis.opname[op2] != 'LOAD_ATTR':
			continue
		if dis.opname[op3] != 'POP_TOP':
			continue

		yield pos, arg2

def _inject_op(buf, offset, op, arg):
	for i in range(_STRUCT1.size):
		buf[offset + i] = _NOP
	_STRUCT2.pack_into(buf, offset, dis.opmap[op], arg)

def _patch_code(code):
	buf = ctypes.create_string_buffer(code.co_code, len(code.co_code))
	labels = {}

	for pos, arg in _find_instructions(code, 'label'):
		_inject_op(buf, pos, 'JUMP_FORWARD', _STRUCT1.size - _STRUCT2.size)
		labels[arg] = pos + _STRUCT1.size

	for pos, arg in _find_instructions(code, 'goto'):
		target = labels.get(arg)
		if target is not None:
			_inject_op(buf, pos, 'JUMP_ABSOLUTE', target)

	return _make_code(code, buf.raw)

def with_goto(func_or_code):
	if isinstance(func_or_code, types.CodeType):
		return _patch_code(func_or_code)

	code = _patch_code(getattr(func_or_code, _FUNC_CODE_ATTRIBUTE))
	setattr(func_or_code, _FUNC_CODE_ATTRIBUTE, code)
	return func_or_code
