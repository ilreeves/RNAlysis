from collections import namedtuple

import copy
import joblib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from rnalysis import filtering
from rnalysis.utils import enrichment_runner, validation
from rnalysis.utils.enrichment_runner import *
from rnalysis.utils.io import *
from tests import __attr_ref__, __biotype_ref__

matplotlib.use('Agg')


def test_enrichment_runner_from_results():
    alpha = 0.05
    plot_horizontal = False
    set_name = 'set_name'
    results = pd.read_csv('tests/test_files/enrichment_hypergeometric_res.csv', index_col=0)
    runner = EnrichmentRunner.from_results_df(results, alpha, plot_horizontal, set_name)

    assert runner.results is results
    assert runner.alpha == 0.05
    assert runner.plot_horizontal == plot_horizontal
    assert runner.set_name == set_name


def test_get_pval_asterisk():
    assert EnrichmentRunner._get_pval_asterisk(0.6) == ('ns', 'normal')
    assert EnrichmentRunner._get_pval_asterisk(0.001, 0.00099) == ('ns', 'normal')
    assert EnrichmentRunner._get_pval_asterisk(0.04) == (u'\u2217', 'bold')
    assert EnrichmentRunner._get_pval_asterisk(0.0099) == (u'\u2217' * 2, 'bold')
    assert EnrichmentRunner._get_pval_asterisk(0) == (u'\u2217' * 4, 'bold')


def test_calc_randomization_pval():
    np.random.seed(42)
    hypergeom_pval = 0.2426153598589023
    avg_pval = 0
    for i in range(5):
        avg_pval += EnrichmentRunner._calc_randomization_pval(500, 1, np.random.random(10000) < 0.1, 100000, 0.11)
    avg_pval /= 5
    assert np.isclose(avg_pval, hypergeom_pval, atol=0.02)


def test_calc_hypergeometric_pvalues():
    [M, n, N, X] = [13588, 59, 611, 19]
    truth = 4.989682834519698 * 10 ** -12
    pval = EnrichmentRunner._calc_hypergeometric_pval(M, n, N, X)
    assert np.isclose(truth, pval, atol=0, rtol=0.00001)

    [M, n, N, X] = [20000, 430, 700, 6]
    truth = 0.006249179131697138
    pval = EnrichmentRunner._calc_hypergeometric_pval(M, n, N, X)
    assert np.isclose(truth, pval, atol=0, rtol=0.00001)

    [M, n, N, X] = [20000, 43, 300, 3]
    truth = 0.0265186938062861
    pval = EnrichmentRunner._calc_hypergeometric_pval(M, n, N, X)
    assert np.isclose(truth, pval, atol=0, rtol=0.00001)


def test_enrichment_get_attrs_int_index_attributes():
    genes = {'WBGene00000041', 'WBGene00002074', 'WBGene00000105', 'WBGene00000106', 'WBGene00199484',
             'WBGene00001436', 'WBGene00000137', 'WBGene00001996', 'WBGene00014208', 'WBGene00001133'}
    e = EnrichmentRunner(genes, [0, 2, 3], 0.05, __attr_ref__, True, False, '', False, True, 'test_set', False,
                         'hypergeometric', 'all', None, __biotype_ref__)
    e.fetch_annotations()
    e.fetch_attributes()
    e.get_background_set()
    e.update_gene_set()
    e.filter_annotations()
    attrs = e.attributes
    attrs_truth = ['attribute1', 'attribute3', 'attribute4']
    assert attrs == attrs_truth

    e = EnrichmentRunner(genes, 1, 0.05, __attr_ref__, True, False, '', False, True, 'test_set', False,
                         'hypergeometric', 'all', None, __biotype_ref__)
    e.fetch_annotations()
    e.fetch_attributes()
    e.get_background_set()
    e.update_gene_set()
    e.filter_annotations()
    attr = e.attributes
    attr_truth_single = ['attribute2']
    assert attr == attr_truth_single


def test_enrichment_get_attrs_all_attributes():
    genes = {'WBGene00000041', 'WBGene00002074', 'WBGene00000105', 'WBGene00000106', 'WBGene00199484',
             'WBGene00001436', 'WBGene00000137', 'WBGene00001996', 'WBGene00014208', 'WBGene00001133'}
    e = EnrichmentRunner(genes, 'all', 0.05, __attr_ref__, True, False, '', False, True, 'test_set', False,
                         'hypergeometric',
                         'all', None, __biotype_ref__)
    e.fetch_annotations()
    e.fetch_attributes()
    e.get_background_set()
    e.update_gene_set()
    e.filter_annotations()
    attrs = e.attributes
    attrs_truth = ['attribute1', 'attribute2', 'attribute3', 'attribute4']
    plt.close('all')
    assert attrs == attrs_truth


def test_enrichment_get_attrs_from_string(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda x: 'attribute1\nattribute4\n')
    genes = {'WBGene00000041', 'WBGene00002074', 'WBGene00000105', 'WBGene00000106', 'WBGene00199484',
             'WBGene00001436', 'WBGene00000137', 'WBGene00001996', 'WBGene00014208', 'WBGene00001133'}
    e = EnrichmentRunner(genes, None, 0.05, __attr_ref__, True, False, '', False, True, 'test_set', False,
                         'hypergeometric',
                         'all', None, __biotype_ref__)
    e.fetch_annotations()
    e.fetch_attributes()
    e.get_background_set()
    e.update_gene_set()
    e.filter_annotations()
    attrs = e.attributes
    attrs_truth = ['attribute1', 'attribute4']
    plt.close('all')
    assert attrs == attrs_truth


def test_enrichment_get_attrs_bad_path():
    e = EnrichmentRunner({'_'}, 'attribute1', 0.05, 'fakepath', True, False, '', False, True, 'test_set', False,
                         'hypergeometric', biotypes='all', biotype_ref_path=__biotype_ref__)
    with pytest.raises(FileNotFoundError):
        e.fetch_annotations()
        e.fetch_attributes()
        e.get_background_set()
        e.update_gene_set()
        e.filter_annotations()


def _enrichment_get_ref_tests_setup(truth, bg_genes):
    genes = {'WBGene00000041', 'WBGene00002074', 'WBGene00000019', 'WBGene00000105', 'WBGene00000106', 'WBGene00199484',
             'WBGene00001436', 'WBGene00000137', 'WBGene00001996', 'WBGene00014208'}
    biotype = bg_genes if isinstance(bg_genes, str) else 'all'
    background = None if isinstance(bg_genes, str) else bg_genes
    e = EnrichmentRunner(genes, 'all', 0.05, __attr_ref__, True, False, '', False, True, 'test_set', False,
                         'hypergeometric', biotype, background, __biotype_ref__)
    e.fetch_annotations()
    e.fetch_attributes()
    e.get_background_set()
    e.update_gene_set()
    e.filter_annotations()
    res = e.annotation_df

    truth.sort_index(inplace=True)
    res.sort_index(inplace=True)
    assert np.all(res.index == truth.index)
    assert np.all(res.columns == truth.columns)
    assert np.all(res.attribute1.isna() == truth.attribute1.isna())
    assert np.all(res.attribute2.isna() == truth.attribute2.isna())


def test_enrichment_get_ref_biotype():
    truth = io.load_csv('tests/test_files/attr_ref_table_for_tests_biotype.csv', 0)
    bg_genes = 'protein_coding'
    _enrichment_get_ref_tests_setup(truth, bg_genes)


def test_enrichment_get_ref_custom_background():
    truth = io.load_csv('tests/test_files/attr_ref_table_for_tests_specified_bg.csv', 0)
    bg_genes = {'WBGene00003902', 'WBGene00000106', 'WBGene00001436', 'WBGene00000864', 'WBGene00011910',
                'WBGene00000859', 'WBGene00268189', 'WBGene00000865', 'WBGene00003864', 'WBGene00048863',
                'WBGene00000369', 'WBGene00000863', 'WBGene00002074', 'WBGene00000041', 'WBGene00199486',
                'WBGene00000105', 'WBGene00001131'}
    _enrichment_get_ref_tests_setup(truth, bg_genes)


def test_enrichment_get_ref_custom_background_from_featureset_object():
    truth = io.load_csv('tests/test_files/attr_ref_table_for_tests_specified_bg.csv', 0)
    bg_genes = {'WBGene00003902', 'WBGene00000106', 'WBGene00001436', 'WBGene00000864', 'WBGene00011910',
                'WBGene00000859', 'WBGene00268189', 'WBGene00000865', 'WBGene00003864', 'WBGene00048863',
                'WBGene00000369', 'WBGene00000863', 'WBGene00002074', 'WBGene00000041', 'WBGene00199486',
                'WBGene00000105', 'WBGene00001131'}
    _enrichment_get_ref_tests_setup(truth, bg_genes)


def test_enrichment_get_ref_custom_background_from_filter_object():
    truth = io.load_csv('tests/test_files/attr_ref_table_for_tests_specified_bg.csv', 0)
    bg_genes = filtering.CountFilter(r'tests/test_files/test_bg_genes_from_filter_object.csv')
    _enrichment_get_ref_tests_setup(truth, bg_genes)


def test_results_to_csv():
    try:
        en = EnrichmentRunner({''}, 'all', 0.05, __attr_ref__, True, True, 'tests/test_files/tmp_enrichment_csv.csv',
                              False, True, 'test_set', False, 'hypergeometric', 'all', None, __biotype_ref__)
        df = pd.read_csv('tests/test_files/enrichment_hypergeometric_res.csv', index_col=0)
        en.results = df
        en.results_to_csv()
        df_loaded = pd.read_csv('tests/test_files/tmp_enrichment_csv.csv', index_col=0)
        assert df.equals(df_loaded)
    except Exception as e:
        raise e
    finally:
        try:
            os.remove('tests/test_files/tmp_enrichment_csv.csv')
        except:
            pass


def _comp_go_res_df(res, truth):
    res.drop('name', axis=1, inplace=True)
    res.rename_axis('go_id')
    assert res.loc[:, ['n', 'obs']].equals(truth.loc[:, ['n', 'obs']])
    assert np.allclose(res.loc[:, ['exp', 'log2fc']], res.loc[:, ['exp', 'log2fc']])
    assert np.allclose(res['pval'], truth['pval'], atol=0)


def test_classic_pvals(monkeypatch):
    goa_df = pd.read_csv('tests/test_files/goa_table.csv', index_col=0).astype('bool')
    gene_set = {'gene1', 'gene2', 'gene5', 'gene12', 'gene13', 'gene17', 'gene19', 'gene25', 'gene27', 'gene28'}
    truth = pd.read_csv('tests/test_files/go_pvalues_classic_truth.csv', index_col=0).sort_index()
    dummy_go_node = namedtuple('DummyGONode', field_names='name')

    class DummyDAGTree:
        def __init__(self):
            self.dummy_node = dummy_go_node('content of name field')

        def __getitem__(self, item):
            return self.dummy_node

    monkeypatch.setattr(io, 'fetch_go_basic', lambda: DummyDAGTree())

    e = GOEnrichmentRunner(gene_set, 'elegans', 'WBGene', 0.05, 'classic', 'any', 'any', None, 'any', None, 'any', None,
                           False, False, '', False, False, False, '', False, 'hypergeometric', 'all')
    e.annotation_df = goa_df
    e.mod_annotation_dfs = goa_df,
    e.attributes = list(goa_df.columns)

    res = pd.DataFrame.from_dict(e._go_classic_on_batch(tuple(goa_df.columns), 0), orient='index',
                                 columns=['name', 'n', 'obs', 'exp', 'log2fc', 'pval']).sort_index()
    _comp_go_res_df(res, truth)


