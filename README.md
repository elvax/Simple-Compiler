Simple compiler for C-like language. Full specification in [labor4.pdf](labor4.pdf)

## Requirements:
    Python 3.6.8
    ply 3.11    (python lib)
    bison
    flex
    c++ compiler

## Instalation
    sudo apt install bison
    sudo apt install flex
    pip install ply
    make
    
## Example
In tests/time we have `0-div-mod.imp`
```
[ div-mod.imp 
  1 0
  1 0 0 0
]

DECLARE
	a; b; c;
IN
	READ a;
	READ b;
	c := a / a;
	WRITE c;
	c := a / b;
	WRITE c;
	c := a % a;
	WRITE c;
	c := a % b;
	WRITE c;
END
```
This program reads input to 2 variables and does basic math operations
We compile it:
```
python3 main.py tests/time/0-div-mod.imp 0-div-mod.out.mr
```
which produces:
```
$cat 0-div-mod.out.mr 
GET B
SUB A A
STORE B
GET B
SUB A A
INC A
STORE B
...
```
Then we run compiled code:
```
$maszyna_rejestrowa/maszyna-rejestrowa 0-div-mod.out.mr 
Czytanie kodu.
Skończono czytanie kodu (liczba rozkazów: 164).
Uruchamianie programu.
? 1
? 0
> 1
> 0
> 0
> 0
Skończono program (koszt: 1881).
```
