Descriptions of op-codes and registers can be found in `ISA attempt rriscv.xlsx`. There are only two types of instrucions, being the one listed in that spreadsheet and one which merges the imm and rd fields into an immRD field which is just a longer immediate (you will see this in the op-codes).

The assembler uses the same format for instruction parameters defined in the spreadsheet. 

This is just a toy processor but I hope to add forwarding and branch prediction soon enough once I get the compiler somewhat down.

Update: Forwarding/bypassing has been added and the compiler has been abondoned to be rewritten later

Update #2: `rriscvmcompiler.py` contains the start of a compiler for a stack based byte code language. Currently only `push (segment) (index)`, `pop (segment) (index)`, and basic arithmetic operations are implemented. This will be based off of the language used in the `nand2tetris` lecture notes.

Update #3: added `label`, `goto`, `if-goto` (pops top of stack and checks if it should jump) to byte language. At some point, I may restructure the way instructions are defined to allow for bigger fields when the others are not needed (other than just immRD).

Updte #4: added `function`, `call`, and `return` along with logic for the call stack. Memory layout documented in the spreadsheet.