def test_elim_pvals(monkeypatch):
    goa_df = pd.read_csv('tests/test_files/goa_table.csv', index_col=0).astype('bool')
    threshold = 0.2  # make sure there are both significant and non-significant examples with our small bg size (30)
    gene_set = {'gene1', 'gene2', 'gene5', 'gene12', 'gene13', 'gene17', 'gene19', 'gene25', 'gene27', 'gene28'}
    truth = pd.read_csv('tests/test_files/go_pvalues_elim_truth.csv', index_col=0).sort_index()
    with open('tests/test_files/obo_for_go_tests.obo', 'r') as f:
        dag_tree = ontology.DAGTree(f, ['is_a'])
    monkeypatch.setattr(io, 'fetch_go_basic', lambda: dag_tree)

    e = GOEnrichmentRunner(gene_set, 'elegans', 'WBGene', threshold, 'classic', 'any', 'any', None, 'any', None, 'any',
                           None, False, False, '', False, False, False, '', False, 'hypergeometric', 'all')
    e.annotation_df = goa_df
    e.mod_annotation_dfs = goa_df.copy(deep=True),
    e.attributes = list(goa_df.columns)
    e.attributes_set = set(e.attributes)

    res = pd.DataFrame.from_dict(e._go_elim_on_aspect('all'), orient='index',
                                 columns=['name', 'n', 'obs', 'exp', 'log2fc', 'pval']).sort_index()

    _comp_go_res_df(res, truth)


def test_weight_pvals(monkeypatch):
    goa_df = pd.read_csv('tests/test_files/goa_table.csv', index_col=0).astype('bool')
    gene_set = {'gene1', 'gene2', 'gene5', 'gene12', 'gene13', 'gene17', 'gene19', 'gene25', 'gene27', 'gene28'}
    truth = pd.read_csv('tests/test_files/go_pvalues_weight_truth.csv', index_col=0).sort_index()
    with open('tests/test_files/obo_for_go_tests.obo', 'r') as f:
        dag_tree = ontology.DAGTree(f, ['is_a'])

    monkeypatch.setattr(io, 'fetch_go_basic', lambda: dag_tree)

    e = GOEnrichmentRunner(gene_set, 'elegans', 'WBGene', 0.05, 'classic', 'any', 'any', None, 'any', None, 'any', None,
                           False, False, '', False, False, False, '', False, 'hypergeometric', 'all')
    e.annotation_df = goa_df
    e.mod_annotation_dfs = goa_df.copy(deep=True),
    e.attributes = list(goa_df.columns)
    e.attributes_set = set(e.attributes)

    res = pd.DataFrame.from_dict(e._go_weight_on_aspect('all'), orient='index',
                                 columns=['name', 'n', 'obs', 'exp', 'log2fc', 'pval']).sort_index()
    _comp_go_res_df(res, truth)


def test_allm_pvals(monkeypatch):
    goa_df = pd.read_csv('tests/test_files/goa_table.csv', index_col=0).astype('bool')
    threshold = 0.2  # make sure there are both significant and non-significant examples with our small bg size (30)
    gene_set = {'gene1', 'gene2', 'gene5', 'gene12', 'gene13', 'gene17', 'gene19', 'gene25', 'gene27', 'gene28'}
    truth = pd.read_csv('tests/test_files/go_pvalues_allm_truth.csv', index_col=0).sort_index()
    with open('tests/test_files/obo_for_go_tests.obo', 'r') as f:
        dag_tree = ontology.DAGTree(f, ['is_a'])
    monkeypatch.setattr(io, 'fetch_go_basic', lambda: dag_tree)

    e = GOEnrichmentRunner(gene_set, 'elegans', 'WBGene', threshold, 'classic', 'any', 'any', None, 'any', None, 'any',
                           None, False, False, '', False, False, False, '', False, 'hypergeometric', 'all')
    e.annotation_df = goa_df
    e.mod_annotation_dfs = goa_df.copy(deep=True),
    e.attributes = list(goa_df.columns)
    e.attributes_set = set(e.attributes)

    res = pd.DataFrame.from_dict(e._go_allm_pvalues_serial(), orient='index',
                                 columns=['name', 'n', 'obs', 'exp', 'log2fc', 'pval']).sort_index()

    _comp_go_res_df(res, truth)


def test_enrichment_runner_update_ranked_genes():
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    truth = np.array([['111', '000', '222', '777', '333', '888']], dtype='str')
    runner.ranked_genes = np.array(['111', '000', '222', '777', '333', '000', '111', '888', '000'], dtype='str')
    runner.gene_set = {'111', '000', '222', '777', '333', '888'}
    runner._update_ranked_genes()
    assert np.all(truth == runner.ranked_genes)


@pytest.mark.parametrize("test_input,expected", [
    ('fisher', EnrichmentRunner._fisher_enrichment),
    ('HYPERGEOMETRIC', EnrichmentRunner._hypergeometric_enrichment),
    ('Randomization', EnrichmentRunner._randomization_enrichment),
    ('XLmHG', EnrichmentRunner._xlmhg_enrichment)])
def test_enrichment_runner_get_enrichment_func(test_input, expected):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    if test_input.lower() == 'xlmhg' and not does_python_version_support_single_set():
        assert runner._get_enrichment_func(test_input) == False
        return
    assert runner._get_enrichment_func(test_input).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.upper()).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.lower()).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.capitalize()).__name__ == expected.__name__


@pytest.mark.parametrize("test_input,err", [
    ('fifty', ValueError),
    (50, AssertionError),
    (True, AssertionError),
    (max, AssertionError)])
def test_enrichment_runner_get_enrichment_func_invalid_value(test_input, err):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    with pytest.raises(err):
        runner._get_enrichment_func(test_input)


@pytest.mark.parametrize('attr,results',
                         [('attribute1', (38, 6, 11, 3)),
                          ('attribute3', (38, 6, 14, 4)),
                          ('attribute4', (38, 6, 13, 4))])
def test_enrichment_runner_get_hypergeometric_parameters(attr, results):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    runner.gene_set = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915',
                       'WBGene00268195'}
    assert runner._get_hypergeometric_parameters(attr) == results


@pytest.mark.parametrize('params,truth',
                         [((38, 11, 6, 5), ['attribute', 11, 5, (6 / 38) * 11, np.log2(5 / ((6 / 38) * 11)), 0.05]),
                          ((40, 10, 15, 0), ['attribute', 10, 0, (15 / 40) * 10, -np.inf, 0.05])])
def test_enrichment_runner_hypergeometric_enrichment(monkeypatch, params, truth):
    monkeypatch.setattr(EnrichmentRunner, '_get_hypergeometric_parameters', lambda self, attr: params)

    def alt_calc_pval(self, bg_size, de_size, go_size, go_de_size):
        assert (bg_size, de_size, go_size, go_de_size) == params
        return 0.05

    monkeypatch.setattr(EnrichmentRunner, '_calc_hypergeometric_pval', alt_calc_pval)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    assert runner._hypergeometric_enrichment('attribute') == truth


def _randomization_enrichment_setup_runner(monkeypatch, truth, runner_class, notna: bool = False):
    reps_truth = 100
    df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    bg_array_truth = pd.read_csv('tests/test_files/annotation_df_bg_array_truth.csv', index_col=0)[truth[0]].values

    if notna:
        df = df.notna()

    gene_set_truth = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106',
                      'WBGene00001133', 'WBGene00003915', 'WBGene00268195'}

    def alt_calc_pval(self, n: int, log2fc: float, bg_array: np.ndarray, reps: int, obs_frac: float):
        assert reps == reps_truth
        assert n == len(gene_set_truth)
        assert log2fc == truth[4]
        assert isinstance(bg_array, np.ndarray)
        assert obs_frac == truth[2] / truth[1]
        assert np.all(bg_array == bg_array_truth)
        return 0.05

    monkeypatch.setattr(EnrichmentRunner, '_calc_randomization_pval', alt_calc_pval)
    runner = runner_class.__new__(runner_class)
    runner.gene_set = gene_set_truth
    runner.annotation_df = df
    runner.pvalue_kwargs = {'reps': reps_truth}
    return runner


@pytest.mark.parametrize('truth', [(['attribute1', 6, 3, (11 / 38) * 6, np.log2(3 / ((11 / 38) * 6)), 0.05]),
                                   (['attribute4', 6, 4, (13 / 38) * 6, np.log2(4 / ((13 / 38) * 6)), 0.05])])
def test_enrichment_runner_randomization_enrichment(monkeypatch, truth):
    runner = _randomization_enrichment_setup_runner(monkeypatch, truth, EnrichmentRunner)
    assert runner._randomization_enrichment(truth[0], runner.pvalue_kwargs['reps']) == truth


@pytest.mark.parametrize('params,truth',
                         [((38, 11, 6, 5), ['attribute', 11, 5, (6 / 38) * 11, np.log2(5 / ((6 / 38) * 11)), 0.05]),
                          ((40, 10, 15, 0), ['attribute', 10, 0, (15 / 40) * 10, -np.inf, 0.05])])
def test_enrichment_runner_fisher_enrichment(monkeypatch, params, truth):
    monkeypatch.setattr(EnrichmentRunner, '_get_hypergeometric_parameters', lambda self, attr: params)

    def alt_calc_pval(self, bg_size, de_size, go_size, go_de_size):
        assert (bg_size, de_size, go_size, go_de_size) == params
        return 0.05

    monkeypatch.setattr(EnrichmentRunner, '_calc_fisher_pval', alt_calc_pval)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    assert runner._fisher_enrichment('attribute') == truth


def test_enrichment_runner_update_gene_set():
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.single_set = False
    runner.background_set = set(pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0).index)
    runner.gene_set = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915',
                       'WBGene99991111'}
    updated_gene_set_truth = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915'}
    runner.update_gene_set()
    assert runner.gene_set == updated_gene_set_truth


def test_enrichment_runner_update_gene_set_single_list(monkeypatch):
    monkeypatch.setattr(EnrichmentRunner, '_update_ranked_genes', lambda x: None)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.single_set = True
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    runner.gene_set = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915',
                       'WBGene99991111'}
    updated_gene_set_truth = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915'}
    runner.update_gene_set()
    assert runner.gene_set == updated_gene_set_truth


@pytest.mark.parametrize('save_csv,', [True, False])
@pytest.mark.parametrize('return_nonsignificant,', [True, False])
@pytest.mark.parametrize('fname', ['fname', None])
@pytest.mark.parametrize(
    'single_list,genes,biotypes,pval_func,background_set,biotype_ref_path, random_seed,kwargs',
    [(True, np.array(['WBGene1', 'WBGene2'], dtype=str), None, 'xlmhg', None, None, None, {}),
     (False, {'WBGene00000001', 'WBGene00000002'}, 'protein_coding', 'randomization',
      {'WBGene00000001', 'WBGene00000002', 'EBGene00000003'},
      'path/to/biotype/ref', 42, {'reps': 10000})])
def test_enrichment_runner_api(return_nonsignificant, save_csv, fname, single_list, genes, biotypes, pval_func,
                               background_set, biotype_ref_path, random_seed, kwargs, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda x: 'fname')

    runner = EnrichmentRunner(genes, ['attr1', 'attr2'], 0.05, 'path/to/attr/ref', return_nonsignificant, save_csv,
                              fname, False, False, 'set_name', False, pval_func, biotypes,
                              background_set, biotype_ref_path, single_list, random_seed, **kwargs)
    if save_csv:
        assert runner.fname == 'fname'
    else:
        with pytest.raises(AttributeError):
            _ = runner.fname


