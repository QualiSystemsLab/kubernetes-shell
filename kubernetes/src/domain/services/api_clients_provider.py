from cloudshell.cp.core.utils import first_or_default
from kubernetes import config
from kubernetes.client import CoreV1Api

from model.clients import KubernetesClients


class ApiClientsProvider(object):

    def get_api_clients(self, cluster_name):
        contexts, active_context = config.list_kube_config_contexts()
        if not contexts:
            raise ValueError("Cannot find any context in kube-config file.")

        # find context by cluster name
        context = first_or_default(contexts, lambda x: x['context']['cluster'] == cluster_name)
        if not context:
            raise ValueError("Cannot find cluster '{}' in kube-config file.".format(cluster_name))

        # init api clients
        api_client = config.new_client_from_config(context=context['name'])
        core_api = CoreV1Api(api_client=api_client)

        return KubernetesClients(api_client, core_api)
