This is a processor I created so that I can follow along with some of the concepts in `Computer Architecture: A Quantitative Approach` by John Hennessy and David Patterson. I have also put together a simple ISA (described in `ISA attempt rriscv.xlsx`) and assembler to go along with it. I have also written a stack based virtual machine compiler inspired by the one in the `nand2tetris` series but with a different hardware level implementation and memory layout. A custom object oriented higher level language called `rubellite` (cheap version of rubyies, lightly based off the `ruby` language), which will compile down to the bytecode language, is currently in development (currently generating ASTs, working on final compiler).

## Processor/assembler features:

- 32 bit
- 5 stage pipeline (IF, ID, EX, MEM, WB)
- 32 registers
- 32 implemented opcodes (up to 64)
- Register forwarding/bypassing

Descriptions of op-codes and registers can be found in `ISA attempt rriscv.xlsx`. There are only two types of instrucions, being the one listed in that spreadsheet and one which merges the imm and rd fields into an immRD field which is just a longer immediate (this is subject to change, I will probably add more).

The assembler uses the same format for instruction parameters defined in the spreadsheet. 

## VM compiler features:

- Push/pop operations
- temp, static, result, local, argument, ptr1, and ptr2 segments in memory that push/pop can use
    - ptr1 and ptr2 segment adresses can be set with `pop pointer` `0`/`1` and allow for popping to arbitrary memory locations (heap eventually)
- Labels, conditional label jumps
- Functions, calls, returns

## Rubellite programming language features (in development):

- Classes
- Fields, static, and local variables
- Methods and static functions
- If (else) statements, while statements
- Expression parseing (no order of operations yet though)
- Comments

## devlog

Update #1: Forwarding/bypassing has been added.

Update #2: `rriscvmcompiler.py` contains the start of a compiler for a stack based byte code language. Currently only `push (segment) (index)`, `pop (segment) (index)`, and basic arithmetic operations are implemented. This will be based off of the language used in the `nand2tetris` lecture notes.

Update #3: added `label`, `goto`, `if-goto` (pops top of stack and checks if it should jump) to byte language. At some point, I may restructure the way instructions are defined to allow for bigger fields when the others are not needed (other than just immRD).

Updte #4: added `function`, `call`, and `return` along with logic for the call stack. Memory layout documented in the spreadsheet.

Update #5: This took a lot longer than expected but I have began writing my own Object Oriented language to compile down to the bytecode language. Its syntax is very vaguely based on `ruby` and I have it called `rubellite` (a gem which is known as a cheaper version of a ruby) with the file extension `rbl`. So far I have defined the grammer (currently LL(3)), created a tokenizer and parser which gets it to an AST and am going to began working on the compiler. The choice to go with an Object Oriented language was made as the VM I put together based on the one from the `nand2tetris` project is only really designed to be able to push one value onto the stack at the time, so any implementation of structs would just be working on pointers to structs, and at that point there's really no reason not to just have objects. This will also allow me to base the OS somewhat on the one from `nand2tetris` as they also use a custom object oriented language (although they skip AST generation which I found odd) and I have no prior experience with operating systems and some guidence would be nice. Also I renamed the `this` and `that` sections in the bytecode language to `ptr1` and `ptr2` as I found those to be more intuitive. Other minor hardware fixes.
