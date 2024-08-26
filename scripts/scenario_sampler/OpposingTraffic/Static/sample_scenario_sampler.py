import argparse
import numpy as np




#############################################################################



                ## NAMINGS HAS TO BE CORRECTED



#############################################################################



def replace_params(input_file, output_file, replacements):

    with open(input_file, 'r') as file:
        file_content = file.read()

    for param, value in replacements.items():
        file_content = file_content.replace(param, str(value))

    with open(output_file, 'w') as file:
        file.write(file_content)

    print(f"scenario created and saved to {output_file}")



param_gap = np.random.normal(5.5, 3)
param_bias = np.random.normal(0, 0.5)
param_distance = np.random.uniform(0, 10)
param_velocity = np.random.uniform(0.5, 10)

np.random.uniform(0.5, 10)


parser = argparse.ArgumentParser(description="Designs a scenario based on given arguments in a scenario file.")


parser.add_argument('--gap', type=float, default=param_gap, help='the gab between the left and right car')
parser.add_argument('--bias', type=float, default=param_bias, help='shift of two cars twoard one side (skewed paarkingg space)')
parser.add_argument('--left_yaw', type=float, default=param_distance, help='yaw of the car parked in the left')
parser.add_argument('--right_yaw', type=float, default=param_velocity, help='yaw of the car parked in the right')

args = parser.parse_args()




dep_right_bias = -229 + args.bias + args.gap/2
dep_left_bias = -229 + args.bias - args.gap/2
dep_bike = args.left_yaw


input_file = 'raw.xosc'
output_file = 'output.xosc'

replacements = {
    'PARAM_1': dep_bike,
    'PARAM_2': dep_left_bias,
    'PARAM_3': dep_right_bias,
    'PARAM_4': args.right_yaw
}

replace_params(input_file, output_file, replacements)



