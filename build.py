#!/usr/bin/env python3

from lib import *

parser = OptionParser()
parser.add_option(
    "--version",
    action="store", dest="version",
    default=None, help="Choose which version will be used in generated yaml."
)
parser.add_option("--staging", action="store_true", dest="staging", help="Choose staging for generated yaml.")
parser.add_option("--production", action="store_true", dest="production", help="Choose production for generated yaml.")
parser.add_option("--website", action="store_true", dest="website", help="Generate website yaml.")
parser.add_option("--api", action='store_true', dest="api", help="Generate api yaml.")
parser.add_option("--databases", action='store_true', dest="databases", help="Generate databases yaml files.")
parser.add_option("--redis", action='store_true', dest="redis", help="Generate redis yaml files.")
parser.add_option("--clean", action='store_true', dest="clean", help="Clean all generated files")
(opts, args) = parser.parse_args()

if opts.clean is None:
    if opts.redis is None and opts.databases is None:
        parser.check_required("--version")
    parser.check_required("--staging" if opts.staging is not None else "--production")
    parser.check_required("--production" if opts.production is not None else "--staging")


def writeToFile(container: Container, currentEnv: Env, dockerFileContent: str, outputDir: Directory):
    f = open(container.toYaml(outputDir, currentEnv), "w")
    f.write(dockerFileContent)
    f.close()
    print("Generated " + container.toRelativeGeneratedFile(outputDir, currentEnv))


def generateKubernetesDeployment(container: Container, selectedRegistry: Registry, currentEnv: Env, template: Template):
    dockerFileContent = open(template.toPath()).read()

    registrySecret = selectedRegistry.toRegistrySecret()

    dockerFileContent = dockerFileContent \
        .replace(Token.VERSION.value, opts.version) \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.REGISTRY.value, selectedRegistry.value) \
        .replace(Token.REGISTRY_SECRET.value, str(registrySecret)) \
        .replace(Token.ENV.value, str(currentEnv))

    if container.isPhpFpm():
        migrate_cmd = SystemCommand.LARAVEL_MIGRATE.value
        migrate_cmd += " --seed'"

        dockerFileContent = dockerFileContent \
            .replace(Token.DIRECTORY.value, container.toProjectDirectory()) \
            .replace(Token.MIGRATE_CMD.value, migrate_cmd)

        if container == Container.PHP_FPM_API:
            dockerFileContent = dockerFileContent.replace(Token.SCRIPT.value, " 'elastic:create-indexes'")
        elif container == Container.PHP_FPM_WEBSITE and env == Env.STAGING:
            dockerFileContent = dockerFileContent.replace(Token.SCRIPT.value, " 'api:retrieve'")
        else:
            dockerFileContent = dockerFileContent.replace(Token.SCRIPT.value, "")
    elif container.isScheduler() and env == Env.PRODUCTION:
        dockerFileContent = dockerFileContent \
            .replace(Token.OPTIONAL_VOLUME_MOUNT.value, 'volumeMounts:') \
            .replace(Token.OPTIONAL_CONTAINER_MOUNT_PATH.value,
                     'mountPath: /mnt/exosuite/containers/exosuite-users-api/storage/vsftpd') \
            .replace(Token.OPTIONAL_VOLUME_NAME.value, '- name: exosuite-scheduler-vsftpd-mount') \
            .replace(Token.OPTIONAL_VOLUME.value, 'volumes:') \
            .replace(Token.OPTIONAL_VOLUME_HOST_PATH.value, 'hostPath:') \
            .replace(Token.OPTIONAL_VOLUME_PATH.value, 'path: "/mnt/exosuite/containers/exosuite-vsftpd"') \
            .replace(Token.OPTIONAL_NODE_TYPE.value, 'type: production') \
            .replace(Token.OPTIONAL_NODE_SELECTOR.value, 'nodeSelector:')

    else:
        dockerFileContent = dockerFileContent \
            .replace(Token.OPTIONAL_VOLUME_MOUNT.value, '') \
            .replace(Token.OPTIONAL_CONTAINER_MOUNT_PATH.value, '') \
            .replace(Token.OPTIONAL_VOLUME_NAME.value, '') \
            .replace(Token.OPTIONAL_VOLUME.value, '') \
            .replace(Token.OPTIONAL_VOLUME_HOST_PATH.value, '') \
            .replace(Token.OPTIONAL_VOLUME_PATH.value, '') \
            .replace(Token.OPTIONAL_NODE_TYPE.value, '') \
            .replace(Token.OPTIONAL_NODE_SELECTOR.value, '') \
            .replace(Token.OPTIONAL_NODE_TYPE.value, '') \
            .replace(Token.OPTIONAL_NODE_SELECTOR.value, '')

    outputDir = Directory.API if opts.api else Directory.WEBSITE
    writeToFile(container, currentEnv, dockerFileContent, outputDir)


