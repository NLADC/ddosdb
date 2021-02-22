#!/usr/bin/env python3
import secrets;

# print("".join(secrets.token_hex(32)), end="")
generated_key = secrets.token_urlsafe(32)
print (generated_key)
