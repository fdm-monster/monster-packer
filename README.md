# MonsterPacker 

## What?

MonsterPacker is a variant of MeatPack - a proposal mostly focused on Prusa Marlin and OctoPrint.
Find that algorithm here https://plugins.octoprint.org/plugins/meatpack/ and find the author Scott Mudge here https://github.com/scottmudge.

## Why 

I need an algorithm that encodes GCode (meant for storing on NOR Flash) in a computationally tractable way, line per line, on an embedded STM32 device equipped with ethernet stack (f.e. lwIP).
The decoding step will occur on a 200 MHz STM32 F7 microcontroller. Therefore LZ77/GZip options are not the first pick due to memory/CPU requirements.

When I found MeatPack it did not look efficient. I must say now, it seems to do a good job for the simplicity!
Still, I found some improvements.

# How

I made the MeatPack compression more efficient by use of three tricks/assumptions:
1) we remove whitespace altogether
2) we remove G1 codes, the most common operation in 3D printing by far
3) we avoid escaping Y-characters: they replace the whitespace in the MeatPack lookup table (4-bit values)

Most of the above assumptions were (probably) not possible for MeatPack, as it is used as a generically-reliable printer-compatible serial transformer for OctoPrint.
MonsterPacker also has to be extremely reliable, but there is no need to be compatible with all printers out there (just Prusa MK3S and Mini).
More importantly, my STM32 device will be serving GCode over UART to printers, therefore I have the opportunity to re-insert whitespace and G1 codes before transmission\*.
Concluding, the MonsterPack algorithm is equivalent to MeatPack and it is able to do this with more efficiency.

Example:
- (100%) ~20.687MB gcode file (7zip lvl-9 compressed: 1667kB)
- (-14%) ~17.783MB gcode without comments
- (-51%) ~10.064MB with an trivial algorithm, my initial attempt (replacing numbers with floats, gcodes with op-codes)
- (-53%) ~9.622MB with meatpack (whitespace included)
- (-59.5%) ~8.371MB meatpack (whitespace removed, Y-replaced in LUT, G1 codes removed)

Result: 6% improvement on a quite beefy GCode file. I expect this improvement to be present on most GCode files, but your mileage may vary (of course).

\*The whitespace 'should' be reconstructable on the fly given common sense. All parameters starting with X,Y,Z,S,R,F,T,W, etc can be prefixed with a whitespace to restore the original gcode line.

# Results

From my results it is clear that MonsterPacker is a decent approach to encoding GCode 5% more efficiently than MeatPacker in its default mode. Still, I would like to add that block encoding/compressing - multiple lines at the same time - must result in better efficiency. 
The latter is proven by the fact that the practical upper bound of 1.667MB (-91.9%) by 7Zip, Zip and XZ is still quite far from -59.5%.

I hope this helps you and your project!