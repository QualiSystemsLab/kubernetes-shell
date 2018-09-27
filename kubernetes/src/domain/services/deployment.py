from logging import Logger
from typing import List, Dict

from kubernetes.client import V1ObjectMeta, AppsV1beta1Deployment, AppsV1beta1Api, AppsV1beta1DeploymentSpec, \
    V1PodTemplateSpec, V1PodSpec, V1Container, V1ContainerPort, V1EnvVar

from domain.services.tags import TagsService
from model.deployment_requests import AppComputeSpecKubernetes, AppComputeSpecKubernetesResources, \
    AppDeploymentRequest, ApplicationImage
from model.clients import KubernetesClients


class KubernetesDeploymentService:
    def __init__(self):
        pass

    def create_app(self,
                   logger,
                   clients,
                   namespace,
                   name,
                   labels,
                   app):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str name:
        :param Dict labels:
        :param AppDeploymentRequest app:
        :rtype: AppsV1beta1Deployment
        """

        meta = V1ObjectMeta(name=name)

        annotations = {}
        # self.set_apps_info([name], annotations)
        # self.set_apps_debugging_protocols([app_request], annotations)
        template_meta = V1ObjectMeta(labels=labels, annotations=annotations)

        container = self._prepare_app_container(image=app.image,
                                                compute_spec=app.compute_spec,
                                                name=app.name,
                                                internal_ports=app.internal_ports,
                                                external_ports=app.external_ports)

        pod_spec = V1PodSpec(containers=[container])
        app_template = V1PodTemplateSpec(metadata=template_meta, spec=pod_spec)
        app_spec = AppsV1beta1DeploymentSpec(replicas=app.replicas, template=app_template)
        deployment = AppsV1beta1Deployment(metadata=meta, spec=app_spec)

        return clients.apps_api.create_namespaced_deployment(namespace=namespace,
                                                             body=deployment,
                                                             pretty='true')

    @staticmethod
    def _prepare_app_container(image,
                               compute_spec,
                               name,
                               internal_ports,
                               external_ports):
        """
        :param ApplicationImage image:
        :param AppComputeSpecKubernetes compute_spec:
        :param str name:
        :param List[int] internal_ports:
        :param List[int] external_ports:
        :rtype: V1Container
        """

        container_ports = list()
        for port in internal_ports:
            container_ports.append(V1ContainerPort(name='{}{}'.format(TagsService.INTERNAL_PORT_PREFIX, port),
                                                   container_port=port))

        for port in external_ports:
            container_ports.append(V1ContainerPort(name='{}{}'.format(TagsService.EXTERNAL_PORT_PREFIX, port),
                                                   container_port=port))

        # env_list = [V1EnvVar(name=i.name, value=i.value) for i in inputs] if inputs else []
        # env_list.append(V1EnvVar(name="SANDBOX_ID", value=namespace))
        #
        # user_data_str = KubernetesDeploymentService._get_user_data(
        #     name=name,
        #     start_command=start_command,
        #     script_name=script_name,
        #     healthcheck_script_name=healthcheck_script_name,
        #     namespace=namespace,
        #     start_command_script_name=start_command_script_name,
        #     has_artifacts=has_artifacts)

        command = ['/bin/bash', '-c', '--']
        args = ["while true; do sleep 30; done;"]  # run a task that will never finish

        if image.tag == 'latest' or image.tag == '':
            full_image_name = image.name
        else:
            full_image_name = "{name}:{tag}".format(name=image.name, tag=image.tag)

        if compute_spec:
            resources = {
                "requests": {
                    "cpu": compute_spec.requests.cpu,
                    "memory": compute_spec.requests.ram
                },
                "limits": {
                    "cpu": compute_spec.limits.cpu,
                    "memory": compute_spec.limits.ram
                }
            }

            return V1Container(name=name,
                               image=full_image_name,
                               resources=resources,
                               command=command,
                               args=args,
                               ports=container_ports)
            # env=env_list)
        else:
            return V1Container(name=name,
                               image=full_image_name,
                               command=command,
                               args=args,
                               ports=container_ports)
            # env=env_list)

    # @staticmethod
    # def set_apps_info(app_names: [], annotations: {}):
    #     app_name_to_status_map = {app_name: '' for app_name in app_names}
    #     annotations[DevboxTags.APPS] = KubernetesConverter.format_apps_status_annotation_value(app_name_to_status_map)

    # @staticmethod
    # def set_apps_debugging_protocols(apps: [CreateSandboxAppRequest], annotations: {}):
    #     debugging_protocols = list(set([p for a in apps for p in a.debugging_protocols]))
    #     annotations[DevboxTags.DEBUGGING_PROTOCOLS] = KubernetesConverter.format_annotation_value(debugging_protocols)
