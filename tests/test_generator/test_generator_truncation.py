from os.path import join

import pandas as pd
import pandas.testing as pdt

from gaiaxpy import load_additional_systems, remove_additional_systems
from gaiaxpy.generator.generator import _generate
from tests.files.paths import files_path, c04_trunc_input

# Solution
data = {
    "source_id": [152978866705760640, 201160668826278016, 391555027165505152, 486951645284929920, 627751389191309568,
                  651991158115411200, 714711768130180736, 1889737648342773504, 2006813612112026240, 2203440857061753600,
                  2254098999877596160, 2608189641492933248, 2646861007335777152, 2837684587525919872,
                  2869998959388645888, 2910914845074190592, 3537850873379048704, 3731840462941245824,
                  3739662590525303552, 4635905927421101824, 4674906017177476480, 5284312016205282432,
                  5354888400585719936, 5404851274113345792, 5448054040886794368, 5631016795835504384,
                  6192032978886326912, 6214255728090340992, 6732876529476328192, 6775363243618987904],
    "synth_bp": [16.02474605927837, 7896844.30529891, 361076.47710989055, 5.487285793827075, 543568.0424974755,
                 5716.714239392889, 991.2983571055354, 3769525.7444547303, 2483993.4310260955, 145621.4316548542,
                 1249648.2968451553, 502796.92222208204, 12971.477542229566, 4521.115724682713, 1638018.9006144507,
                 88854.13523893339, 10599411.31725928, 161246.15980400416, 271948.6949846586, 8355482.3568904465,
                 38171299.44954957, 949426.9647771989, 32205.441202248378, 25540560.91422463, 1010200.2021410404,
                 5102645.831917911, 257.2431616318339, 1041357.1881351518, 1695742.1799273137, 75213.32510236598],
    "synth_trunc_bp": [68.50420887668125, 2158183.511208343, 630364.244421662, 44.81253156467705, -514542.29357598483,
                       10302.537854110997, 273.2715297507185, 917717.7864358134, 1024085.959254284, 630221.9138859881,
                       421947.4138963691, 485375.9782026344, 652.6243209749639, -3730.2379609737186, 174233.51038099866,
                       258996.68865060704, -119011.588226464, 136629.50882351032, -43704.64248228084,
                       -3321602.9867904885, 345335878.38335305, 318346.95656676363, 3490.445886371083,
                       -4589695.036995165, -8651.586456676501, 4894373.058824644, 249.97606209097893, 939312.9040850125,
                       17611290.115720753, 5692.020619987301]
}
solution = pd.DataFrame(data)


def test_truncation():
    _PhotometricSystem = remove_additional_systems()
    _PhotometricSystem = load_additional_systems(join(files_path, 'generator_truncation'))

    no_trunc = _generate(c04_trunc_input, photometric_system=_PhotometricSystem.USER_GaiaC4Eps, truncation=False,
                         save_file=False)
    trunc = _generate(c04_trunc_input, photometric_system=_PhotometricSystem.USER_GaiaC4Eps, truncation=True,
                      save_file=False)

    columns_to_keep = ['source_id', 'USER_GaiaC4Eps_flux_BP']

    no_trunc = no_trunc[columns_to_keep].sort_values(by=['source_id'], ignore_index=True).rename(
        columns={'USER_GaiaC4Eps_flux_BP': 'synth_bp'})
    trunc = trunc[columns_to_keep].sort_values(by=['source_id'], ignore_index=True).rename(
        columns={'USER_GaiaC4Eps_flux_BP': 'synth_trunc_bp'})

    merged_df = pd.merge(no_trunc, trunc, on='source_id', how='inner')
    pdt.assert_frame_equal(merged_df, solution, check_dtype=False)

    _PhotometricSystem = remove_additional_systems()
