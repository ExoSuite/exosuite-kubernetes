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
    def __str__(self) -> str:
        return str(self.value)


class Env(Enum):
    STAGING = "staging"
    PRODUCTION = "production"


class Directory(Enum):
    API = "build/api"
    WEBSITE = "build/website"
    TEMPLATES = "templates"
    REDIS = "redis"
    DATABASE = "database"

    def toPath(self, env: Env = None):
        path = os.path.dirname(os.path.realpath(__file__))
        path += "/../" + self.value
        path = os.path.normpath(path) + "/"
        if env is None:
            return path
        return path + str(env) + '/'


class ContainerType(Enum):
    PHP_FPM = "php-fpm"
    NGINX = "nginx"
    POSTGRES = "postgres"


class DockerImage(Enum):
    POSTGIS = "mdillon/postgis:11-alpine"
    POSTGRES = "postgres:11.1-alpine"


class Container(Enum):
    PHP_FPM_API = "exosuite-users-api-php-fpm"
    PHP_FPM_WEBSITE = "exosuite-website-php-fpm"
    NGINX_API = "exosuite-users-api-nginx"
    NGINX_WEBSITE = "exosuite-website-nginx"
    REDIS_LIVE = "exosuite-redis-live"
    REDIS_STORE = "exosuite-redis-store"
    POSTGRES_WEBSITE = "exosuite-website-postgres"
    POSTGRES_API = "exosuite-users-api-postgres"

    def toYaml(self, outputDir: Directory, env: Env = None) -> str:
        return outputDir.toPath(env) + self.value + '.yaml'

    def toRelativeGeneratedFile(self, outputDir: Directory, env: Env = None) -> str:
        directory = outputDir.toPath(env) + self.value + '.yaml'
        path = os.path.dirname(os.path.realpath(__file__))
        path += "/../"
        path = os.path.normpath(path) + "/"
        return directory.replace(path, '')

    def toProjectDirectory(self) -> str:
        container_str = str(self.value)
        for containerType in ContainerType:
            pos = container_str.find(str(containerType.value))
            if pos > 0:
                return container_str[0:pos - 1]  # -1 remove the '-' char

    def isPhpFpm(self) -> bool:
        return str(self.value).find(str(ContainerType.PHP_FPM)) > 0

    def isNginx(self) -> bool:
        return str(self.value).find(str(ContainerType.NGINX)) > 0

    def toDatabaseSettings(self, env: Env):
        container_str = str(self.value)
        container_str = container_str.split("exosuite-")[1].split("-postgres")[0]
        if container_str.find("api") > 0:
            container_str = container_str.split("users-")[1]
        return getattr(DatabaseSetting, env.value.upper())[container_str.upper()]

    def toDatabaseDockerImage(self) -> str:
        if str(self.value).find("api") > 0:
            return str(DockerImage.POSTGIS.value)
        return str(DockerImage.POSTGRES.value)


class Token(Enum):
    VERSION = '<VERSION>'
    CONTAINER = '<CONTAINER>'
    REGISTRY = '<REGISTRY>'
    REGISTRY_SECRET = '<REGISTRY_SECRET>'
    DIRECTORY = '<DIRECTORY>'
    ENV = "<ENV>"
    IMAGE = "<IMAGE>"
    DATABASE = "<DATABASE>"
    DATABASE_USER = "<DATABASE_USER>"
    DATABASE_PASSWORD = "<DATABASE_PASSWORD>"

    def key(self):
        return str(self.value).replace("<", '').replace(">", '')


class Template(Enum):
    PHP_FPM = "exosuite-php-fpm.template.yaml"
    NGINX = "exosuite-nginx.template.yaml"
    REDIS = "exosuite-redis.template.yaml"
    POSTGRES = "exosuite-postgres.template.yaml"

    def toPath(self):
        return Directory.TEMPLATES.toPath() + self.value


class RegistrySecret(Enum):
    STAGING = "staging-registry"
    PRODUCTION = "production-registry"


class Registry(Enum):
    STAGING = "dev.exosuite.fr:5000/exosuite"
    PRODUCTION = "exosuite.fr:5000/exosuite"

    def toRegistrySecret(self):
        return RegistrySecret.STAGING if self == Registry.STAGING else RegistrySecret.PRODUCTION


class DatabaseSetting:
    WEBSITE = "WEBSITE"
    API = "API"

    STAGING = {
        API: {
            Token.DATABASE.key(): Container.POSTGRES_API.toProjectDirectory(),
            Token.DATABASE_PASSWORD.key(): "AyLVJWHp##LtSx4g%qYt",
            Token.DATABASE_USER.key(): "exosuite"
        },
        WEBSITE: {
            Token.DATABASE.key(): Container.POSTGRES_WEBSITE.toProjectDirectory(),
            Token.DATABASE_PASSWORD.key(): "w8RP3#Ex++8EdHaH",
            Token.DATABASE_USER.key(): "exosuite"
        }
    }

    PRODUCTION = {
        API: {
            Token.DATABASE.key(): Container.POSTGRES_API.toProjectDirectory(),
            'DATABASE_PASSWORD': "MAy5UBgd2YVgv8WTzSACQrGSddURGdzfpa9",
            Token.DATABASE_USER.key(): "exosuite"
        },
        WEBSITE: {
            Token.DATABASE.key(): Container.POSTGRES_WEBSITE.toProjectDirectory(),
            'DATABASE_PASSWORD': "4tpaBrVqCqDXct7862VmFAmfrAvjpYuNReqJx7Snqy",
            Token.DATABASE_USER.key(): "exosuite"
        }
    }

    def __getitem__(self, item):
        print(item, "hello")