def test_enrichment_runner_format_results(monkeypatch):
    monkeypatch.setattr(EnrichmentRunner, '_correct_multiple_comparisons', lambda self: None)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    results_list = [['name1', 50, 10, 5.5, 2.3, 0.05], ['name2', 17, 0, 3, 0, 1], ['name3', 1, np.nan, -2, -0.7, 0.04]]
    truth = pd.read_csv('tests/test_files/enrichment_runner_format_results_truth.csv', index_col=0)
    runner.en_score_col = 'colName'
    runner.single_set = False
    runner.return_nonsignificant = True

    runner.format_results(results_list)
    assert truth.equals(runner.results)


def test_enrichment_runner_format_results_single_list(monkeypatch):
    monkeypatch.setattr(EnrichmentRunner, '_correct_multiple_comparisons', lambda self: None)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    results_list = [['name1', 50, 2.3, 0.05], ['name2', 17, 0, 1], ['name3', 1, -0.7, np.nan]]
    truth = pd.read_csv('tests/test_files/enrichment_runner_single_list_format_results_truth.csv', index_col=0)
    runner.en_score_col = 'colName'
    runner.single_set = True
    runner.return_nonsignificant = True

    runner.format_results(results_list)
    assert truth.equals(runner.results)


@pytest.mark.parametrize('mode', ['EnrichmentRunner', 'GOEnrichmentRunner'])
@pytest.mark.parametrize('attr,index_vector, pvalue_kwargs,p_values,e_scores,params_truth',
                         [('attr1', [3, 5, 2], {}, (0.05, 0.9), (2, 1.5),
                           {'L': 1, 'X': 2, 'N': 10, 'table': np.empty((3 + 1, 10 - 3 + 1), dtype=np.longdouble)}),
                          ('attr 2', [1, 2, 3, 4], {'L': 2, 'X': 7}, (0, 0), (0, 0),
                           {'L': 2, 'X': 7, 'N': 10, 'table': np.empty((4 + 1, 10 - 4 + 1), dtype=np.longdouble)}),
                          ('attr,3', [2, 9], {'other_arg': 13}, (0.8, 0.1), (1, 1.2),
                           {'L': 1, 'X': 1, 'N': 10, 'table': np.empty((2 + 1, 10 - 2 + 1), dtype=np.longdouble)})])
def test_enrichment_runner_xlmhg_enrichment(monkeypatch, attr, index_vector, pvalue_kwargs, p_values, e_scores,
                                            params_truth, mode):
    n_calls_xlmhg_test = [0]
    params_truth['indices'] = index_vector

    class ResultObject:
        def __init__(self, pval, escore):
            self.pval = pval
            self.escore = escore

    monkeypatch.setattr(EnrichmentRunner, '_generate_xlmhg_index_vectors',
                        lambda self, attribute: (index_vector, index_vector))
    monkeypatch.setattr(GOEnrichmentRunner, '_generate_xlmhg_index_vectors',
                        lambda self, attribute, mod_df_ind: (index_vector, index_vector))

    def _xlmhg_test_validate_parameters(**kwargs):
        for key in ['X', 'L', 'N', 'indices']:
            assert params_truth[key] == kwargs[key]
        assert params_truth['table'].shape == kwargs['table'].shape
        assert params_truth['table'].dtype == kwargs['table'].dtype

        pval = p_values[n_calls_xlmhg_test[0]]
        escore = e_scores[n_calls_xlmhg_test[0]]
        n_calls_xlmhg_test[0] += 1
        return ResultObject(pval, escore)

    monkeypatch.setattr(xlmhg, 'get_xlmhg_test_result', _xlmhg_test_validate_parameters)

    if mode == 'GOEnrichmentRunner':
        runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)

        class FakeGOTerm:
            def __init__(self, go_id, name):
                self.go_id = go_id
                self.name = name

        runner.dag_tree = {attr: FakeGOTerm(attr, attr + '_name')}
    else:
        runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.ranked_genes = np.array(
        ['gene0', 'gene1', 'gene2', 'gene3', 'gene4', 'gene5', 'gene6', 'gene7', 'gene8', 'gene9'], dtype='str')
    runner.pvalue_kwargs = pvalue_kwargs

    log2fc = np.log2(e_scores[0] if p_values[0] <= p_values[1] else (1 / e_scores[1]))
    output_truth = [attr + '_name' if mode == 'GOEnrichmentRunner' else attr, len(runner.ranked_genes), log2fc,
                    min(p_values)]

    result = runner._xlmhg_enrichment(attr)
    assert result == output_truth


@pytest.mark.parametrize('attribute,truth, truth_rev',
                         [('attribute1', np.array([0, 1], dtype='uint16'), np.array([2, 3], dtype='uint16')),
                          ('attribute4', np.array([0, 2], dtype='uint16'), np.array([1, 3], dtype='uint16'))])
def test_enrichment_runner_generate_xlmhg_index_vectors(attribute, truth, truth_rev):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.ranked_genes = np.array(['WBGene00000106', 'WBGene00000019', 'WBGene00000865', 'WBGene00001131'],
                                   dtype='str')
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    vec, rev_vec = runner._generate_xlmhg_index_vectors(attribute)
    assert np.all(vec == truth)
    assert np.all(rev_vec == truth_rev)


def test_enrichment_runner_fetch_annotations(monkeypatch):
    monkeypatch.setattr(validation, 'validate_attr_table', lambda x: None)
    truth = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.attr_ref_path = 'tests/test_files/attr_ref_table_for_tests.csv'
    runner.fetch_annotations()
    assert truth.equals(runner.annotation_df)


@pytest.mark.parametrize('attributes,truth,annotation_df_cols',
                         [(['all', ['col1', 'col2', 'col3'], ['col1', 'col2', 'col3']]),
                          (None, ['first-attr', 'second attr', 'third. attr '],
                           ['first-attr', 'second attr', 'third. attr ', 'fourth', 'fifth']),
                          (['col2', 'col3'], ['col2', 'col3'], ['col1', 'col2', 'col3']),
                          ([0, 2], ['col1', 'col3'], ['col1', 'col2', 'col3']),
                          ({0, 2}, ['col1', 'col3'], ['col1', 'col2', 'col3']),
                          ({'col2', 'col3'}, ['col2', 'col3'], ['col1', 'col2', 'col3'])])
def test_enrichment_runner_fetch_attributes(attributes, truth, annotation_df_cols, monkeypatch):
    monkeypatch.setattr(EnrichmentRunner, '_validate_attributes', lambda self, attrs, all_attrs: None)
    monkeypatch.setattr('builtins.input', lambda x: 'first-attr\nsecond attr\nthird. attr \n')
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.attributes = attributes
    runner.annotation_df = pd.DataFrame([], columns=annotation_df_cols)
    runner.fetch_attributes()
    assert sorted(runner.attributes) == sorted(truth)


@pytest.mark.parametrize('attibute_list,all_attrs,is_legal',
                         [(['a', 'b', 'c'], {'c', 'a', 'b', 'd', 'A', 'f'}, True),
                          (['a', 'c', 1], ['c', 'b', 'a'], True),
                          ([3, 2, 1], {'a', 'b', 'c'}, False),
                          (['a', -1, 2], ['a', 'b', 'c'], False),
                          (['A', 'b', 'c'], {'c', 'b', 'a'}, False),
                          (['a', 'b', True], {'a', 'b', True}, False),
                          (['a', 'b', 'c'], 'abc', False),
                          ('abc', {'a', 'b', 'c', 'abc'}, False)])
def test_enrichment_runner_validate_attributes(attibute_list, all_attrs, is_legal):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    if is_legal:
        runner._validate_attributes(attibute_list, all_attrs)
    else:
        with pytest.raises(AssertionError):
            runner._validate_attributes(attibute_list, all_attrs)


def test_enrichment_runner_filter_annotations():
    truth = pd.read_csv('tests/test_files/enrichment_runner_filter_annotations_truth.csv', index_col=0)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    runner.background_set = {'WBGene00000019', 'WBGene00000106', 'WBGene00000137', 'WBGene00000369', 'WBGene00000860',
                             'WBGene00048865', 'WBGene00268195'}
    runner.attributes = ['attribute1', 'attribute3', 'attribute4']
    runner.single_set = False
    runner.filter_annotations()
    assert truth.equals(runner.annotation_df)


def test_enrichment_runner_filter_annotations_single_list():
    truth = pd.read_csv('tests/test_files/enrichment_runner_filter_annotations_single_list_truth.csv', index_col=0)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    runner.attributes = ['attribute1', 'attribute3', 'attribute4']
    runner.single_set = True
    runner.filter_annotations()
    assert truth.equals(runner.annotation_df)


def test_enrichment_runner_calculate_enrichment(monkeypatch):
    random_seed_status = [False]

    def set_seed(self):
        random_seed_status[0] = True

    monkeypatch.setattr(EnrichmentRunner, 'set_random_seed', set_seed)
    monkeypatch.setattr(EnrichmentRunner, '_calculate_enrichment_parallel', lambda self: 'parallel')
    monkeypatch.setattr(EnrichmentRunner, '_calculate_enrichment_serial', lambda self: 'serial')

    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.parallel = True
    assert runner.calculate_enrichment() == 'parallel'
    assert random_seed_status[0]

    random_seed_status[0] = False
    runner.parallel = False
    assert runner.calculate_enrichment() == 'serial'
    assert random_seed_status[0]


@pytest.mark.parametrize('seed,is_legal',
                         [(5, True),
                          (42, True),
                          (-1, False),
                          (0.1, False),
                          ('seed', False)])
def test_enrichment_runner_set_random_seed(seed, is_legal):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.random_seed = seed
    if is_legal:
        runner.set_random_seed()
        val = np.random.random()
        np.random.seed(seed)
        truth = np.random.random()
        assert val == truth
    else:
        with pytest.raises(AssertionError):
            runner.set_random_seed()


def _test_enrichment_runner_calculate_enrichment_get_constants():
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.attributes = ['attribute1', 'attribute2', 'attribute4']
    runner.pvalue_kwargs = {'arg1': 'val1', 'arg2': 'val2'}

    def enrichment_func(attr, **kwargs):
        return [attr, kwargs]

    runner.enrichment_func = enrichment_func
    truth = [[attr, runner.pvalue_kwargs] for attr in runner.attributes]
    return runner, truth


def test_enrichment_runner_calculate_enrichment_parallel():
    runner, truth = _test_enrichment_runner_calculate_enrichment_get_constants()
    assert truth == runner._calculate_enrichment_parallel()


def test_enrichment_runner_calculate_enrichment_serial():
    runner, truth = _test_enrichment_runner_calculate_enrichment_get_constants()
    assert truth == runner._calculate_enrichment_serial()


