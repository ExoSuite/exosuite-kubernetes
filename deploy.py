import os

from lib import OptionParser, Container, Directory

parser = OptionParser()
parser.add_option("--website", action="store_true", dest="website")
parser.add_option("--api", action='store_true', dest="api")
parser.add_option("--redis", action='store_true', dest="api")
(opts, args) = parser.parse_args()

kubectl_base_cmd = "kubectl apply -f "

if opts.website:
    directory = Directory.WEBSITE.toPath()
    os.system(kubectl_base_cmd + directory + Container.PHP_FPM_WEBSITE.toYaml())
    os.system(kubectl_base_cmd + directory + Container.NGINX_WEBSITE.toYaml())
elif opts.api:
    directory = Directory.API.toPath()
    os.system(kubectl_base_cmd + directory + Container.PHP_FPM_API.toYaml())
    os.system(kubectl_base_cmd + directory + Container.NGINX_API.toYaml())
elif opts.redis:
    directory = Directory.API.toPath()
    os.system(kubectl_base_cmd + directory + Container.REDIS_LIVE.toYaml())
    os.system(kubectl_base_cmd + directory + Container.REDIS_STORE.toYaml())
else:
    parser.print_help()
