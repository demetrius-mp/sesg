---
hide:
  - navigation
---

# FAQ

## Why do I get too many duplicate search strings?

During our tests, when providing a small number of documents (`#!python < 10`), we detected lots of duplicate strings. For example, when providing the same 10 documents, but varying the model, and formulation parameters, almost half of the generated strings were duplicate.

With this in mind, we highly recommend to maintain some sort of cache for the generated strings, in order to avoid searching for a duplicate string in Scopus.