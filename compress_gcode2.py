import monsterpacker as mp2
import meatpack as mp

origin_filename = 'input.gcode'
out_file = 'input_no_comment.gcode'

# out1_file = 'meatpacker.mpcode'
# mp.initialize()
# mp.strip_comments(origin_filename, out_file)
# mp.pack_file(out_file, out1_file)

out2_file = 'monster_withg1.m2code'
out2b_file = 'monster.m2code' # used for decoding

# Strip the GCode from comments
mp2.initialize()
mp2.strip_comments(origin_filename, out_file)

# Pack the file keeping G1 codes intact
mp2.pack_file(out_file, out2_file, remove_g1=False)

# Now run again but removing G1 from lines
# All other GCode commands are kept intact
mp2.pack_file(out_file, out2b_file, remove_g1=True)
