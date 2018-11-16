import data_model
from domain.services.clients import ApiClientsProvider


class AutolaodOperation(object):

    def __init__(self, api_clients_provider):
        """
        :param ApiClientsProvider api_clients_provider:
        """
        self.api_clients_provider = api_clients_provider

    def validate_config(self, cloud_provider_resource):
        """
        :param data_model.Kubernetes cloud_provider_resource:
        :return:
        """

        # create api clients by cluster name
        clients = self.api_clients_provider.get_api_clients(cloud_provider_resource)

        # list nodes and make sure we have 1 or more nodes just to check authentication works
        nodes = clients.core_api.list_node(watch=False)
        if not nodes or len(nodes.items) < 1:
            raise ValueError("Cluster '{}' has zero (0) nodes".format(cloud_provider_resource.cluster_name))
