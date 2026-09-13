# Authoritative sources

- Derived dataset source: https://github.com/Iqbalez/laboratory-procedure-links
- Original STAR Protocols XML access: https://europepmc.org/RestfulWebService
- CC BY4.0 terms: https://creativecommons.org/licenses/by/4.0/
- Encoder model card: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Pinned encoder revision:1110a243fdf4706b3f48f1d95db1a4f5529b4d41. encoder_metadata.json pins the local safetensors checksum and inference settings.

Individual source article authors, titles, DOIs and URLs are retained in the separately supplied raw source_index.json. Each retained article's XML rights statement was independently checked for CC BY4.0. The encoder's model card declares Apache-2.0; its weights are not part of this dataset. Semantic features are fixed independent per-text inferences, not training on any release split.

Original source-extraction release1.0.2 contains604 article records from the frozen first1,000 core query results, with999 successful downloads. Feature augmentation release2.0.0 adds passages.py, encode.py and pinned encoder metadata. Public source publication excludes frozen article records, vectors, source membership, answers and split membership.
