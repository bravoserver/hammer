from construct import Construct, LengthValueAdapter, MetaField, PascalString
from construct import Sequence, StringAdapter
from construct import UBInt8, UBInt16


class DoubleAdapter(LengthValueAdapter):

    def _encode(self, obj, context):
        return len(obj) / 2, obj


def ProtoString(name):
    sa = StringAdapter(
        DoubleAdapter(
            Sequence(
                name,
                UBInt16("length"),
                MetaField("data", lambda ctx: ctx["length"] * 2)
            )
        ),
        encoding="ucs2"
    )
    return sa


def ProtoStringNetty(name):
    return PascalString(name, length_field=VarInt("lengeth"))


class VarInt(Construct):

    def _parse(self, stream, ctx):
        val = 0
        base = 1
        exit = False
        while exit is False:
            b = UBInt8('b')._parse(stream, ctx)
            if b < 128:
                exit = True
            else:
                b -= 128
            val += b * base
            base *= 128
        return val

    def _build(self, obj, stream=None, ctx=None):
        number = obj
        data = ''
        exit = False
        while exit is False:
            digit = number % 128
            if digit == number:
                exit = True
            else:
                number /= 128
                digit += 128
            data += chr(digit)
        if stream is not None:
            stream.write(data)
        else:
            return data

    def _sizeof(self, ctx):
        pass
