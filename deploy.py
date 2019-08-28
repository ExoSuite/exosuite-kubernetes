#!/usr/bin/env python3

import os

from lib import OptionParser, Container, Directory, Env, RegistrySecret


def createKubectlRegistryCmd(secretName: RegistrySecret, server: str, username: str, passwd: str) -> str:
    namespace = Env.PRODUCTION if secretName == RegistrySecret.PRODUCTION else Env.STAGING

    command = "kubectl create secret docker-registry " + secretName.value
    command += " --docker-server=" + server
    command += " --docker-username=" + username
    command += " --docker-username=" + username
    command += " --docker-password=" + passwd
    command += " --docker-email=dev@exosuite.fr"
    command += " --namespace=" + str(namespace)

    return command


parser = OptionParser()
parser.add_option("--website", action="store_true", dest="website", help="Deploy website pods.")
parser.add_option("--api", action='store_true', dest="api", help="Deploy api pods.")
parser.add_option("--staging", action="store_true", dest="staging", help="Choose staging deployment")
parser.add_option("--production", action="store_true", dest="production", help="Choose production deployment")
parser.add_option("--redis", action='store_true', dest="redis", help="Deploy databases yaml.")
parser.add_option("--databases", action='store_true', dest="databases", help="Deploy databases yaml.")
parser.add_option("--namespaces", action='store_true', dest="namespaces", help="Deploy exosuite namespaces.")
parser.add_option("--storage-class", action='store_true', dest="storageclass", help="Deploy local storageclass.")
parser.add_option("--registries", action="store_true", dest="registries",
                  help="Deploy secret registry for prod and staging.")
parser.add_option("--init-cluster", action="store_true", dest="init_cluster", help="Init ExoSuite Kubernetes cluster.")
parser.add_option("--elasticsearch", action="store_true", dest="elastic_search", help="Deploy elasticsearch cluster.")
parser.add_option("--laravel-echo", action="store_true", dest="laravel_echo", help="Deploy laravel-echo-server.")
parser.add_option("--ftp", action="store_true", dest='ftp', help='Deploy ftp server.')
parser.add_option("--auto-scaler", action="store_true", dest='auto_scaler', help='Deploy autoscalers.')

(opts, args) = parser.parse_args()
if opts.namespaces is None and opts.storageclass is None and opts.registries is None and opts.init_cluster is None:
    parser.check_required("--staging" if opts.staging is not None else "--production")
    parser.check_required("--production" if opts.production is not None else "--staging")

if opts.staging:
    env = Env.STAGING
else:
    env = Env.PRODUCTION


def registries():
    os.system(
        createKubectlRegistryCmd(RegistrySecret.STAGING, "teamexosuite.cloud:5000", "exosuite-dev", "N8jSfUeH4kPyYSLW"))
    os.system(createKubectlRegistryCmd(RegistrySecret.PRODUCTION, "exosuite.fr:5000", "exosuite", "eG4FE5NbknfT79uR"))


def namespaces():
    os.system("kubectl apply -f namespaces/prod.yaml")
    os.system("kubectl apply -f namespaces/staging.yaml")


def storageClasses():
    os.system("kubectl apply -f StorageClass/local.yaml")


def autoscaler() -> None:
    scaler = " --cpu-percent=50 --min=1 --max=10"

    # NGINX #
    os.system(Container.NGINX_API.toKubectlAutoscaleCmd(scaler, env))
    os.system(Container.NGINX_WEBSITE.toKubectlAutoscaleCmd(scaler, env))
    # END NGINX #
    # PHP_FPM #
    os.system(Container.PHP_FPM_API.toKubectlAutoscaleCmd(scaler, env))
    os.system(Container.PHP_FPM_WEBSITE.toKubectlAutoscaleCmd(scaler, env))
    # END PHP_FPM #
    # ARTISAN #
    os.system(Container.SCHEDULER.toKubectlAutoscaleCmd(scaler, env))
    os.system(Container.HORIZON.toKubectlAutoscaleCmd(scaler, env))
    # END ARTISAN #

    # MISC #
    os.system(Container.LARAVEL_ECHO.toKubectlAutoscaleCmd(scaler, env))
    # END MISC #



if opts.website:
    os.system(Container.PHP_FPM_WEBSITE.toKubectlDeployCmd(Directory.WEBSITE, env))
    os.system(Container.NGINX_WEBSITE.toKubectlDeployCmd(Directory.WEBSITE, env))
elif opts.api:
    os.system(Container.PHP_FPM_API.toKubectlDeployCmd(Directory.API, env))
    os.system(Container.NGINX_API.toKubectlDeployCmd(Directory.API, env))
    os.system(Container.HORIZON.toKubectlDeployCmd(Directory.API, env))
    os.system(Container.SCHEDULER.toKubectlDeployCmd(Directory.API, env))
elif opts.redis:
    os.system(Container.REDIS_LIVE.toKubectlDeployCmd(Directory.REDIS, env))
    os.system(Container.REDIS_STORE.toKubectlDeployCmd(Directory.REDIS, env))
elif opts.databases:
    os.system(Container.POSTGRES_API.toKubectlDeployCmd(Directory.DATABASE, env))
    os.system(Container.POSTGRES_WEBSITE.toKubectlDeployCmd(Directory.DATABASE, env))
elif opts.elastic_search:
    os.system(Container.ELASTICSEARCH.toKubectlDeployCmd(Directory.ELASTICSEARCH, env))
elif opts.laravel_echo:
    os.system(Container.LARAVEL_ECHO.toKubectlDeployCmd(Directory.LARAVEL_ECHO, env))
elif opts.ftp:
    os.system(Container.VSFTPD.toKubectlDeployCmd(Directory.FTP, env))
elif opts.registries:
    registries()
elif opts.namespaces:
    namespaces()
elif opts.storageclass:
    storageClasses()
elif opts.auto_scaler:
    autoscaler()
elif opts.init_cluster:
    os.system("kubectl taint nodes --all node-role.kubernetes.io/master-")
    storageClasses()
    namespaces()
    registries()
    os.system("git clone https://github.com/kubernetes-incubator/metrics-server.git")
    os.system("kubectl create -f metrics-server/deploy/1.8+/")
    os.system("rm -r metrics-server")
else:
    parser.print_help()
