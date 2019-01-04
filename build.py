#!/usr/bin/env python3

import os

from lib import OptionParser, Enum, Container, Directory, ContainerType, Env


class Token(Enum):
    VERSION = '<VERSION>'
    CONTAINER = '<CONTAINER>'
    REGISTRY = '<REGISTRY>'
    REGISTRY_SECRET = '<REGISTRY_SECRET>'
    DIRECTORY = '<DIRECTORY>'


class Template(Enum):
    PHP_FPM = "exosuite-php-fpm.template.yaml"
    NGINX = "exosuite-nginx.template.yaml"

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


parser = OptionParser()
parser.add_option("--version", action="store", dest="version", default=None)
parser.add_option("--staging", action="store_true", dest="staging")
parser.add_option("--production", action="store_true", dest="production")
parser.add_option("--website", action="store_true", dest="website")
parser.add_option("--api", action='store_true', dest="api")
parser.add_option("--clean", action='store_true', dest="clean")
(opts, args) = parser.parse_args()

if opts.clean is None:
    parser.check_required("--version")
    parser.check_required("--staging" if opts.staging is not None else "--production")
    parser.check_required("--production" if opts.production is not None else "--staging")


def generateKubernetesDeployment(container: Container, selectedRegistry: Registry, currentEnv: Env):
    template = Template.PHP_FPM if container.isPhpFpm() > 0 else Template.NGINX
    dockerFileContent = open(template.toPath()).read()

    registrySecret = selectedRegistry.toRegistrySecret()

    dockerFileContent = dockerFileContent \
        .replace(Token.VERSION.value, opts.version) \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.REGISTRY.value, selectedRegistry.value) \
        .replace(Token.REGISTRY_SECRET.value, str(registrySecret))

    if container.isPhpFpm():
        dockerFileContent = dockerFileContent.replace(Token.DIRECTORY.value, container.toProjectDirectory())

    outputDir = Directory.API if opts.api else Directory.WEBSITE
    f = open(container.toYaml(outputDir, currentEnv), "w")
    f.write(dockerFileContent)
    f.close()


env = Env.STAGING if opts.staging else Env.PRODUCTION

if env == Env.STAGING:
    registry = Registry.STAGING
else:
    registry = Registry.PRODUCTION

if opts.api:
    generateKubernetesDeployment(Container.NGINX_API, registry, env)
    generateKubernetesDeployment(Container.PHP_FPM_API, registry, env)
elif opts.website:
    generateKubernetesDeployment(Container.NGINX_WEBSITE, registry, env)
    generateKubernetesDeployment(Container.PHP_FPM_WEBSITE, registry, env)
elif opts.clean:
    os.system("rm -f ./build/api/* && rm -f ./build/website/*")
    print("Build directories cleaned!")
else:
    parser.print_help()
