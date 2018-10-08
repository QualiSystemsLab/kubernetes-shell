from data_model import KubernetesService
from cloudshell.cp.core.models import DeployApp


def convert_to_int_list(list_str, separator=','):
    """
    :param str list_str:
    :param str separator:
    :rtype: List[int]
    """
    if not list_str:
        return []
    separated_list = list_str.split(separator)
    trimmed_list = list(map(lambda x: x.strip(), separated_list))
    return list(map(int, trimmed_list))


def create_deployment_model_from_action(deploy_app_action):
    """
    :param DeployApp deploy_app_action:
    :rtype: KubernetesService
    """
    if deploy_app_action.actionParams.deployment.deploymentPath == 'Kubernetes.Kubernetes Service':
        kube_service_model = KubernetesService(deploy_app_action.actionParams.appName)
        kube_service_model.attributes = deploy_app_action.actionParams.deployment.attributes
        return kube_service_model

    raise ValueError('Unsupported deployment path')


def convert_app_name_to_valide_kubernetes_name(app_name):
    """
    :param str app_name:
    :rtype: str
    """
    return app_name.lower().replace(' ', '-').replace('_', '-')


def get_custom_params_value(custom_params_list, key):
    """
    :param List custom_params_list:
    :param str key:
    :rtype: str
    """
    param = next(iter(
        filter(lambda x: x['name'] == key,
               custom_params_list)), None)
    if param:
        return param['value']
    else:
        return None
