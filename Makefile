all: mr setup


mr: 
	make -C maszyna_rejestrowa

setup: run_errors_tests.sh run_time_tests.sh main.py
	chmod +x $^

test_errors: run_errors_tests.sh
	./run_errors_tests.sh

clean:
	make -C maszyna_rejestrowa clean


# $@ to nazwa bieżącej reguły
# $^ to lista wszystkich bieżących zależności
# $? to lista nieaktualnych plików zależności
# $< to pierwszy plik z listy zależności