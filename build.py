#!/usr/bin/env python3

import os

from lib import OptionParser, Enum, Container, Directory


class Token(Enum):
    VERSION = '<VERSION>'
    CONTAINER = '<CONTAINER>'
    REGISTRY = '<REGISTRY>'
    REGISTRY_SECRET = '<REGISTRY_SECRET>'


class Template(Enum):
    PHP_FPM = "exosuite-php-fpm.template.yaml"
    NGINX = "exosuite-nginx.template.yaml"


class Registry(Enum):
    STAGING = "dev.exosuite.fr:5000/exosuite"
    PRODUCTION = "exosuite.fr:5000/exosuite"


class RegistrySecret(Enum):
    STAGING = "staging-registry"
    PRODUCTION = "production-registry"


parser = OptionParser()
parser.add_option("--version", action="store", dest="version", default=None)
parser.add_option("--staging", action="store_true", dest="staging")
parser.add_option("--production", action="store_true", dest="production")
parser.add_option("--website", action="store_true", dest="website")
parser.add_option("--api", action='store_true', dest="api")
parser.add_option("--clean", action='store_true', dest="clean")
(opts, args) = parser.parse_args()
required = "--staging" if opts.staging else "--production"
parser.check_required("--version")
parser.check_required("--staging" if opts.staging else "--production")


def generateKubernetesDeployment(container: Container, registry: Registry):
    template = Template.PHP_FPM.value if container.value.find("php-fpm") > 0 else Template.NGINX.value
    dockerFileContent = open("./" + template).read()

    registrySecret = RegistrySecret.STAGING.value if registry == Registry.STAGING else RegistrySecret.PRODUCTION.value

    dockerFileContent = dockerFileContent \
        .replace(Token.VERSION.value, opts.version) \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.REGISTRY.value, registry.value) \
        .replace(Token.REGISTRY_SECRET.value, registrySecret)

    outputDir = Directory.API.value if container.value.find("api") > 0 else Directory.WEBSITE.value

    f = open("./" + outputDir + container.toYaml(), "w")
    f.write(dockerFileContent)
    f.close()


registry = Registry.STAGING if opts.staging else Registry.PRODUCTION

if opts.api:
    generateKubernetesDeployment(Container.NGINX_API, registry)
    generateKubernetesDeployment(Container.PHP_FPM_API, registry)
elif opts.website:
    generateKubernetesDeployment(Container.NGINX_WEBSITE, registry)
    generateKubernetesDeployment(Container.PHP_FPM_WEBSITE, registry)
elif opts.clean:
    os.system("rm -f ./build/api/* && rm -f ./build/website/*")
    print("Build directories cleaned!")
else:
    parser.print_help()
