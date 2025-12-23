# -*- coding: utf-8 -*-
from api.models.function_specs import FUNCTION_SPECS

spec = FUNCTION_SPECS.get('96')
print(f'Function 96 Registered: {spec is not None}')
if spec:
    print(f'  Name: {spec.name}')
    print(f'  Required: {spec.required_params}')
    print(f'  CLI Flags: {spec.cli_flag_map}')
    print(f'  Description: {spec.description}')