def test_enrichment_runner_correct_multiple_comparisons():
    runner = EnrichmentRunner.__new__(EnrichmentRunner)

    runner.results = pd.DataFrame([[0, 0, 0, 0, 0, 0.005],
                                   [0, 0, 0, 0, 0, 0.017],
                                   [0, 0, 0, 0, 0, np.nan],
                                   [0, 0, 0, 0, -3, np.nan],
                                   [0, 0, 0, 0, 0, 0.92]],
                                  columns=['name', 'samples', 'obs', 'exp', 'colName', 'pval']).set_index('name')
    runner.alpha = 0.02
    truth = pd.DataFrame([[0, 0, 0, 0, 0, 0.005, 0.015, True],
                          [0, 0, 0, 0, 0, 0.017, 0.0255, False],
                          [0, 0, 0, 0, 0, np.nan, np.nan, False],
                          [0, 0, 0, 0, -3, np.nan, np.nan, False],
                          [0, 0, 0, 0, 0, 0.92, 0.92, False]],
                         columns=['name', 'samples', 'obs', 'exp', 'colName', 'pval', 'padj', 'significant']).set_index(
        'name')

    runner._correct_multiple_comparisons()

    assert np.all(np.isclose(truth['padj'].values, runner.results['padj'].values, atol=0, equal_nan=True))
    for val, val_truth in zip(runner.results['significant'], truth['significant']):
        assert val == val_truth or (np.isnan(val) and np.isnan(val_truth))
    assert truth.loc['name':'pval'].equals(runner.results.loc['name':'pval'])


@pytest.mark.parametrize('single_list', [True, False])
def test_enrichment_runner_plot_results(monkeypatch, single_list):
    def validate_params(self, title, ylabel=''):
        assert isinstance(title, str)
        assert self.set_name in title
        assert isinstance(ylabel, str)
        return plt.Figure()

    monkeypatch.setattr(EnrichmentRunner, 'enrichment_bar_plot', validate_params)
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.single_set = single_list
    runner.set_name = 'name of the set'
    res = runner.plot_results()
    assert isinstance(res, plt.Figure)


@pytest.mark.parametrize('n_bars', ['all', 2])
@pytest.mark.parametrize('plot_horizontal', [True, False])
def test_enrichment_runner_enrichment_bar_plot(plot_horizontal, n_bars):
    runner = EnrichmentRunner.__new__(EnrichmentRunner)
    runner.results = pd.read_csv('tests/test_files/enrichment_hypergeometric_res.csv')
    runner.en_score_col = 'log2_fold_enrichment'
    runner.alpha = 0.05
    runner.plot_horizontal = plot_horizontal
    runner.enrichment_bar_plot(n_bars=n_bars)


def test_noncategorical_enrichment_runner_api():
    runner = NonCategoricalEnrichmentRunner({'gene1', 'gene2', 'gene4'}, ['attr1', 'attr2'], 0.05, 'protein_coding',
                                            {'gene1', 'gene2', 'gene3', 'gene4'}, 'path/to/attr/ref',
                                            'path/to/biotype/ref', False, 'fname', False, False, 'overlap', 5,
                                            'set_name', False, True)


@pytest.mark.parametrize("test_input,expected", [
    ('T_Test', NonCategoricalEnrichmentRunner._one_sample_t_test_enrichment),
    ('sign_test', NonCategoricalEnrichmentRunner._sign_test_enrichment),
    ('SIGN_TEST', NonCategoricalEnrichmentRunner._sign_test_enrichment), ])
def test_noncategorical_enrichment_runner_get_enrichment_func(test_input, expected):
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    assert runner._get_enrichment_func(test_input).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.upper()).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.lower()).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.capitalize()).__name__ == expected.__name__


@pytest.mark.parametrize("test_input,expected_exception",
                         [('ttest', ValueError),
                          (55, AssertionError),
                          (True, AssertionError),
                          (None, AssertionError),
                          ('other', ValueError)])
def test_noncategorical_enrichment_runner_get_enrichment_func_invalid_value(test_input, expected_exception):
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    with pytest.raises(expected_exception):
        runner._get_enrichment_func(test_input)


@pytest.mark.parametrize("attr,gene_set,truth",
                         [('attr5', {f'WBGene0000000{i + 1}' for i in range(4)},
                           ['attr5', 4, 16.85912542, 6.986579003, 0.05]),
                          ('attr4', {f'WBGene0000000{i + 1}' for i in range(4)},
                           ['attr4', 4, 15.5, 14, 0.05]),
                          ('attr1', {'WBGene00000001', 'WBGene00000029', 'WBGene00000030'},
                           ['attr1', 3, np.nan, 3, np.nan])])
def test_noncategorical_enrichment_runner_sign_test_enrichment(monkeypatch, attr, gene_set, truth):
    df = pd.read_csv('tests/test_files/attr_ref_table_for_non_categorical.csv', index_col=0)

    def validate_params(values, exp):
        assert np.isclose(exp, truth[3])
        assert np.all(values == df.loc[gene_set, attr].values)
        return None, 0.05

    monkeypatch.setattr(enrichment_runner, 'sign_test', validate_params)
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    runner.annotation_df = df
    runner.gene_set = gene_set

    res = runner._sign_test_enrichment(attr)
    for res_val, truth_val in zip(res, truth):
        if isinstance(truth_val, float):
            assert np.isclose(truth_val, res_val, equal_nan=True)
        else:
            assert truth_val == res_val


@pytest.mark.parametrize("attr,gene_set,truth",
                         [('attr5', {f'WBGene0000000{i + 1}' for i in range(4)},
                           ['attr5', 4, 14.93335321, 7.709139128, 0.05]),
                          ('attr4', {f'WBGene0000000{i + 1}' for i in range(4)},
                           ['attr4', 4, 14.25, 13.60714286, 0.05]),
                          ('attr1', {'WBGene00000001', 'WBGene00000029', 'WBGene00000030'},
                           ['attr1', 3, np.nan, 4.75, np.nan])])
def test_noncategorical_enrichment_runner_one_sample_t_test_enrichment(monkeypatch, attr, gene_set, truth):
    df = pd.read_csv('tests/test_files/attr_ref_table_for_non_categorical.csv', index_col=0)

    def validate_params(values, popmean):
        assert np.isclose(popmean, truth[3])
        assert np.all(values == df.loc[gene_set, attr].values)
        return None, 0.05

    monkeypatch.setattr(enrichment_runner, 'ttest_1samp', validate_params)
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    runner.annotation_df = df
    runner.gene_set = gene_set

    res = runner._one_sample_t_test_enrichment(attr)
    for res_val, truth_val in zip(res, truth):
        if isinstance(truth_val, float):
            assert np.isclose(truth_val, res_val, equal_nan=True)
        else:
            assert truth_val == res_val


def test_noncategorical_enrichment_runner_format_results(monkeypatch):
    monkeypatch.setattr(NonCategoricalEnrichmentRunner, '_correct_multiple_comparisons', lambda self: None)
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    results_list = [['name1', 50, 10, 5.5, 0.05], ['name2', 17, 0, 3, 1], ['name3', 1, np.nan, -2, np.nan]]
    truth = pd.read_csv('tests/test_files/non_categorical_enrichment_runner_format_results_truth.csv', index_col=0)

    runner.format_results(results_list)
    assert truth.equals(runner.results)


def test_noncategorical_enrichment_runner_plot_results(monkeypatch):
    attrs_without_nan_truth = ['attr1', 'attr2', 'attr4']
    attrs_without_nan = []

    def proccess_attr(self, attr):
        attrs_without_nan.append(attr)
        return plt.Figure()

    monkeypatch.setattr(NonCategoricalEnrichmentRunner, 'enrichment_histogram', proccess_attr)
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    runner.attributes = ['attr1', 'attr2', 'attr3', 'attr4']
    runner.results = {'padj': [0.05, 0.3, np.nan, 1]}

    res = runner.plot_results()
    assert attrs_without_nan == attrs_without_nan_truth
    assert len(res) == len(attrs_without_nan)
    for plot in res:
        assert isinstance(plot, plt.Figure)


@pytest.mark.parametrize('plot_style', ['interleaved', 'overlap'])
@pytest.mark.parametrize('plot_log_scale', [True, False])
@pytest.mark.parametrize('parametric_test', [True, False])
@pytest.mark.parametrize('n_bins', [2, 8])
def test_noncategorical_enrichment_runner_enrichment_histogram(plot_style, plot_log_scale, parametric_test, n_bins):
    runner = NonCategoricalEnrichmentRunner.__new__(NonCategoricalEnrichmentRunner)
    runner.plot_style = plot_style
    runner.plot_log_scale = plot_log_scale
    runner.parametric_test = parametric_test
    runner.n_bins = n_bins
    runner.alpha = 0.15
    runner.set_name = 'set_name'
    runner.results = pd.read_csv('tests/test_files/enrich_non_categorical_nan_parametric_truth.csv', index_col=0)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_non_categorical.csv', index_col=0)
    runner.gene_set = {f'WBGene0000000{i + 1}' for i in range(5)}

    res = runner.enrichment_histogram('attr5')
    assert isinstance(res, plt.Figure)


@pytest.mark.parametrize('single_list,genes,biotypes,pval_func,background_set,biotype_ref_path, random_seed,kwargs',
                         [(True, np.array(['WBGene1', 'WBGene2'], dtype=str), None, 'xlmhg', None, None, None, {}),
                          (False, {'WBGene00000001', 'WBGene00000002'}, 'protein_coding', 'randomization',
                           {'WBGene00000001', 'WBGene00000002', 'EBGene00000003'},
                           'path/to/biotype/ref', 42, {'reps': 10000})])
def test_go_enrichment_runner_api(monkeypatch, single_list, genes, biotypes, pval_func, background_set,
                                  biotype_ref_path, random_seed, kwargs):
    monkeypatch.setattr(io, 'fetch_go_basic', lambda: 'dag_tree')
    runner = GOEnrichmentRunner(genes, 'organism', 'gene_id_type', 0.05, 'elim', 'any', 'any', None, 'any', None, 'any',
                                None, False, False, 'fname', False, False, False, 'set_name', False, pval_func,
                                biotypes, background_set, biotype_ref_path, single_list, random_seed, **kwargs)
    if pval_func.lower() == 'xlmhg' and not does_python_version_support_single_set():
        assert runner.enrichment_func == False
        return
    assert runner.dag_tree == 'dag_tree'


def test_go_enrichment_runner_run(monkeypatch):
    organism_truth = 'my_organism'

    def get_taxon(self, organism):
        return 'taxon_id', organism

    def run(self):
        self.results = 'results'

    monkeypatch.setattr(EnrichmentRunner, 'run', run)
    monkeypatch.setattr(GOEnrichmentRunner, 'get_taxon_id', get_taxon)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.taxon_id, runner.organism = runner.get_taxon_id(organism_truth)
    runner.run()
    assert runner.results == 'results'
    assert runner.organism == organism_truth
    assert runner.taxon_id == 'taxon_id'


@pytest.mark.parametrize("test_input,expected", [
    ('fisher', EnrichmentRunner._fisher_enrichment),
    ('HYPERGEOMETRIC', EnrichmentRunner._hypergeometric_enrichment),
    ('Randomization', EnrichmentRunner._randomization_enrichment),
    ('XLmHG', EnrichmentRunner._xlmhg_enrichment)])
@pytest.mark.parametrize("propagate_annotations", ["no", "elim"])
def test_go_enrichment_runner_get_enrichment_func(test_input, expected, propagate_annotations):
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.propagate_annotations = propagate_annotations
    if test_input.lower() == 'xlmhg' and not does_python_version_support_single_set():
        assert runner._get_enrichment_func(test_input) == False
        return

    assert runner._get_enrichment_func(test_input).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.upper()).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.lower()).__name__ == expected.__name__
    assert runner._get_enrichment_func(test_input.capitalize()).__name__ == expected.__name__


@pytest.mark.parametrize("test_input,err", [
    ('fifty', ValueError),
    (50, AssertionError),
    (True, AssertionError),
    (max, AssertionError),
    ('randomization', NotImplementedError),
    ('xlmhg', NotImplementedError)])
