from rnalysis.utils import io, parsing
import requests

BIOTYPES = ('protein_coding', 'pseudogene', 'lincRNA', 'miRNA', 'ncRNA', 'piRNA', 'rRNA', 'snoRNA', 'snRNA', 'tRNA')
BIOTYPE_ATTRIBUTE_NAMES = ('biotype', 'gene_biotype', 'transcript_biotype', 'gene_type', 'transcript_type')
GO_ASPECTS = ('biological_process', 'molecular function', 'cellular component')
GO_EVIDENCE_TYPES = ('experimental', 'phylogenetic', 'computational', 'author', 'curator', 'electronic')
GO_QUALIFIERS = ('not', 'contributes_to', 'colocalizes_with')
DEFAULT_ORGANISMS = tuple(sorted(['Caenorhabditis elegans',
                                  'Mus musculus',
                                  'Drosophila melanogaster',
                                  'Homo sapiens',
                                  'Arabodopsis thaliana',
                                  'Danio rerio',
                                  'Escherichia coli',
                                  'Saccharomyces cerevisiae',
                                  'Schizosaccharomyces pombe']))
try:
    GENE_ID_TYPES = parsing.data_to_tuple(io.get_legal_gene_id_types()[0].keys())


except requests.exceptions.ConnectionError:
    GENE_ID_TYPES = tuple()
