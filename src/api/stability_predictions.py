"""Expose published, identity-linked ThermoMPNN records without reducing them."""
from collections import defaultdict
from .db import query
from .evidence_common import clean

FIELD = 'ThermoMPNN_ddg'
DEFINITION = dict(field=FIELD, source='ThermoMPNN', scope='protein_substitution', tool='ThermoMPNN', label='ThermoMPNN ΔΔG')
CONVENTION = ('Negative values predict stabilization; positive values predict destabilization. '
              'Original ThermoMPNN mutant-minus-wild-type output; no classification threshold is applied.')


def stability_records(ids, accession=''):
    if not ids:
        return []
    return query('''SELECT d.variant_id,d.annotation_id,d.gene_id,d.prediction_id,d.accession,
        d.sequence_id,d.position,d.ref_aa,d.alt_aa,d.ddg_pred,d.model,d.checkpoint
        FROM web_variant.variant_ddg_detail d WHERE d.variant_id=ANY(:ids)
        AND d.model='ThermoMPNN' AND d.checkpoint='thermoMPNN_default.pt' ''' +
        (' AND d.accession=:accession' if accession else '') +
        ' ORDER BY d.variant_id,d.annotation_id,d.gene_id,d.prediction_id',
        {'ids':ids,'accession':accession})


def attach_stability(rows, accession=''):
    selected = [row for row in rows if any(p['field'] == FIELD for p in row['predictions'])]
    if not selected:
        return
    by_identity = defaultdict(list)
    for record in stability_records(list({r['variant_id'] for r in selected}), accession):
        record.update(unit='kcal/mol', effect_convention=CONVENTION)
        record['ddg_pred'] = clean(record['ddg_pred'])
        by_identity[(record['variant_id'],record['annotation_id'],record['gene_id'])].append(record)
    for row in selected:
        records = by_identity[(row['variant_id'],row['annotation_id'],row['gene_id'])]
        for prediction in row['predictions']:
            if prediction['field'] != FIELD:
                continue
            prediction.update(records=records, unit='kcal/mol', effect_convention=CONVENTION,
                              value=records[0]['ddg_pred'] if len(records)==1 else None,
                              status='available' if records else 'no_linked_prediction')
