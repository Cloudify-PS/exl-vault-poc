#!/usr/bin/env python
import time
from cloudify.state import ctx_parameters as inputs

timeout = inputs.get('timeout')
time.sleep(timeout)
