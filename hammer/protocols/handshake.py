from importlib import import_module

from construct import Container, IfThenElse, OptionalGreedyRange, Peek, Struct
from construct import Switch
from construct import SBInt8, SBInt32, UBInt8, UBInt16, UBInt32, UBInt64
from twisted.internet import protocol, reactor
from twisted.python import log

from hammer.types import ProtoString, ProtoStringNetty, VarInt

from hammer.encodings import ucs2
from codecs import register
register(ucs2)

SHOW_PACKETS = False

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
            lambda ctx: ctx.peeked not in [1, 2],
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
        log.msg("Couldn't create unsupported packet: %s" % packet)
        return ""

    header = packets_by_name[packet]

    for arg in args:
        kwargs.update(dict(arg))

    container = Container(**kwargs)
    payload = packets[header].build(container)

    if SHOW_PACKETS:
        log.msg("Making packet: <%s> (0x%.2x)" % (packet, header))
        log.msg(payload)

    return chr(header)+payload


def parse_packets(buff):
    container = packet_stream.parse(buff)

    l = [(i.header, i.payload) for i in container.old_or_new]
    leftovers = "".join(chr(i) for i in container.leftovers)

    if SHOW_PACKETS:
        for header, payload in l:
            log.msg("Parsed packet 0x%.2x" % header)
            log.msg(payload)

    return l, leftovers


class HammerHandshakeProtocol(protocol.Protocol):

    buff = ""
    protocol_version = None
    loaded_protocol = None

    def write_packet(self, header, **payload):
        self.transport.write(make_packet(header, **payload))

    def extract_protocol(self, data):
        if not self.protocol_version and not self.loaded_protocol:
            self.buff += data
            packets, self.buff = parse_packets(self.buff)

            for header, payload in packets:
                if header == packets_by_name["handshake"]:
                    if 'protocol' in payload.old_handshake.keys():
                        return "prenetty_%d" % (
                            payload.old_handshake.protocol
                        )
                    else:
                        container = Container(username="-")
                        payload = handshake22.build(container)
                        log.msg("sending handshake back")
                        self.transport.write(chr(header)+payload)

                elif (header == packets_by_name["login"] and
                      not self.protocol_version):
                    return "prenetty_%d" % payload.protocol

                elif header == packets_by_name_netty["handshake"]:
                    if payload.state == 2:
                        return "netty_%d" % payload.protocol

    def dataReceived(self, data):

        self.protocol_version = self.extract_protocol(data)

        if self.protocol_version and not self.loaded_protocol:
            try:
                log.msg("Loading protocol: %s" % self.protocol_version)
                p = import_module(self.protocol_version, "hammer.protocols")
                self.loaded_protocol = p
                self.loaded_protocol.connected = 1
                self.loaded_protocol.transport = self.transport
                self.loaded_protocol.connectionMade()
                if self.buff:
                    self.protocol.dataReceived(self.buff)
            except:
                log.msg("Unable to load protocol: %s" % self.protocol_version)
                self.transport.loseConnection()
        elif self.loaded_protocol:
            self.loaded_protocol.dataReceived(data)

    def connectionLost(self, reason):
        if self.loaded_protocol:
            self.loaded_protocol.connectionLost(reason)
