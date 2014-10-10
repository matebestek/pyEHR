import json
import numpy as np
import itertools as it
from random import randint

import archetype_builder

from pyehr.ehr.services.dbmanager.dbservices.wrappers import ArchetypeInstance
from archetype_builder import Composition


def get_composition_label(labels):
    return 'composition.%s' % labels[randint(0, len(labels) - 1)]


def get_random_subtree(max_depth, max_width, composition_labels):
    if max_depth == 0:
        leafs = [a for a in archetype_builder.BUILDERS.keys() if a != 'composition']
        children = [leafs[x] for x in np.random.randint(0, len(leafs), max_width)]
    else:
        # always go deeper with the first child node in order to achieve max_depth in at least one case
        children = [{get_composition_label(composition_labels):
                         get_random_subtree(max_depth-1, randint(1, max_width),
                                            composition_labels)}]
        for i in xrange(max_width-1):
            nodes = archetype_builder.BUILDERS.keys()
            ch = nodes[randint(0, len(archetype_builder.BUILDERS)-1)]
            if ch.startswith('composition'):
                ch = {get_composition_label(composition_labels):
                          get_random_subtree(max_depth-1, randint(1, max_width),
                                             composition_labels)}
            children.append(ch)
    return children


def build_structure(max_depth, max_width, labels):
    return {get_composition_label(labels): get_random_subtree(max_depth-1, max_width, labels)}


def build_structures(json_output_file, structures_count, mean_depth, max_width):
    structures = []
    labels = get_labels()
    for depth, width in it.izip([int(i) for i in np.random.normal(mean_depth, 1, structures_count)],
                                [int(i) for i in np.random.uniform(1, max_width, structures_count)]):
        if depth < 1:
            depth = 1
        elif depth > mean_depth + (mean_depth-1):
            depth = mean_depth + (mean_depth-1)
        structures.append(build_structure(depth, width, labels))
    with open(json_output_file, 'w') as f:
        f.write(json.dumps(structures))


def build_record(record_description, archetypes_dir, match, record_to_match=None):
    if isinstance(record_description, dict):
        for k, v in record_description.iteritems():
            if not k.startswith('composition'):
                raise ValueError('Container type %s unknown' % k)
            children = [build_record(x, archetypes_dir, match, record_to_match) for x in v]
            composition_label = k.split('.')[1]
            return ArchetypeInstance(*archetype_builder.BUILDERS['composition'](archetypes_dir, children,
                                                                                composition_label).build())
    else:
        kw = {}
        if record_description == 'blood_pressure':
            if match and record_to_match == 'blood_pressure':
                kw.update({'systolic': randint(121, 130), 'dyastolic': randint(80, 90)})
            else:
                kw.update({'systolic': randint(100, 105), 'dyastolic': randint(60, 75)})
        elif record_description == 'urin_analysis':
            if match and record_to_match == 'urin_analysis':
                kw.update({'glucose': 'at0120', 'protein': 'at0101'})
            else:
                glucose_values = ['at0115', 'at0116', 'at0117', 'at0118', 'at0119']
                protein_values = ['at0096', 'at0097', 'at0098', 'at0099', 'at0100']
                kw.update({
                    'glucose': glucose_values[randint(0, len(glucose_values)-1)],
                    'protein': protein_values[randint(0, len(protein_values)-1)]
                })
        return ArchetypeInstance(*archetype_builder.BUILDERS[record_description](archetypes_dir, **kw).build())


def contains_archetype(structure_description, archetype_label):
    element_label = archetype_label[0]
    if isinstance(structure_description, dict):
        for k, v in structure_description.iteritems():
            if not k.startswith('composition'):
                raise ValueError('Container type %s unknown' % k)
            if k == element_label:
                to_be_checked = archetype_label[1:]
            else:
                to_be_checked = archetype_label
            for child in v:
                matched, leaf = contains_archetype(child, to_be_checked)
                if matched:
                    return True, leaf
    else:
        if structure_description == element_label:
            return True, element_label
    return False, None


def get_labels(labels_set_size=20):
    return ['lbl-%05d' % x for x in xrange(0, labels_set_size)]


def _build_record_full_random(max_width, height, archetypes_dir):
    def _get_random_builder(_builders):
        builder_idx = randint(0, len(_builders)-1)
        cls = archetype_builder.get_builder( _builders[builder_idx] )
        return cls

    if height < 1:
        raise ValueError('Height must be greater than 0')

    builders = archetype_builder.BUILDERS.keys()

    if height == 1: # if height is zero it creates a leaf archetype (i.e an Observation)
        # deletes the composition from the possible builders
        leaf_builders = [b for b in builders if b != 'composition']
        children = []
        for i in xrange(max_width):
            cls = _get_random_builder(leaf_builders)
            arch = ArchetypeInstance( *cls(archetypes_dir).build() )
            children.append(arch)

    else:
        width = randint(1, max_width)
        arch = _build_record_full_random(width, height - 1, archetypes_dir)
        children = [arch]

        # creates the other children. They can be Composition or Observation
        for i in xrange(max_width - 1):
            cls = _get_random_builder(builders)
            if cls == Composition:
                width = randint(1, max_width)
                arch = _build_record_full_random(width, height - 1, archetypes_dir)
            else:
                arch = ArchetypeInstance( *cls(archetypes_dir).build() )
            children.append(arch)

    return ArchetypeInstance(*Composition(archetypes_dir, children).build())