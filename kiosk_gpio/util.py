from datetime import datetime


def log(message: str):
    print(f'{datetime.timestamp(datetime.now())} :: {message}')
