def ro_param(obj, param_name):
    return (lambda: getattr(obj, param_name), None)

def rw_param(obj, param_name):
    return (lambda: getattr(obj, param_name), lambda value: setattr(obj, param_name, value))