import sys
sys.path.append('../../')
from hydraseq import Hydraseq

face_spaced = """
0 0  0  0 0
0 o  o  0 0
0 0  db 0 0
0 v  u  v 0
0 0  0  0 0
_end
"""

face = """
o o
db
v u v
_end
"""

hdq1 = Hydraseq('0_')
for pattern in [
    "o 0_eye",
    "db 0_nose",
    "v 0_left_mouth",
    "u 0_mid_mouth",
    "v 0_right_mouth",
]:
    hdq1.insert(pattern)

hdq2 = Hydraseq('1_')
for pattern in [
    "0_eye 0_eye 1_eyes",
    "0_nose 1_nose",
    "0_left_mouth 0_mid_mouth 0_right_mouth 1_mouth",
]:
    hdq2.insert(pattern)
hdq3 = Hydraseq('2_')
for pattern in [
    "1_eyes 1_nose 1_mouth 2_FACE"
]:
    hdq3.insert(pattern)

hdq0 = Hydraseq("_")
cortex = [hdq0, hdq1, hdq2, hdq3]