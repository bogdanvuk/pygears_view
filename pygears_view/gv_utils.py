def create_row(in_id, out_id, height, width):
    row_template = """
<tr>
    <td {0} width="2" height="{2}" fixedsize="true"></td>
    <td width="{3}" height="{2}" fixedsize="true"></td>
    <td {1} width="2" height="{2}" fixedsize="true"></td>
</tr>"""
    return row_template.format(
        '' if in_id is None else f'port="i{in_id}"',
        '' if out_id is None else f'port="o{out_id}"',
        height,
        width - 4,
    )


def get_node_record(node):
    label_template = """
<<table border="0" cellspacing="0" cellborder="1">
{}
</table>>"""

    input_ports = node.inputs
    output_ports = node.outputs
    rows = []

    iin = 0
    iout = 0

    cur_h = 0

    while True:

        try:
            pin = input_ports[iin].y()
        except IndexError:
            pin = None

        try:
            pout = output_ports[iout].y()
        except IndexError:
            pout = None

        if pin is None and pout is None:
            rows.append(
                create_row(None, None, node.height - cur_h, node.width))
            break

        if pout is None or (pin is not None and pin < pout):
            rows.append(create_row(None, None, pin - cur_h, node.width))

            rows.append(
                create_row(iin, None, input_ports[iin]._height, node.width))
            cur_h = pin + input_ports[iin]._height
            iin += 1
        elif pin is None or pout < pin:
            rows.append(create_row(None, None, pout - cur_h, node.width))
            rows.append(
                create_row(None, iout, output_ports[iout]._height, node.width))
            cur_h = pout + output_ports[iout]._height
            iout += 1
        else:
            rows.append(create_row(None, None, pout - cur_h, node.width))
            rows.append(
                create_row(iin, iout, output_ports[iout]._height, node.width))
            cur_h = pout + output_ports[iout]._height
            iin += 1
            iout += 1

    return label_template.format('\n'.join(rows))