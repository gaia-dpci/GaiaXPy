import xml.etree.ElementTree as et

import numpy as np


def get_file_root(xml_file):
    return et.parse(xml_file).getroot()


def iterative_find(x_root, tag_list):
    def find_in_root(_x_root, _tag):
        return _x_root.find(_tag)

    result = find_in_root(x_root, tag_list[0])
    for tag in tag_list[1:]:
        result = find_in_root(result, tag)
    return result


def parse_array(x_root, tag):
    values, _ = get_array_text(x_root, tag)
    return np.array([float(element) for element in values])


def get_xp_merge(x_root):
    output = []
    tags = ['sampleMeanWavelengths', 'bpWeights', 'rpWeights']
    for tag in tags:
        xp_merge_array = iterative_find(x_root, ['XpMerge', tag])
        xp_merge_array = np.array([float(element.text) for element in xp_merge_array])
        output.append(xp_merge_array)
    return tuple(output)


def get_array_text(x_root, tag):
    result = x_root.find(tag)
    result = [element.text for element in result] if result else None
    length = len(result) if result else None
    return result, length


def get_xp_sampling_matrix(x_root, xp, n_bands):
    xp_config = iterative_find(x_root, ['XpSampling', f'{xp.lower()}SampledBases'])
    xp_dimension = int(xp_config.attrib['dimension'])
    xp_sampling = np.array([float(element.text) for element in xp_config])
    if not n_bands:
        # TODO: A bit too custom, could be improved adding a variable to the filter files.
        n_bands = len(xp_sampling) // xp_dimension
    xp_sampling = xp_sampling.reshape(n_bands, xp_dimension)
    return np.transpose(xp_sampling)
