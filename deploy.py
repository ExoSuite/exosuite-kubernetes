import os

from lib import OptionParser, Container, Directory, Env

parser = OptionParser()
parser.add_option("--website", action="store_true", dest="website")
parser.add_option("--api", action='store_true', dest="api")
parser.add_option("--staging", action="store_true", dest="staging")
parser.add_option("--production", action="store_true", dest="production")
parser.add_option("--redis", action='store_true', dest="redis")
parser.add_option("--postgres", action='store_true', dest="postgres")
(opts, args) = parser.parse_args()
parser.check_required("--staging" if opts.staging is not None else "--production")
parser.check_required("--production" if opts.production is not None else "--staging")

kubectl_base_cmd = "kubectl apply -f "

if opts.staging:
    env = Env.STAGING
else:
    env = Env.PRODUCTION

if opts.website:
    os.system(kubectl_base_cmd + Container.PHP_FPM_WEBSITE.toYaml(Directory.WEBSITE, env))
    os.system(kubectl_base_cmd + Container.NGINX_WEBSITE.toYaml(Directory.WEBSITE, env))
elif opts.api:
    os.system(kubectl_base_cmd + Container.PHP_FPM_API.toYaml(Directory.API, env))
    os.system(kubectl_base_cmd + Container.NGINX_API.toYaml(Directory.API))
elif opts.redis:
    os.system(kubectl_base_cmd + Container.REDIS_LIVE.toYaml(Directory.REDIS))
    os.system(kubectl_base_cmd + Container.REDIS_STORE.toYaml(Directory.REDIS))
else:
    parser.print_help()
