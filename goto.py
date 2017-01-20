import sys
import dis
import struct
import array
import types
import functools

if sys.version_info >= (3, 6):
    _STRUCT_ARG = struct.Struct('B')

    def _has_arg(opcode):
        return True
else:
    _STRUCT_ARG = struct.Struct('<H')

    def _has_arg(opcode):
        return opcode >= dis.HAVE_ARGUMENT


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


def _parse_instructions(code):
    extended_arg = 0
    extended_arg_offset = None
    pos = 0

    while pos < len(code):
        offset = pos
        if extended_arg_offset is not None:
            offset = extended_arg_offset

        opcode = struct.unpack_from('B', code, pos)[0]
        pos += 1

        oparg = None
        if _has_arg(opcode):
            oparg = _STRUCT_ARG.unpack_from(code, pos)[0] | extended_arg
            pos += _STRUCT_ARG.size

            if opcode == dis.EXTENDED_ARG:
                extended_arg = oparg << _STRUCT_ARG.size * 8
                extended_arg_offset = offset
                continue

        extended_arg = 0
        extended_arg_offset = None
        yield (dis.opname[opcode], oparg, offset)


def _write_instruction(buf, pos, opcode, oparg=0):
    arg_bits = _STRUCT_ARG.size * 8
    extended_arg = oparg >> arg_bits
    if extended_arg != 0:
        pos = _write_instruction(buf, pos, dis.EXTENDED_ARG, extended_arg)
        oparg &= (1 << arg_bits) - 1

    buf[pos] = opcode
    pos += 1
    if _has_arg(opcode):
        _STRUCT_ARG.pack_into(buf, pos, oparg)
        pos += _STRUCT_ARG.size

    return pos


def _find_labels_and_gotos(code):
    labels = {}
    gotos = []

    block_stack = []
    block_counter = 0

    opname1 = oparg1 = offset1 = None
    opname2 = oparg2 = offset2 = None
    opname3 = oparg3 = offset3 = None

    for opname4, oparg4, offset4 in _parse_instructions(code.co_code):
        if opname1 in ('LOAD_GLOBAL', 'LOAD_NAME'):
            if opname2 == 'LOAD_ATTR' and opname3 == 'POP_TOP':
                name = code.co_names[oparg1]
                if name == 'label':
                    labels[oparg2] = (offset1,
                                      offset4,
                                      tuple(block_stack))
                elif name == 'goto':
                    gotos.append((offset1,
                                  offset4,
                                  oparg2,
                                  tuple(block_stack)))
        elif opname1 in ('SETUP_LOOP',
                         'SETUP_EXCEPT', 'SETUP_FINALLY',
                         'SETUP_WITH', 'SETUP_ASYNC_WITH'):
            block_counter += 1
            block_stack.append(block_counter)
        elif opname1 == 'POP_BLOCK' and block_stack:
            block_stack.pop()

        opname1, oparg1, offset1 = opname2, oparg2, offset2
        opname2, oparg2, offset2 = opname3, oparg3, offset3
        opname3, oparg3, offset3 = opname4, oparg4, offset4

    return labels, gotos


def _inject_nop_sled(buf, pos, end):
    while pos < end:
        pos = _write_instruction(buf, pos, dis.opmap['NOP'])


def _patch_code(code):
    labels, gotos = _find_labels_and_gotos(code)
    buf = array.array('B', code.co_code)

    for pos, end, _ in labels.values():
        _inject_nop_sled(buf, pos, end)

    for pos, end, label, origin_stack in gotos:
        try:
            _, target, target_stack = labels[label]
        except KeyError:
            raise SyntaxError('Unknown label {0!r}'.format(code.co_names[label]))

        target_depth = len(target_stack)
        if origin_stack[:target_depth] != target_stack:
            raise SyntaxError('Jump into different block')

        failed = False
        try:
            for i in range(len(origin_stack) - target_depth):
                pos = _write_instruction(buf, pos, dis.opmap['POP_BLOCK'])
            pos = _write_instruction(buf, pos, dis.opmap['JUMP_ABSOLUTE'], target)
        except (IndexError, struct.error):
            failed = True

        if failed or pos > end:
            raise SyntaxError('Jump out of too many nested blocks')

        _inject_nop_sled(buf, pos, end)

    return _make_code(code, buf.tostring())


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
