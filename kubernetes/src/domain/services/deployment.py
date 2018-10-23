import time
from logging import Logger
from multiprocessing import TimeoutError

from typing import List, Dict

from kubernetes.client import V1ObjectMeta, AppsV1beta1Deployment, AppsV1beta1Api, AppsV1beta1DeploymentSpec, \
    V1PodTemplateSpec, V1PodSpec, V1Container, V1ContainerPort, V1EnvVar, V1DeleteOptions
from kubernetes.client.rest import ApiException

from domain.services.tags import TagsService
from model.deployment_requests import AppComputeSpecKubernetes, AppComputeSpecKubernetesResources, \
    AppDeploymentRequest, ApplicationImage
from model.clients import KubernetesClients


class KubernetesDeploymentService:
    def __init__(self):
        pass

    def delete_app(self, logger, clients, namespace, app_name_to_delete):
        """
        Delete a deployment immediately. All pods are deleted in the foreground.
        :param Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str app_name_to_delete:
        :return:
        """
        try:
            delete_options = V1DeleteOptions(propagation_policy='Foreground',
                                             grace_period_seconds=0)
            clients.apps_api.delete_namespaced_deployment(name=app_name_to_delete,
                                                          namespace=namespace,
                                                          body=delete_options,
                                                          pretty='true')
        except ApiException as e:
            if e.status == 404:
                # Deployment does not exist, nothing to delete but
                # we can consider this a success.
                logger.warn('not deleting nonexistent deploy/{} from ns/{}'.format(app_name_to_delete, namespace))
            else:
                raise
        else:
            logger.info('deleted deploy/{} from ns/{}'.format(app_name_to_delete, namespace))

    def create_app(self, logger, clients, namespace, name, labels, app):
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

        container = self._prepare_app_container(name=app.name,
                                                image=app.image,
                                                start_command=app.start_command,
                                                environment_variables=app.environment_variables,
                                                compute_spec=app.compute_spec,
                                                internal_ports=app.internal_ports,
                                                external_ports=app.external_ports)

        pod_spec = V1PodSpec(containers=[container])
        app_template = V1PodTemplateSpec(metadata=template_meta, spec=pod_spec)
        app_spec = AppsV1beta1DeploymentSpec(replicas=app.replicas, template=app_template)
        deployment = AppsV1beta1Deployment(metadata=meta, spec=app_spec)

        logger.info("Creating namespaced deployment for app {}".format(name))
        logger.debug("Creating namespaced deployment with the following specs:")
        logger.debug(deployment.to_str())

        return clients.apps_api.create_namespaced_deployment(namespace=namespace,
                                                             body=deployment,
                                                             pretty='true')

    @staticmethod
    def _prepare_app_container(name, image, start_command, environment_variables, compute_spec, internal_ports,
                               external_ports):
        """
        :param str start_command:
        :param Dict[str, str] environment_variables:
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

        env_list = [V1EnvVar(name=key, value=value) for key, value in environment_variables.iteritems()] \
            if environment_variables else []

        # user_data_str = KubernetesDeploymentService._get_user_data(
        #     name=name,
        #     start_command=start_command,
        #     script_name=script_name,
        #     healthcheck_script_name=healthcheck_script_name,
        #     namespace=namespace,
        #     start_command_script_name=start_command_script_name,
        #     has_artifacts=has_artifacts)

        command = None
        args = None
        if start_command:
            command = ['/bin/bash', '-c', '--']
            args = [start_command]  # ["while true; do sleep 30; done;"]  # run a task that will never finish

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
                               ports=container_ports,
                               env=env_list)
        else:
            return V1Container(name=name,
                               image=full_image_name,
                               command=command,
                               args=args,
                               ports=container_ports,
                               env=env_list)

    def wait_until_all_replicas_ready(self, logger, clients, namespace, app_name, deployed_app_name,
                                      delay=10, timeout=120):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str app_name:
        :param str deployed_app_name:
        :param int delay:
        :param int timeout:
        :return:
        """
        start_time = time.time()
        while True:
            deployment = self.get_deployment_by_name(clients, namespace, app_name)

            if not deployment:
                raise ValueError('Something went wrong. Deployment {} not found.')

            # check if all replicas are ready
            if deployment.spec.replicas == deployment.status.ready_replicas:
                # all replicas are ready - success
                return

            if time.time() - start_time >= timeout:
                try:
                    query_selector = self._prepare_deployment_default_label_selector(app_name)
                    pods = clients.core_api.list_namespaced_pod(namespace=namespace, label_selector=query_selector).items
                    logger.error("Deployment dump:")
                    logger.error(str(deployment))
                    logger.error("Pods dump:")
                    logger.error(str(pods))
                except:
                    logger.exception("Failed to get more data about pods and deployment for deployed app {}"
                                     .format(deployed_app_name))

                raise TimeoutError('Timeout waiting for {} replicas to be ready for deployed app {}. '
                                   'Please look at the logs for more information'
                                   .format(deployment.status.replicas, deployed_app_name))

            time.sleep(delay)

    def wait_until_exists(self, logger, clients, namespace, app_name, delay=10, timeout=600):
        """
        Waits until the deployment called 'app_name' exists in Kubernetes regardless of state
        :param int delay: the time in seconds between each pull
        :param int timeout: timeout in seconds until time out exception will raised
        :param Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str app_name:
        """
        query_selector = self._prepare_deployment_default_label_selector(app_name)

        start_time = time.time()

        while True:
            result = \
                clients.apps_api.list_namespaced_deployment(namespace=namespace, label_selector=query_selector).items
            if not result:
                return
            if time.time() - start_time >= timeout:
                raise TimeoutError('Timeout: Waiting for deployment {} to be deleted'.format(app_name))
            time.sleep(delay)

    def _prepare_deployment_default_label_selector(self, app_name):
        query_selector = "{app_selector}=={app_name}".format(
            app_selector=TagsService.get_default_selector(app_name),
            app_name=app_name)
        return query_selector

    def update_deployment(self, logger, clients, namespace, app_name, updated_deployment):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str app_name:
        :param AppsV1beta1Deployment updated_deployment:
        :return:
        """
        api_response = clients.apps_api.patch_namespaced_deployment(
            name=app_name,
            namespace=namespace,
            body=updated_deployment)
        logger.debug("Deployment {} in ns/{} updated. Status='{}'".format(app_name, namespace, str(api_response.status)))

    def get_deployment_by_name(self, clients, namespace, app_name):
        """
        :param KubernetesClients clients:
        :param str namespace:
        :param str app_name:
        :rtype: AppsV1beta1Deployment
        """
        query_selector = self._prepare_deployment_default_label_selector(app_name)
        items = clients.apps_api.list_namespaced_deployment(namespace=namespace, label_selector=query_selector).items
        if not items:
            return None
        if len(items) > 1:
            raise ValueError("More than a one deployment found with the same app name {}".format(app_name))
        return items[0]

    # @staticmethod
    # def set_apps_info(app_names: [], annotations: {}):
    #     app_name_to_status_map = {app_name: '' for app_name in app_names}
    #     annotations[DevboxTags.APPS] = KubernetesConverter.format_apps_status_annotation_value(app_name_to_status_map)

    # @staticmethod
    # def set_apps_debugging_protocols(apps: [CreateSandboxAppRequest], annotations: {}):
    #     debugging_protocols = list(set([p for a in apps for p in a.debugging_protocols]))
    #     annotations[DevboxTags.DEBUGGING_PROTOCOLS] = KubernetesConverter.format_annotation_value(debugging_protocols)
