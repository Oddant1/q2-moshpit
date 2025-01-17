# ----------------------------------------------------------------------------
# Copyright (c) 2023-2023, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import shutil
import tempfile

import pandas as pd
import pandas.testing
from pandas._testing import assert_frame_equal
import skbio
from q2_moshpit.kraken2 import kraken2_to_features  # , kraken2_to_mag_features
from q2_moshpit.kraken2.select import _kraken_to_ncbi_tree, _find_lcas
from qiime2.plugin.testing import TestPluginBase

from q2_types_genomics.kraken2 import (
    Kraken2ReportDirectoryFormat,  # Kraken2OutputDirectoryFormat,
)


class MockTempDir(tempfile.TemporaryDirectory):
    pass


class TestKrakenSelect(TestPluginBase):
    package = "q2_moshpit.kraken2.tests"

    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()

        fp = self.get_data_path(
            "kraken2-reports-select/kraken2_reads_table.json"
        )
        self.kraken2_reads_table = pd.read_json(fp)
        self.kraken2_reads_table.columns = [
            str(x) for x in self.kraken2_reads_table.columns
        ]

        fp = self.get_data_path(
            "kraken2-reports-select/kraken2_reads_table_filtered.json"
        )
        self.kraken2_reads_table_filtered = pd.read_json(fp)
        self.kraken2_reads_table_filtered.columns = [
            str(x) for x in self.kraken2_reads_table_filtered.columns
        ]

        fp = self.get_data_path(
            "kraken2-reports-select/kraken2_taxonomy.tsv"
        )
        self.kraken_taxonomy = pd.read_csv(
            fp, sep='\t', header=0,
            dtype={"Feature ID": "object", "Taxon": str})
        self.kraken_taxonomy.set_index("Feature ID", inplace=True)

        fp = self.get_data_path(
            "kraken2-reports-select/kraken2_taxonomy_filtered.tsv"
        )
        self.kraken_taxonomy_filtered = pd.read_csv(
            fp, sep='\t', header=0,
            dtype={"Feature ID": "object", "Taxon": str})
        self.kraken_taxonomy_filtered.set_index("Feature ID", inplace=True)

        self.taxa_mag1 = pd.read_csv(
            self.get_data_path('mag-taxa-1.csv'), index_col=0
        )
        self.taxa_mag2 = pd.read_csv(
            self.get_data_path('mag-taxa-2.csv'), index_col=0
        )
        self.taxa_mag3 = pd.read_csv(
            self.get_data_path('mag-taxa-3.csv'), index_col=0
        )
        self.taxa_mag4 = pd.read_csv(
            self.get_data_path('mag-taxa-4.csv'), index_col=0
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_kraken2_to_features_coverage_threshold(self):
        reports = Kraken2ReportDirectoryFormat(
            self.get_data_path("kraken2-reports-select/samples"), "r"
        )
        obs_table, obs_taxonomy = kraken2_to_features(
            reports, coverage_threshold=0.1)

        assert_frame_equal(obs_table, self.kraken2_reads_table_filtered)
        assert_frame_equal(obs_taxonomy, self.kraken_taxonomy_filtered)

    def test_kraken2_to_features_no_coverage_threshold(self):
        reports = Kraken2ReportDirectoryFormat(
            self.get_data_path("kraken2-reports-select/samples"), "r"
        )
        obs_table, obs_taxonomy = kraken2_to_features(reports, 0.0)

        assert_frame_equal(obs_table, self.kraken2_reads_table)
        assert_frame_equal(obs_taxonomy, self.kraken_taxonomy)

    def test_kraken_to_ncbi_tree(self):
        reports = Kraken2ReportDirectoryFormat(
            self.get_data_path("kraken2-to-ncbi-tree/example1"), "r"
        )
        reports = list(reports.reports.iter_views(pd.DataFrame))
        report_df = reports[0][1]

        exp_tree_fp = self.get_data_path("kraken2-to-ncbi-tree/exp-tree1.txt")
        exp_tree = skbio.TreeNode.read(exp_tree_fp)

        obs_tree = _kraken_to_ncbi_tree(report_df)

        # skbio.TreeNode doesn't define an equality operator, so performing
        # this test on newick strings (which is probably fragile)
        self.assertEqual(str(obs_tree), str(exp_tree))

        raise NotImplementedError('Additional tests needed.')

    # The following test is currently failing b/c the format is looking
    # for file names that don't exist in the `outputs-mags` directory. It's
    # looking for `outputs-mags/sample1/sample1.output.txt`, but the file
    # that is present is `outputs-mags/sample1/bin1.output.txt`. This
    # will be addressed as part of the changes discussed under
    # https://github.com/bokulich-lab/q2-moshpit/discussions/45
    # def test_kraken2_to_mag_features_default(self):
    #     reports = Kraken2ReportDirectoryFormat(
    #         self.get_data_path("reports-mags"), "r"
    #     )
    #     hits = Kraken2OutputDirectoryFormat(
    #         self.get_data_path("outputs-mags"), "r"
    #     )
    #     obs_table, obs_taxonomy = kraken2_to_mag_features(
    #         reports, hits, 0.0
    #     )

    def test_find_lcas_mode_lca(self):
        taxa = [self.taxa_mag1, self.taxa_mag2, self.taxa_mag3, self.taxa_mag4]
        obs = _find_lcas(taxa, mode='lca')
        exp = pd.DataFrame.from_dict({
            '0e514d88-16c4-4273-a1df-1a360eb2c823': [
                'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
                'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium'
            ],
            '3acec411-b0d0-4441-b936-5b8b571fa328': [
                'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
                'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium'
            ],
            '3af39f47-e90a-46f2-9b5f-b236ae6551f0': [
                'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
                'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium'
            ],
            'fed92059-3222-4573-b0ec-726c49fbfabb': [
                'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
                'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium;'
                's__Mycobacterium florentinum'
            ]
        }, orient='index')
        exp.columns = ['Taxon']
        exp.index.name = 'Feature ID'
        pandas.testing.assert_frame_equal(obs, exp)

    # def test_find_lcas_mode_majority(self):
    #     taxa = [
    #       self.taxa_mag1, self.taxa_mag2, self.taxa_mag3, self.taxa_mag4
    #     ]
    #     obs = _find_lcas(taxa, mode='majority')
    #     exp = pd.DataFrame.from_dict({
    #         '0e514d88-16c4-4273-a1df-1a360eb2c823': [
    #             'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
    #             'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium,'
    #             's__Mycobacterium avium;'
    #             'ssp__Mycobacterium avium subsp. hominissuis'
    #         ],
    #         '3acec411-b0d0-4441-b936-5b8b571fa328': [
    #             'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
    #             'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium;'
    #             's__Mycobacterium florentinum'
    #         ],
    #         '3af39f47-e90a-46f2-9b5f-b236ae6551f0': [
    #             'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
    #             'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium;'
    #             's__Mycobacterium avium;'
    #             'ssp__Mycobacterium avium subsp. hominissuis'
    #         ],
    #         'fed92059-3222-4573-b0ec-726c49fbfabb': [
    #             'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
    #             'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium;'
    #             's__Mycobacterium florentinum'
    #         ]
    #     }, orient='index')
    #     exp.columns = ['Taxon']
    #     exp.index.name = 'Feature ID'
    #     pandas.testing.assert_frame_equal(obs, exp)
    #
    # def test_find_lcas_mode_majority_terminal_none(self):
    #     taxa = [self.taxa_mag2, self.taxa_mag4]
    #     obs = _find_lcas(taxa, mode='majority')
    #     exp = pd.DataFrame.from_dict({
    #         '3acec411-b0d0-4441-b936-5b8b571fa328': [
    #             'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
    #             'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium;'
    #             's__Mycobacterium florentinum'
    #         ],
    #         'fed92059-3222-4573-b0ec-726c49fbfabb': [
    #             'd__Bacteria;k__Bacteria;p__Actinomycetota;c__Actinomycetes;'
    #             'o__Mycobacteriales;f__Mycobacteriaceae;g__Mycobacterium;'
    #             's__Mycobacterium florentinum'
    #         ]
    #     }, orient='index')
    #     exp.columns = ['Taxon']
    #     exp.index.name = 'Feature ID'
    #     pandas.testing.assert_frame_equal(obs, exp)
