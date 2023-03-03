import monsterpacker as mp2
import time

in_file = 'monster.m2code'
out_file = 'original.gcode'
mp2.initialize()

tm = time.time()
data = mp2.decode_file(in_file)

out_file = open(out_file, "w")
out_file.writelines(data)
out_file.flush()

tm2 = time.time()

print(tm2-tm)