def generateRedisKubernetesDeployment(container: Container, currentEnv: Env):
    template = Template.REDIS
    dockerFileContent = open(template.toPath()).read()

    dockerFileContent = dockerFileContent \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.ENV.value, currentEnv.value) \
        .replace(Token.NODE.value, currentEnv.value)

    if env == Env.PRODUCTION:
        dockerFileContent = dockerFileContent.replace("-volume", "-volume-prod") \
            .replace(Token.STORAGE.value, '50Gi')
    else:
        dockerFileContent = dockerFileContent.replace(Token.STORAGE.value, '10Gi')

    writeToFile(container, currentEnv, dockerFileContent, Directory.REDIS)


def generateDatabaseKubernetesDeployment(container: Container, currentEnv: Env):
    template = Template.POSTGRES
    dockerFileContent = open(template.toPath()).read()
    databaseSettings = container.toDatabaseSettings(currentEnv)

    dockerFileContent = dockerFileContent \
        .replace(Token.CONTAINER.value, container.value) \
        .replace(Token.ENV.value, currentEnv.value) \
        .replace(Token.DATABASE.value, databaseSettings[Token.DATABASE.key()]) \
        .replace(Token.DATABASE_USER.value, databaseSettings[Token.DATABASE_USER.key()]) \
        .replace(Token.DATABASE_PASSWORD.value, databaseSettings[Token.DATABASE_PASSWORD.key()]) \
        .replace(Token.IMAGE.value, container.toDatabaseDockerImage()) \
        .replace(Token.NODE.value, currentEnv.value)

    if env == Env.PRODUCTION:
        dockerFileContent = dockerFileContent.replace("-volume", "-volume-prod").replace(Token.STORAGE.value, '50Gi')
    else:
        dockerFileContent = dockerFileContent.replace(Token.STORAGE.value, '50Gi')

    writeToFile(container, currentEnv, dockerFileContent, Directory.DATABASE)


env = Env.STAGING if opts.staging else Env.PRODUCTION

if env == Env.STAGING:
    registry = Registry.STAGING
else:
    registry = Registry.PRODUCTION

if opts.api:
    generateKubernetesDeployment(Container.NGINX_API, registry, env, Template.NGINX)
    generateKubernetesDeployment(Container.PHP_FPM_API, registry, env, Template.PHP_FPM)
    generateKubernetesDeployment(Container.HORIZON, registry, env, Template.ARTISAN)
    generateKubernetesDeployment(Container.SCHEDULER, registry, env, Template.ARTISAN)
    print("Deploy cmd: \n\tpython3 deploy.py --api --" + env.value)
elif opts.website:
    generateKubernetesDeployment(Container.NGINX_WEBSITE, registry, env, Template.NGINX)
    generateKubernetesDeployment(Container.PHP_FPM_WEBSITE, registry, env, Template.PHP_FPM)
    print("Deploy cmd: \n\tpython3 deploy.py --website --" + env.value)
elif opts.redis:
    generateRedisKubernetesDeployment(Container.REDIS_LIVE, env)
    generateRedisKubernetesDeployment(Container.REDIS_STORE, env)
    print("Deploy cmd: \n\tpython3 deploy.py --redis --" + env.value)
elif opts.databases:
    generateDatabaseKubernetesDeployment(Container.POSTGRES_WEBSITE, env)
    generateDatabaseKubernetesDeployment(Container.POSTGRES_API, env)
    print("Deploy: \n\tpython3 deploy.py --databases --" + env.value)
elif opts.clean:
    os.system("find ./build -name '*.yaml' -type f -delete")
    os.system("find ./database -name '*.yaml' -type f -delete")
    os.system("find ./redis -name '*.yaml' -type f -delete")
    print("Build directories cleaned!")
else:
    parser.print_help()
