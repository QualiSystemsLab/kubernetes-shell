from kubernetes.client import V1Namespace, V1ObjectMeta, V1NamespaceList, V1DeleteOptions
from kubernetes.client.rest import ApiException

from domain.services.tags import TagsService
from model.clients import KubernetesClients


class KubernetesNamespaceService(object):
    TERMINATING_STATUS = "Terminating"

    def __init__(self):
        pass

    def create(self, clients, name, labels, annotations):
        """
        :param KubernetesClients clients:
        :param str name:
        :param Dict labels:
        :param Dict annotations:
        :rtype: V1Namespace
        """
        # enable_network_policy = {'net.beta.kubernetes.io/network-policy': '{"ingress": {"isolation": "DefaultDeny"}}'}
        # namespace_meta = V1ObjectMeta(name=name, labels=labels, annotations={**enable_network_policy})
        namespace_meta = V1ObjectMeta(name=name, labels=labels, annotations=annotations)
        namespace = V1Namespace(metadata=namespace_meta)

        return clients.core_api.create_namespace(body=namespace, pretty='true')

    def get_namespace_name_for_sandbox(self, sandbox_id):
        """
        :param str sandbox_id:
        :rtype: str
        """
        return "cloudshell-{}".format(sandbox_id)
        # return "default"  # todo - alexaz - change this after implementing PrepreSandboxInfra

    def get_all(self, clients):
        """
        :param KubernetesClients clients:
        :rtype: V1NamespaceList
        """
        filter_query = '{sandbox_id_tag}'.format(sandbox_id_tag=TagsService.SANDBOX_ID)
        # if space_id:
        #     filter_query += ',{tag}={value}'.format(tag=DevboxTags.SPACE_ID, value=space_id)
        # if cloud_account_id:
        #     filter_query += ',{tag}={value}'.format(tag=DevboxTags.CLOUD_ACCOUNT_ID, value=cloud_account_id)

        return clients.core_api.list_namespace(label_selector=filter_query)

    def get_by_id(self, clients, sandbox_id):
        """
        :param KubernetesClients clients:
        :param str sandbox_id:
        :rtype: V1NamespaceList
        """

        filter_query = '{label}=={value}'.format(label=TagsService.SANDBOX_ID, value=sandbox_id)

        return self.get(clients, filter_query)

    def get(self, clients, filter_query):
        """
        :param KubernetesClients clients:
        :param str filter_query:
        :rtype: V1NamespaceList
        """
        return clients.core_api.list_namespace(label_selector=filter_query)

    def terminate(self, clients, sandbox_id):
        """
        :param KubernetesClients clients:
        :param str sandbox_id:
        :return:
        """
        namespaces = self.get_all(clients)
        tag = TagsService.SANDBOX_ID
        namespace_to_delete = next(iter([namespace for namespace in namespaces.items
                                         if namespace.metadata.labels[tag] == sandbox_id]), None)
        if namespace_to_delete:
            if self.get_status(clients, namespace_to_delete.metadata.name) == KubernetesNamespaceService.TERMINATING_STATUS:
                return

            body = V1DeleteOptions(grace_period_seconds=5, orphan_dependents=False)
            clients.core_api.delete_namespace(name=namespace_to_delete.metadata.name, body=body, pretty='true'),

    def get_status(self, clients, namespace_name):
        """
        :param KubernetesClients clients:
        :param str namespace_name:
        :rtype: str
        """
        try:
            response = clients.core_api.read_namespace_status(name=namespace_name)
            return response.status.phase
        except ApiException as exc:
            if exc.reason == 'Not Found' and exc.status == 404:
                return KubernetesNamespaceService.TERMINATING_STATUS
            raise

    # def update_annotation(self, namespace, key: str, value: str):
    #     namespace_meta = V1ObjectMeta(annotations={key: value})
    #     patched_namespace = V1Namespace(metadata=namespace_meta)
    #     Utils.run_and_log_time(func=lambda: self.core_v1_api.patch_namespace(name=namespace.metadata.name,
    #                                                                          body=patched_namespace),
    #                            logger=self._logger)
