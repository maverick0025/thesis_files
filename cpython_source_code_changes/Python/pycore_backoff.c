// Ashok starts here (this is a new file)

#include "Python.h"              // Brings in PyObject, PyTypeObject, etc.
#include "pycore_backoff.h"      // Our header
#include "pycore_optimizer.h"
#include "pycore_code.h"
// #include "optimizer.c"

int _Py_JumpBackwardInitialValue = JUMP_BACKWARD_INITIAL_VALUE;
int _Py_JumpBackwardInitialBackoff = JUMP_BACKWARD_INITIAL_BACKOFF;

int _Py_SideExitInitialValue = SIDE_EXIT_INITIAL_VALUE;
int _Py_SideExitInitialBackoff = SIDE_EXIT_INITIAL_BACKOFF;

int _Py_AdaptiveCoolDownValue = ADAPTIVE_COOLDOWN_VALUE;
int _Py_MaxChainDepth = MAX_CHAIN_DEPTH;

int _Py_ConfidenceLowerLimit = 333;

//Once this is added, add Python/pycore_backoff.o \ at around line 480 in Makefile.pre.in file

//Ashok until here (this whole file ; also add this file name in make file so that it's object code will be generated later on with others)