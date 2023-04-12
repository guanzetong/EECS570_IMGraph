from serial_links import SL
from collections import deque
in_port = deque()
for i in range(20):
    in_port.append(i)
out_port = deque()
sl = SL(in_port, out_port)
for i in range(10):
    print(f'cycle{i}\n')
    sl.one_cycle()
# Initialize the two-cycle delay function

# def two_cycle_delay(input_value):
#     """Returns the value from two cycles ago."""
#     previous_values = two_cycle_delay.previous_values
#     previous_values.append(input_value)
#     if len(previous_values) < 3:
#         return None
#     return previous_values.pop(0)

# # Initialize the previous_values attribute with two None values
# two_cycle_delay.previous_values = [None, None]
# two_cycle_delay.previous_values = [None, None]

# # Simulate two cycles
# input_value = 42
# output_value = two_cycle_delay(input_value)
# print(f"Input value: {input_value}")
# print(f"Output value: {output_value}")

# input_value = 87
# output_value = two_cycle_delay(input_value)
# print(f"Input value: {input_value}")
# print(f"Output value: {output_value}")

# # Simulate another cycle
# input_value = 99
# output_value = two_cycle_delay(input_value)
# print(f"Input value: {input_value}")
# print(f"Output value: {output_value}")
