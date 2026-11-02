# Vendored third-party sources

`legacy/vendor/connectome0121/` holds the Nilearn 0.12.1, NiBabel 5.3.2 and Packaging 25.0
packages exactly as pip installed them into the original analysis environment, with tests and
bytecode removed. The runner imports them from this path so the v2 replay uses the same library
code that produced the frozen results. Their licenses are kept in each `.dist-info/licenses/`
directory and apply separately from this project's MIT license.

## Comparison with the official wheels (2 November 2026)

**No library source file is modified.** Every vendored file was compared byte for byte with the
official PyPI wheels:

| Wheel | SHA256 |
|---|---|
| `nilearn-0.12.1-py3-none-any.whl` | `2112e1cdf9f7b96e0af87d679997e834ee36534fc0a970811a703700820edc4c` |
| `nibabel-5.3.2-py3-none-any.whl` | `52970a5a8a53b1b55249cba4d9bcfaa8cc57e3e5af35a29d7352237e8680a6f8` |
| `packaging-25.0-py3-none-any.whl` | `29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484` |

| Result | Files |
|---|---:|
| Identical to the wheel | 441 |
| `RECORD` differs: pip's installed record, which adds `__pycache__` and install-marker entries and drops no wheel entry | 3 |
| Added by pip at install time (`INSTALLER`, `REQUESTED`) | 6 |
| In the wheel but not vendored (test modules) | 445 |

An earlier version of [the reproduction guide](README.md) called these sources "patched". That
was inaccurate: they are unmodified upstream code.

## Repeating the check

```bash
python -m pip download --no-deps --only-binary=:all: -d wheels \
  nilearn==0.12.1 nibabel==5.3.2 packaging==25.0
mkdir upstream && for w in wheels/*.whl; do unzip -q -o "$w" -d upstream; done
diff -rq upstream reproduction/legacy/vendor/connectome0121
```

Expected output: the three `RECORD` files differ, the six install markers exist only in the
vendored tree, and the `tests/` directories exist only upstream.
