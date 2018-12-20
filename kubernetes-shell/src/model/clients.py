from kubernetes.client import ApiClient, CoreV1Api, AppsV1beta1Api


class KubernetesClients(object):

    def __init__(self, api_client, core_api, apps_api):
        """
        :param AppsV1beta1Api apps_api:
        :param ApiClient api_client:
        :param CoreV1Api core_api:
        """
        self._api_client = api_client
        self.apps_api = apps_api
        self.core_api = core_api