def test_go_enrichment_runner_get_enrichment_func_invalid_value(test_input, err):
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.propagate_annotations = 'weight'
    with pytest.raises(err):
        runner._get_enrichment_func(test_input)


@pytest.mark.parametrize('got_gene_id_type', (True, False))
@pytest.mark.parametrize('organism,truth',
                         [('auto', ('inferred_id', 'inferred_organism')),
                          ('c elegans', ('c elegans_mapped_id', 'organism'))])
def test_go_enrichment_runner_get_taxon_id(monkeypatch, organism, got_gene_id_type, truth):
    gene_id_type_truth = 'UniProtKB'

    def alt_infer_taxon_id(gene_set, gene_id_type=None):
        assert isinstance(gene_set, set)
        if got_gene_id_type:
            assert gene_id_type == gene_id_type_truth
        else:
            assert gene_id_type is None
        return ('inferred_id', 'inferred_organism'), 'map_from'

    monkeypatch.setattr(io, 'map_taxon_id', lambda input_organism: (input_organism + '_mapped_id', 'organism'))
    monkeypatch.setattr(io, 'infer_taxon_from_gene_ids', alt_infer_taxon_id)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.gene_set = {'gene1', 'gene2', 'gene4'}
    runner.organism = organism

    if got_gene_id_type:
        runner.gene_id_type = gene_id_type_truth
        res = runner.get_taxon_id(organism)
    else:
        runner.gene_id_type = 'auto'
        res = runner.get_taxon_id(organism)

    assert res == truth


def test_go_enrichment_runner_fetch_annotations(monkeypatch):
    monkeypatch.setattr(GOEnrichmentRunner, '_get_query_key', lambda self: 'the_query_key')
    monkeypatch.setattr(GOEnrichmentRunner, '_generate_annotation_df', lambda self: 'goa_df')
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.fetch_annotations()
    assert runner.annotation_df == 'goa_df'
    assert runner.GOA_DF_QUERIES['the_query_key'] == 'goa_df'

    runner.GOA_DF_QUERIES['the_query_key'] = 'another_goa_df'
    runner.fetch_annotations()
    assert runner.annotation_df == 'another_goa_df'
    assert runner.GOA_DF_QUERIES['the_query_key'] == 'another_goa_df'


def test_go_enrichment_runner_get_annotation_iterator(monkeypatch):
    def alt_init(self, taxon_id, aspects, evidence_types, excluded_evidence_types, databases, excluded_databases,
                 qualifiers, excluded_qualifiers):
        assert taxon_id == 'taxon_id'
        assert aspects == 'aspects'
        assert evidence_types == 'evidence_types'
        assert excluded_evidence_types == 'exc_evidence_types'
        assert databases == 'databases'
        assert excluded_databases == 'exc_databases'
        assert qualifiers == 'qualifiers'
        assert excluded_qualifiers == 'exc_qualifiers'

    monkeypatch.setattr(io.GOlrAnnotationIterator, '__init__', alt_init)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.taxon_id = 'taxon_id'
    runner.aspects = 'aspects'
    runner.evidence_types = 'evidence_types'
    runner.excluded_evidence_types = 'exc_evidence_types'
    runner.databases = 'databases'
    runner.excluded_databases = 'exc_databases'
    runner.qualifiers = 'qualifiers'
    runner.excluded_qualifiers = 'exc_qualifiers'
    res = runner._get_annotation_iterator()
    assert isinstance(res, io.GOlrAnnotationIterator)


@pytest.mark.parametrize('propagate', ['other', 'no'])
@pytest.mark.parametrize("gene_id,go_id,truth",
                         [('gene1', 'GO1',
                           {'gene1': {'GO1', 'GO2', 'GO3', 'GO4', 'GO5'}, 'gene2': {'GO1'}, 'gene3': {'GO2'}}),
                          ('gene2', 'GO1',
                           {'gene1': {'GO1', 'GO2'}, 'gene2': {'GO1', 'GO3', 'GO4', 'GO5'}, 'gene3': {'GO2'}}),
                          ('gene1', 'GO2',
                           {'gene1': {'GO1', 'GO2'}, 'gene2': {'GO1'}, 'gene3': {'GO2'}}),
                          ('gene3', 'GO2',
                           {'gene1': {'GO1', 'GO2'}, 'gene2': {'GO1'}, 'gene3': {'GO2'}}),
                          ])
def test_go_enrichment_runner_propagate_annotation(monkeypatch, propagate, gene_id, go_id, truth):
    annotation_dict = {'gene1': {'GO1', 'GO2'}, 'gene2': {'GO1'}, 'gene3': {'GO2'}}
    if propagate == 'no':
        truth = copy.deepcopy(annotation_dict)

    def upper_induced_graph_iter(self, go_id):
        if go_id == 'GO1':
            for upper_go_id in {'GO3', 'GO4', 'GO5'}:
                yield upper_go_id

    monkeypatch.setattr(ontology.DAGTree, 'upper_induced_graph_iter', upper_induced_graph_iter)
    dag = ontology.DAGTree.__new__(ontology.DAGTree)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.dag_tree = dag
    runner.propagate_annotations = propagate
    runner._propagate_annotation(gene_id, go_id, annotation_dict)

    assert annotation_dict == truth


@pytest.mark.parametrize("mapping_dict,truth", [
    ({}, {}),
    ({'gene1': 'gene1_translated', 'gene3': 'gene3_translated'},
     {'gene1_translated': {'GO1', 'GO2'}, 'gene3_translated': {'GO2'}}),
    ({'gene1': 'gene1_translated', 'gene2': 'gene2_translated', 'gene3': 'gene3_translated'},
     {'gene1_translated': {'GO1', 'GO2'}, 'gene2_translated': {'GO1'}, 'gene3_translated': {'GO2'}})])
def test_go_enrichment_runner_translate_gene_ids(monkeypatch, mapping_dict, truth):
    monkeypatch.setattr(io, 'map_gene_ids', lambda gene_id, source, gene_id_type: mapping_dict)
    source_to_gene_id_dict = {'source1': {'gene1', 'gene3'}, 'source2': {'gene2'}}
    sparse_annotation_dict = {'gene1': {'GO1', 'GO2'}, 'gene2': {'GO1'}, 'gene3': {'GO2'}}

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.gene_id_type = 'gene_id_type'

    res = runner._translate_gene_ids(sparse_annotation_dict, source_to_gene_id_dict)
    assert res == truth


@pytest.mark.parametrize('propagate_annotations', ['no', 'elim'])
def test_go_enrichment_runner_get_query_key(propagate_annotations):
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.propagate_annotations = propagate_annotations
    runner.taxon_id = 'taxon_id'
    runner.gene_id_type = 'id_type'
    runner.aspects = {'aspect1', 'aspect2'}
    runner.evidence_types = {'ev2', 'ev1', 'ev5'}
    runner.excluded_evidence_types = {'ev3'}
    runner.databases = {'db1'}
    runner.excluded_databases = set()
    runner.qualifiers = {'qual1'}
    runner.excluded_qualifiers = set()

    propagate = True if propagate_annotations != 'no' else False

    truth = (
        'taxon_id', 'id_type', ('aspect1', 'aspect2'), ('ev1', 'ev2', 'ev5'), ('ev3',), ('db1',), tuple(), ('qual1',),
        tuple(), propagate)
    key = runner._get_query_key()
    assert key == truth
    try:
        _ = hash(key)
    except TypeError:
        assert False


def test_go_enrichment_runner_fetch_attributes():
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    truth_attributes = ['attribute1', 'attribute2', 'attribute3', 'attribute4']
    truth_attributes_set = {'attribute1', 'attribute2', 'attribute3', 'attribute4'}
    runner.fetch_attributes()
    assert runner.attributes == truth_attributes
    assert runner.attributes_set == truth_attributes_set


def test_go_enrichment_runner_correct_multiple_comparisons():
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)

    runner.results = pd.DataFrame([[0, 0, 0, 0, 0, 0.005],
                                   [0, 0, 0, 0, 0, 0.017],
                                   [0, 0, 0, 0, 0, np.nan],
                                   [0, 0, 0, 0, -3, np.nan],
                                   [0, 0, 0, 0, 0, 0.92]],
                                  columns=['go_id', 'samples', 'obs', 'exp', 'colName', 'pval']).set_index('go_id')
    runner.alpha = 0.04
    truth = pd.DataFrame([[0, 0, 0, 0, 0, 0.005, 0.0275, True],
                          [0, 0, 0, 0, 0, 0.017, 0.04675, False],
                          [0, 0, 0, 0, 0, np.nan, np.nan, np.nan],
                          [0, 0, 0, 0, -3, np.nan, np.nan, np.nan],
                          [0, 0, 0, 0, 0, 0.92, 1.0, False]],
                         columns=['go_id', 'samples', 'obs', 'exp', 'colName', 'pval', 'padj',
                                  'significant']).set_index('go_id')

    runner._correct_multiple_comparisons()

    assert np.all(np.isclose(truth['padj'].values, runner.results['padj'].values, atol=0, equal_nan=True))
    for val, val_truth in zip(runner.results['significant'], truth['significant']):
        assert val == val_truth or (np.isnan(val) and np.isnan(val_truth))
    assert truth.loc['go_id':'pval'].equals(runner.results.loc['go_id':'pval'])


@pytest.mark.parametrize('single_list', [True, False])
@pytest.mark.parametrize('results,n_bars_truth', [([1, 2, 3], 3), (list(range(15)), 10)])
@pytest.mark.parametrize('plot_ontology_graph', [False, True])
def test_go_enrichment_runner_plot_results(monkeypatch, single_list, results, n_bars_truth, plot_ontology_graph):
    dag_plotted = []

    def validate_params(self, title, n_bars, ylabel=''):
        assert isinstance(title, str)
        assert self.set_name in title
        assert isinstance(ylabel, str)
        assert isinstance(n_bars, int)
        assert n_bars == n_bars_truth
        return plt.Figure()

    def go_dag_plot(dpi, **kwargs):
        assert plot_ontology_graph
        dag_plotted.append(True)

    monkeypatch.setattr(GOEnrichmentRunner, 'enrichment_bar_plot', validate_params)
    monkeypatch.setattr(GOEnrichmentRunner, 'go_dag_plot', go_dag_plot)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.single_set = single_list
    runner.set_name = 'name of the set'
    runner.results = results
    runner.plot_ontology_graph = plot_ontology_graph
    res = runner.plot_results()
    assert isinstance(res, plt.Figure)
    if plot_ontology_graph:
        assert dag_plotted == [True]


@pytest.mark.parametrize('return_nonsignificant,truth_file',
                         [(True, 'tests/test_files/go_enrichment_runner_format_results_with_nonsignificant_truth.csv'),
                          (False, 'tests/test_files/go_enrichment_runner_format_results_truth.csv')])
def test_go_enrichment_runner_format_results(monkeypatch, return_nonsignificant, truth_file):
    truth = pd.read_csv(truth_file, index_col=0)
    results_dict = {'name1': ['desc1', 50, 10, 5, 2.3, 0.05], 'name2': ['desc2', 17, 0, 3, 0, 1],
                    'name3': ['desc3', 1, np.nan, -2, -0.7, 0.04]}

    def add_sig(self):
        self.results['significant'] = [False, True, True]

    monkeypatch.setattr(GOEnrichmentRunner, '_correct_multiple_comparisons', add_sig)

    dag_tree = ontology.DAGTree.__new__(ontology.DAGTree)
    dag_tree.go_terms = {'name1': ontology.GOTerm(), 'name2': ontology.GOTerm(), 'name3': ontology.GOTerm()}
    dag_tree['name1'].set_level(2)
    dag_tree['name2'].set_level(1)
    dag_tree['name3'].set_level(5)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.dag_tree = dag_tree
    runner.en_score_col = 'colName'
    runner.single_set = False
    runner.return_nonsignificant = return_nonsignificant

    runner.format_results(results_dict)

    assert truth.equals(runner.results)


