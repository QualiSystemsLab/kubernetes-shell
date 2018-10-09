import json

from cloudshell.shell.core.driver_context import ResourceContextDetails

from domain.common.additional_data_keys import DeployedAppAdditionalDataKeys
from domain.common.utils import get_custom_params_value


class DeployedAppResource(object):
    def __init__(self, resource_context):
        """
        :param ResourceContextDetails resource_context:
        """
        self._resource = resource_context

        self.app_request_json = json.loads(self._resource.app_context.app_request_json)
        self.deployed_app_dict = json.loads(self._resource.app_context.deployed_app_json)
        self.vm_details = self.deployed_app_dict['vmdetails']
        self.vm_custom_params = self.vm_details['vmCustomParams']

    @property
    def cloudshell_resource_name(self):
        return self._resource.name

    @property
    def kubernetes_name(self):
        return self.vm_details['uid']

    @property
    def namespace(self):
        """
        :rtype: str
        """
        namespace = get_custom_params_value(self.vm_custom_params,
                                            DeployedAppAdditionalDataKeys.NAMESPACE)
        if not namespace:
            raise ValueError("Something went wrong. Couldn't get namespace from custom params for deployed app '{}'"
                             .format(self._resource.name))

        return namespace

    @property
    def replicas(self):
        """
        :rtype: int
        """
        replicas_str = get_custom_params_value(self.vm_custom_params,
                                               DeployedAppAdditionalDataKeys.REPLICAS)
        if not replicas_str:
            raise ValueError("Something went wrong. Couldn't get replicas from custom params for deployed app '{}'"
                             .format(self._resource.name))

        try:
            return int(replicas_str)
        except:
            raise ValueError("Something went wrong. Couldn't parse replicas value {replicas} from custom params data "
                             "for deployed app '{deployed_app}' "
                             .format(deployed_app=self._resource.name, replicas=replicas_str))
