



def report_time(t):
	# https://chatgpt.com/c/6732e473-b504-8005-a431-f6c863623545
    units = [
        ('h', 3600, None),
        ('min', 60, 3600),
        ('s', 1, 60),
        ('ms', 1e-3, 1),
        ('µs', 1e-6, 1e-4)
    ][::-1]
    if t == 0:
        return '0 µs'
    for i, (unit_name, unit_scale, next_unit_threshold) in enumerate(units):
        value = t / unit_scale
        formatted_value = format_sig_figs(value, 2)
        rounded_value = float(formatted_value)

        # Check if the rounded value reaches or exceeds the threshold for the next unit
        if next_unit_threshold is not None:
            next_unit_value = next_unit_threshold / unit_scale
            if rounded_value > next_unit_value:
                continue  # Move to the next larger unit

        return f"{formatted_value}{unit_name}"
    # If none of the units matched, default to the largest unit
    value = t / units[-1][1]
    formatted_value = format_sig_figs(value, 2)
    return f"{formatted_value}{units[-1][0]}"


def format_sig_figs(num, sig_figs):
    if num == 0:
        return "0"
    else:
        import math
        order = int(math.floor(math.log10(abs(num))))
        factor = 10 ** (sig_figs - 1 - order)
        rounded_num = round(num * factor) / factor
        decimals = max(sig_figs - order - 1, 0)
        # Avoid unnecessary decimal places if rounded_num is an integer
        if rounded_num == int(rounded_num):
            decimals = 0
        format_string = "{0:." + str(decimals) + "f}"
        return format_string.format(rounded_num)
