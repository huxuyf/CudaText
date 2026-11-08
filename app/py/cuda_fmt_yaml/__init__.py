from . import yaml

def do_format(text):
    obj = yaml.load(text)
    return yaml.dump(obj)
