This is a simple 32 bit 5-stage processor built in Logisim based on the book `Computer Architecture a Quantitative Approach`, which I've thrown together so I can play around with it while reading the book. The `adders.circ` file contains the processor in the `rrisc` subcircuit, everything before that was some old stuff from school that I wanted to reuse parts of.

Descriptions of op-codes and registers can be found in `ISA attempt rriscv.xlsx`. There are only two types of instrucions, being the one listed in that spreadsheet and one which merges the imm and rd fields into an immRD field which is just a longer immediate (you will see this in the op-codes).

This is just a toy processor but I hope to add forwarding and branch prediction soon enough once I get the compiler somewhat down.

Update: Forwarding/bypassing has been added and the compiler has been abondoned to be rewritten later
