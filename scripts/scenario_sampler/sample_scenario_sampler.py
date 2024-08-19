import argparse
import numpy as np


def replace_params(input_file, output_file, replacements):

    with open(input_file, 'r') as file:
        file_content = file.read()

    for param, value in replacements.items():
        file_content = file_content.replace(param, str(value))

    with open(output_file, 'w') as file:
        file.write(file_content)

    print(f"Replaced parameters and saved to {output_file}")

input_file = 'raw.xosc'
output_file = 'output.xosc'

replacements = {
    'PARAM_1': -221 + np.random.normal(0, 10),
    'PARAM_2': -233 + np.random.normal(0, 1),
    'PARAM_3': -226 + np.random.normal(0, 1),
    'PARAM_4': np.random.uniform(0.5, 10)
}

replace_params(input_file, output_file, replacements)




