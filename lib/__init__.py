import optparse
import os
from enum import Enum as EnumProvider


class OptionParser(optparse.OptionParser):
    def check_required(self, opt):
        option = self.get_option(opt)

        # Assumes the option's 'default' is set to None!
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)


class Enum(EnumProvider):
    def __str__(self):
        return str(self.value)


class Container(Enum):
    PHP_FPM_API = "exosuite-users-api-php-fpm"
    PHP_FPM_WEBSITE = "exosuite-website-php-fpm"
    NGINX_API = "exosuite-users-api-nginx"
    NGINX_WEBSITE = "exosuite-website-nginx"
    REDIS_LIVE = "exosuite-redis-live"
    REDIS_STORE = "exosuite-redis-store"

    def toYaml(self):
        return self.value + '.yaml'


class Env(Enum):
    STAGING = "staging"
    PRODUCTION = "production"


class Directory(Enum):
    API = "build/api/"
    WEBSITE = "build/website/"

    def toPath(self):
        path = os.path.dirname(os.path.realpath(__file__))
        return path + "/../" + self.value
