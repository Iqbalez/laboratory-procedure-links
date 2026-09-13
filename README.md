# Laboratory Procedure Links

A derived collection of author-published laboratory method steps and troubleshooting notes. Each included article supplies its own problem descriptions, remedies, and explicit references to numbered method steps. The records support research on locating the procedural scope of existing troubleshooting guidance. They are not clinical recommendations, validated diagnoses, or instructions to perform an experiment safely.

## Source and rights

The source is the CC BY 4.0 subset of STAR Protocols articles available as JATS XML through Europe PMC. Article-level XML permission statements are checked individually; an index claiming open access is insufficient. Copyright remains with the respective authors. The raw source_index.json retains the authors, article titles, DOI and publisher repository URL needed for attribution. Data is CC BY 4.0; extraction code is MIT. No figures, external supplementary files, third-party full texts, author emails or personal contact information are redistributed in the extracted records.

## Release contents

Release 1.0.1 starts with a frozen 1,000-article metadata census. Of 999 successfully downloaded XML articles, 604 pass the extraction scope and article-license checks. The raw upload contains nine files: records.jsonl, source_index.json, source_report.json, generate.py, requirements.txt, RELEASE.json, DATA_LICENSE.txt, LICENSE and README.md. The source_report.json records every excluded article and reason. The source_index.json includes metadata used to connect author groups, including metadata for articles excluded from the modeling records.

records.jsonl stores one extracted article per line, with article_id, title, xml_sha256, numbered steps, and original problem/remedy cards. Targets are not invented: downstream preparation parses the author's step references. The generator does not assign train/test membership. The separate prepare.py creates participant data and private answer files from these raw inputs.

This public repository contains only eight source, license and documentation files. It does not contain the frozen article records, challenge answers, split membership, or learned checkpoints. Its purpose is to document the derived dataset and make its extraction procedure inspectable.

## Reproducing the source extraction

Use Python 3.12 and the standard library. Acquire an eligible Europe PMC core-search index and the corresponding fullTextXML files under their article licenses. Run: python generate.py --xml-dir /path/to/xml --index /path/to/index.json --out /path/to/raw . Keep the downloaded source XML snapshots to verify their recorded SHA-256 values. A new query or changed source article can produce a different collection; exact release reproduction uses the retained snapshots, not an assumed immutable live API.

## Intended use and limitations

This is a closed-data text-retrieval research resource for mapping an existing troubleshooting note to the procedure stages it references. It does not generate fixes or certify their safety or effectiveness. Authors may cite an observation point, an upstream cause, a recovery action, or a range of steps. The annotations record those explicit references, not every medically or scientifically plausible connection. Top-level numbered steps include their lettered substeps. Articles with duplicate step numbering, unsupported method scope, or fewer than two usable cards are excluded. Some interpretation depends on figures or specialist background not supplied in the extracted text. The collection covers one English-language journal and is not representative of all laboratories. Source annotations are publicly recoverable outside a supplied-data-only evaluation setting.

## Publication metadata

See SOURCES.md for authoritative access endpoints and DATA_LICENSE.txt for data terms. RELEASE.json pins the extraction code and documented release counts. CHANGELOG.md records the release history.

Published contact email addresses are redacted during extraction. R object-slot syntax is preserved. The records otherwise retain the extracted procedure and troubleshooting text; preparation separately removes answer-bearing references and URLs.

Release 1.0.1 preserves adjacent inline XML text, keeps block boundaries separate, and recognizes spaced lettered substeps and common conjunctions in numerical reference lists. Bibliographic citation markers remain separated from procedure numbers.
