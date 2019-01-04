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


class Env(Enum):
    STAGING = "staging"
    PRODUCTION = "production"


class Directory(Enum):
    API = "build/api"
    WEBSITE = "build/website"
    TEMPLATES = "templates"
    REDIS = "redis"

    def toPath(self, env: Env = None):
        path = os.path.dirname(os.path.realpath(__file__))
        path += "/../" + self.value + "/"
        if env is None:
            return path

        return path + str(env) + '/'


class ContainerType(Enum):
    PHP_FPM = "php-fpm"
    NGINX = "nginx"


class Container(Enum):
    PHP_FPM_API = "exosuite-users-api-php-fpm"
    PHP_FPM_WEBSITE = "exosuite-website-php-fpm"
    NGINX_API = "exosuite-users-api-nginx"
    NGINX_WEBSITE = "exosuite-website-nginx"
    REDIS_LIVE = "exosuite-redis-live"
    REDIS_STORE = "exosuite-redis-store"

    def toYaml(self, outputDir: Directory, env: Env = None):

        return outputDir.toPath(env) + self.value + '.yaml'

    def toProjectDirectory(self):
        container_str = str(self)
        pos = container_str.find(str(ContainerType.PHP_FPM))
        if pos > 0:
            return container_str[0:pos - 1] # -1 remove the '-' char

        pos = container_str.find(str(ContainerType.NGINX))
        return container_str[0:pos - 1] # -1 remove the '-' char

    def isPhpFpm(self):
        return str(self).find(str(ContainerType.PHP_FPM)) > 0

    def isNginx(self):
        return str(self).find(str(ContainerType.NGINX)) > 0
