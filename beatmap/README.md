# Running the backend API

First, install uv.
```bash
pip install uv
```

Then, install the dependencies.
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Then, run the API.
```bash
uvicorn api:app --reload
```


