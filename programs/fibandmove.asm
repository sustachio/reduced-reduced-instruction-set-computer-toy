# 3 operations in between function and dependent

# alternate between x2 and x3 as sum of x2+x3
li x2,1
li x3,1
li x4,1 # mem counter
li x5,9 # max iterations (0 indexed, add 1)
sw x1,0(x0)
sw x1,1(x0)

## load first 10 fibonacci numbers into ram
L: add2
add x2,x2,x3
add x4,x4,x1 # next in mem
sw x2,0(x4)
add x3,x3,x2
add x4,x4,x1 # next in mem
sw x3,0(x4)
blt x4,x5, Ladd2
nop
nop
nop

## copy the first 10 ram values into 20-29
li x4,0  # count 0-9
li x5,10 # upper bound (adding after we write)
L: moveDat
lw x3,0(x4)
add x4,x4,x1 # next in mem
sw x3,20(x4)
blt x4,x5,LmoveDat
