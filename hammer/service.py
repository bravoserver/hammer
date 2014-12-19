from ConfigParser import SafeConfigParser

from twisted.application.service import MultiService
from twisted.application.strports import service as strports_service
from twisted.python import log

from hammer.factory import HammerFactory


def services_for_endpoints(interfaces, factory):
    l = []
    for interface in interfaces:
        server = strports_service(interface, factory)
        server.setName("%s (%s)" % (factory.name, interface))
        l.append(server)
    return l


class HammerService(MultiService):

    def __init__(self, path):

        MultiService.__init__(self)

        # Read config
        self.config = SafeConfigParser()
        self.config.readfp(path.open("rb"))

        # Start all the services
        self.configure_services()

    def configure_services(self):

        # For each section, setup any interfaces as services
        for section in self.config.sections():
            if section.startswith("world "):
                factory = HammerFactory(self.config, section[6:])
                interfaces = []

                for w in self.config.get(section, "interfaces").split(","):
                    interfaces.append(w.strip())

                for service in services_for_endpoints(interfaces, factory):
                    self.addService(service)

service = HammerService