@pytest.mark.parametrize("propagate_annotations,truth",
                         [('no', 'classic'),
                          ('classic', 'classic'),
                          ('elim', 'elim'),
                          ('weight', 'weight'),
                          ('all.m', 'all.m')])
def test_go_enrichment_runner_calculate_enrichment_serial(monkeypatch, propagate_annotations, truth):
    monkeypatch.setattr(GOEnrichmentRunner, '_go_classic_pvalues_serial', lambda self, desc: 'classic')
    monkeypatch.setattr(GOEnrichmentRunner, '_go_elim_pvalues_serial', lambda self, desc: 'elim')
    monkeypatch.setattr(GOEnrichmentRunner, '_go_weight_pvalues_serial', lambda self, desc: 'weight')
    monkeypatch.setattr(GOEnrichmentRunner, '_go_allm_pvalues_serial', lambda self: 'all.m')
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.propagate_annotations = propagate_annotations
    runner.attributes = []
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0).notna()

    res = runner._calculate_enrichment_serial()

    if propagate_annotations != 'all.m':
        assert len(runner.mod_annotation_dfs) == 1

    if propagate_annotations in {'classic', 'no'}:
        assert runner.annotation_df is runner.mod_annotation_dfs[0]
    elif propagate_annotations == 'elim':
        assert runner.annotation_df.equals(runner.mod_annotation_dfs[0])
        assert runner.annotation_df is not runner.mod_annotation_dfs[0]
    elif propagate_annotations == 'weight':
        assert runner.annotation_df.equals((runner.mod_annotation_dfs[0] == 1))
        assert runner.mod_annotation_dfs[0].values.dtype.name == 'float64'
        assert runner.annotation_df is not runner.mod_annotation_dfs[0]

    assert res == truth


@pytest.mark.parametrize("propagate_annotations,truth",
                         [('no', 'classic'),
                          ('classic', 'classic'),
                          ('elim', 'elim'),
                          ('weight', 'weight'),
                          ('all.m', 'all.m')])
def test_go_enrichment_runner_calculate_enrichment_parallel(monkeypatch, propagate_annotations, truth):
    monkeypatch.setattr(GOEnrichmentRunner, '_go_classic_pvalues_parallel', lambda self, desc: 'classic')
    monkeypatch.setattr(GOEnrichmentRunner, '_go_elim_pvalues_parallel', lambda self, desc: 'elim')
    monkeypatch.setattr(GOEnrichmentRunner, '_go_weight_pvalues_parallel', lambda self, desc: 'weight')
    monkeypatch.setattr(GOEnrichmentRunner, '_go_allm_pvalues_parallel', lambda self: 'all.m')

    def go_level_iter(self, namespace):
        mapper = {'namespace1': ['attribute1', 'attribute4'], 'namespace2': ['attribute2', 'attribute3']}
        if namespace == 'all':
            return [f'attribute{i + 1}' for i in range(4)]
        return mapper[namespace]

    monkeypatch.setattr(GOEnrichmentRunner, '_go_level_iterator', go_level_iter)

    class DAGTreePlaceHolder:
        def __init__(self):
            self.namespaces = ['namespace1', 'namespace2']

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.propagate_annotations = propagate_annotations
    runner.attributes = []
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0).notna()
    runner.dag_tree = DAGTreePlaceHolder()

    res = runner._calculate_enrichment_parallel()

    if propagate_annotations in {'classic', 'no'}:
        assert runner.annotation_df is runner.mod_annotation_dfs[0]
        assert len(runner.mod_annotation_dfs) == 1
    elif propagate_annotations == 'elim':
        assert len(runner.mod_annotation_dfs) == len(runner.dag_tree.namespaces)
        for namespace, mod_df in zip(runner.dag_tree.namespaces, runner.mod_annotation_dfs):
            assert runner.annotation_df[go_level_iter(None, namespace)].equals(mod_df)
    elif propagate_annotations == 'weight':
        assert len(runner.mod_annotation_dfs) == len(runner.dag_tree.namespaces)
        for namespace, mod_df in zip(runner.dag_tree.namespaces, runner.mod_annotation_dfs):
            assert runner.annotation_df[go_level_iter(None, namespace)].equals(mod_df == 1)
            assert mod_df.values.dtype.name == 'float64'

    assert res == truth


def test_go_enrichment_runner_generate_annotation_df(monkeypatch):
    annotation_dict = {}
    source_to_id_dict = {}

    def process_annotations(self):
        annotation_dict['proccess_annotations'] = True
        source_to_id_dict['process_annotations_source'] = True
        return annotation_dict, source_to_id_dict

    def translate_gene_ids(self, annotation_dict, source_dict):
        assert annotation_dict['proccess_annotations']
        assert source_to_id_dict['process_annotations_source']
        return {'translate_annotation': True}

    def sparse_dict_to_bool_df(annotation_dict, progress_bar_desc):
        assert annotation_dict['translate_annotation']
        return 'bool_df'

    monkeypatch.setattr(GOEnrichmentRunner, '_process_annotations', process_annotations)
    monkeypatch.setattr(GOEnrichmentRunner, '_translate_gene_ids', translate_gene_ids)
    monkeypatch.setattr(parsing, 'sparse_dict_to_bool_df', sparse_dict_to_bool_df)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)

    res = runner._generate_annotation_df()
    assert res == 'bool_df'


def test_go_enrichment_runner_process_annotations_no_annotations(monkeypatch):
    class AnnotationIterator:
        def __init__(self, n_annotations):
            self.n_annotations = n_annotations

        def __iter__(self):
            return [None].__iter__()

    def _get_annotation_iter_zero(self):
        return AnnotationIterator(0)

    monkeypatch.setattr(GOEnrichmentRunner, '_get_annotation_iterator', _get_annotation_iter_zero)
    with pytest.raises(AssertionError) as e:
        runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
        runner.propagate_annotations = "no"
        runner.organism = "organism"
        runner.taxon_id = "taxon id"
        runner._process_annotations()
    print(e)


def test_go_enrichment_runner_process_annotations(monkeypatch):
    propagated_annotations = set()
    propagated_annotations_truth = {('gene_id1', 'go_id1'), ('gene_id1', 'go_id2'), ('gene_id2', 'go_id1'),
                                    ('gene_id2', 'go_id3'), ('gene_id3', 'go_id4')}
    annotation_dict_truth = {'gene_id1': {'go_id1', 'go_id2'}, 'gene_id2': {'go_id1', 'go_id3'}, 'gene_id3': {'go_id4'}}
    source_dict_truth = {'source1': {'gene_id1', 'gene_id3'}, 'source2': {'gene_id2'}}

    def get_annotation_iter(self):
        iterator = io.GOlrAnnotationIterator.__new__(io.GOlrAnnotationIterator)
        iterator.n_annotations = 5
        return iterator

    def annotation_iter(self):
        annotations = [{'bioentity_internal_id': 'gene_id1', 'annotation_class': 'go_id1', 'source': 'source1'},
                       {'bioentity_internal_id': 'gene_id1', 'annotation_class': 'go_id2', 'source': 'source1'},
                       {'bioentity_internal_id': 'gene_id2', 'annotation_class': 'go_id1', 'source': 'source2'},
                       {'bioentity_internal_id': 'gene_id2', 'annotation_class': 'go_id3', 'source': 'source2'},
                       {'bioentity_internal_id': 'gene_id3', 'annotation_class': 'go_id4', 'source': 'source1'}]
        for annotation in annotations:
            yield annotation

    def propagate_annotation(self, gene_id, go_id, sparse_annotation_dict):
        propagated_annotations.add((gene_id, go_id))

    monkeypatch.setattr(io.GOlrAnnotationIterator, '_annotation_generator_func', annotation_iter)
    monkeypatch.setattr(GOEnrichmentRunner, '_propagate_annotation', propagate_annotation)
    monkeypatch.setattr(GOEnrichmentRunner, '_get_annotation_iterator', get_annotation_iter)

    dag = ontology.DAGTree.__new__(ontology.DAGTree)
    dag.alt_ids = {}
    dag.go_terms = {'go_id1': ontology.GOTerm(), 'go_id2': ontology.GOTerm(), 'go_id3': ontology.GOTerm(),
                    'go_id4': ontology.GOTerm()}
    dag.go_terms['go_id1'].set_id('go_id1')
    dag.go_terms['go_id2'].set_id('go_id2')
    dag.go_terms['go_id3'].set_id('go_id3')
    dag.go_terms['go_id4'].set_id('go_id4')

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.propagate_annotations = 'classic'
    runner.organism = 'organism'
    runner.taxon_id = 'taxon_id'
    runner.dag_tree = dag

    annotation_dict, source_dict = runner._process_annotations()

    assert propagated_annotations == propagated_annotations_truth
    assert annotation_dict == annotation_dict_truth
    assert source_dict == source_dict_truth


def test_go_enrichment_runner_go_classic_pvalues_serial(monkeypatch):
    go_ids = ['attr1', 'attr2', 'attr3']

    def validate_input_params_classic_on_batch(self, go_term_batch, mod_df_index=0):
        try:
            chunk_iterator = iter(go_term_batch)
            assert go_ids == list(chunk_iterator)
        except TypeError:
            assert False

        assert mod_df_index == 0

    monkeypatch.setattr(GOEnrichmentRunner, '_go_classic_on_batch', validate_input_params_classic_on_batch)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.attributes = go_ids
    runner._go_classic_pvalues_serial()


def test_go_enrichment_runner_go_classic_pvalues_parallel(monkeypatch):
    go_ids = [f'id_{i}' for i in range(1500)]
    go_ids_batch_truth = [[f'id_{i}' for i in range(1000)], [f'id_{i}' for i in range(1000, 1500)]]

    def validate_input_params_parallel_over_grouping(self, func, go_term_batches, mod_df_inds, progress_bar_desc):
        assert go_term_batches == go_ids_batch_truth
        assert func.__func__ == GOEnrichmentRunner._go_classic_on_batch
        assert isinstance(progress_bar_desc, str)
        mod_df_inds_lst = [i for i in mod_df_inds]
        for ind in mod_df_inds_lst:
            assert ind == 0
        assert len(mod_df_inds_lst) == len(go_ids_batch_truth)

    monkeypatch.setattr(GOEnrichmentRunner, '_parallel_over_grouping', validate_input_params_parallel_over_grouping)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.attributes = go_ids
    runner._go_classic_pvalues_parallel()


def test_go_enrichment_runner_go_elim_pvalues_serial(monkeypatch):
    def validate_input_params_elim_on_aspect(self, go_aspect, progress_bar_desc):
        assert isinstance(progress_bar_desc, str)
        assert go_aspect == 'all'
        return 'success'

    monkeypatch.setattr(GOEnrichmentRunner, '_go_elim_on_aspect', validate_input_params_elim_on_aspect)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    assert runner._go_elim_pvalues_serial() == 'success'


