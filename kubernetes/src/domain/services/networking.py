from logging import Logger
from typing import List

from kubernetes.client import V1ObjectMeta, V1Service, CoreV1Api, V1ServiceSpec, V1ServicePort, V1ServiceList

from domain.services.tags import TagsService
from model.clients import KubernetesClients


class KubernetesNetworkingService(object):
    def __init__(self):
        pass

    def create_internal_external_set(self,
                                     logger,
                                     clients,
                                     namespace,
                                     name,
                                     labels,
                                     internal_ports,
                                     external_ports):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str name:
        :param dict labels:
        :param List[int] internal_ports:
        :param List[int] external_ports:
        :rtype: List[V1Service]
        """

        services = list()
        if internal_ports:
            internal_service_labels = dict(labels)
            internal_service_labels.update({TagsService.INTERNAL_SERVICE: 'true'})
            service = self._create(logger=logger,
                                   core_v1_api=clients.core_api,
                                   namespace=namespace,
                                   name=name,
                                   app_name=name,
                                   labels=internal_service_labels,
                                   ports=internal_ports,
                                   spec_type='ClusterIP')
            services.append(service)

        if external_ports:
            external_service_labels = dict(labels)
            external_service_labels.update({TagsService.EXTERNAL_SERVICE: 'true'})
            service_name = "{}-{}".format(name, TagsService.EXTERNAL_SERVICE_POSTFIX)
            service = self._create(logger=logger,
                                   core_v1_api=clients.core_api,
                                   namespace=namespace,
                                   name=service_name,
                                   app_name=name,
                                   labels=external_service_labels,
                                   ports=external_ports,
                                   spec_type='LoadBalancer')
            services.append(service)

        return services

    def _create(self,
                logger,
                core_v1_api,
                namespace,
                name,
                app_name,
                labels,
                ports,
                spec_type):
        """
        :param Logger logger:
        :param CoreV1Api core_v1_api:
        :param str namespace:
        :param str name:
        :param str app_name:
        :param dict labels:
        :param List[int] ports:
        :param str spec_type:
        :rtype: V1Service
        """
        annotations = {}  # todo add annotations to services
        meta = V1ObjectMeta(name=name, labels=labels, annotations=annotations)
        service_ports = list()

        for port in ports:
            service_ports.append(V1ServicePort(name="port" + str(port), port=port, target_port=port, protocol="TCP"))

        selector_tag = {TagsService.get_default_selector(app_name): app_name}

        if spec_type == "LoadBalancer":
            allowed_ips = None  # todo - alexaz - add option to restrict source ips
            specs = V1ServiceSpec(ports=service_ports,
                                  selector=selector_tag,
                                  type=spec_type,
                                  load_balancer_source_ranges=allowed_ips)
        else:
            specs = V1ServiceSpec(ports=service_ports,
                                  selector=selector_tag,
                                  type=spec_type)

        service = V1Service(metadata=meta, spec=specs)
        return core_v1_api.create_namespaced_service(namespace=namespace,
                                                     body=service,
                                                     pretty='true')

    def get_all(self, clients):
        """
        :param model.clients.KubernetesClients clients:
        :rtype: V1ServiceList
        """
        return clients.core_api.list_service_for_all_namespaces(label_selector=TagsService.SANDBOX_ID)

    def filter_by_label(self, clients, filter_query):
        """
        :param model.clients.KubernetesClients clients:
        :param str filter_query:
        :rtype: V1ServiceList
        """
        return clients.core_api.list_service_for_all_namespaces(label_selector=filter_query)
