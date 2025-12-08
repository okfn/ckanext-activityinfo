import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.activityinfo import helpers
from ckanext.activityinfo.actions import activity_info as activity_info_actions
from ckanext.activityinfo.actions import resource as activityinfo_res_actions
from ckanext.activityinfo.auth import activity_info as activity_info_auth
from ckanext.activityinfo.blueprints import activity_info as activity_info_bp


class ActivityinfoPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "activityinfo")

    # IActions

    def get_actions(self):
        return {
            'act_info_get_databases': activity_info_actions.act_info_get_databases,
            'act_info_get_forms': activity_info_actions.act_info_get_forms,
            'act_info_get_form': activity_info_actions.act_info_get_form,
            'act_info_get_job_status': activity_info_actions.act_info_get_job_status,
            'act_start_download_job': activity_info_actions.act_start_download_job,
            'resource_create': activityinfo_res_actions.resource_create,
            'resource_update': activityinfo_res_actions.resource_update,
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'act_info_get_databases': activity_info_auth.act_info_get_databases,
            'act_info_get_forms': activity_info_auth.act_info_get_forms,
            'act_info_get_form': activity_info_auth.act_info_get_form,
            'act_info_get_job_status': activity_info_auth.act_info_get_job_status,
            'act_start_download_job': activity_info_auth.act_start_download_job,
        }

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_activity_info_api_key': helpers.get_activity_info_api_key,
        }

    # IBlueprint

    def get_blueprint(self):
        return [
            activity_info_bp.activityinfo_bp
        ]
