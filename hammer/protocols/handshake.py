from construct import Container, IfThenElse, OptionalGreedyRange, Peek, Struct
from construct import Switch
from construct import SBInt8, SBInt32, UBInt8, UBInt16, UBInt32, UBInt64
from twisted.internet import protocol, reactor

from hammer.types import ProtoString, ProtoStringNetty, VarInt

from hammer.encodings import ucs2
from codecs import register
register(ucs2)


handshake_netty_4 = Struct(
    "handshake",
    VarInt("protocol"),
    ProtoStringNetty("host"),
    UBInt16("port"),
    VarInt("state")
)

packets_netty = {
    0x00: handshake_netty_4
}

packets_by_name_netty = {
    "handshake": 0x00
}

handshake22 = Struct(
    "handshake22",
    ProtoString("username")
)

handshake39 = Struct(
    "handshake39",
    SBInt8("protocol"),
    ProtoString("username"),
    ProtoString("host"),
    SBInt32("port")
)

handshake_packet = Struct(
    "handshake_packet",
    Peek(SBInt8("peekedVersion")),
    IfThenElse(
        "old_handshake",
        lambda ctx: (ctx.peekedVersion >= 38 and ctx.peekedVersion <= 78),
        handshake39,
        handshake22
    )
)

login22 = Struct(
    "login22",
    UBInt64("22-unused-long"),
    UBInt32("22-unused-int"),
    UBInt8("22-unused-sbyte1"),
    UBInt8("22-unused-sbyte2"),
    UBInt8("22-unused-byte1"),
    UBInt8("22-unused-byte2")
)

login28 = Struct(
    "login28",
    ProtoString("28-unused-emptystring"),
    UBInt32("28-unused-int1"),
    UBInt32("28-unused-int2"),
    UBInt8("28-unused-sbyte1"),
    UBInt8("28-unused-byte1"),
    UBInt8("28-unused-byte2")
)

login_packet = Struct(
    "login",
    UBInt32("protocol"),
    ProtoString("username"),
    Switch(
        "usused-matter",
        lambda ctx: ctx.protocol,
        {
            22: login22,
            23: login22,
            28: login28,
            29: login28,
        },
        default=UBInt8("UNKNOWN-PROTOCOL")
    )
)


packets_by_name = {
    "login": 0x01,
    "handshake": 0x02,
}

packets = {
    0x01: login_packet,
    0x02: handshake_packet,
}

packet_netty = Struct(
    "full_packet",
    VarInt("length"),
    VarInt("header"),
    Switch("payload", lambda ctx: ctx.header, packets_netty)
)

packet = Struct(
    "full_packet",
    UBInt8("header"),
    Switch("payload", lambda ctx: ctx.header, packets)
)

packet_stream = Struct(
    "packet_stream",
    Peek(UBInt8("peeked")),
    OptionalGreedyRange(
        IfThenElse(
            "old_or_new",
            lambda ctx: ctx.peeked not in [chr(1), chr(2)],
            packet_netty,
            packet,
        )
    ),
    OptionalGreedyRange(
        UBInt8("leftovers")
    )
)


def make_packet(packet, *args, **kwargs):
    if packet not in packets_by_name:
        print "Couldn't create unsupported packet: %s" % packet
        return ""

    header = packets_by_name[packet]
    print "0%.2x" % header

    for arg in args:
        kwargs.update(dict(arg))

    container = Container(**kwargs)
    payload = packets[header].build(container)

    print "Making packet: <%s> (0x%.2x)" % (packet, header)
    print payload

    return chr(header)+payload


def parse_packets(buff):
    container = packet_stream.parse(buff)

    l = [(i.header, i.payload) for i in container.old_or_new]
    leftovers = "".join(chr(i) for i in container.leftovers)

    for header, payload in l:
        print "Parsed packet 0x%.2x" % header
        print payload

    return l, leftovers


class Hammer(protocol.Protocol):

    buff = ""
    protocol_found = False

    def write_packet(self, header, **payload):
        self.transport.write(make_packet(header, **payload))

    def dataReceived(self, data):
        self.buff += data

        packets, self.buff = parse_packets(self.buff)

        for header, payload in packets:
            if header == packets_by_name["handshake"]:
                if 'protocol' in payload.old_handshake.keys():
                    self.protocol_found = True
                    print "protocol: %d" % payload.old_handshake.protocol
                else:
                    container = Container(username="-")
                    payload = handshake22.build(container)

                    self.transport.write(chr(header)+payload)

            elif (header == packets_by_name["login"] and
                  not self.protocol_found):
                self.protocol_found = True
                print "protocol: %d" % payload.protocol

            elif header == packets_by_name_netty["handshake"]:
                if payload.state == 2:
                    self.protocol_found = True
                    print "protocol: %d" % payload.protocol