@pytest.mark.parametrize('aspects', [['aspect0', 'aspect1'], ['aspect0'], ['aspect0', 'aspect1', 'aspect2']])
def test_go_enrichment_runner_go_elim_pvalues_parallel(monkeypatch, aspects):
    class FakeDAG:
        def __init__(self, aspect_list):
            self.namespaces = aspect_list

    @joblib.wrap_non_picklable_objects
    def validate_input_params_elim_on_aspect(aspect, mod_df_ind):
        assert mod_df_ind == int(aspect[-1])
        assert aspect in aspects
        return {aspect: 'success'}

    def is_method_of_class(mthd, cls):
        assert cls == GOEnrichmentRunner
        assert mthd == validate_input_params_elim_on_aspect
        return True

    monkeypatch.setattr(GOEnrichmentRunner, '_go_elim_on_aspect', validate_input_params_elim_on_aspect)
    monkeypatch.setattr(validation, 'is_method_of_class', is_method_of_class)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.dag_tree = FakeDAG(aspects)
    assert runner._go_elim_pvalues_parallel() == {aspect: 'success' for aspect in aspects}


def test_go_enrichment_runner_go_weight_pvalues_serial(monkeypatch):
    def validate_input_params_weight_on_aspect(self, go_aspect, mod_df_ind=0, progress_bar_desc=''):
        assert isinstance(progress_bar_desc, str)
        assert go_aspect == 'all'
        assert mod_df_ind == 0
        return 'success'

    monkeypatch.setattr(GOEnrichmentRunner, '_go_weight_on_aspect', validate_input_params_weight_on_aspect)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    assert runner._go_weight_pvalues_serial() == 'success'


@pytest.mark.parametrize('aspects', [['aspect0', 'aspect1'], ['aspect0'], ['aspect0', 'aspect1', 'aspect2']])
def test_go_enrichment_runner_go_weight_pvalues_parallel(monkeypatch, aspects):
    class FakeDAG:
        def __init__(self, aspect_list):
            self.namespaces = aspect_list

    @joblib.wrap_non_picklable_objects
    def validate_input_params_weight_on_aspect(aspect, mod_df_ind):
        assert mod_df_ind == int(aspect[-1])
        assert aspect in aspects
        return {aspect: 'success'}

    def is_method_of_class(mthd, cls):
        assert cls == GOEnrichmentRunner
        assert mthd == validate_input_params_weight_on_aspect
        return True

    monkeypatch.setattr(GOEnrichmentRunner, '_go_weight_on_aspect', validate_input_params_weight_on_aspect)
    monkeypatch.setattr(validation, 'is_method_of_class', is_method_of_class)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.dag_tree = FakeDAG(aspects)
    assert runner._go_weight_pvalues_parallel() == {aspect: 'success' for aspect in aspects}


def test_go_enrichment_runner_go_allm_pvalues_serial(monkeypatch):
    methods_called = {}
    methods_called_truth = {'classic': True, 'elim': True, 'weight': True}
    outputs_truth = {'classic': 'classic', 'elim': 'elim', 'weight': 'weight'}

    def _calculate_enrichment_serial(self: GOEnrichmentRunner):
        methods_called[self.propagate_annotations] = True
        return self.propagate_annotations

    def _calculate_allm(self, outputs):
        assert outputs == outputs_truth

    monkeypatch.setattr(GOEnrichmentRunner, '_calculate_enrichment_serial', _calculate_enrichment_serial)
    monkeypatch.setattr(GOEnrichmentRunner, '_calculate_allm', _calculate_allm)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner._go_allm_pvalues_serial()
    assert methods_called == methods_called_truth
    assert runner.propagate_annotations == 'all.m'


def test_go_enrichment_runner_go_allm_pvalues_serial_error_state(monkeypatch):
    def _calculate_enrichment_serial(self: GOEnrichmentRunner):
        raise AssertionError

    monkeypatch.setattr(GOEnrichmentRunner, '_calculate_enrichment_serial', _calculate_enrichment_serial)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    with pytest.raises(AssertionError):
        runner._go_allm_pvalues_serial()
        assert runner.propagate_annotations == 'all.m'


def test_go_enrichment_runner_go_allm_pvalues_parallel(monkeypatch):
    methods_called = {}
    methods_called_truth = {'classic': True, 'elim': True, 'weight': True}
    outputs_truth = {'classic': 'classic', 'elim': 'elim', 'weight': 'weight'}

    def _calculate_enrichment_parallel(self: GOEnrichmentRunner):
        methods_called[self.propagate_annotations] = True
        return self.propagate_annotations

    def _calculate_allm(self, outputs):
        assert outputs == outputs_truth

    monkeypatch.setattr(GOEnrichmentRunner, '_calculate_enrichment_parallel', _calculate_enrichment_parallel)
    monkeypatch.setattr(GOEnrichmentRunner, '_calculate_allm', _calculate_allm)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner._go_allm_pvalues_parallel()
    assert methods_called == methods_called_truth
    assert runner.propagate_annotations == 'all.m'


def test_go_enrichment_runner_go_allm_pvalues_parallel_error_state(monkeypatch):
    def _calculate_enrichment_parallel(self: GOEnrichmentRunner):
        raise AssertionError

    monkeypatch.setattr(GOEnrichmentRunner, '_calculate_enrichment_parallel', _calculate_enrichment_parallel)

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    with pytest.raises(AssertionError):
        runner._go_allm_pvalues_parallel()
        assert runner.propagate_annotations == 'all.m'


@pytest.mark.parametrize('attrs,output_dict,truth_dict',
                         [(['attr1', 'attr2'],
                           {'classic': {'attr1': ['classic_val1', 'classic_val2', 0.05],
                                        'attr2': ['classic_val3', 'classic_val4', 1]},
                            'elim': {'attr1': ['elim_val1', 'elim_val2', 0.3],
                                     'attr2': ['elim_val3', 'elim_val4', 0.9999]},
                            'weight': {'attr1': ['weight_val1', 'weight_val2', 0.12],
                                       'attr2': ['weight_val3', 'weight_val4', 0.5]}},
                           {'attr1': ('classic_val1', 'classic_val2', 0.12164404),
                            'attr2': ('classic_val3', 'classic_val4', 0.793674068)})])
def test_go_enrichment_runner_calculate_allm(monkeypatch, attrs, output_dict, truth_dict):
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.attributes = attrs
    res = runner._calculate_allm(output_dict)
    assert res.keys() == truth_dict.keys()
    for attr in attrs:
        assert res[attr][:-1] == truth_dict[attr][:-1]
        assert np.isclose(res[attr][-1], truth_dict[attr][-1], atol=0)


def test_go_enrichment_runner_go_level_iterator(monkeypatch):
    this_namespace = 'this_namespace'

    class FakeDAG:
        def __init__(self, go_ids_to_yield: list):
            self.go_ids = go_ids_to_yield

        def level_iter(self, namespace):
            assert namespace == this_namespace
            for go_id in self.go_ids:
                yield go_id

    go_ids_by_level = ['ID1', 'ID5', 'ID4', 'ID10', 'ID2']
    go_ids_in_runner = {'ID1', 'ID2', 'ID3', 'ID4', 'ID10'}

    go_ids_by_level_truth = ['ID1', 'ID4', 'ID10', 'ID2']

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.attributes_set = go_ids_in_runner
    runner.dag_tree = FakeDAG(go_ids_by_level)
    assert list(runner._go_level_iterator(this_namespace)) == go_ids_by_level_truth


@pytest.mark.parametrize('truth',
                         [(['attribute1', 6, 3, (11 / 38) * 6, np.log2(3 / ((11 / 38) * 6)), 0.05]),
                          (['attribute4', 6, 4, (13 / 38) * 6, np.log2(4 / ((13 / 38) * 6)), 0.05])])
def test_go_enrichment_runner_randomization_enrichment(monkeypatch, truth):
    class FakeGOTerm:
        def __init__(self, go_id):
            self.go_id = go_id
            self.name = go_id

    class FakeDAG:
        def __init__(self):
            pass

        def __getitem__(self, item):
            return FakeGOTerm(item)

    runner = _randomization_enrichment_setup_runner(monkeypatch=monkeypatch, truth=truth,
                                                    runner_class=GOEnrichmentRunner, notna=True)
    runner.mod_annotation_dfs = (runner.annotation_df,)
    runner.dag_tree = FakeDAG()
    assert runner._randomization_enrichment(truth[0], runner.pvalue_kwargs['reps']) == truth


@pytest.mark.parametrize('attribute,truth',
                         [('attribute1', (np.array([0, 1], dtype='uint16'), np.array([2, 3], dtype='uint16'))),
                          ('attribute4', (np.array([0, 2], dtype='uint16'), np.array([1, 3], dtype='uint16')))])
def test_go_enrichment_runner_generate_xlmhg_index_vectors(attribute, truth):
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.ranked_genes = np.array(['WBGene00000106', 'WBGene00000019', 'WBGene00000865', 'WBGene00001131'],
                                   dtype='str')
    runner.mod_annotation_dfs = (pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0).notna(),)
    res = runner._generate_xlmhg_index_vectors(attribute, 0)
    assert np.all(res[0] == truth[0])
    assert np.all(res[1] == truth[1])


@pytest.mark.parametrize('params,go_id,truth',
                         [((38, 6, 11, 3), 'attribute1',
                           ['attribute1_name', 6, 3, (13 / 38) * 6, np.log2(3 / ((13 / 38) * 6)), 0.05]), ])
def test_go_enrichment_runner_hypergeometric_enrichment(monkeypatch, params, go_id, truth):
    monkeypatch.setattr(GOEnrichmentRunner, '_get_hypergeometric_parameters', lambda self, go_id, mod_df_ind: params)

    def alt_calc_pval(self, bg_size, de_size, go_size, go_de_size):
        assert (bg_size, de_size, go_size, go_de_size) == params
        return 0.05

    monkeypatch.setattr(GOEnrichmentRunner, '_calc_hypergeometric_pval', alt_calc_pval)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0).apply(np.ceil)
    runner.gene_set = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915',
                       'WBGene00268195'}

    class FakeGOTerm:
        def __init__(self, go_id, name):
            self.go_id = go_id
            self.name = name

    runner.dag_tree = {go_id: FakeGOTerm(go_id, go_id + '_name')}
    assert runner._hypergeometric_enrichment(go_id) == truth


@pytest.mark.parametrize('params,go_id,truth',
                         [((38, 6, 11, 3), 'attribute1',
                           ['attribute1_name', 6, 3, (13 / 38) * 6, np.log2(3 / ((13 / 38) * 6)), 0.05]), ])
def test_go_enrichment_runner_fisher_enrichment(monkeypatch, params, go_id, truth):
    monkeypatch.setattr(GOEnrichmentRunner, '_get_hypergeometric_parameters', lambda self, go_id, mod_df_ind: params)

    def alt_calc_pval(self, bg_size, de_size, go_size, go_de_size):
        assert (bg_size, de_size, go_size, go_de_size) == params
        return 0.05

    monkeypatch.setattr(GOEnrichmentRunner, '_calc_fisher_pval', alt_calc_pval)
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0).apply(np.ceil)
    runner.gene_set = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915',
                       'WBGene00268195'}

    class FakeGOTerm:
        def __init__(self, go_id, name):
            self.go_id = go_id
            self.name = name

    runner.dag_tree = {go_id: FakeGOTerm(go_id, go_id + '_name')}
    assert runner._fisher_enrichment(go_id) == truth


