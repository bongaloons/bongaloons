# Running the backend API

## Installation
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

## Backend server
Then, run the API.
```bash
uvicorn api:app --reload
```


## Find port
```bash
ioreg -p IOUSB
```

```bash
ls /dev/S.usbmodem101 
```


## Pose Detection

```bash
python detect_hand_position.py 
```

```bash
python detect_hand_position.py --use_double
```

