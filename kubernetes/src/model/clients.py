from kubernetes.client import ApiClient, CoreV1Api


class KubernetesClients(object):

    def __init__(self, api_client, core_api):
        """

        :param ApiClient api_client:
        :param CoreV1Api core_api:
        """
        self._api_client = api_client
        self.core_api = core_api