@pytest.mark.parametrize('go_id,results, mod_df_ind',
                         [('attribute1', (38, 6, 13, 3), 0),
                          ('attribute3', (38, 6, 60, 9), 1),
                          ('attribute4', (38, 6, 1, 2), 2)])
def test_go_enrichment_runner_get_hypergeometric_parameters(monkeypatch, go_id, results, mod_df_ind):
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    runner.mod_annotation_dfs = [None, None, None]
    runner.mod_annotation_dfs[mod_df_ind] = annotation_df
    runner.gene_set = {'WBGene00000019', 'WBGene00000041', 'WBGene00000106', 'WBGene00001133', 'WBGene00003915',
                       'WBGene00268195'}
    assert runner._get_hypergeometric_parameters(go_id, mod_df_ind) == results


@pytest.mark.parametrize('grouping,inds,truth',
                         [([['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h']], [1, 2, 1],
                           {'a': 1, 'b': 1, 'c': 1, 'd': 2, 'e': 2, 'f': 2, 'g': 1, 'h': 1})])
def test_go_enrichment_runner_parallel_over_grouping(monkeypatch, grouping, inds, truth):
    monkeypatch.setattr(validation, 'is_method_of_class', lambda func, obj_type: True)

    def my_func(group, ind):
        return {obj: ind for obj in group}

    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    res = runner._parallel_over_grouping(my_func, grouping, inds)
    assert res == truth


@pytest.mark.parametrize('pval_fwd,pval_rev,escore_fwd,escore_rev,pval_truth,log2escore_truth',
                         [(0.05, 0.7, 2, 0.5, 0.05, 1), (0.6, 0.3, 1.2, 4, 0.3, -2),
                          (np.nan, np.nan, 2, np.inf, 1, -np.inf)])
def test_enrichment_runner_extract_xlmhg_results(pval_fwd, pval_rev, escore_fwd, escore_rev, pval_truth,
                                                 log2escore_truth):
    class XLmHGResultObject:
        def __init__(self, pval, escore):
            self.pval = pval
            self.escore = escore

    log2escore, pval = EnrichmentRunner._extract_xlmhg_results(XLmHGResultObject(pval_fwd, escore_fwd),
                                                               XLmHGResultObject(pval_rev, escore_rev))

    assert pval == pval_truth
    assert log2escore == log2escore_truth


@pytest.mark.parametrize('single_list,genes,biotypes,pval_func,background_set,biotype_ref_path, random_seed,kwargs',
                         [(True, np.array(['WBGene1', 'WBGene2'], dtype=str), None, 'xlmhg', None, None, None, {}),
                          (False, {'WBGene00000001', 'WBGene00000002'}, 'protein_coding', 'randomization',
                           {'WBGene00000001', 'WBGene00000002', 'EBGene00000003'},
                           'path/to/biotype/ref', 42, {'reps': 10000})])
def test_kegg_enrichment_runner_api(monkeypatch, single_list, genes, biotypes, pval_func, background_set,
                                    biotype_ref_path, random_seed, kwargs):
    monkeypatch.setattr(KEGGEnrichmentRunner, 'get_taxon_id', lambda *args: ('a', 'b'))
    runner = KEGGEnrichmentRunner(genes, 'organism', 'gene_id_type', 0.05, True, False, 'fname', False, False,
                                  'set_name', False, pval_func,
                                  biotypes, background_set, biotype_ref_path, single_list, random_seed, **kwargs)


@pytest.mark.parametrize('got_gene_id_type', (True, False))
@pytest.mark.parametrize('organism,truth',
                         [('auto', ('inferred_id', 'inferred_organism')),
                          ('c elegans', ('c elegans_mapped_id', 'organism'))])
def test_kegg_enrichment_runner_get_taxon_id(monkeypatch, organism, got_gene_id_type, truth):
    gene_id_type_truth = 'UniProtKB'

    def alt_infer_taxon_id(gene_set, gene_id_type=None):
        assert isinstance(gene_set, set)
        if got_gene_id_type:
            assert gene_id_type == gene_id_type_truth
        else:
            assert gene_id_type is None
        return ('inferred_id', 'inferred_organism'), 'map_from'

    monkeypatch.setattr(io, 'map_taxon_id', lambda input_organism: (input_organism + '_mapped_id', 'organism'))
    monkeypatch.setattr(io, 'infer_taxon_from_gene_ids', alt_infer_taxon_id)
    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    runner.gene_set = {'gene1', 'gene2', 'gene4'}
    runner.organism = organism

    if got_gene_id_type:
        runner.gene_id_type = gene_id_type_truth
        res = runner.get_taxon_id(organism)
    else:
        runner.gene_id_type = 'auto'
        res = runner.get_taxon_id(organism)

    assert res == truth


def test_kegg_enrichment_runner_format_results(monkeypatch):
    def mock_correct_multiple_comparisons(self):
        self.results['significant'] = [False, True, True]

    monkeypatch.setattr(KEGGEnrichmentRunner, '_correct_multiple_comparisons', mock_correct_multiple_comparisons)
    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    results_dict = [['name1', 50, 10, 5.5, 2.3, 0.05], ['name2', 17, 0, 3, 0, 1],
                    ['name3', 1, 2, -2, -0.7, 0.04]]
    truth = pd.read_csv('tests/test_files/kegg_enrichment_runner_format_results_truth.csv', index_col=0)
    runner.en_score_col = 'colName'
    runner.single_set = False
    runner.return_nonsignificant = False
    runner.pathway_names_dict = {'name1': 'desc1', 'name2': 'desc2', 'name3': 'desc3'}

    runner.format_results(results_dict)
    assert np.all(truth.sort_index() == runner.results.sort_index())


def test_kegg_enrichment_runner_fetch_annotations(monkeypatch):
    monkeypatch.setattr(KEGGEnrichmentRunner, '_get_query_key', lambda self: 'the_query_key')
    monkeypatch.setattr(KEGGEnrichmentRunner, '_generate_annotation_df', lambda self: ('kegg_df', 'pathway_names'))
    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    runner.fetch_annotations()
    assert runner.annotation_df == 'kegg_df'
    assert runner.KEGG_DF_QUERIES['the_query_key'] == ('kegg_df', 'pathway_names')
    assert runner.pathway_names_dict == 'pathway_names'

    runner.KEGG_DF_QUERIES['the_query_key'] = ('another_kegg_df', 'other_pathway_names')
    runner.fetch_annotations()
    assert runner.annotation_df == 'another_kegg_df'
    assert runner.pathway_names_dict == 'other_pathway_names'
    assert runner.KEGG_DF_QUERIES['the_query_key'] == ('another_kegg_df', 'other_pathway_names')


def test_kegg_enrichment_runner_generate_annotation_df(monkeypatch):
    annotation_dict = {}
    name_dict = {}
    truth = pd.DataFrame([[True, np.nan], [np.nan, np.nan]])

    def process_annotations(self):
        annotation_dict['proccess_annotations'] = True
        name_dict['process_annotations_source'] = True
        return annotation_dict, name_dict

    def translate_gene_ids(self, annotation_dict):
        assert annotation_dict['proccess_annotations']
        assert name_dict['process_annotations_source']
        return {'translate_annotation': True}

    def sparse_dict_to_bool_df(annotation_dict, progress_bar_desc):
        assert annotation_dict['translate_annotation']
        return pd.DataFrame([[True, False], [False, False]])

    monkeypatch.setattr(KEGGEnrichmentRunner, '_process_annotations', process_annotations)
    monkeypatch.setattr(KEGGEnrichmentRunner, '_translate_gene_ids', translate_gene_ids)
    monkeypatch.setattr(parsing, 'sparse_dict_to_bool_df', sparse_dict_to_bool_df)
    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)

    res, name_res = runner._generate_annotation_df()
    assert np.all(res.notna() == truth.notna())


def test_kegg_enrichment_runner_process_annotations(monkeypatch):
    annotation_dict_truth = {'gene_id1': {'go_id1', 'go_id2'}, 'gene_id2': {'go_id1', 'go_id3'}, 'gene_id3': {'go_id4'}}
    name_dict_truth = {'go_id1': 'name1', 'go_id2': 'name2', 'go_id3': 'name3', 'go_id4': 'name4'}

    def get_annotation_iter(self):
        iterator = io.KEGGAnnotationIterator.__new__(io.KEGGAnnotationIterator)
        iterator.n_annotations = 4
        return iterator

    def annotation_iter(self):
        annotations = [['go_id1', 'name1', {'gene_id1', 'gene_id2'}],
                       ['go_id2', 'name2', {'gene_id1'}],
                       ['go_id3', 'name3', {'gene_id2'}],
                       ['go_id4', 'name4', {'gene_id3'}]]
        for annotation in annotations:
            yield annotation

    monkeypatch.setattr(io.KEGGAnnotationIterator, 'get_pathway_annotations', annotation_iter)
    monkeypatch.setattr(KEGGEnrichmentRunner, '_get_annotation_iterator', get_annotation_iter)

    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    runner.organism = 'organism'
    runner.taxon_id = 'taxon_id'

    annotation_dict, name_dict = runner._process_annotations()

    assert annotation_dict == annotation_dict_truth
    assert name_dict == name_dict_truth


@pytest.mark.parametrize("mapping_dict,truth", [
    ({}, {}),
    ({'gene1': 'gene1_translated', 'gene3': 'gene3_translated'},
     {'gene1_translated': {'GO1', 'GO2'}, 'gene3_translated': {'GO2'}}),
    ({'gene1': 'gene1_translated', 'gene2': 'gene2_translated', 'gene3': 'gene3_translated'},
     {'gene1_translated': {'GO1', 'GO2'}, 'gene2_translated': {'GO1'}, 'gene3_translated': {'GO2'}})])
def test_kegg_enrichment_runner_translate_gene_ids(monkeypatch, mapping_dict, truth):
    monkeypatch.setattr(io, 'map_gene_ids', lambda gene_id, source, gene_id_type: mapping_dict)
    sparse_annotation_dict = {'gene1': {'GO1', 'GO2'}, 'gene2': {'GO1'}, 'gene3': {'GO2'}}

    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    runner.gene_id_type = 'gene_id_type'

    res = runner._translate_gene_ids(sparse_annotation_dict)
    assert res == truth


def test_kegg_enrichment_runner_get_query_key():
    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    runner.taxon_id = 'taxon_id'
    runner.gene_id_type = 'id_type'

    truth = ('taxon_id', 'id_type')
    key = runner._get_query_key()
    assert key == truth
    try:
        _ = hash(key)
    except TypeError:
        assert False


def test_kegg_enrichment_runner_fetch_attributes():
    runner = KEGGEnrichmentRunner.__new__(KEGGEnrichmentRunner)
    runner.annotation_df = pd.read_csv('tests/test_files/attr_ref_table_for_tests.csv', index_col=0)
    truth_attributes = ['attribute1', 'attribute2', 'attribute3', 'attribute4']
    truth_attributes_set = {'attribute1', 'attribute2', 'attribute3', 'attribute4'}
    runner.fetch_attributes()
    assert runner.attributes == truth_attributes
    assert runner.attributes_set == truth_attributes_set


def test_dag_plot_for_namespace():
    runner = GOEnrichmentRunner.__new__(GOEnrichmentRunner)
    runner.results = io.load_csv('tests/test_files/go_enrichment_runner_sample_results.csv', index_col=0)
    runner.dag_tree = io.fetch_go_basic()
    runner.en_score_col = 'colName'
    runner.ontology_graph_format = 'png'
    runner._dag_plot_for_namespace('biological_process', 'title', 'ylabel', 50)
