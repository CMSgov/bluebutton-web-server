## Vendoring python requirements:

1. Edit the `requirements.in` file
2. Use `pip-compile` to generate an updated `requirements.txt` file:

```
pip-compile --output-file requirements.dev.txt requirements.dev.in
```

3. Download the requirements to the `vendor` directory:

```
pip download -r requirements/requirements.txt --dest vendor --platform linux_x86_64 --no-deps
```

4. At install time, tell pip not to use a package index, find packages in the `vendor` dir:

```
pip install -r requirements/requirements.dev.txt --no-index --find-links ./vendor/
```
