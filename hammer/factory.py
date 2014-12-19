from collections import defaultdict

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.python import log

from hammer.protocols.handshake import HammerHandshakeProtocol


class HammerFactory(Factory):

    protocol = HammerHandshakeProtocol

    def __init__(self, config, name):
        """
        Create a factory and world.

        ``name`` is the string used to look up factory-specific settings from
        the configuration.

        :param str name: internal name of this factory
        """

        self.name = name
        self.config = config
        self.config_name = "world %s" % name

        self.protocols = dict()
        self.connectedIPs = defaultdict(int)

    def startFactory(self):
        log.msg("Starting factory for world %s" % self.name)

        log.msg("Successfully setup world %s" % self.name)

    def shutdownFactory(self):
        """
        Called before factory stops listening on ports. Used to perform
        shutdown tasks.
        """

        log.msg("Shutting down world %s" % self.name)

#    def buildProtocol(self, addr):
#        """
#        Create a Protocol
#
#        This overridden method solves entity race conditions and allows the
#        proper protocol to be loaded for the player
#        """
#
#        # Get protocol version
#        pass
