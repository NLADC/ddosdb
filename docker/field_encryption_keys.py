#!/usr/bin/env python
import secrets;

print("".join(secrets.token_hex(32)), end="")
