import xml.etree.ElementTree as et

import numpy as np


def get_file_root(xml_file):
    xtree = et.parse(xml_file)
    return xtree.getroot()


def iterative_find(x_root, tag_list):
    def find_in_root(_x_root, tag):
        return _x_root.find(tag)

    result = find_in_root(x_root, tag_list[0])
    for tag in tag_list[1:]:
        result = find_in_root(result, tag)
    return result


def get_xp_sampling_matrix(x_root, xp, nbands):
    xpConfig = iterative_find(x_root, ['XpSampling', f'{xp.lower()}SampledBases'])
    xpDimension = int(xpConfig.attrib['dimension'])
    xpSampling = np.array([float(element.text) for element in xpConfig]).reshape(xpDimension, nbands)
    return xpSampling


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


def get_xp_sampling_matrix(x_root, xp, nbands):
    xpConfig = iterative_find(x_root, ['XpSampling', f'{xp.lower()}SampledBases'])
    xpDimension = int(xpConfig.attrib['dimension'])
    xpSampling = np.array([float(element.text) for element in xpConfig])
    if not nbands:
        # TODO: A bit too custom, could be improved adding a variable to the filter files.
        nbands = len(xpSampling) // xpDimension
    xpSampling = xpSampling.reshape(nbands, xpDimension)
    return np.transpose(xpSampling)
