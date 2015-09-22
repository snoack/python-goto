import dis
import struct
import ctypes
import types
import functools

_STRUCT_OP_WITH_ARG = struct.Struct('<BH')
_STRUCT_ATTR_LOOKUP = struct.Struct('<BHBHB')

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

def _is_single_attr_lookup(op1, op2, op3):
	if dis.opname[op1] not in ('LOAD_GLOBAL', 'LOAD_NAME'):
		return False
	if dis.opname[op2] != 'LOAD_ATTR':
		return False
	if dis.opname[op3] != 'POP_TOP':
		return False
	return True

def _find_labels_and_gotos(code):
	block_stack = []
	block_counter = 0

	labels = {}
	gotos = []

	pos = 0
	while True:
		try:
			op1, arg1, op2, arg2, op3 = _STRUCT_ATTR_LOOKUP.unpack_from(code.co_code, pos)
		except struct.error:
			break

		if _is_single_attr_lookup(op1, op2, op3):
			varname = code.co_names[arg1]
			if varname == 'label':
				labels[arg2] = (pos, tuple(block_stack))
			elif varname == 'goto':
				gotos.append((pos, arg2, tuple(block_stack)))

		opname = dis.opname[op1]
		if opname.startswith('SETUP_'):
			block_counter += 1
			block_stack.append(block_counter)
		elif opname == 'POP_BLOCK' and block_stack:
			block_stack.pop()

		if op1 < dis.HAVE_ARGUMENT:
			pos += 1
		else:
			pos += _STRUCT_OP_WITH_ARG.size

	return labels, gotos

def _inject_ops(buf, offset, opname, count):
	ctypes.memset(
		(ctypes.c_char * count).from_address(
			ctypes.addressof(buf) + offset
		), dis.opmap[opname], count
	)

def _patch_code(code):
	labels, gotos = _find_labels_and_gotos(code)
	buf = ctypes.create_string_buffer(code.co_code, len(code.co_code))

	for label_pos, _ in labels.values():
		_inject_ops(buf, label_pos, 'NOP', _STRUCT_ATTR_LOOKUP.size)

	for goto_pos, arg, goto_stack in gotos:
		try:
			label_pos, label_stack = labels[arg]
		except KeyError:
			raise SyntaxError('Unknown label %r' % code.co_names[arg])

		label_depth = len(label_stack)
		if goto_stack[:label_depth] != label_stack:
			raise SyntaxError('Jumps into different blocks are not allowed')

		depth_delta = len(goto_stack) - label_depth
		max_depth_delta = _STRUCT_ATTR_LOOKUP.size - _STRUCT_OP_WITH_ARG.size
		if depth_delta > max_depth_delta:
			raise SyntaxError('Jumps out of more than %d nested blocks are not allowed' % max_depth_delta)

		_inject_ops(buf, goto_pos, 'NOP', _STRUCT_ATTR_LOOKUP.size)
		_inject_ops(buf, goto_pos, 'POP_BLOCK', depth_delta)

		jump_pos = goto_pos + depth_delta
		target = label_pos + _STRUCT_ATTR_LOOKUP.size
		_STRUCT_OP_WITH_ARG.pack_into(buf, jump_pos, dis.opmap['JUMP_ABSOLUTE'], target)

	return _make_code(code, buf.raw)

def with_goto(func_or_code):
	if isinstance(func_or_code, types.CodeType):
		return _patch_code(func_or_code)

	return functools.update_wrapper(
		types.FunctionType(
			_patch_code(func_or_code.__code__),
			func_or_code.__globals__,
			func_or_code.__name__,
			func_or_code.__defaults__,
			func_or_code.__closure__,
		),
		func_or_code
	)
