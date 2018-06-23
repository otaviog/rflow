all:
	@echo Tutorial maintaining

run-tutorial.ipynb: tutorial.ipynb
	jupyter nbconvert --to notebook --execute --inplace $^ --ExecutePreprocessor.timeout=-1

tutorial.html: tutorial.ipynb
	jupyter nbconvert --to html --execute --output $@ $^ --ExecutePreprocessor.timeout=-1

clean:
	rm -rf *.pdf *.html full_tutorial.ipynb\
		big-text-freq.txt random-text-freq.txt random-text-freq.txt

