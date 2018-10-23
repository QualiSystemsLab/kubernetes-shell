

def get_provider_tag_name(tag_name):
    """
    :param str tag_name:
    :return:
    """
    return 'cloudshell-{}'.format(tag_name)


class TagsService(object):
    SANDBOX_ID = get_provider_tag_name('sandbox-id')

    INTERNAL_PORT_PREFIX = 'pi'
    EXTERNAL_PORT_PREFIX = 'pe'

    # SERVICES
    INTERNAL_SERVICE = get_provider_tag_name("internal-service")
    EXTERNAL_SERVICE = get_provider_tag_name("external-service")
    SERVICE_APP_NAME = get_provider_tag_name("service-app-name")
    EXTERNAL_SERVICE_POSTFIX = 'external'

    @staticmethod
    def get_default_selector(app_name):
        """
        :param str app_name:
        :return:
        """
        return get_provider_tag_name('selector-{app_name}'.format(app_name=app_name))
