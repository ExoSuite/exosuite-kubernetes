import os

from lib import OptionParser, Container, Directory, Env

parser = OptionParser()
parser.add_option("--website", action="store_true", dest="website", help="Deploy website pods.")
parser.add_option("--api", action='store_true', dest="api", help="Deploy api pods.")
parser.add_option("--staging", action="store_true", dest="staging", help="Choose staging deployment")
parser.add_option("--production", action="store_true", dest="production", help="Choose production deployment")
parser.add_option("--redis", action='store_true', dest="redis", help="Deploy databases yaml.")
parser.add_option("--databases", action='store_true', dest="databases", help="Deploy databases yaml.")
parser.add_option("--namespaces", action='store_true', dest="namespaces", help="Deploy exosuite namespaces.")
parser.add_option("--storage-class", action='store_true', dest="storageclass", help="Deploy local storageclass.")
(opts, args) = parser.parse_args()
if opts.namespaces is None and opts.storageclass is None:
    parser.check_required("--staging" if opts.staging is not None else "--production")
    parser.check_required("--production" if opts.production is not None else "--staging")

if opts.staging:
    env = Env.STAGING
else:
    env = Env.PRODUCTION

if opts.website:
    os.system(Container.PHP_FPM_WEBSITE.toKubectlDeployCmd(Directory.WEBSITE, env))
    os.system(Container.NGINX_WEBSITE.toKubectlDeployCmd(Directory.WEBSITE, env))
elif opts.api:
    os.system(Container.PHP_FPM_API.toKubectlDeployCmd(Directory.API, env))
    os.system(Container.NGINX_API.toKubectlDeployCmd(Directory.API, env))
elif opts.redis:
    os.system(Container.REDIS_LIVE.toKubectlDeployCmd(Directory.REDIS, env))
    os.system(Container.REDIS_STORE.toKubectlDeployCmd(Directory.REDIS, env))
elif opts.databases:
    os.system(Container.POSTGRES_API.toKubectlDeployCmd(Directory.DATABASE, env))
    os.system(Container.POSTGRES_WEBSITE.toKubectlDeployCmd(Directory.DATABASE, env))
elif opts.namespaces:
    os.system("kubectl apply -f namespaces/prod.yaml")
    os.system("kubectl apply -f namespaces/staging.yaml")
elif opts.storageclass:
    os.system("kubectl apply -f StorageClass/local.yaml")
else:
    parser.print_help()
