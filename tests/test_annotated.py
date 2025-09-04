from typing import Annotated


def say_hello(name: Annotated[str, "this is just metadata"]) -> str:
    return f"Hello {name.__repr__()}"


if __name__=='__main__':
    print(say_hello("Jack"))