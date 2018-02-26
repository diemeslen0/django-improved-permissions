""" permissions utils """
import inspect

from improved_permissions.exceptions import ParentNotFound, RoleNotFound


def is_role(role_class):
    """
    Check if the argument is a valid Role class.
    This method DOES NOT check if the class is registered in RoleManager.
    """
    from improved_permissions.roles import Role
    return inspect.isclass(role_class) and issubclass(role_class, Role) and role_class != Role


def get_roleclass(role_class):
    """
    Get the role class signature
    by string or by itself.
    """
    from improved_permissions.roles import RoleManager
    roles_list = RoleManager.get_roles()
    if role_class in roles_list:
        # Already a Role class.
        return role_class

    elif isinstance(role_class, str):
        # Trying to get via string.
        for role in roles_list:
            if role.get_class_name() == role_class:
                return role

    raise RoleNotFound()


def string_to_permission(perm):
    """
    Transforms a string representation
    into a Permissin instance.
    """
    from django.contrib.auth.models import Permission
    try:
        app_label, codename = perm.split('.')
    except (ValueError, IndexError):
        raise AttributeError
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def permission_to_string(perm):
    """
    Transforms a Permission instance
    into a string representation.
    """
    app_label = perm.content_type.app_label
    codename = perm.codename
    return '%s.%s' % (app_label, codename)


def get_permissions_list(models_list):
    """
    Given a list of Model instances or a Model
    classes, return all Permissions related to it.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    if models_list is None:
        return list()

    ct_list = ContentType.objects.get_for_models(*models_list)
    ct_ids = [ct.id for cls, ct in ct_list.items()]

    return list(Permission.objects.filter(content_type_id__in=ct_ids))


def get_parents(model):
    """
    Return the list of instances refered
    as "parents" of a given model instance.
    """
    result = list()
    if hasattr(model, 'RoleOptions'):
        options = getattr(model, 'RoleOptions')
        if hasattr(options, 'permission_parents'):
            parents_list = getattr(options, 'permission_parents')
            for parent in parents_list:
                if hasattr(model, parent):
                    result.append(getattr(model, parent))
                else:
                    raise ParentNotFound()
    return result


def inherit_check(role_obj, permission):
    """
    Check if the role class has the following
    permission in inherit mode.
    """
    from improved_permissions import ALL_MODELS, ALLOW_MODE

    role = get_roleclass(role_obj.role_class)
    if role.inherit is True:
        if role.get_inherit_mode() == ALLOW_MODE:
            if permission in role.inherit_allow:
                return True, True
            elif role.models == ALL_MODELS:
                return True, False
        else:
            if permission in role.inherit_deny:
                return True, False
            elif role.models == ALL_MODELS:
                return True, True

    return False, False
