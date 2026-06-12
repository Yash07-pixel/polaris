.PHONY: install test dev docker clean

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -q

dev:
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

docker:
	docker-compose up --build

clean:
	python -c "import pathlib; [p.unlink() for p in pathlib.Path('.').glob('test_molgenix*.db')]"
