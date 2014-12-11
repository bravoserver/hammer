from construct import OptionalGreedyRange, Sequence, StringAdapter, Peek
from construct import LengthValueAdapter, Struct, Switch, Container, IfThenElse
from construct import PascalString
from construct import MetaField, SBInt8, SBInt32, UBInt8, UBInt16
from construct import UBInt32, UBInt64
from twisted.internet import protocol, reactor
from varint import VarInt

from hammerencodings import ucs2
from codecs import register
register(ucs2)

class VarIntLengthAdapter(LengthValueAdapter):
    def _encode(self, obj, ctx):
        return VarInt("lengeth").build(len(obj)), obj


def ProtoStringNew(name):
    return PascalString(name, length_field=VarInt("length"))


handshake = Struct(
    "handshake",
    VarInt("protocol"),
    ProtoStringNew("host"),
    UBInt16("port"),
    VarInt("state")
)

packets_by_name = {
    "handshake": 0x00,
}

packets = {
    0x00: handshake,
}

packet_stream = Struct(
    "packet_stream",
    OptionalGreedyRange(
        VarIntLengthAdapter(
            Sequence(
                "packet_sequence",
                VarInt("length"),
                Struct(
                    "full_packet",
                    VarInt("header"),
                    Switch("payload", lambda ctx: ctx.header, packets)
                )
            )
        )
    ),
    OptionalGreedyRange(
        VarInt("leftovers")
    )
)

def parse_packets(buff):
    container = packet_stream.parse(buff)

    l = [(i.header, i.payload) for i in container.full_packet]
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
            print "header: %s" % header
            if header == packets_by_name["handshake"]:
                if 'protocol' in payload.keys():
                    self.protocol_found = True
                    print "protocol = %s" % payload.protocol
                else:
                    print "nope"

def main():
    factory = protocol.ServerFactory()
    factory.protocol = Hammer
    reactor.listenTCP(25565, factory)
    reactor.run()

if __name__ == '__main__':
    main()
