# API Examples

Example scripts interacting with USDtb Minting API

# Quick start for minting

## Prepare .env file

1. Create a `.env` file in the root directory:

```
$ cp .env.example .env
```

2. Edit the `.env` file with your credentials. These will be loaded into environment variables on start.

## Install Python

1. Install Python 3.11
2. Create and activate a self-contained Python environment:

```
$ python3 -m venv venv
$ source venv/bin/activate
```

3. Install requirements:

```
(venv) $ pip install -r requirements.txt
```

## Run mint

```
(venv) $ python3 ./py/usdtb_mint_script.py
```
