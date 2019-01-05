#!/usr/bin/env python3

from lib import *

parser = OptionParser()
parser.add_option("--version", action="store", dest="version", default=None)
parser.add_option("--staging", action="store_true", dest="staging")
parser.add_option("--production", action="store_true", dest="production")
parser.add_option("--website", action="store_true", dest="website")
parser.add_option("--api", action='store_true', dest="api")
parser.add_option("--database", action='store_true', dest="database")
parser.add_option("--redis", action='store_true', dest="redis")
parser.add_option("--clean", action='store_true', dest="clean")
(opts, args) = parser.parse_args()

if opts.clean is None:
    if opts.redis is None and opts.database is None:
        parser.check_required("--version")
    parser.check_required("--staging" if opts.staging is not None else "--production")
    parser.check_required("--production" if opts.production is not None else "--staging")


def writeToFile(container: Container, currentEnv: Env, dockerFileContent: str, outputDir: Directory):
    f = open(container.toYaml(outputDir, currentEnv), "w")
    f.write(dockerFileContent)
    f.close()
    print("Generated " + container.toRelativeGeneratedFile(outputDir, currentEnv))


def generateKubernetesDeployment(container: Container, selectedRegistry: Registry, currentEnv: Env):
    template = Template.PHP_FPM if container.isPhpFpm() else Template.NGINX
    dockerFileContent = open(template.toPath()).read()

    registrySecret = selectedRegistry.toRegistrySecret()

    dockerFileContent = dockerFileContent \
        .replace(Token.VERSION.value, opts.version) \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.REGISTRY.value, selectedRegistry.value) \
        .replace(Token.REGISTRY_SECRET.value, str(registrySecret)) \
        .replace(Token.ENV.value, str(currentEnv))

    if container.isPhpFpm():
        dockerFileContent = dockerFileContent.replace(Token.DIRECTORY.value, container.toProjectDirectory())

    outputDir = Directory.API if opts.api else Directory.WEBSITE
    writeToFile(container, currentEnv, dockerFileContent, outputDir)


def generateRedisKubernetesDeployment(container: Container, currentEnv: Env):
    template = Template.REDIS
    dockerFileContent = open(template.toPath()).read()

    dockerFileContent = dockerFileContent \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.ENV.value, currentEnv.value)

    writeToFile(container, currentEnv, dockerFileContent, Directory.REDIS)


def generateDatabaseKubernetesDeployment(container: Container, currentEnv: Env):
    template = Template.POSTGRES
    dockerFileContent = open(template.toPath()).read()

    databaseSettings = container.toDatabaseSettings(currentEnv)

    dockerFileContent = dockerFileContent \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.ENV.value, currentEnv.value)\
        .replace(Token.DATABASE.value, databaseSettings[Token.DATABASE.key()])\
        .replace(Token.DATABASE_USER.value, databaseSettings[Token.DATABASE_USER.key()]) \
        .replace(Token.DATABASE_PASSWORD.value, databaseSettings[Token.DATABASE_PASSWORD.key()])\
        .replace(Token.IMAGE.value, container.toDatabaseDockerImage())

    writeToFile(container, currentEnv, dockerFileContent, Directory.DATABASE)


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
elif opts.redis:
    generateRedisKubernetesDeployment(Container.REDIS_LIVE, env)
    generateRedisKubernetesDeployment(Container.REDIS_STORE, env)
elif opts.database:
    generateDatabaseKubernetesDeployment(Container.POSTGRES_WEBSITE, env)
    generateDatabaseKubernetesDeployment(Container.POSTGRES_API, env)
elif opts.clean:
    os.system("rm -f ./build/api/* && rm -f ./build/website/*")
    print("Build directories cleaned!")
else:
    parser.print_help()
