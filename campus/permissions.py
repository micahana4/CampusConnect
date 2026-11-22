from .models import Registration, Student


def has_record_permission(user, model, action):
    if action == "view" and model not in (Registration, Student):
        return True
    required = [f"campus.{action}_{model._meta.model_name}"]
    if model is Registration and action in ("add", "change"):
        required.append("campus.view_student")
    return user.has_perms(required)
