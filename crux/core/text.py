def safe_text(value):
    # Filenames, Git paths and environment values are untrusted terminal text.
    return "".join(c if c.isprintable() else f"\\x{ord(c):02x}" for c in str(value))

