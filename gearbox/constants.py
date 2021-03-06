#!/usr/bin/python

# PIPE
PIPE_WIDTH = 1.2
PIPE_STYLE_DEFAULT = 'line'
PIPE_STYLE_DASHED = 'dashed'
PIPE_STYLE_DOTTED = 'dotted'
PIPE_DEFAULT_COLOR = (127, 149, 151, 255)
PIPE_WAITED_COLOR = (50, 90, 160, 255)
PIPE_ACTIVE_COLOR = (180, 50, 90, 255)
PIPE_HANDSHAKED_COLOR = (60, 100, 20, 255)

PIPE_HIGHLIGHT_COLOR = (232, 184, 13, 255)
PIPE_LAYOUT_STRAIGHT = 0
PIPE_LAYOUT_CURVED = 1

# PORT DEFAULTS
IN_PORT = 'in'
OUT_PORT = 'out'
PORT_ACTIVE_COLOR = (29, 80, 84, 255)
PORT_ACTIVE_BORDER_COLOR = (45, 215, 255, 255)
PORT_HOVER_COLOR = (17, 96, 20, 255)
PORT_HOVER_BORDER_COLOR = (136, 255, 35, 255)

# NODE DEFAULTS
NODE_ICON_SIZE = 24
NODE_SEL_COLOR = (255, 255, 255, 30)
NODE_SEL_BORDER_COLOR = (254, 207, 42, 255)

# DRAW STACK ORDER
Z_VAL_PIPE = -1
Z_VAL_NODE = 1
Z_VAL_PORT = 2
Z_VAL_NODE_WIDGET = 3
