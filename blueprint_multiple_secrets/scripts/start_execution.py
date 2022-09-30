#!/usr/bin/env python
from cloudify import manager
from cloudify.state import ctx_parameters as inputs


create_inputs = { key: inputs.get(key, True) for key in inputs['inputs_list'] }
manager.get_rest_client().executions.start(**create_inputs)
