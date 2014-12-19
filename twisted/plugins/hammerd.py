import os
from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python.filepath import FilePath
from twisted.python.usage import Options

class HammerOptions(Options):
    optParameters = [["config", "c", "hammer.cfg", "Configuration file"]]

class HammerServiceMaker(object):

    implements(IPlugin, IServiceMaker)

    tapname = "hammer"
    description = "A Minecraft server"
    options = HammerOptions
    locations = ['/etc/hammer', os.path.expanduser('~/.hammer'), '.']

    def makeService(self, options):
        # Grab our configuration file's path.
        conf = options["config"]
        # If config is default value, check locations for configuration file.
        if conf == options.optParameters[0][2]:
            for location in self.locations:
                path = FilePath(os.path.join(location, conf))
                if path.exists():
                    break
        else:
            path = FilePath(conf)
        if not path.exists():
            raise RuntimeError("Couldn't find config file %r" % conf)

        # Create our service and return it.
        from hammer.service import service
        return service(path)

hsm = HammerServiceMaker()
