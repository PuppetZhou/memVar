"""Project source cross-references without guessing absent identifiers."""
from __future__ import annotations

import json
import re
from urllib.parse import quote


def identifier(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value in {'', '-', '?'} else value


def identifier_type(database, value):
    value = identifier(value)
    if value is None:
        return None
    if database == 'Ensembl':
        for prefix, kind in [('ENSG', 'gene'), ('ENST', 'transcript'), ('ENSP', 'protein')]:
            if re.fullmatch(prefix + r'\d+(?:\.\d+)?', value):
                return kind
    if database == 'RefSeq':
        if re.fullmatch(r'(?:NP|XP|YP|WP|AP|ZP)_\d+(?:\.\d+)?', value):
            return 'protein'
        if re.fullmatch(r'(?:NM|XM|NR|XR)_\d+(?:\.\d+)?', value):
            return 'transcript'
        if re.fullmatch(r'(?:NC|NG|NT|NW|NZ)_\w+(?:\.\d+)?', value):
            return 'nucleotide'
    if database == 'HGNC' and re.fullmatch(r'HGNC:\d+', value):
        return 'gene'
    if database == 'UniProt' and re.fullmatch(r'[A-Z0-9]+(?:-\d+)?', value):
        return 'protein_entry'
    return None


def identifier_url(database, value):
    value = identifier(value)
    kind = identifier_type(database, value)
    if not kind:
        return None
    encoded = quote(value, safe='')
    if database == 'RefSeq':
        collection = 'protein' if kind == 'protein' else 'nuccore'
        return f'https://www.ncbi.nlm.nih.gov/{collection}/{encoded}'
    if database == 'Ensembl':
        return f'https://www.ensembl.org/id/{encoded}'
    if database == 'UniProt':
        return f'https://www.uniprot.org/uniprotkb/{encoded}/entry'
    return 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/' + value


def reference_fields(database, external_id, *, gene_id=None, protein_id=None, transcript_id=None, nucleotide_id=None):
    external_id = identifier(external_id)
    kind = identifier_type(database, external_id)
    ids = {'gene': identifier(gene_id), 'protein': identifier(protein_id),
           'transcript': identifier(transcript_id), 'nucleotide': identifier(nucleotide_id)}
    if kind in ids and ids[kind] is None:
        ids[kind] = external_id
    if database == 'RefSeq' and kind == 'transcript' and ids['nucleotide'] is None:
        ids['nucleotide'] = external_id
    fields = {'external_id': external_id, 'identifier_type': kind,
              'url': identifier_url(database, external_id)}
    for role, value in ids.items():
        fields[role + '_id_full'] = value
        fields[role + '_url'] = identifier_url(database, value)
    return fields


def uniprot_xref_fields(row):
    properties = {p['key']: p.get('value') for p in json.loads(row.get('properties_json') or '[]')}
    nucleotide = identifier(properties.get('NucleotideSequenceId'))
    transcript = nucleotide if identifier_type(row['database'], nucleotide) == 'transcript' else None
    return reference_fields(row['database'], row.get('external_id'),
                            gene_id=row.get('gene_id_full'), protein_id=row.get('protein_id_full'),
                            transcript_id=transcript, nucleotide_id=nucleotide)
