import os
import yaml
import datetime
import jsonschema
from jsonschema import Draft4Validator, exceptions
import uri


def load(filename, base_path):
    file = read_file(os.path.join(base_path,
                                  '{}.yaml'.format(filename)))

    return yaml.safe_load(file)

def read_file(filepath):
    return open(filepath).read()

def urls(ruleset):
    return map(url, ruleset)

def find_by_url(url, ruleset):
    return head(filter(lambda x: x['url'] == url,
                       ruleset))

def filter_urls(request_url, urls):
    return filter(match_url(request_url), urls)

##
# Actual: The current url checked from the ruleset.
# Expected: The url from the request.
def match_url(expected):
    return lambda actual: uri.eq(actual, expected)


def head(collection):
    try:
        return collection[0]
    except:
        return None

# Rule functions
def body(filename, base_path):
    return read_file(os.path.join(base_path,
                                  filename))

def body_filename(rule):
    if 'response' in rule:
        if 'body' in rule['response']:
            return rule['response']['body']
    return None

def url(rule):
    return rule['url']

def delay(rule):
    if 'response' in rule:
        if 'delay' in rule['response']:
            return int(rule['response']['delay'])
    return None

def skip(rule):
    if 'request' in rule:
        if 'skip' in rule['request']:
            return rule['request']['skip']
    return False

def process_headers(target, rule, flow_headers):
    if target in rule:
        if 'headers' in rule[target]:
            headers = rule[target]['headers']
            remove_headers(headers, flow_headers)
            add_headers(headers, flow_headers)


def remove_headers(headers, flow_headers):
    to_remove = headers.get('remove', {})
    for header in to_remove:
        if header in flow_headers:
            del flow_headers[header]

def add_headers(headers, flow_headers):
    to_add = headers.get('add', {})

    for (header, value) in to_add.items():
        flow_headers[header] = value

def status_code(rule):
    if 'response' in rule:
        if 'code' in rule['response']:
            return int(rule['response']['code'])
    return None

def schema(rule, base_path):
    if not 'schema' in rule: return

    return yaml.safe_load(read_file(os.path.join(base_path,
                                                 rule['schema'])))

def check(instance, schema):
    v = Draft4Validator(schema)
    timestamp = datetime.datetime.utcnow().isoformat()

    return [to_hashmap(x, timestamp) for x in sorted(v.iter_errors(yaml.safe_load(instance)),
                                                     key=exceptions.relevance)]

def to_hashmap(item, timestamp):
    return {"message": item.message,
            "context": item.context,
            "timestamp": timestamp,
            "cause": item.cause,
            "schema_path": list(item.schema_path),
            "path": list(item.absolute_path)}
